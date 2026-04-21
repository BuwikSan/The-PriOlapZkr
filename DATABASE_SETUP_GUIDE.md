# Database Setup & OLAP Configuration Guide

**Purpose**: Complete reference for BMW OLAP implementation with PostgreSQL (ROLAP) vs DuckDB (Columnar).  
**Audience**: Developers implementing Phase 3+ (schema setup, data loading, OLAP queries)  
**Data Source**: BMW sales dataset (bmw.csv) - 10,781 records with production year metadata

---

## Table of Contents
1. [Overview](#overview)
2. [Star Schema Design](#star-schema-design)
3. [PostgreSQL Configuration](#postgresql-configuration)
4. [DuckDB Configuration](#duckdb-configuration)
5. [Data Loading Pipeline](#data-loading-pipeline)
6. [Python Integration](#python-integration)
7. [OLAP Query Framework](#olap-query-framework)
8. [Docker Deployment](#docker-deployment)

---

## Overview

### Project Architecture
- **Objective**: Build a comparative OLAP system demonstrating ROLAP (PostgreSQL) vs Columnar (DuckDB) approaches
- **Frontend**: PHP web application for vehicle search/filtering + OLAP query builder
- **Backend**: Python wrappers for both database engines with unified query interface
- **Data**: BMW vehicle sales (10,781 records) with multiple dimensions
- **Comparison**: Performance (query time), result accuracy, and analytics capability

### Database Roles

| Aspect | PostgreSQL (ROLAP) | DuckDB (Columnar) |
|--------|------------------|-----------------|
| **Type** | Traditional relational RDBMS | Columnar analytics engine |
| **Storage** | Persistent volume (`postgres_data/`) | File-based (`/var/www/db/olap.duckdb`) |
| **Purpose** | Source of truth, primary OLAP DB | Replication target for comparison |
| **Data Sync** | Loads from bmw.csv | Synced from PostgreSQL after init |
| **Query Pattern** | Joined row-oriented queries | Columnar aggregations |
| **Web App Use** | Comparison mode only | Primary search/filtering |
| **Access** | TCP/5432 (Docker network) | File I/O via Python (in-process) |

---

## Star Schema Design

### Why Star Schema with Separate Dimensions?

**Principle**: Each CSV column maps to either a **dimension** or a **measure**

```
CSV columns:     Mapping:
model       →    dim_model (PK: model_id)
year        →    dim_time (PK: time_id) + decade calc
fuelType    →    dim_fuel_type (PK: fuel_type_id)
transmission →   dim_transmission (PK: transmission_id)
engineSize  →    dim_engine (PK: engine_id)
price       →    fact_sales (measure)
tax         →    fact_sales (measure)
mileage     →    fact_sales (measure)
mpg         →    fact_sales (measure)
```

### Advantage for Web Application

**Separate dimensions enable dynamic filtering** (Slicing & Dicing):

```javascript
// User selects: Diesel + Automatic + 1.5L engine (should also be an option to select multiple values of one dimension)
User Interface:
┌─ Fuel Type ─┐  ┌─ Transmission ─┐  ┌─ Engine ────┐
│ □ Diesel    │  │ □ Automatic    │  │ □ 1.5L      │
│ □ Petrol    │  │ □ Manual       │  │ □ 2.0L      │
│ ☑ Diesel    │  │ ☑ Automatic    │  │ ☑ 1.5L      │
└─────────────┘  └────────────────┘  └─────────────┘

Python Query Builder:
→ Builds WHERE clause dynamically
→ No SQL hardcoding needed
→ Filters apply independently (OR/AND logic)
```

### Complete Star Schema (ETL-Ready)

```sql
-- Dimension Tables (5 total)
dim_model           (24 records)     - BMW models (3 Series, 5 Series, etc.)
dim_time            (25 records)     - Production years (1996-2020) + decade
dim_fuel_type       (5 records)      - Diesel, Petrol, Hybrid, Electric, Other
dim_transmission    (3 records)      - Automatic, Manual, Semi-Auto
dim_engine          (17 records)     - Engine sizes (0.6L, 1.5L, 2.0L, 3.0L, etc.)

-- Fact Table (1 fact)
fact_sales          (10,781 records) - One row per vehicle sale
```

### File Location
> **`db/schema.sql`** - DDL for all tables + indexes

---

## PostgreSQL Configuration

### Connection Details

**Host**: `postgres` (Docker internal network name)  
**Port**: `5432`  
**Database**: `bmw_olap`  
**User**: `bmw_user`  
**Password**: `bmw_password`  
**Container**: `bmw_postgres_db`

### Docker Compose Service

```yaml
services:
  postgres:
    image: postgres:15-alpine
    container_name: bmw_postgres_db
    restart: unless-stopped
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: bmw_olap
      POSTGRES_USER: bmw_user
      POSTGRES_PASSWORD: bmw_password
      TZ: Europe/Prague
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/01-init.sql
      - ./docker/postgres/load_data.sql:/docker-entrypoint-initdb.d/02-load_data.sql
      - ./db:/tmp/db  # Schema file accessible in container
      - ./project/bmw.csv:/tmp/bmw.csv
    networks:
      - bmw_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U bmw_user -d bmw_olap"]
      interval: 10s
      timeout: 5s
      retries: 5
```

### Initialization Process (Two-Phase)

**Phase 1: Schema Creation** (`docker/postgres/init.sql`)
```sql
-- Read and execute db/schema.sql
\i /tmp/db/schema.sql

-- Create any views or helper functions
-- Grant permissions
GRANT SELECT ON ALL TABLES IN SCHEMA public TO bmw_user;
```

**Phase 2: Data Loading** (`docker/postgres/load_data.sql`)
```sql
-- Load dimension tables from CSV
-- Populate fact_sales with processed CSV data
-- Build indexes
-- Create query statistics
```

**Execution Order**: 
`01-init.sql` (schema) → `02-load_data.sql` (data) → Container ready

### Schema Structure (Star Schema - 5 Dimensions + 1 Fact)

```
┌─ DIMENSIONS ─────────────────────┐
│  dim_model          (24 records)  │  ← BMW models
│  dim_time           (25 records)  │  ← Production years
│  dim_fuel_type      (5 records)   │  ← Fuel modes
│  dim_transmission   (3 records)   │  ← Gears
│  dim_engine         (17 records)  │  ← Engine sizes
└──────────────────────────────────┘
         ↓ (all foreign keys)
┌─ FACT ──────────────────────────┐
│  fact_sales    (10,781 records)  │  ← Sales transactions
└──────────────────────────────────┘
```

### Python Connection Example

```python
import psycopg2
import psycopg2.extras

class PostgreSQLOLAP:
    def __init__(self, host='postgres', port=5432, db='bmw_olap', 
                 user='bmw_user', password='bmw_password'):
        self.conn = psycopg2.connect(
            host=host,
            port=port,
            database=db,
            user=user,
            password=password
        )
    
    def execute_query(self, query: str):
        """Execute query and return results as list of dicts"""
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(query)
        return cursor.fetchall()
    
    def close(self):
        self.conn.close()

# Usage
pg_olap = PostgreSQLOLAP()
results = pg_olap.execute_query("""
    SELECT dm.model_name, COUNT(*) as sales_count, AVG(fs.price) as avg_price
    FROM fact_sales fs
    JOIN dim_model dm ON fs.model_id = dm.model_id
    WHERE fs.fuel_type_id = 1  -- Diesel
    GROUP BY dm.model_name
    ORDER BY sales_count DESC
""")
```

### Quick Testing

```bash
# Access PostgreSQL CLI
docker exec -it bmw_postgres_db psql -U bmw_user -d bmw_olap

# Common queries
\dt                          # List all tables
\d fact_sales                # Show schema
SELECT COUNT(*) FROM fact_sales;
SELECT COUNT(DISTINCT model_id) FROM fact_sales;
```

---

## DuckDB Configuration

### Connection Details

**File Path**: `/var/www/db/olap.duckdb` (mounted volume in Docker container)  
**Access**: Python DuckDB library (in-process, zero network overhead)  
**Type**: File-based columnar database (OLAP-optimized)  
**Persistence**: Automatic disk writes after each operation
**Primary Use**: Web application search/filtering (not comparison mode)

### Python Connection Example

```python
import duckdb
import pandas as pd

class DuckDBANALYTICS:
    def __init__(self, db_path='/var/www/db/olap.duckdb'):
        self.conn = duckdb.connect(db_path)
    
    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute query and return results as DataFrame"""
        return self.conn.execute(query).fetchdf()
    
    def execute_fetch(self, query: str):
        """Execute query and return raw results"""
        return self.conn.execute(query).fetchall()
    
    def close(self):
        self.conn.close()

# Usage (for web search)
duck = DuckDBANALYTICS()
results = duck.execute_query("""
    SELECT 
        dm.model_name,
        dft.fuel_type_name,
        dt.production_year,
        COUNT(*) as sales_count,
        AVG(fs.price) as avg_price,
        MIN(fs.price) as min_price,
        MAX(fs.price) as max_price
    FROM fact_sales fs
    JOIN dim_model dm ON fs.model_id = dm.model_id
    JOIN dim_fuel_type dft ON fs.fuel_type_id = dft.fuel_type_id
    JOIN dim_time dt ON fs.time_id = dt.time_id
    WHERE dft.fuel_type_name = 'Diesel'
    GROUP BY dm.model_name, dft.fuel_type_name, dt.production_year
    ORDER BY avg_price DESC
""")
print(results)
```

### Data Synchronization (PostgreSQL → DuckDB)

**Triggered**: Upon first startup (Phase 3) via Python script

**Process**:
```python
import psycopg2
import duckdb
import pandas as pd

def replicate_postgresql_to_duckdb():
    """One-time sync: PostgreSQL → DuckDB"""
    
    # 1. Connect to both
    pg_conn = psycopg2.connect(
        host='postgres', database='bmw_olap', 
        user='bmw_user', password='bmw_password'
    )
    duck_conn = duckdb.connect('/var/www/db/olap.duckdb')
    
    # 2. Replicate each table from PostgreSQL
    for table_name in ['dim_model', 'dim_time', 'dim_fuel_type', 
                       'dim_transmission', 'dim_engine', 'fact_sales']:
        
        # Query PostgreSQL
        df = pd.read_sql(f"SELECT * FROM {table_name}", pg_conn)
        
        # Write to DuckDB
        duck_conn.register(table_name, df)
        duck_conn.execute(f"CREATE TABLE {table_name}_tmp AS SELECT * FROM {table_name}")
        duck_conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM {table_name}_tmp")
    
    # 3. Verify
    pg_cursor = pg_conn.cursor()
    pg_cursor.execute("SELECT COUNT(*) FROM fact_sales")
    pg_count = pg_cursor.fetchone()[0]
    
    duck_count = duck_conn.execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0]
    
    assert pg_count == duck_count, f"Row count mismatch: PG={pg_count}, Duck={duck_count}"
    print(f"✓ Replication complete: {pg_count} records synced")
    
    pg_conn.close()
    duck_conn.close()

# Run once at startup
if __name__ == '__main__':
    replicate_postgresql_to_duckdb()
```

### Advantages for Search/Filtering

- **Ultra-fast aggregations**: Columnar storage excels at SUM, COUNT, AVG
- **In-process access**: No network latency (vs PostgreSQL TCP)
- **Automatic indexing**: DuckDB adapts indexes to query patterns
- **Perfect for dashboards**: Real-time interactive filtering

---

## Data Loading Pipeline

### Complete ETL Flow

```
┌─ SOURCE ─────────────────────────────────────┐
│  bmw.csv (10,781 records)                     │
│  mode, year, price, transmission, mileage,    │
│  fuelType, tax, mpg, engineSize               │
└──────────────────────────────────────────────┘
           ↓
┌─ POSTGRES INIT ──────────────────────────────┐
│  01-init.sql                                  │
│  • Creates dim_model (24)                     │
│  • Creates dim_time (25)                      │
│  • Creates dim_fuel_type (5)                  │
│  • Creates dim_transmission (3)               │
│  • Creates dim_engine (17)                    │
│  • Creates fact_sales (empty)                 │
└──────────────────────────────────────────────┘
           ↓
┌─ DATA LOAD ───────────────────────────────────┐
│  02-load_data.sql                             │
│  • COPY dim_* from CSV (lookup logic)         │
│  • COPY fact_sales from CSV (with FK refs)   │
│  • CREATE indexes on PK/FK/measures          │
│  • ANALYZE for query optimization            │
└──────────────────────────────────────────────┘
           ↓
┌─ DUCKDB SYNC ─────────────────────────────────┐
│  sync_duckdb.py (Python)                      │
│  • Query all tables from PostgreSQL           │
│  • Create identical structure in DuckDB       │
│  • Verify row counts match                    │
│  • Both databases now ready                   │
└──────────────────────────────────────────────┘
           ↓
┌─ APPLICATIONS ────────────────────────────────┐
│  www/search.php → DuckDB (web search)        │
│  www/compare.php → Both DBs (performance)    │
│  Python wrappers for unified query interface │
└──────────────────────────────────────────────┘
```

### SQL Init Script Structure

**File**: `docker/postgres/init.sql`
```sql
-- 1. Set search path
SET search_path TO public;

-- 2. Load schema from db/schema.sql
\i /tmp/db/schema.sql

-- 3. Seed dimension tables (minimal)
INSERT INTO dim_fuel_type(fuel_type_name) VALUES
  ('Diesel'), ('Petrol'), ('Hybrid'), ('Electric'), ('Other');

INSERT INTO dim_transmission(transmission_name) VALUES
  ('Automatic'), ('Manual'), ('Semi-Auto');

-- 4. Grant permissions
GRANT SELECT ON ALL TABLES IN SCHEMA public TO bmw_user;

-- 5. Verify
SELECT COUNT(*) FROM dim_fuel_type;  -- Should be 5
```

### Data Load Script Structure

**File**: `docker/postgres/load_data.sql`
```sql
-- Load dimensions from CSV with deduplication
INSERT INTO dim_model(model_name)
SELECT DISTINCT model FROM (
  SELECT DISTINCT model FROM read_csv('/tmp/bmw.csv')
) t
ORDER BY model;

-- Similar for dim_time (extract UNIQUE years + calculate decade)
-- Similar for dim_engine (extract UNIQUE engine sizes)

-- Load fact_sales with FK resolution
INSERT INTO fact_sales(
  model_id, time_id, fuel_type_id, transmission_id, engine_id,
  price, tax, mileage, mpg
)
SELECT
  dm.model_id,
  dt.time_id,
  dft.fuel_type_id,
  dtr.transmission_id,
  de.engine_id,
  csv.price,
  csv.tax,
  csv.mileage,
  csv.mpg
FROM read_csv('/tmp/bmw.csv') csv
JOIN dim_model dm ON csv.model = dm.model_name
JOIN dim_time dt ON csv.year = dt.production_year
JOIN dim_fuel_type dft ON csv.fuelType = dft.fuel_type_name
JOIN dim_transmission dtr ON csv.transmission = dtr.transmission_name
JOIN dim_engine de ON csv.engineSize = de.engine_size;

-- Create indexes
CREATE INDEX idx_fact_model ON fact_sales(model_id);
CREATE INDEX idx_fact_time ON fact_sales(time_id);
CREATE INDEX idx_fact_fuel ON fact_sales(fuel_type_id);
CREATE INDEX idx_fact_transmission ON fact_sales(transmission_id);
CREATE INDEX idx_fact_engine ON fact_sales(engine_id);

-- Statistics for query planner
ANALYZE;
```

---

## Schema Design Guidelines

### Design Principles for This Project

1. **Star Schema** (recommended for OLAP):
   - Central fact table (sales/transactions)
   - Surrounding dimension tables
   - Denormalization acceptable for performance
   - Multiple fact tables possible (e.g., fact_sales, fact_inventory)

2. **Dimension Table Rules**:
   - Surrogate keys (auto-increment integers)
   - Slow-changing dimensions (track history if needed)
   - Complete coverage (no nulls in foreign keys)
   - Reasonable size (hundreds to millions of rows)

3. **Fact Table Rules**:
   - Granularity: One row per transaction/vehicle sale
   - Foreign keys to all dimensions
   - Additive measures (can SUM across any dimension)
   - Facts are immutable (append-only)

4. **Indexing Strategy**:
   - PostgreSQL: Indexes on FK columns, measure columns, commonly filtered columns
   - DuckDB: Minimal indexing (automatic, adaptive)
   - No clustered index needed (columnar storage is ordered)

### Typical BMW Sales Star Schema

**Fact Table**: `fact_sales` or `fact_transactions`
- One row per sale event
- Foreign keys: model_id, time_id, version_id, customer_id (optional)
- Measures: price, quantity, discount, margin, commission

**Dimensions**:
- `dim_model`: What was sold (BMW models)
- `dim_time`: When was it sold (dates/time periods)
- `dim_version`: Specific variant (generation, engine, fuel, transmission)
- `dim_customer`: Who bought it (optional)
- `dim_region`: Where (optional)

### Grain Formula

*"Each row in the fact table represents [one vehicle sale on one date by one model version]"*

This drives the schema design and query structure.

---

## Development Workflow

### Phase 3 Breakdown (Database Population)

**Task 1: Schema Definition**
- [ ] Define and validate all dimension tables
- [ ] Define fact table with appropriate grain
- [ ] Choose surrogate vs natural keys
- [ ] Plan denormalization (if needed)
- [ ] Design indexes

**Task 2: SQL Implementation**
- [ ] Write PostgreSQL DDL (CREATE TABLE statements)
- [ ] Write load scripts (COPY from CSV or INSERT)
- [ ] Verify row counts and data quality
- [ ] Create indexes on all FK columns
- [ ] Test query performance

**Task 3: DuckDB Replication**
- [ ] Write Python script to replicate from PostgreSQL
- [ ] Create DuckDB table schema (same as PostgreSQL)
- [ ] Test data equivalence (checksums, row counts)
- [ ] Verify no data loss in replication

**Task 4: Validation**
- [ ] Run sample queries on both databases
- [ ] Compare result sets (must be identical)
- [ ] Measure baseline query performance
- [ ] Document any schema adjustments

### Development Checklist

```
Database Setup
----- PostgreSQL -----
[ ] Connect successfully to postgres:5432
[ ] Verify schema created from init.sql
[ ] Verify data loaded from load_data.sql
[ ] Test basic SELECT queries
[ ] Verify indexes exist
[ ] Check table statistics

----- DuckDB -----
[ ] File created at /var/www/db/olap.duckdb
[ ] Tables replicated from PostgreSQL
[ ] Data count matches PostgreSQL
[ ] Test basic SELECT queries
[ ] Verify column data types match

----- Data Equivalence -----
[ ] Run SLICE query on both → results match
[ ] Run DICE query on both → results match
[ ] Run DRILL-DOWN query on both → results match
[ ] No NULL values where not expected
[ ] Decimal/numeric precision preserved
```

---

## Integration with Python Backend

### Backend Architecture (`src/olap/olap_backend.py`)

```python
class OLAPBackend:
    """
    Interface between PHP frontend and database queries.
    Executes queries on PostgreSQL and DuckDB, compares results.
    """
    
    def __init__(self):
        self.pg_conn = psycopg2.connect(...)  # PostgreSQL
        self.duck_conn = duckdb.connect(...)  # DuckDB
    
    def execute_on_pg(self, query: str, num_runs: int = 3) -> Tuple[List, float]:
        """Execute query on PostgreSQL, return results and avg time (ms)"""
        pass
    
    def execute_on_duck(self, query: str, num_runs: int = 3) -> Tuple[List, float]:
        """Execute query on DuckDB, return results and avg time (ms)"""
        pass
    
    def compare_results(self, pg_results: List, duck_results: List) -> bool:
        """Verify results are identical"""
        pass
    
    # Per-query methods
    def execute_slice_query(self, query_id: int, columns: List[str]) -> Dict:
        """Execute SLICE query (1-dimension filter)"""
        pass
    
    def execute_dice_query(self, query_id: int, columns: List[str]) -> Dict:
        """Execute DICE query (multi-dimension filter)"""
        pass
    
    def execute_drilldown_query(self, query_id: int, columns: List[str]) -> Dict:
        """Execute DRILL-DOWN query (hierarchical aggregation)"""
        pass
```

### JSON API Response Format

```json
{
    "query_type": "SLICE",
    "query_id": 1,
    "query_description": "Diesel vehicles in 2010s",
    "columns": ["model", "year", "quantity", "avg_price"],
    "results": [
        {"model": "3 Series", "year": 2015, "quantity": 125, "avg_price": 35000},
        {"model": "5 Series", "year": 2015, "quantity": 87, "avg_price": 45000},
        ...
    ],
    "postgres": {
        "execution_time_ms": 45.3,
        "row_count": 42,
        "runs": 3
    },
    "duckdb": {
        "execution_time_ms": 28.1,
        "row_count": 42,
        "runs": 3
    },
    "comparison": {
        "results_match": true,
        "speedup_factor": 1.61,
        "description": "DuckDB is 1.61x faster"
    }
}
```

### PHP Wrapper Integration

```php
<?php
// www/includes/olap_wrapper.php

function execute_olap_query($query_type, $query_id, $selected_columns = []) {
    $cmd = sprintf(
        "python3 %s %s %s %s",
        escapeshellarg('/var/www/src/olap/olap_backend.py'),
        escapeshellarg($query_type),
        escapeshellarg($query_id),
        escapeshellarg(json_encode($selected_columns))
    );
    
    $output = shell_exec($cmd);
    return json_decode($output, true);
}

// Usage in www/olap.php
$result = execute_olap_query('SLICE', 1, ['model_name', 'year', 'quantity']);
echo json_encode($result, JSON_PRETTY_PRINT);
?>
```

---

## Testing Strategy

### Unit Tests (pytest)

**PostgreSQL Tests**:
```
test_pg_connection()
test_pg_schema_exists()
test_pg_fact_table_populated()
test_pg_dimension_tables_populated()
test_pg_indexes_exist()
test_pg_query_slice_1()
test_pg_query_dice_2()
test_pg_query_drilldown_3()
```

**DuckDB Tests**:
```
test_duck_connection()
test_duck_tables_exist()
test_duck_data_replicated()
test_duck_row_counts_match()
test_duck_query_slice_1()
test_duck_query_dice_2()
test_duck_query_drilldown_3()
```

**Comparison Tests**:
```
test_slice_results_equivalent()
test_dice_results_equivalent()
test_drilldown_results_equivalent()
test_execution_times_reasonable()
test_speedup_factor_calculated()
```

### Manual Verification Queries

Run these after loading data:

```sql
-- PostgreSQL
SELECT COUNT(*) FROM fact_sales;
SELECT COUNT(DISTINCT model_id) FROM dim_model;
SELECT MIN(price), MAX(price), AVG(price) FROM fact_sales;
SELECT year, COUNT(*) FROM fact_sales GROUP BY year ORDER BY year;
```

```python
# DuckDB
import duckdb
conn = duckdb.connect('/var/www/db/olap.duckdb')
print(conn.execute("SELECT COUNT(*) FROM fact_sales").fetchall())
print(conn.execute("SELECT COUNT(DISTINCT model_id) FROM dim_model").fetchall())
```

---

## Troubleshooting Reference

### PostgreSQL Issues

| Problem | Solution |
|---------|----------|
| "Connection refused" | Verify `postgres` service in `docker-compose ps` |
| "permission denied for database" | Check user permissions: `GRANT ALL ON DATABASE bmw_olap TO bmw_user` |
| "Table doesn't exist" | Check `init.sql` was mounted correctly, inspect logs: `docker logs bmw_postgres_db` |
| "Out of memory" | Check indexes aren't bloating, vacuum: `VACUUM ANALYZE` |

### DuckDB Issues

| Problem | Solution |
|---------|----------|
| "File not found" | Verify path `/var/www/db/olap.duckdb` exists, check permissions `chmod 666` |
| "Connection timeout" | No network connection needed, verify Python has file access |
| "Data type mismatch" | Check schema matches PostgreSQL, use TYPE CAST in DuckDB |

---

## Next Steps for Future Sessions

1. **Session 2 (Schema & OLAP Dev)**:
   - Define final schema based on bmw.csv structure
   - Write init.sql for PostgreSQL
   - Write load_data.sql for bulk import
   - Create Python replication script
   - Implement all 9 OLAP queries
   - Run tests, verify equivalence

2. **Session 3 (Integration)**:
   - Finalize src/olap/olap_backend.py
   - Integrate with www/olap.php wrapper
   - Test end-to-end (PHP → Python → Database)
   - Measure performance, document results

---

**Created**: 2026-04-17  
**Status**: Reference Document  
**For**: BMW OLAP Project - Database Session
