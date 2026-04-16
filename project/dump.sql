-- Vytvoření staging tabulky pro import z CSV (s správnými datovými typy)
CREATE TABLE staging_bmw (
    model VARCHAR(100) NOT NULL,
    year BIGINT NOT NULL,
    price BIGINT NOT NULL,
    transmission VARCHAR(50) NOT NULL,
    mileage BIGINT NOT NULL,
    fuelType VARCHAR(50) NOT NULL,
    tax BIGINT NOT NULL,
    mpg DOUBLE PRECISION NOT NULL,
    engineSize DOUBLE PRECISION NOT NULL
);

-- Import dat z CSV (cesta upravit podle prostředí)
COPY staging_bmw (
    model,
    year,
    price,
    transmission,
    mileage,
    fuelType,
    tax,
    mpg,
    engineSize
)
FROM
    'C:\GitHub\OLAP-a-DM\project\bmw.csv'
WITH
    (FORMAT csv, HEADER TRUE, DELIMITER ',');

-- ============================================================================
-- OLAP SNOWFLAKE SCHÉMA S 5 DIMENZEMI
-- ============================================================================
-- Dimenze Model (24 hodnot)
CREATE TABLE Dim_Model (
    model_id SERIAL PRIMARY KEY,
    model VARCHAR(100) NOT NULL UNIQUE
);

INSERT INTO
    Dim_Model (model)
SELECT DISTINCT
    model
FROM
    staging_bmw
ORDER BY
    model;

-- Dimenze Year + Decade (25 roků: 1996-2020)
CREATE TABLE Dim_Time (
    time_id SERIAL PRIMARY KEY,
    year BIGINT NOT NULL UNIQUE,
    decade BIGINT NOT NULL
);

INSERT INTO
    Dim_Time (year, decade)
SELECT DISTINCT
    year,
    (year / 10) * 10 AS decade
FROM
    staging_bmw
ORDER BY
    year;

-- Dimenze Version (933 uniq kombinací: model + year + engineSize + fuelType + transmission)
CREATE TABLE Dim_Version (
    version_id SERIAL PRIMARY KEY,
    model_id INT NOT NULL REFERENCES Dim_Model (model_id),
    time_id INT NOT NULL REFERENCES Dim_Time (time_id),
    engineSize DOUBLE PRECISION NOT NULL,
    fuelType VARCHAR(50) NOT NULL,
    transmission VARCHAR(50) NOT NULL,
    UNIQUE (
        model_id,
        time_id,
        engineSize,
        fuelType,
        transmission
    )
);

INSERT INTO
    Dim_Version (
        model_id,
        time_id,
        engineSize,
        fuelType,
        transmission
    )
SELECT DISTINCT
    m.model_id,
    t.time_id,
    s.engineSize,
    s.fuelType,
    s.transmission
FROM
    (
        SELECT DISTINCT
            model,
            year,
            engineSize,
            fuelType,
            transmission
        FROM
            staging_bmw
    ) s
    JOIN Dim_Model m ON s.model = m.model
    JOIN Dim_Time t ON s.year = t.year
ORDER BY
    m.model_id,
    t.time_id;

-- Faktová tabulka (10 781 prodejů)
CREATE TABLE Fact_Sales (
    sale_id SERIAL PRIMARY KEY,
    version_id INT NOT NULL REFERENCES Dim_Version (version_id),
    price BIGINT NOT NULL,
    tax BIGINT NOT NULL,
    mileage BIGINT NOT NULL,
    mpg DOUBLE PRECISION NOT NULL
);

-- Naplnění faktové tabulky
INSERT INTO
    Fact_Sales (version_id, price, tax, mileage, mpg)
SELECT
    v.version_id,
    s.price,
    s.tax,
    s.mileage,
    s.mpg
FROM
    staging_bmw s
    JOIN Dim_Model m ON s.model = m.model
    JOIN Dim_Time t ON s.year = t.year
    JOIN Dim_Version v ON v.model_id = m.model_id
    AND v.time_id = t.time_id
    AND v.engineSize = s.engineSize
    AND v.fuelType = s.fuelType
    AND v.transmission = s.transmission;

-- Čištění staging tabulky
DROP TABLE staging_bmw;

-- ============================================================================
-- POSTGRES OLAP: CUBE/ROLLUP AGREGACE
-- ============================================================================
-- 1. CUBE - Všechny kombinace dimenzí (model, year, engineSize, fuelType, transmission)
-- Vytvoří SUBTOTÁLY pro každou kombinaci včetně GRAND TOTAL
CREATE TABLE olap_cube_5d AS
SELECT
    m.model,
    t.year,
    v.engineSize,
    v.fuelType,
    v.transmission,
    COUNT(*) AS sales_count,
    AVG(f.price) AS avg_price,
    MIN(f.price) AS min_price,
    MAX(f.price) AS max_price,
    SUM(f.price) AS total_price,
    AVG(f.mileage) AS avg_mileage,
    AVG(f.mpg) AS avg_mpg,
    AVG(f.tax) AS avg_tax
FROM
    Fact_Sales f
    JOIN Dim_Version v ON f.version_id = v.version_id
    JOIN Dim_Model m ON v.model_id = m.model_id
    JOIN Dim_Time t ON v.time_id = t.time_id
GROUP BY
    m.model,
    t.year,
    v.engineSize,
    v.fuelType,
    v.transmission
ORDER BY
    m.model,
    t.year,
    v.engineSize,
    v.fuelType,
    v.transmission;

CREATE INDEX idx_olap_cube_5d ON olap_cube_5d (model, year, engineSize, fuelType, transmission);

-- 2. ROLLUP - Hierarchická agregace (model → year → engineSize → fuelType → transmission)
-- Vytvoří agregace na každé úrovni hierarchie
CREATE TABLE olap_rollup_hierarchy AS
SELECT
    m.model,
    t.year,
    v.engineSize,
    v.fuelType,
    v.transmission,
    COUNT(*) AS sales_count,
    AVG(f.price) AS avg_price,
    MIN(f.price) AS min_price,
    MAX(f.price) AS max_price,
    SUM(f.price) AS total_price,
    AVG(f.mileage) AS avg_mileage,
    AVG(f.mpg) AS avg_mpg,
    AVG(f.tax) AS avg_tax
FROM
    Fact_Sales f
    JOIN Dim_Version v ON f.version_id = v.version_id
    JOIN Dim_Model m ON v.model_id = m.model_id
    JOIN Dim_Time t ON v.time_id = t.time_id
GROUP BY
    ROLLUP (
        m.model,
        t.year,
        v.engineSize,
        v.fuelType,
        v.transmission
    )
ORDER BY
    m.model,
    t.year,
    v.engineSize,
    v.fuelType,
    v.transmission;

CREATE INDEX idx_olap_rollup ON olap_rollup_hierarchy (model, year, engineSize, fuelType, transmission);

-- 3. Hierarchická agregace: Model → Year → Decade
-- Ukazuje trend cen po dekádě a roce
CREATE MATERIALIZED VIEW olap_time_hierarchy AS
SELECT
    m.model,
    t.decade,
    t.year,
    COUNT(*) AS sales_count,
    AVG(f.price) AS avg_price,
    MIN(f.price) AS min_price,
    MAX(f.price) AS max_price,
    STDDEV(f.price) AS stddev_price
FROM
    Fact_Sales f
    JOIN Dim_Version v ON f.version_id = v.version_id
    JOIN Dim_Model m ON v.model_id = m.model_id
    JOIN Dim_Time t ON v.time_id = t.time_id
GROUP BY
    m.model,
    t.decade,
    t.year
ORDER BY
    m.model,
    t.decade DESC,
    t.year DESC;

CREATE INDEX idx_olap_time ON olap_time_hierarchy (model, decade, year);

-- ============================================================================
-- PŘÍKLADY OLAP DOTAZŮ (Slicing & Dicing)
-- ============================================================================
-- SLICE 1: Ceny v jednom roce (2017)
-- SELECT model, engineSize, fuelType, transmission, avg_price, sales_count
-- FROM olap_cube_5d
-- WHERE year = 2017 AND model IS NOT NULL AND engineSize IS NOT NULL
-- ORDER BY avg_price DESC;
-- SLICE 2: Diesel auta v konkrétní dekádě (2010s)
-- SELECT model, year, avg_price, sales_count
-- FROM olap_time_hierarchy
-- WHERE decade = 2010
-- ORDER BY avg_price DESC;
-- DICE: Top 10 nejdražších kombinací (model + engine + fuel + transmission)
-- SELECT model, year, engineSize, fuelType, transmission, avg_price, sales_count
-- FROM olap_cube_5d
-- WHERE model IS NOT NULL AND year IS NOT NULL AND engineSize IS NOT NULL
--   AND fuelType IS NOT NULL AND transmission IS NOT NULL
-- ORDER BY avg_price DESC LIMIT 10;
-- DRILL DOWN: Od agregace (jen modely) až k detailu (vše)
-- Level 1: Průměr po modelech
-- SELECT model, AVG(avg_price) as model_avg_price
-- FROM olap_cube_5d
-- WHERE model IS NOT NULL GROUP BY model ORDER BY model;
-- Level 2: Průměr po modelech a rocích
-- SELECT model, year, AVG(avg_price) as year_avg_price
-- FROM olap_cube_5d
-- WHERE model IS NOT NULL AND year IS NOT NULL
-- GROUP BY model, year ORDER BY model, year;
-- Level 3: Detail - vše včetně engineSize
-- SELECT model, year, engineSize, avg_price, sales_count
-- FROM olap_cube_5d
-- WHERE model IS NOT NULL AND year IS NOT NULL AND engineSize IS NOT NULL
-- ORDER BY model, year, engineSize;
-- TREND: Jak se vyvíjí ceny v čase
-- SELECT model, decade, year, avg_price, sales_count
-- FROM olap_time_hierarchy
-- WHERE model = '5 Series' AND model IS NOT NULL AND year IS NOT NULL
-- ORDER BY decade DESC, year DESC;
-- BENCHMARK: Porovnání modelů v jednom roce
-- SELECT model, year, avg_price, sales_count
-- FROM olap_cube_5d
-- WHERE year = 2017 AND model IS NOT NULL
--   AND engineSize IS NULL AND fuelType IS NULL AND transmission IS NULL
-- ORDER BY avg_price DESC;