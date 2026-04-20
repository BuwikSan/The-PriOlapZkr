# Database Setup & OLAP Configuration Guide

**Purpose**: Reference document for developing BMW OLAP schema and queries in a separate AI chat session.  
**Audience**: AI assistant developing Phase 3+ (database schema, OLAP queries, data pipeline)  
**Status**: Temporary - for effective knowledge transfer between chat sessions

---

## Table of Contents
1. [Overview](#overview)
2. [PostgreSQL Configuration](#postgresql-configuration)
3. [DuckDB Configuration](#duckdb-configuration)
4. [Architecture & Data Flow](#architecture--data-flow)
5. [OLAP Requirements](#olap-requirements)
6. [Schema Design Guidelines](#schema-design-guidelines)
7. [Development Workflow](#development-workflow)
8. [Integration with Python Backend](#integration-with-python-backend)

---

## Overview

### Project Context
- **Project**: BMW Sales OLAP & Data Mining Comparison
- **Purpose**: Compare traditional RDBMS (PostgreSQL) vs columnar analytics engine (DuckDB)
- **Data Source**: BMW sales dataset (bmw.csv)
- **Comparison Focus**: Query performance, execution time, result accuracy

### Database Roles

| Aspect | PostgreSQL | DuckDB |
|--------|-----------|---------|
| **Type** | Traditional RDBMS | Columnar Analytics Engine |
| **Storage** | Persistent volume (`postgres_data/`) | File-based (`/var/www/db/olap.duckdb`) |
| **Purpose** | Production OLAP DB, normalized schema | Analytical queries, comparison baseline |
| **Data Sync** | Source of truth | Replicated from PostgreSQL |
| **Query Pattern** | Normalized joins, traditional SQL | Columnar aggregations, OLAP-optimized |
| **Access** | TCP/5432 (internal network) | Python DuckDB library (in-process) |

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
    - ./project/bmw.csv:/tmp/bmw.csv
  networks:
    - bmw_network
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U bmw_user -d bmw_olap"]
    interval: 10s
    timeout: 5s
    retries: 5
```

### Initialization Process

**Phase**: Automatic on container startup

1. **Schema Initialization** (`01-init.sql`):
   - Creates dimension tables (dim_model, dim_time, dim_version)
   - Creates fact table (fact_sales)
   - Creates indexes for performance
   - Grants permissions to `bmw_user`

2. **Data Loading** (`02-load_data.sql`):
   - Loads BMW CSV data from `/tmp/bmw.csv`
   - Uses COPY command for bulk insert (fast)
   - Verifies row counts
   - Creates statistics for query optimizer

### Python Connection Example

```python
import psycopg2
from psycopg2 import sql

# Connection
conn = psycopg2.connect(
    host='postgres',
    port=5432,
    database='bmw_olap',
    user='bmw_user',
    password='bmw_password'
)

cursor = conn.cursor()

# Query example
cursor.execute("SELECT model_name, COUNT(*) FROM fact_sales fs JOIN dim_model dm ON fs.model_id = dm.model_id GROUP BY model_name")
results = cursor.fetchall()

cursor.close()
conn.close()
```

### PHP Connection Example

```php
<?php
$conn = pg_connect("host=" . getenv('DB_HOST') . 
                   " port=5432 dbname=bmw_olap user=bmw_user password=bmw_password");

if (!$conn) {
    die("PostgreSQL connection failed");
}

$result = pg_query($conn, "SELECT COUNT(*) FROM fact_sales");
$row = pg_fetch_row($result);
echo "Total sales records: " . $row[0];

pg_close($conn);
?>
```

### Schema Structure (Typical Star Schema)

```
dim_model
├── model_id (PK)
├── model_name
├── manufacturer
└── created_at

dim_time
├── time_id (PK)
├── year
├── quarter
├── month
└── created_at

dim_version
├── version_id (PK)
├── generation
├── engine_type
├── fuel_type
├── transmission
└── created_at

fact_sales (fact table)
├── sale_id (PK)
├── model_id (FK → dim_model)
├── time_id (FK → dim_time)
├── version_id (FK → dim_version)
├── price
├── quantity
├── mpg
├── horsepower
└── created_at
```

### Querying PostgreSQL

**CLI Access**:
```bash
docker exec -it bmw_postgres_db psql -U bmw_user -d bmw_olap
```

**Common Commands**:
```sql
-- List tables
\dt

-- Show table structure
\d fact_sales

-- Query with joins
SELECT dm.model_name, SUM(fs.quantity) as total_sales
FROM fact_sales fs
JOIN dim_model dm ON fs.model_id = dm.model_id
GROUP BY dm.model_name
ORDER BY total_sales DESC;

-- Check row count
SELECT COUNT(*) FROM fact_sales;
```

---

## DuckDB Configuration

### Connection Details

**File Path**: `/var/www/db/olap.duckdb` (mounted volume in container)  
**Access**: Python DuckDB library (in-process, no network)  
**Type**: File-based columnar database  
**Persistence**: Automatic on disk

### Python Connection Example

```python
import duckdb

# Connection (file-based)
conn = duckdb.connect('/var/www/db/olap.duckdb')

# Or in-memory (for testing)
# conn = duckdb.connect(':memory:')

# Query
result = conn.execute("""
    SELECT model_name, COUNT(*) as sales_count
    FROM fact_sales
    GROUP BY model_name
    ORDER BY sales_count DESC
""").fetchall()

# Get column names
columns = [desc[0] for desc in conn.description]

conn.close()
```

### Setup Process (Python Backend Responsibility)

**When**: Phase 3 (database population)

**Workflow**:
1. Query PostgreSQL for all data
2. Create DuckDB tables with same schema
3. Populate DuckDB from PostgreSQL results
4. Verify data equivalence (row counts, checksums)
5. Both databases ready for OLAP queries

**Example Script**:
```python
import psycopg2
import duckdb

# Step 1: Connect to both databases
pg_conn = psycopg2.connect(host='postgres', database='bmw_olap', user='bmw_user', password='bmw_password')
duck_conn = duckdb.connect('/var/www/db/olap.duckdb')

# Step 2: Get PostgreSQL data
pg_cursor = pg_conn.cursor()
pg_cursor.execute("SELECT * FROM fact_sales")
data = pg_cursor.fetchall()

# Step 3: Create DuckDB table
duck_conn.execute("""
    CREATE TABLE fact_sales (
        sale_id INTEGER,
        model_id INTEGER,
        time_id INTEGER,
        version_id INTEGER,
        price DECIMAL(12, 2),
        quantity INTEGER,
        mpg DECIMAL(5, 2),
        horsepower INTEGER,
        created_at TIMESTAMP
    )
""")

# Step 4: Insert data
for row in data:
    duck_conn.execute("INSERT INTO fact_sales VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", row)

duck_conn.commit()
pg_conn.close()
duck_conn.close()
```

### Advantages for OLAP

- **Columnar Storage**: Efficient for aggregations (SUM, COUNT, AVG)
- **Vector Operations**: Fast bulk processing
- **In-Process**: No network overhead
- **Automatic Indexing**: Adaptive indexing for queries
- **Perfect for Comparisons**: Same queries on both engines for benchmarking

### Query Example in OLAP Context

```python
import duckdb
import time

conn = duckdb.connect('/var/www/db/olap.duckdb')

# Time measurement
start = time.time()

result = conn.execute("""
    SELECT 
        model_name,
        year,
        COUNT(*) as sales_count,
        AVG(price) as avg_price,
        SUM(quantity) as total_quantity
    FROM fact_sales fs
    JOIN dim_model dm ON fs.model_id = dm.model_id
    JOIN dim_time dt ON fs.time_id = dt.time_id
    WHERE year >= 2017 AND dt.fuel_type = 'Diesel'
    GROUP BY model_name, year
    ORDER BY year DESC, sales_count DESC
""").fetchall()

elapsed = time.time() - start

print(f"DuckDB query took {elapsed*1000:.2f}ms")
```

---

## Architecture & Data Flow

### Complete Data Pipeline

```
bmw.csv (source file)
    ↓
1. Data Load (Phase 3)
    ↓
PostgreSQL (normalized star schema)
    ↓
2. Replication (Python)
    ↓
DuckDB (columnar copy)
    ↓
3. OLAP Queries (Phase 6)
    ↓
Python Backend (src/olap/olap_backend.py)
    ├── Execute Query on PostgreSQL
    ├── Execute Query on DuckDB
    ├── Measure Timing (avg 3 runs)
    ├── Compare Results
    └── Return JSON
    ↓
4. Frontend Display (www/olap.php)
    ↓
Browser (results + timing comparison)
```

### Query Execution Flow

```
User clicks "Run Query" (www/olap.php)
    ↓
POST to includes/olap_wrapper.php
    ↓
shell_exec("python src/olap/olap_backend.py query_id column_selections")
    ↓
Python Backend:
    1. Parse query ID (SLICE_1, DICE_2, etc.)
    2. Get selected columns from POST
    3. Build dynamic SELECT clause
    4. Execute on PostgreSQL (3 times, average)
    5. Execute on DuckDB (3 times, average)
    6. Compare results (should be identical)
    7. Calculate speedup factor
    ↓
Return JSON {query, pg_time, duck_time, speedup, results}
    ↓
PHP displays in table with timing info
```

---

## OLAP Requirements

### 9 Pre-Built Queries (From Existing Code)

**SLICE Queries** (1-dimensional filtering):
1. Diesel vehicles in 2010s decade
2. Premium petrol vehicles (price > 30k)
3. [One more to be defined from existing code]

**DICE Queries** (multi-dimensional filtering + ranking):
1. Top 15 most expensive combinations (minimum 5 sales)
2. Top 10 cheapest vehicles (minimum 10 sales)
3. Best price/MPG ratio (calculated column, 2010 onwards)

**DRILL-DOWN Queries** (hierarchical aggregation):
1. Model-only aggregation (1 level)
2. Model + Year (2 levels)
3. Model + Year + Engine + Fuel (4 levels)

### Query Characteristics

- **No transactions needed** (read-only)
- **Parameterized construction** (prevent SQL injection)
- **Column selection** (dynamic SELECT clause via checkboxes)
- **Consistent results** (both DBs must return identical data)
- **Performance measurement** (millisecond precision)

### Expected Columns (From BMW Dataset)

**Dimensions**:
- Model (e.g., 3 Series, 5 Series)
- Year (2010-2023 range)
- Generation (F30, G20, F32, etc.)
- Engine Type (TwinScroll, TwinPower, N/A, S55, etc.)
- Fuel Type (Diesel, Petrol, Hybrid, Electric)
- Transmission (Manual, Automatic)

**Measures**:
- Price (decimal)
- Quantity (integer)
- MPG (fuel efficiency)
- Horsepower (integer)
- Sales Count (aggregate)

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
