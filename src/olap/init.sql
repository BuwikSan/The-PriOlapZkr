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