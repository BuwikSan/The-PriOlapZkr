# 🚗 BMW OLAP Analytics - Data Loading Guide

## Quick Start

### 1️⃣ Start Containers

```bash
cd /var/www/The-PriOlapZkr
docker-compose up -d
```

This will:

- Start PostgreSQL (port 5432)
- Start PHP web server (port 8080)
- Create database schema automatically

### 2️⃣ Load BMW Sales Data

```bash
# Option A: Using setup script (automated)
docker exec bmw_analytics_web bash /var/www/src/olap/setup_databases.sh

# Option B: Manual step-by-step
docker exec bmw_analytics_web python3 /var/www/src/olap/load_bmw_data.py /var/www/data/bmw.csv
```

### 3️⃣ Verify Data Loading

```bash
# Check PostgreSQL
docker exec bmw_postgres_db psql -U bmw_user -d bmw_olap -c \
  "SELECT COUNT(*) as total_sales FROM fact_sales;"

# Check DuckDB
docker exec bmw_analytics_web python3 << 'EOF'
import duckdb
conn = duckdb.connect('/var/www/html/db/olap.duckdb')
result = conn.execute("SELECT COUNT(*) FROM fact_sales").fetchall()
print(f"DuckDB Sales: {result[0][0]:,}")
EOF
```

### 4️⃣ Test OLAP Queries

```bash
# Test Q1 on PostgreSQL
docker exec bmw_analytics_web python3 /var/www/src/olap/olap_backend.py execute_query q1 postgres

# Compare Q1 (PostgreSQL vs DuckDB)
docker exec bmw_analytics_web python3 /var/www/src/olap/olap_backend.py compare q1

# List all available queries
docker exec bmw_analytics_web python3 /var/www/src/olap/olap_backend.py list_queries
```

### 5️⃣ Open Web Interface

```
http://localhost:8080
```

Navigate to: **OLAP Showcase** tab to test queries interactively

---

## 📊 What Gets Loaded

### Data from CSV (10,782 records)

```
BMW Models: 3 Series, 5 Series, X1, X3, X5, M4, M5, M3, etc.
Time Range: 2013-2020
Fuel Types: Diesel, Petrol, Hybrid, Other
Transmissions: Manual, Automatic, Semi-Auto, CVT
Engine Sizes: 1.5 - 5.0 liters
```

### Database Schema (Star Schema)

```
Fact Table: fact_sales (10,782 records)
├── model_id (16 models)
├── time_id (27 years/decades)
├── fuel_type_id (4 types)
├── transmission_id (4 types)
├── engine_id (10 sizes)
├── price (£)
├── tax (£)
├── mileage (miles)
└── mpg (MPG)

Dimensions:
├── dim_model (16 rows)
├── dim_time (27 rows)
├── dim_fuel_type (4 rows)
├── dim_transmission (4 rows)
└── dim_engine (10 rows)
```

---

## 🔍 Available OLAP Queries

### SLICE Operations (3)

- **Q1**: Sales by Model
- **Q2**: Sales by Year
- **Q3**: Top 10 Models by Revenue

### DICE Operations (3)

- **Q4**: Sales by Fuel Type & Transmission
- **Q5**: Premium Segment Analysis
- **Q6**: Engine Performance Analysis

### DRILL-DOWN Operations (3)

- **Q7**: Model Detail Drill-Down
- **Q8**: Temporal Analysis Drill-Down
- **Q9**: Complete Hierarchy Analysis

---

## 🛠️ Troubleshooting

### PostgreSQL Connection Error

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check logs
docker logs bmw_postgres_db
```

### DuckDB File Permission Error

```bash
# Fix permissions
docker exec bmw_analytics_web chmod -R 755 /var/www/html/db
```

### Data Not Appearing in Queries

```bash
# Re-run setup
docker exec bmw_analytics_web bash /var/www/src/olap/setup_databases.sh

# Check fact_sales record count
docker exec bmw_analytics_web python3 /var/www/src/olap/olap_backend.py execute_query q1 postgres
```

### CSV File Not Found

Ensure `bmw.csv` is in: `/depricated_or_tobeused/bmw.csv`

Or copy manually:

```bash
docker cp depricated_or_tobeused/bmw.csv bmw_analytics_web:/var/www/data/bmw.csv
```

---

## 📈 Performance Notes

### PostgreSQL vs DuckDB

```
PostgreSQL: Row-oriented, ACID transactions, ideal for OLTP
DuckDB: Column-oriented, vectorized operations, better for analytics

Expected Results:
- Simple aggregations: DuckDB ~2-5x faster
- Complex joins: PostgreSQL competitive
- Large scans: DuckDB significantly faster
```

### Query Optimization

- Indices created on all foreign keys and price column
- Decade hierarchy in dim_time for fast roll-ups
- Use LIMIT in frontend to avoid large result sets

---

## 🔄 Updating Data

To reload with fresh CSV:

```bash
# Clear existing data
docker exec bmw_postgres_db psql -U bmw_user -d bmw_olap -c \
  "TRUNCATE TABLE fact_sales CASCADE;"

docker exec bmw_analytics_web python3 << 'EOF'
import duckdb
conn = duckdb.connect('/var/www/html/db/olap.duckdb')
conn.execute("DELETE FROM fact_sales")
EOF

# Re-run setup
docker exec bmw_analytics_web bash /var/www/src/olap/setup_databases.sh
```

---

## 📝 Environment Variables

Set in `docker-compose.yml`:

```yaml
DB_HOST: postgres
DB_PORT: 5432
DB_NAME: bmw_olap
DB_USER: bmw_user
DB_PASS: bmw_password
DUCKDB_PATH: /var/www/html/db/olap.duckdb
```

Alternatively, set in shell:

```bash
export DB_HOST=postgres
export DB_USER=bmw_user
export DB_PASS=bmw_password
python3 /var/www/src/olap/load_bmw_data.py /path/to/bmw.csv
```

---

## ✅ Verification Checklist

- [ ] Containers are running: `docker ps`
- [ ] PostgreSQL schema exists: `docker exec bmw_postgres_db psql -U bmw_user -d bmw_olap -c "\dt"`
- [ ] CSV file copied: `docker exec bmw_analytics_web ls -lh /var/www/data/bmw.csv`
- [ ] Data loaded: `execute_query q1 postgres` returns results
- [ ] Web interface accessible: `http://localhost:8080`
- [ ] OLAP Showcase tab works: Select query and click "Spustit Dotaz"

---

**Happy OLAP analyzing! 🎯**
