-- ============================================
-- DIMENSION TABLES (stejné v obou DB)
-- ============================================

-- DIMENSIONS (nezávislé, jednotlivé filtry)
CREATE TABLE dim_model (
    model_id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE dim_fuel_type (
    fuel_type_id SERIAL PRIMARY KEY,
    fuel_type_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE dim_transmission (
    transmission_id SERIAL PRIMARY KEY,
    transmission_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE dim_engine (
    engine_id SERIAL PRIMARY KEY,
    engine_size DECIMAL(5,2) NOT NULL UNIQUE
);

-- 2. DIM_TIME (25 let výroby)
CREATE TABLE dim_time (
    time_id SERIAL PRIMARY KEY,
    production_year INTEGER NOT NULL UNIQUE,
    decade INTEGER NOT NULL,  -- pro hierarchické agregace (1990, 2000, 2010, 2020)
);



-- ============================================
-- FACT TABLE (10,781 záznamů)
-- ============================================

CREATE TABLE fact_sales (
    sale_id SERIAL PRIMARY KEY,
    model_id INTEGER NOT NULL REFERENCES dim_model(model_id),
    time_id INTEGER NOT NULL REFERENCES dim_time(time_id),
    fuel_type_id INTEGER NOT NULL REFERENCES dim_fuel_type(fuel_type_id),
    transmission_id INTEGER NOT NULL REFERENCES dim_transmission(transmission_id),
    engine_id INTEGER NOT NULL REFERENCES dim_engine(engine_id),
    price INTEGER NOT NULL,   -- pounds
    tax INTEGER NOT NULL,     -- pounds
    mileage INTEGER NOT NULL, -- miles
    mpg DECIMAL(5,2) NOT NULL -- MPG
);

-- ============================================
-- INDEXY (pro performance)
-- ============================================

CREATE INDEX idx_fact_model ON fact_sales(model_id);
CREATE INDEX idx_fact_time ON fact_sales(time_id);
CREATE INDEX idx_fact_fuel ON fact_sales(fuel_type_id);
CREATE INDEX idx_fact_transmission ON fact_sales(transmission_id);
CREATE INDEX idx_fact_engine ON fact_sales(engine_id);
CREATE INDEX idx_fact_price ON fact_sales(price);