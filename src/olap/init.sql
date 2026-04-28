-- BMW Sales OLAP Database Initialization
-- Creates star schema with dimensions and facts
-- ============================================
-- DIMENSION TABLES
-- ============================================
-- DIM_MODEL: BMW vehicle models
CREATE TABLE IF NOT EXISTS dim_model (
    model_id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL UNIQUE
);

-- DIM_FUEL_TYPE: Fuel types
CREATE TABLE IF NOT EXISTS dim_fuel_type (
    fuel_type_id SERIAL PRIMARY KEY,
    fuel_type_name VARCHAR(50) NOT NULL UNIQUE
);

-- DIM_TRANSMISSION: Transmission types
CREATE TABLE IF NOT EXISTS dim_transmission (
    transmission_id SERIAL PRIMARY KEY,
    transmission_name VARCHAR(50) NOT NULL UNIQUE
);

-- DIM_ENGINE: Engine sizes
CREATE TABLE IF NOT EXISTS dim_engine (
    engine_id SERIAL PRIMARY KEY,
    engine_size DECIMAL(5, 2) NOT NULL UNIQUE
);

-- DIM_TIME: Time dimension (1994-2020)
CREATE TABLE IF NOT EXISTS dim_time (
    time_id SERIAL PRIMARY KEY,
    production_year INTEGER NOT NULL UNIQUE,
    decade INTEGER NOT NULL
);

-- ============================================
-- FACT TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS fact_sales (
    sale_id SERIAL PRIMARY KEY,
    model_id INTEGER NOT NULL REFERENCES dim_model (model_id),
    time_id INTEGER NOT NULL REFERENCES dim_time (time_id),
    fuel_type_id INTEGER NOT NULL REFERENCES dim_fuel_type (fuel_type_id),
    transmission_id INTEGER NOT NULL REFERENCES dim_transmission (transmission_id),
    engine_id INTEGER NOT NULL REFERENCES dim_engine (engine_id),
    price INTEGER NOT NULL,
    tax INTEGER NOT NULL,
    mileage INTEGER NOT NULL,
    mpg DECIMAL(5, 2) NOT NULL
);

-- ============================================
-- INDEXES (Performance optimization)
-- ============================================
CREATE INDEX IF NOT EXISTS idx_fact_model ON fact_sales (model_id);

CREATE INDEX IF NOT EXISTS idx_fact_time ON fact_sales (time_id);

CREATE INDEX IF NOT EXISTS idx_fact_fuel ON fact_sales (fuel_type_id);

CREATE INDEX IF NOT EXISTS idx_fact_transmission ON fact_sales (transmission_id);

CREATE INDEX IF NOT EXISTS idx_fact_engine ON fact_sales (engine_id);

CREATE INDEX IF NOT EXISTS idx_fact_price ON fact_sales (price);

-- ============================================
-- SAMPLE DATA (for testing)
-- ============================================
-- Insert fuel types
INSERT INTO
    dim_fuel_type (fuel_type_name)
VALUES
    ('Petrol'),
    ('Diesel'),
    ('Hybrid'),
    ('Electric')
ON CONFLICT (fuel_type_name) DO NOTHING;

-- Insert transmission types
INSERT INTO
    dim_transmission (transmission_name)
VALUES
    ('Manual'),
    ('Automatic'),
    ('CVT'),
    ('Semi-Automatic')
ON CONFLICT (transmission_name) DO NOTHING;

-- Insert engine sizes
INSERT INTO
    dim_engine (engine_size)
VALUES
    (1.5),
    (1.6),
    (1.8),
    (2.0),
    (2.5),
    (3.0),
    (3.5),
    (4.0),
    (4.4),
    (5.0)
ON CONFLICT (engine_size) DO NOTHING;

-- Insert time dimension (1994-2020)
INSERT INTO
    dim_time (production_year, decade)
VALUES
    (1994, 1990),
    (1995, 1990),
    (1996, 1990),
    (1997, 1990),
    (1998, 1990),
    (1999, 1990),
    (2000, 2000),
    (2001, 2000),
    (2002, 2000),
    (2003, 2000),
    (2004, 2000),
    (2005, 2000),
    (2006, 2000),
    (2007, 2000),
    (2008, 2000),
    (2009, 2000),
    (2010, 2010),
    (2011, 2010),
    (2012, 2010),
    (2013, 2010),
    (2014, 2010),
    (2015, 2010),
    (2016, 2010),
    (2017, 2010),
    (2018, 2010),
    (2019, 2010),
    (2020, 2010)
ON CONFLICT (production_year) DO NOTHING;

-- Insert popular BMW models
INSERT INTO
    dim_model (model_name)
VALUES
    ('3 Series'),
    ('5 Series'),
    ('7 Series'),
    ('X1'),
    ('X3'),
    ('X5'),
    ('X7'),
    ('M3'),
    ('M4'),
    ('M5'),
    ('M550i'),
    ('Z4'),
    ('i3'),
    ('i8'),
    ('X4'),
    ('X6')
ON CONFLICT (model_name) DO NOTHING;