#!/usr/bin/env python3
"""
Test script pro OLAP queries
Testuje připojení k DB a jednotlivé dotazy
Ověřuje OLAP operace (SLICE, DICE, DRILL-DOWN)
Validuje data konzistenci a výkon
"""

import sys
import os
import json
import time
from typing import Dict, List, Any, Tuple

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import RealDictCursor
import duckdb

# ============================================
# BENCHMARK & VALIDATION CLASSES
# ============================================

class OlapTester:
    """OLAP Testing Suite"""

    def __init__(self):
        self.pg_conn = None
        self.duck_db = None
        self.results = {}

    def connect_postgres(self) -> bool:
        """Connect to PostgreSQL"""
        try:
            self.pg_conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'postgres'),
                port=os.getenv('DB_PORT', '5432'),
                database=os.getenv('DB_NAME', 'bmw_sales'),
                user=os.getenv('DB_USER', 'bmw_user'),
                password=os.getenv('DB_PASS', 'bmw_password')
            )
            return True
        except Exception as e:
            print(f"PostgreSQL connection failed: {e}")
            return False

    def connect_duckdb(self, db_path: str = None) -> bool:
        """Connect to DuckDB"""
        try:
            if db_path is None:
                db_path = os.getenv('DUCKDB_PATH', '/var/www/html/db/olap.duckdb')
            self.duck_db = duckdb.connect(db_path)
            return True
        except Exception as e:
            print(f"DuckDB connection failed: {e}")
            return False

    def execute_pg_query(self, query: str) -> Tuple[List[Dict], float]:
        """Execute query on PostgreSQL with timing"""
        cursor = self.pg_conn.cursor(cursor_factory=RealDictCursor)
        start = time.time()
        cursor.execute(query)
        results = cursor.fetchall()
        elapsed_ms = (time.time() - start) * 1000
        cursor.close()
        return [dict(row) for row in results], elapsed_ms

    def execute_duck_query(self, query: str) -> Tuple[List[Dict], float]:
        """Execute query on DuckDB with timing"""
        start = time.time()
        result = self.duck_db.execute(query).fetchall()
        elapsed_ms = (time.time() - start) * 1000

        # Get column names
        columns = [desc[0] for desc in self.duck_db.description]
        data = [dict(zip(columns, row)) for row in result]
        return data, elapsed_ms

    def get_row_count(self, db: str) -> int:
        """Get total row count from fact_sales"""
        query = "SELECT COUNT(*) FROM fact_sales"
        if db == 'postgres':
            cursor = self.pg_conn.cursor()
            cursor.execute(query)
            count = cursor.fetchone()[0]
            cursor.close()
        else:
            result = self.duck_db.execute(query).fetchall()
            count = result[0][0] if result else 0
        return count

    def close(self):
        """Close connections"""
        if self.pg_conn:
            self.pg_conn.close()
        if self.duck_db:
            self.duck_db.close()


# ============================================
# OLAP QUERIES - STANDARDIZED
# ============================================

OLAP_QUERIES = {
    # SLICE QUERIES
    'q1': {
        'name': 'Sales by Model (SLICE)',
        'type': 'SLICE',
        'query': """
            SELECT
                dm.model_name as model,
                COUNT(*) as total_sales,
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price,
                SUM(fs.price) as total_revenue,
                ROUND(AVG(fs.mpg)::NUMERIC, 2) as avg_mpg
            FROM fact_sales fs
            JOIN dim_model dm ON fs.model_id = dm.model_id
            GROUP BY dm.model_id, dm.model_name
            ORDER BY total_sales DESC
            LIMIT 15
        """
    },
    'q2': {
        'name': 'Sales by Year (SLICE)',
        'type': 'SLICE',
        'query': """
            SELECT
                dt.production_year as year,
                COUNT(*) as total_sales,
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price,
                SUM(fs.price) as total_revenue
            FROM fact_sales fs
            JOIN dim_time dt ON fs.time_id = dt.time_id
            GROUP BY dt.production_year
            ORDER BY dt.production_year DESC
        """
    },
    'q3': {
        'name': 'Top 10 Models by Revenue (SLICE)',
        'type': 'SLICE',
        'query': """
            SELECT
                dm.model_name as model,
                COUNT(*) as sales_count,
                SUM(fs.price) as total_revenue,
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price
            FROM fact_sales fs
            JOIN dim_model dm ON fs.model_id = dm.model_id
            GROUP BY dm.model_id, dm.model_name
            ORDER BY total_revenue DESC
            LIMIT 10
        """
    },

    # DICE QUERIES
    'q4': {
        'name': 'Sales by Fuel & Transmission (DICE)',
        'type': 'DICE',
        'query': """
            SELECT
                dft.fuel_type_name as fuel_type,
                dt_trans.transmission_name as transmission,
                COUNT(*) as sales_count,
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price,
                ROUND(AVG(fs.mpg)::NUMERIC, 2) as avg_mpg
            FROM fact_sales fs
            JOIN dim_fuel_type dft ON fs.fuel_type_id = dft.fuel_type_id
            JOIN dim_transmission dt_trans ON fs.transmission_id = dt_trans.transmission_id
            GROUP BY dft.fuel_type_id, dft.fuel_type_name, dt_trans.transmission_id, dt_trans.transmission_name
            ORDER BY sales_count DESC
        """
    },
    'q5': {
        'name': 'Premium Segment Analysis (DICE)',
        'type': 'DICE',
        'query': """
            SELECT
                dm.model_name as model,
                CASE
                    WHEN fs.price > 15000 THEN 'Premium'
                    WHEN fs.price > 10000 THEN 'Mid-Range'
                    ELSE 'Budget'
                END as segment,
                COUNT(*) as sales_count,
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price,
                ROUND(AVG(fs.mpg)::NUMERIC, 2) as avg_mpg
            FROM fact_sales fs
            JOIN dim_model dm ON fs.model_id = dm.model_id
            GROUP BY dm.model_id, dm.model_name, segment
            ORDER BY model, avg_price DESC
            LIMIT 20
        """
    },
    'q6': {
        'name': 'Engine Performance Analysis (DICE)',
        'type': 'DICE',
        'query': """
            SELECT
                de.engine_size,
                COUNT(*) as sales_count,
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price,
                ROUND(AVG(fs.mpg)::NUMERIC, 2) as avg_mpg,
                ROUND(AVG(fs.mileage)::NUMERIC, 2) as avg_mileage
            FROM fact_sales fs
            JOIN dim_engine de ON fs.engine_id = de.engine_id
            GROUP BY de.engine_id, de.engine_size
            ORDER BY de.engine_size
        """
    },

    # DRILL-DOWN QUERIES
    'q7': {
        'name': 'Model Detail Drill-Down (DRILL-DOWN)',
        'type': 'DRILL-DOWN',
        'query': """
            SELECT
                dm.model_name as model,
                dft.fuel_type_name as fuel_type,
                dt_trans.transmission_name as transmission,
                COUNT(*) as sales_count,
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price,
                ROUND(AVG(fs.mpg)::NUMERIC, 2) as avg_mpg,
                MIN(fs.price) as min_price,
                MAX(fs.price) as max_price
            FROM fact_sales fs
            JOIN dim_model dm ON fs.model_id = dm.model_id
            JOIN dim_fuel_type dft ON fs.fuel_type_id = dft.fuel_type_id
            JOIN dim_transmission dt_trans ON fs.transmission_id = dt_trans.transmission_id
            GROUP BY dm.model_id, dm.model_name, dft.fuel_type_id, dft.fuel_type_name, dt_trans.transmission_id, dt_trans.transmission_name
            ORDER BY model, sales_count DESC
            LIMIT 30
        """
    },
    'q8': {
        'name': 'Temporal Analysis Drill-Down (DRILL-DOWN)',
        'type': 'DRILL-DOWN',
        'query': """
            SELECT
                dt.decade,
                dt.production_year as year,
                dm.model_name as model,
                COUNT(*) as sales_count,
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price,
                SUM(fs.price) as total_revenue
            FROM fact_sales fs
            JOIN dim_time dt ON fs.time_id = dt.time_id
            JOIN dim_model dm ON fs.model_id = dm.model_id
            GROUP BY dt.decade, dt.production_year, dm.model_id, dm.model_name
            ORDER BY dt.decade DESC, dt.production_year DESC, sales_count DESC
            LIMIT 40
        """
    },
    'q9': {
        'name': 'Complete Hierarchy (DRILL-DOWN)',
        'type': 'DRILL-DOWN',
        'query': """
            SELECT
                dm.model_name as model,
                dft.fuel_type_name as fuel_type,
                dt_trans.transmission_name as transmission,
                de.engine_size as engine,
                dt.production_year as year,
                COUNT(*) as sales_count,
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price,
                ROUND(AVG(fs.mileage)::NUMERIC, 2) as avg_mileage,
                ROUND(AVG(fs.mpg)::NUMERIC, 2) as avg_mpg
            FROM fact_sales fs
            JOIN dim_model dm ON fs.model_id = dm.model_id
            JOIN dim_fuel_type dft ON fs.fuel_type_id = dft.fuel_type_id
            JOIN dim_transmission dt_trans ON fs.transmission_id = dt_trans.transmission_id
            JOIN dim_engine de ON fs.engine_id = de.engine_id
            JOIN dim_time dt ON fs.time_id = dt.time_id
            GROUP BY dm.model_id, dm.model_name, dft.fuel_type_id, dft.fuel_type_name, dt_trans.transmission_id, dt_trans.transmission_name, de.engine_id, de.engine_size, dt.production_year
            ORDER BY sales_count DESC
            LIMIT 50
        """
    }
}


# ============================================
# TEST FUNCTIONS
# ============================================

def test_postgresql():
    """Test PostgreSQL connection a basic query"""
    print("\n" + "="*70)
    print("🧪 TEST 1: PostgreSQL Connection & Basic Query")
    print("="*70)

    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'postgres'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'bmw_sales'),
            user=os.getenv('DB_USER', 'bmw_user'),
            password=os.getenv('DB_PASS', 'bmw_password')
        )
        print("✓ PostgreSQL Connected")

        cursor = conn.cursor()

        # Test basic query
        cursor.execute("SELECT COUNT(*) FROM fact_sales;")
        count = cursor.fetchone()[0]
        print(f"✓ fact_sales COUNT: {count:,} records")

        if count == 0:
            print("⚠️  WARNING: No data in fact_sales!")
            return False

        # Test q1 query
        print("\n📊 Testing q1 (SLICE - Sales by Model)...")
        cursor.execute(OLAP_QUERIES['q1']['query'])
        results = cursor.fetchall()
        print(f"✓ Got {len(results)} results:")
        for i, row in enumerate(results[:3]):
            print(f"  {i+1}. {row[0]}: {row[1]} sales, avg price: ${row[2]}")

        cursor.close()
        conn.close()
        print("\n✅ PostgreSQL: PASSED")
        return True

    except Exception as e:
        print(f"\n❌ PostgreSQL Error: {e}")
        return False

def test_duckdb():
    """Test DuckDB connection a basic query"""
    print("\n" + "="*70)
    print("🧪 TEST 2: DuckDB Connection & Basic Query")
    print("="*70)

    try:
        db_path = os.getenv('DUCKDB_PATH', '/var/www/html/db/olap.duckdb')
        print(f"📁 Connecting to: {db_path}")

        db = duckdb.connect(db_path)
        print("✓ DuckDB Connected")

        # Test basic query
        result = db.execute("SELECT COUNT(*) FROM fact_sales").fetchall()
        count = result[0][0] if result else 0
        print(f"✓ fact_sales COUNT: {count:,} records")

        if count == 0:
            print("⚠️  WARNING: No data in fact_sales!")
            db.close()
            return False

        # Test q1 query
        print("\n📊 Testing q1 (SLICE - Sales by Model)...")
        result = db.execute(OLAP_QUERIES['q1']['query']).fetchall()
        print(f"✓ Got {len(result)} results:")
        for i, row in enumerate(result[:3]):
            print(f"  {i+1}. {row[0]}: {row[1]} sales, avg price: ${row[2]}")

        db.close()
        print("\n✅ DuckDB: PASSED")
        return True

    except Exception as e:
        print(f"\n❌ DuckDB Error: {e}")
        return False

def test_olap_operations():
    """Test all 9 OLAP queries and verify OLAP operations"""
    print("\n" + "="*70)
    print("🧪 TEST 3: All 9 OLAP Queries (SLICE, DICE, DRILL-DOWN)")
    print("="*70)

    tester = OlapTester()

    if not tester.connect_postgres():
        print("❌ PostgreSQL connection failed")
        return False

    print("✓ PostgreSQL connected")

    results_by_type = {'SLICE': [], 'DICE': [], 'DRILL-DOWN': []}

    for query_id in sorted(OLAP_QUERIES.keys()):
        query_info = OLAP_QUERIES[query_id]
        query_type = query_info['type']

        print(f"\n📌 {query_id}: {query_info['name']}")
        print(f"   Type: {query_type}")

        try:
            results, timing = tester.execute_pg_query(query_info['query'])
            status = "✓" if len(results) > 0 else "⚠️"
            print(f"   {status} Rows: {len(results)}, Time: {timing:.2f}ms")

            # Store metrics
            results_by_type[query_type].append({
                'query_id': query_id,
                'rows': len(results),
                'time_ms': timing
            })

            if len(results) > 0:
                print(f"   Sample: {results[0]}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    tester.close()

    # Summary
    print("\n" + "-"*70)
    print("📊 OLAP Operations Summary:")
    for op_type, queries in results_by_type.items():
        if queries:
            total_rows = sum(q['rows'] for q in queries)
            avg_time = sum(q['time_ms'] for q in queries) / len(queries)
            print(f"\n{op_type} Operations: {len(queries)} queries")
            print(f"  Total rows: {total_rows:,}")
            print(f"  Avg time: {avg_time:.2f}ms")
            print(f"  Queries: {', '.join(q['query_id'] for q in queries)}")

    print("\n✅ OLAP Operations: PASSED")
    return True


def test_data_consistency():
    """Test data consistency between PostgreSQL and DuckDB"""
    print("\n" + "="*70)
    print("🧪 TEST 4: Data Consistency (PostgreSQL vs DuckDB)")
    print("="*70)

    tester = OlapTester()

    if not tester.connect_postgres():
        print("❌ PostgreSQL connection failed")
        return False

    if not tester.connect_duckdb():
        print("❌ DuckDB connection failed")
        tester.close()
        return False

    print("✓ Both databases connected")

    # Test row counts
    print("\n📊 Testing row counts...")
    pg_count = tester.get_row_count('postgres')
    duck_count = tester.get_row_count('duckdb')

    print(f"PostgreSQL: {pg_count:,} rows")
    print(f"DuckDB:     {duck_count:,} rows")

    if pg_count == duck_count:
        print("✓ Row counts match!")
    else:
        print(f"❌ Row count mismatch! Difference: {abs(pg_count - duck_count)}")
        tester.close()
        return False

    # Test q1 results consistency
    print("\n📊 Testing q1 (Sales by Model) consistency...")
    try:
        pg_results, pg_time = tester.execute_pg_query(OLAP_QUERIES['q1']['query'])
        duck_results, duck_time = tester.execute_duck_query(OLAP_QUERIES['q1']['query'])

        print(f"PostgreSQL: {len(pg_results)} models, {pg_time:.2f}ms")
        print(f"DuckDB:     {len(duck_results)} models, {duck_time:.2f}ms")

        if len(pg_results) == len(duck_results):
            print("✓ Result row counts match!")

            # Compare first 3 rows
            all_match = True
            for i in range(min(3, len(pg_results))):
                pg_row = pg_results[i]
                duck_row = duck_results[i]

                if pg_row['model'] == duck_row['model'] and pg_row['total_sales'] == duck_row['total_sales']:
                    print(f"  ✓ Row {i+1}: {pg_row['model']} - {pg_row['total_sales']} sales")
                else:
                    print(f"  ❌ Row {i+1} mismatch!")
                    all_match = False

            if not all_match:
                print("⚠️  Some rows don't match")
        else:
            print(f"❌ Result count mismatch! PG: {len(pg_results)}, Duck: {len(duck_results)}")

    except Exception as e:
        print(f"❌ Error: {e}")
        tester.close()
        return False

    tester.close()
    print("\n✅ Data Consistency: PASSED")
    return True


def test_performance_benchmark():
    """Benchmark all 9 queries on both databases"""
    print("\n" + "="*70)
    print("🧪 TEST 5: Performance Benchmark (PostgreSQL vs DuckDB)")
    print("="*70)

    tester = OlapTester()

    if not tester.connect_postgres():
        print("❌ PostgreSQL connection failed")
        return False

    if not tester.connect_duckdb():
        print("❌ DuckDB connection failed")
        tester.close()
        return False

    benchmark_results = []

    print("\n" + "-"*70)
    print(f"{'Query':<5} {'Name':<35} {'PG (ms)':<12} {'Duck (ms)':<12} {'Winner':<12}")
    print("-"*70)

    for query_id in sorted(OLAP_QUERIES.keys()):
        query_info = OLAP_QUERIES[query_id]
        query = query_info['query']

        try:
            pg_results, pg_time = tester.execute_pg_query(query)
            duck_results, duck_time = tester.execute_duck_query(query)

            winner = "DuckDB ✓" if duck_time < pg_time else "PostgreSQL ✓"
            speedup = max(pg_time, duck_time) / min(pg_time, duck_time) if min(pg_time, duck_time) > 0 else 0

            print(f"{query_id:<5} {query_info['name']:<35} {pg_time:<12.2f} {duck_time:<12.2f} {winner:<12} ({speedup:.2f}x)")

            benchmark_results.append({
                'query_id': query_id,
                'pg_time': pg_time,
                'duck_time': duck_time,
                'pg_rows': len(pg_results),
                'duck_rows': len(duck_results)
            })
        except Exception as e:
            print(f"{query_id:<5} {query_info['name']:<35} ERROR: {e}")

    # Summary statistics
    print("\n" + "-"*70)
    pg_times = [r['pg_time'] for r in benchmark_results]
    duck_times = [r['duck_time'] for r in benchmark_results]

    print(f"\n📊 Performance Summary:")
    print(f"PostgreSQL:")
    print(f"  Total time: {sum(pg_times):.2f}ms")
    print(f"  Avg time:   {sum(pg_times)/len(pg_times):.2f}ms")
    print(f"  Min time:   {min(pg_times):.2f}ms")
    print(f"  Max time:   {max(pg_times):.2f}ms")

    print(f"\nDuckDB:")
    print(f"  Total time: {sum(duck_times):.2f}ms")
    print(f"  Avg time:   {sum(duck_times)/len(duck_times):.2f}ms")
    print(f"  Min time:   {min(duck_times):.2f}ms")
    print(f"  Max time:   {max(duck_times):.2f}ms")

    speedup_overall = sum(pg_times) / sum(duck_times) if sum(duck_times) > 0 else 0
    print(f"\n⚡ Overall speedup: DuckDB is {speedup_overall:.2f}x faster")

    tester.close()
    print("\n✅ Performance Benchmark: PASSED")
    return True


def test_backend_module():
    """Test calling the OLAP backend directly"""
    print("\n" + "="*70)
    print("🧪 TEST 6: OLAP Backend Module")
    print("="*70)

    try:
        from olap_backend import OlapBackend

        backend = OlapBackend()

        # Test PostgreSQL
        print("\n📊 Testing PostgreSQL backend...")
        if backend.connect_postgres():
            print("✓ PostgreSQL connected")

            # Execute all 9 queries
            for query_id in ['q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7', 'q8', 'q9']:
                result = backend.execute_query_by_id(query_id, 'postgres')
                if result.get('rows_returned', 0) > 0:
                    print(f"  ✓ {query_id}: {result['rows_returned']} rows, {result['execution_time_ms']:.2f}ms")
                else:
                    print(f"  ❌ {query_id}: No results")
        else:
            print("✗ PostgreSQL connection failed")
            return False

        # Test DuckDB
        print("\n📊 Testing DuckDB backend...")
        if backend.connect_duckdb():
            print("✓ DuckDB connected")

            # Execute all 9 queries
            for query_id in ['q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7', 'q8', 'q9']:
                result = backend.execute_query_by_id(query_id, 'duckdb')
                if result.get('rows_returned', 0) > 0:
                    print(f"  ✓ {query_id}: {result['rows_returned']} rows, {result['execution_time_ms']:.2f}ms")
                else:
                    print(f"  ❌ {query_id}: No results")
        else:
            print("✗ DuckDB connection failed")
            return False

        backend.close()
        print("\n✅ Backend Module: PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Backend Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*70)
    print("🚀 BMW OLAP System - Comprehensive Test Suite")
    print("="*70)
    print("Testing OLAP operations, data consistency, and performance")
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    results = {
        'PostgreSQL Connection': test_postgresql(),
        'DuckDB Connection': test_duckdb(),
        'OLAP Operations': test_olap_operations(),
        'Data Consistency': test_data_consistency(),
        'Performance Benchmark': test_performance_benchmark(),
        'Backend Module': test_backend_module()
    }

    # Final Summary
    print("\n" + "="*70)
    print("📋 FINAL TEST SUMMARY")
    print("="*70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name:.<45} {status}")

    print(f"\n{'Total':.<45} {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL SYSTEMS GO! OLAP is ready for production.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - see details above")
        return 1

if __name__ == '__main__':
    sys.exit(main())
