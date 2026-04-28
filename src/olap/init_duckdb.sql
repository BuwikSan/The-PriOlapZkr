-- BMW Sales OLAP Database - DuckDB Schema
-- Note: DuckDB doesn't use SERIAL, uses CAST for auto-increment behavior
-- DIMENSION TABLES
CREATE TABLE dim_model (
    model_id INTEGER PRIMARY KEY,
    model_name VARCHAR NOT NULL UNIQUE
);

CREATE TABLE dim_fuel_type (
    fuel_type_id INTEGER PRIMARY KEY,
    fuel_type_name VARCHAR NOT NULL UNIQUE
);

CREATE TABLE dim_transmission (
    transmission_id INTEGER PRIMARY KEY,
    transmission_name VARCHAR NOT NULL UNIQUE
);

CREATE TABLE dim_engine (
    engine_id INTEGER PRIMARY KEY,
    engine_size DECIMAL(5, 2) NOT NULL UNIQUE
);

CREATE TABLE dim_time (
    time_id INTEGER PRIMARY KEY,
    production_year INTEGER NOT NULL UNIQUE,
    decade INTEGER NOT NULL
);

-- FACT TABLE
CREATE TABLE fact_sales (
    sale_id INTEGER PRIMARY KEY,
    model_id INTEGER NOT NULL,
    time_id INTEGER NOT NULL,
    fuel_type_id INTEGER NOT NULL,
    transmission_id INTEGER NOT NULL,
    engine_id INTEGER NOT NULL,
    price INTEGER NOT NULL,
    tax INTEGER NOT NULL,
    mileage INTEGER NOT NULL,
    mpg DECIMAL(5, 2) NOT NULL
);

CREATE INDEX idx_fact_model ON fact_sales (model_id);

CREATE INDEX idx_fact_time ON fact_sales (time_id);

CREATE INDEX idx_fact_fuel ON fact_sales (fuel_type_id);

CREATE INDEX idx_fact_trans ON fact_sales (transmission_id);

CREATE INDEX idx_fact_engine ON fact_sales (engine_id);

CREATE INDEX idx_fact_price ON fact_sales (price);