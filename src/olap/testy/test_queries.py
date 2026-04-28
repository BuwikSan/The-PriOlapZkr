#!/usr/bin/env python3
"""
Test script pro OLAP queries
Testuje připojení k DB a jednotlivé dotazy
"""

import sys
import os
import json
import time

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
import duckdb

def test_postgresql():
    """Test PostgreSQL connection a simple query"""
    print("\n" + "="*60)
    print("🧪 TEST: PostgreSQL Connection & Query")
    print("="*60)

    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'postgres'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'bmw_olap'),
            user=os.getenv('DB_USER', 'bmw_user'),
            password=os.getenv('DB_PASS', 'bmw_password')
        )
        print("✓ PostgreSQL Connected")

        cursor = conn.cursor()

        # Test basic query
        cursor.execute("SELECT COUNT(*) FROM fact_sales;")
        count = cursor.fetchone()[0]
        print(f"✓ fact_sales COUNT: {count} records")

        # Test q1 query
        print("\n📊 Testing q1 query...")
        cursor.execute("""
            SELECT
                dm.model_name as model,
                COUNT(*) as total_sales,
                ROUND(AVG(fs.price), 2) as avg_price,
                SUM(fs.price) as total_revenue,
                ROUND(AVG(fs.mpg), 2) as avg_mpg
            FROM fact_sales fs
            JOIN dim_model dm ON fs.model_id = dm.model_id
            GROUP BY dm.model_id, dm.model_name
            ORDER BY total_sales DESC
            LIMIT 5
        """)

        results = cursor.fetchall()
        print(f"✓ Got {len(results)} results:")
        for row in results:
            print(f"  {row[0]}: {row[1]} sales, avg price: {row[2]}")

        cursor.close()
        conn.close()
        print("\n✅ PostgreSQL: ALL TESTS PASSED")
        return True

    except Exception as e:
        print(f"\n❌ PostgreSQL Error: {e}")
        return False

def test_duckdb():
    """Test DuckDB connection a simple query"""
    print("\n" + "="*60)
    print("🧪 TEST: DuckDB Connection & Query")
    print("="*60)

    try:
        db_path = os.getenv('DUCKDB_PATH', '/var/www/db/olap.duckdb')
        print(f"Connecting to: {db_path}")

        db = duckdb.connect(db_path)
        print("✓ DuckDB Connected")

        # Test basic query
        result = db.execute("SELECT COUNT(*) FROM fact_sales").fetchall()
        count = result[0][0] if result else 0
        print(f"✓ fact_sales COUNT: {count} records")

        # Test q1 query
        print("\n📊 Testing q1 query...")
        result = db.execute("""
            SELECT
                dm.model_name as model,
                COUNT(*) as total_sales,
                ROUND(AVG(fs.price), 2) as avg_price,
                SUM(fs.price) as total_revenue,
                ROUND(AVG(fs.mpg), 2) as avg_mpg
            FROM fact_sales fs
            JOIN dim_model dm ON fs.model_id = dm.model_id
            GROUP BY dm.model_id, dm.model_name
            ORDER BY total_sales DESC
            LIMIT 5
        """).fetchall()

        print(f"✓ Got {len(result)} results:")
        for row in result:
            print(f"  {row[0]}: {row[1]} sales, avg price: {row[2]}")

        db.close()
        print("\n✅ DuckDB: ALL TESTS PASSED")
        return True

    except Exception as e:
        print(f"\n❌ DuckDB Error: {e}")
        return False

def test_backend():
    """Test calling the OLAP backend directly"""
    print("\n" + "="*60)
    print("🧪 TEST: OLAP Backend Module")
    print("="*60)

    try:
        from olap_backend import OlapBackend

        backend = OlapBackend()

        # Test PostgreSQL
        print("\n📊 Testing PostgreSQL backend...")
        if backend.connect_postgres():
            print("✓ PostgreSQL connected")
            result = backend.query_sales_by_model()
            if result:
                print(f"✓ Query returned {len(result)} rows")
                print(f"  First row: {result[0]}")
            backend.pg_conn.close()
        else:
            print("✗ PostgreSQL connection failed")
            return False

        # Test DuckDB
        print("\n📊 Testing DuckDB backend...")
        if backend.connect_duckdb():
            print("✓ DuckDB connected")
            result = backend.query_sales_by_model()
            if result:
                print(f"✓ Query returned {len(result)} rows")
                print(f"  First row: {result[0]}")
            backend.duck_db.close()
        else:
            print("✗ DuckDB connection failed")
            return False

        print("\n✅ Backend: ALL TESTS PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Backend Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*60)
    print("BMW OLAP System - Test Suite")
    print("="*60)

    results = {
        'PostgreSQL': test_postgresql(),
        'DuckDB': test_duckdb(),
        'Backend': test_backend()
    }

    print("\n" + "="*60)
    print("📋 SUMMARY")
    print("="*60)

    for name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name:20} {status}")

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL SYSTEMS GO!")
        return 0
    else:
        print("\n⚠️  Some tests failed - check output above")
        return 1

if __name__ == '__main__':
    sys.exit(main())
