# 🧪 OLAP System - Complete Testing Guide

## Overview

Tato testovací sada ověřuje:

1. **Data Integrity** - Konzistence dat mezi PostgreSQL a DuckDB
2. **OLAP Operations** - Správné implementace SLICE, DICE, DRILL-DOWN operací
3. **ROLAP Implementation** - Ověření, že PostgreSQL používá GROUP BY agregace
4. **Performance Benchmark** - Porovnání výkonu obou databází
5. **Backend Module** - Testování Python OLAP backend

## 📁 Test Files

```
src/olap/testy/
├── test_queries.py                 # Hlavní testovací sada (6 testů)
├── test_rolap_operations.py        # ROLAP operace verifikace
├── test_olap_report.py            # Komprehenzivní report
└── README.md                       # Tato dokumentace
```

## 🚀 Quick Start

### Inside Docker Container

```bash
# Connect to PHP container
docker exec -it bmw_analytics_web bash

# Run all tests
cd /var/www/html/../src/olap/testy
python3 test_queries.py

# Run ROLAP verification
python3 test_rolap_operations.py

# Generate detailed report
python3 test_olap_report.py
```

### From Local Machine (if Python + libraries installed)

```bash
# Set environment variables
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=bmw_sales
export DB_USER=bmw_user
export DB_PASS=bmw_password
export DUCKDB_PATH=/path/to/olap.duckdb

# Run tests
python3 test_queries.py
```

## 📊 Test Suite Details

### Test 1: PostgreSQL Connection & Basic Query

- ✓ Ověří připojení k PostgreSQL
- ✓ Kontroluje počet záznamů v fact_sales
- ✓ Spustí Q1 (SLICE - Sales by Model)

**Expected Output:**

```
fact_sales COUNT: 10,566 records
✓ Got 15 results:
  1. 3 Series: 2,047 sales, avg price: $12,456.78
  2. 5 Series: 1,834 sales, avg price: $15,678.90
  ...
```

### Test 2: DuckDB Connection & Basic Query

- ✓ Ověří připojení k DuckDB
- ✓ Kontroluje počet záznamů v fact_sales
- ✓ Spustí Q1 (SLICE)

**Expected Output:** Stejné jako Test 1

### Test 3: All 9 OLAP Queries

- ✓ Spustí všech 9 dotazů sekvenciálně
- ✓ Ověří, že každý dotaz vrátí data
- ✓ Zobrazí metriky pro každý typ operace

**Query Distribution:**

```
SLICE Operations: 3 queries (Q1, Q2, Q3)
  - Sales by Model
  - Sales by Year
  - Top 10 by Revenue

DICE Operations: 3 queries (Q4, Q5, Q6)
  - Fuel Type × Transmission
  - Premium Segment Analysis
  - Engine Performance Analysis

DRILL-DOWN Operations: 3 queries (Q7, Q8, Q9)
  - Model Detail Drill-Down
  - Temporal Analysis
  - Complete Hierarchy
```

### Test 4: Data Consistency

- ✓ Porovnává počet řádků: PostgreSQL vs DuckDB
- ✓ Spustí Q1 na obou databází
- ✓ Ověří, že výsledky jsou shodné
- ✓ Porovnává první 3 řádky

**Expected Output:**

```
PostgreSQL: 10,566 rows
DuckDB:     10,566 rows
✓ Row counts match!

Q1 Results:
  ✓ Row 1: 3 Series - 2,047 sales  ← both match
  ✓ Row 2: 5 Series - 1,834 sales  ← both match
  ✓ Row 3: X Series - 1,456 sales  ← both match
```

### Test 5: Performance Benchmark

- ✓ Spustí všech 9 dotazů na obou databází
- ✓ Měří čas provedení pro každý dotaz
- ✓ Vypočítá speedup faktor
- ✓ Zobrazí celkové statistiky

**Output Table Example:**

```
Query  Name                                  PG (ms)      Duck (ms)    Winner
q1     Sales by Model                        24.56        14.32        DuckDB ✓ (1.72x)
q2     Sales by Year                         18.90        11.45        DuckDB ✓ (1.65x)
q3     Top 10 Models by Revenue              22.34        13.78        DuckDB ✓ (1.62x)
q4     Sales by Fuel & Transmission          45.67        28.90        DuckDB ✓ (1.58x)
...

Performance Summary:
PostgreSQL:
  Total time: 289.45ms
  Avg time:   32.16ms
  Min time:   18.90ms
  Max time:   67.89ms

DuckDB:
  Total time: 172.34ms
  Avg time:   19.15ms
  Min time:   11.45ms
  Max time:   38.90ms

⚡ Overall speedup: DuckDB is 1.68x faster
```

### Test 6: Backend Module

- ✓ Importuje olap_backend.py
- ✓ Conecta se k PostgreSQL
- ✓ Conecta se k DuckDB
- ✓ Spustí všech 9 dotazů na obou databází

**Expected Output:**

```
✓ PostgreSQL connected
  ✓ q1: 15 rows, 24.56ms
  ✓ q2: 27 rows, 18.90ms
  ...
✓ DuckDB connected
  ✓ q1: 15 rows, 14.32ms
  ✓ q2: 27 rows, 11.45ms
  ...
```

## 🔍 ROLAP Verification

### Overview of ROLAP Implementation

PostgreSQL implementuje ROLAP (Relational OLAP) pomocí:

1. **GROUP BY agregace** - Agregace na libovolné kombinaci dimenzí
2. **Star Schema** - 1 fact table + 5 dimension tables
3. **Indexes** - Na cizích klíčích v fact table
4. **Hierarchical Queries** - Multi-level GROUP BY pro drill-down

### Test: ROLAP Operations

```bash
python3 test_rolap_operations.py
```

**Verifies:**

#### SLICE Operation (Single Dimension Aggregation)

```sql
SELECT
    dm.model_name as model,
    COUNT(*) as total_sales,
    AVG(fs.price) as avg_price,
    SUM(fs.price) as total_revenue
FROM fact_sales fs
JOIN dim_model dm ON fs.model_id = dm.model_id
GROUP BY dm.model_id, dm.model_name  ← ROLAP: GROUP BY single dimension
ORDER BY total_sales DESC
```

**Verification Criteria:**

- ✓ GROUP BY uses 1 dimension (model_id)
- ✓ Aggregate functions: COUNT, AVG, SUM
- ✓ Returns aggregated data at model level

#### DICE Operation (Multi-Dimensional Filtering)

```sql
SELECT
    dft.fuel_type_name as fuel_type,
    dt_trans.transmission_name as transmission,
    COUNT(*) as sales_count,
    AVG(fs.price) as avg_price
FROM fact_sales fs
JOIN dim_fuel_type dft ON fs.fuel_type_id = dft.fuel_type_id
JOIN dim_transmission dt_trans ON fs.transmission_id = dt_trans.transmission_id
GROUP BY dft.fuel_type_id, dft.fuel_type_name,     ← ROLAP: GROUP BY 2 dimensions
         dt_trans.transmission_id, dt_trans.transmission_name
ORDER BY sales_count DESC
```

**Verification Criteria:**

- ✓ GROUP BY uses 2 dimensions (fuel_type_id, transmission_id)
- ✓ Returns cross-product of dimensions (4 fuels × 4 transmissions = ~16 rows)
- ✓ Each combination shows aggregated metrics

#### DRILL-DOWN Operation (Hierarchical Aggregation)

```sql
SELECT
    dt.decade,              ← Level 1: Coarse (1990s, 2000s, etc.)
    dt.production_year,     ← Level 2: Medium (1994, 1995, etc.)
    dm.model_name,          ← Level 3: Fine (specific model)
    COUNT(*) as sales_count,
    AVG(fs.price) as avg_price
FROM fact_sales fs
JOIN dim_time dt ON fs.time_id = dt.time_id
JOIN dim_model dm ON fs.model_id = dm.model_id
GROUP BY dt.decade, dt.production_year, dm.model_id, dm.model_name
         ↑ ROLAP: GROUP BY 3 levels of hierarchy
ORDER BY dt.decade DESC, dt.production_year DESC, sales_count DESC
```

**Verification Criteria:**

- ✓ GROUP BY uses 3 hierarchical levels
- ✓ Supports navigation from general (decade) → specific (model)
- ✓ Proper drill-down path

## 📈 Performance Targets

Expected performance (on typical hardware):

| Query Type | Count | PG Time | Duck Time | Target |
|-----------|-------|---------|-----------|--------|
| SLICE | 3 | 20ms avg | 12ms avg | < 50ms |
| DICE | 3 | 35ms avg | 20ms avg | < 50ms |
| DRILL-DOWN | 3 | 45ms avg | 25ms avg | < 100ms |
| **Total (9)** | - | ~300ms | ~180ms | < 500ms |

## 🔧 Troubleshooting

### "Connection refused"

```bash
# Check if containers are running
docker ps | grep bmw

# Restart containers if needed
docker-compose down
docker-compose up -d
```

### "Database 'bmw_sales' does not exist"

```bash
# Verify schema was initialized
docker exec bmw_analytics_web python3 /var/www/html/../src/olap/quick_init.py

# Check data was loaded
docker exec bmw_postgres_db psql -U bmw_user -d bmw_sales -c "SELECT COUNT(*) FROM fact_sales"
```

### "DuckDB file not found"

```bash
# Check file exists with correct permissions
ls -la /var/www/html/db/olap.duckdb
chmod 666 /var/www/html/db/olap.duckdb

# Check DuckDB path in environment
docker exec bmw_analytics_web env | grep DUCKDB
```

### "No data returned"

```bash
# Verify data is loaded
docker exec bmw_postgres_db psql -U bmw_user -d bmw_sales -c "SELECT COUNT(*) FROM fact_sales"

# Should return: 10,566 rows
```

## 📊 Expected Results Summary

✅ **All tests should PASS:**

| Test | Status | Expected |
|------|--------|----------|
| PostgreSQL Connection | ✅ | Connected, 10,566 rows |
| DuckDB Connection | ✅ | Connected, 10,566 rows |
| OLAP Operations | ✅ | All 9 queries return results |
| Data Consistency | ✅ | PG and Duck results match |
| Performance | ✅ | Duck ~1.5-1.8x faster than PG |
| Backend Module | ✅ | All queries execute successfully |

## 🎯 Next Steps

After successful testing:

1. ✅ Document any performance issues
2. ✅ Verify data matches source CSV (bmw.csv - 10,566 rows)
3. ✅ Test frontend OLAP page at `/pages/olap.php`
4. ✅ Verify API endpoint returns correct JSON format
5. ✅ Consider adding materialized views for frequent queries
6. ✅ Proceed to crypto backend implementation

## 📝 Notes

- All tests use standardized query definitions in `OLAP_QUERIES` dict
- Tests are independent and can be run individually
- Performance times will vary based on hardware
- DuckDB is typically 1.5-2x faster due to columnar storage
- PostgreSQL is more suitable for transactional accuracy

---

**Last Updated:** April 28, 2026
**Test Suite Version:** 2.0
**Author:** OLAP Test Framework
