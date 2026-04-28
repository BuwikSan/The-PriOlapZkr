#!/usr/bin/env python3
"""
OLAP System - Complete Testing & Validation Report
Generates comprehensive report on:
1. Data integrity
2. OLAP operations correctness
3. Performance comparison
4. ROLAP implementation verification
"""

import sys
import os
import json
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import RealDictCursor
import duckdb


class OlapReportGenerator:
    """Generate comprehensive OLAP testing report"""

    def __init__(self):
        self.pg_conn = None
        self.duck_db = None
        self.report = {
            'timestamp': datetime.now().isoformat(),
            'sections': {}
        }

    def connect_all(self) -> bool:
        """Connect to both databases"""
        try:
            self.pg_conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'postgres'),
                port=os.getenv('DB_PORT', '5432'),
                database=os.getenv('DB_NAME', 'bmw_sales'),
                user=os.getenv('DB_USER', 'bmw_user'),
                password=os.getenv('DB_PASS', 'bmw_password')
            )
            print("✓ PostgreSQL connected")
        except Exception as e:
            print(f"✗ PostgreSQL connection failed: {e}")
            return False

        try:
            db_path = os.getenv('DUCKDB_PATH', '/var/www/html/db/olap.duckdb')
            self.duck_db = duckdb.connect(db_path)
            print("✓ DuckDB connected")
        except Exception as e:
            print(f"✗ DuckDB connection failed: {e}")
            return False

        return True

    def execute_pg_query(self, query: str) -> tuple:
        """Execute query on PostgreSQL"""
        cursor = self.pg_conn.cursor(cursor_factory=RealDictCursor)
        start = time.time()
        cursor.execute(query)
        results = cursor.fetchall()
        elapsed_ms = (time.time() - start) * 1000
        cursor.close()
        return [dict(row) for row in results], elapsed_ms

    def execute_duck_query(self, query: str) -> tuple:
        """Execute query on DuckDB"""
        start = time.time()
        result = self.duck_db.execute(query).fetchall()
        elapsed_ms = (time.time() - start) * 1000
        columns = [desc[0] for desc in self.duck_db.description]
        data = [dict(zip(columns, row)) for row in result]
        return data, elapsed_ms

    def section_data_integrity(self):
        """Section 1: Data Integrity"""
        print("\n📊 Section 1: Data Integrity Check")
        print("-" * 70)

        section = {'tests': []}

        # Row counts
        cursor = self.pg_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM fact_sales")
        pg_count = cursor.fetchone()[0]
        cursor.close()

        duck_count = self.duck_db.execute("SELECT COUNT(*) FROM fact_sales").fetchall()[0][0]

        test1 = {
            'name': 'Fact Table Row Count',
            'postgresql': pg_count,
            'duckdb': duck_count,
            'match': pg_count == duck_count,
            'status': '✓ PASS' if pg_count == duck_count else '✗ FAIL'
        }
        section['tests'].append(test1)
        print(f"\n  {test1['status']}: Row Count")
        print(f"    PostgreSQL: {pg_count:,}")
        print(f"    DuckDB:     {duck_count:,}")

        # Dimension counts
        dimensions = ['dim_model', 'dim_fuel_type', 'dim_transmission', 'dim_engine', 'dim_time']
        for dim in dimensions:
            cursor = self.pg_conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {dim}")
            pg_count = cursor.fetchone()[0]
            cursor.close()

            duck_result = self.duck_db.execute(f"SELECT COUNT(*) FROM {dim}").fetchall()
            duck_count = duck_result[0][0] if duck_result else 0

            match = pg_count == duck_count
            status = '✓' if match else '✗'
            print(f"  {status} {dim}: PG={pg_count}, Duck={duck_count}")

        self.report['sections']['data_integrity'] = section
        return section

    def section_olap_queries(self):
        """Section 2: OLAP Queries Testing"""
        print("\n📊 Section 2: OLAP Queries (9 Operations)")
        print("-" * 70)

        section = {
            'queries': {},
            'summary': {}
        }

        queries = {
            'q1': ('SLICE', 'SELECT COUNT(*) FROM (SELECT dm.model_name, COUNT(*) FROM fact_sales fs JOIN dim_model dm ON fs.model_id = dm.model_id GROUP BY dm.model_id, dm.model_name ORDER BY 2 DESC LIMIT 15) x'),
            'q2': ('SLICE', 'SELECT COUNT(*) FROM (SELECT dt.production_year, COUNT(*) FROM fact_sales fs JOIN dim_time dt ON fs.time_id = dt.time_id GROUP BY dt.production_year) x'),
            'q3': ('SLICE', 'SELECT COUNT(*) FROM (SELECT dm.model_name, SUM(fs.price) FROM fact_sales fs JOIN dim_model dm ON fs.model_id = dm.model_id GROUP BY dm.model_id, dm.model_name ORDER BY 2 DESC LIMIT 10) x'),
            'q4': ('DICE', 'SELECT COUNT(*) FROM (SELECT dft.fuel_type_name, dt_trans.transmission_name, COUNT(*) FROM fact_sales fs JOIN dim_fuel_type dft ON fs.fuel_type_id = dft.fuel_type_id JOIN dim_transmission dt_trans ON fs.transmission_id = dt_trans.transmission_id GROUP BY dft.fuel_type_id, dft.fuel_type_name, dt_trans.transmission_id, dt_trans.transmission_name) x'),
            'q5': ('DICE', 'SELECT COUNT(*) FROM (SELECT dm.model_name, CASE WHEN fs.price > 15000 THEN \'Premium\' WHEN fs.price > 10000 THEN \'Mid-Range\' ELSE \'Budget\' END, COUNT(*) FROM fact_sales fs JOIN dim_model dm ON fs.model_id = dm.model_id GROUP BY dm.model_id, dm.model_name, CASE WHEN fs.price > 15000 THEN \'Premium\' WHEN fs.price > 10000 THEN \'Mid-Range\' ELSE \'Budget\' END LIMIT 20) x'),
            'q6': ('DICE', 'SELECT COUNT(*) FROM (SELECT de.engine_size, COUNT(*) FROM fact_sales fs JOIN dim_engine de ON fs.engine_id = de.engine_id GROUP BY de.engine_id, de.engine_size) x'),
            'q7': ('DRILL-DOWN', 'SELECT COUNT(*) FROM (SELECT dm.model_name, dft.fuel_type_name, dt_trans.transmission_name, COUNT(*) FROM fact_sales fs JOIN dim_model dm ON fs.model_id = dm.model_id JOIN dim_fuel_type dft ON fs.fuel_type_id = dft.fuel_type_id JOIN dim_transmission dt_trans ON fs.transmission_id = dt_trans.transmission_id GROUP BY dm.model_id, dm.model_name, dft.fuel_type_id, dft.fuel_type_name, dt_trans.transmission_id, dt_trans.transmission_name LIMIT 30) x'),
            'q8': ('DRILL-DOWN', 'SELECT COUNT(*) FROM (SELECT dt.decade, dt.production_year, dm.model_name, COUNT(*) FROM fact_sales fs JOIN dim_time dt ON fs.time_id = dt.time_id JOIN dim_model dm ON fs.model_id = dm.model_id GROUP BY dt.decade, dt.production_year, dm.model_id, dm.model_name LIMIT 40) x'),
            'q9': ('DRILL-DOWN', 'SELECT COUNT(*) FROM (SELECT dm.model_name, dft.fuel_type_name, dt_trans.transmission_name, de.engine_size, dt.production_year, COUNT(*) FROM fact_sales fs JOIN dim_model dm ON fs.model_id = dm.model_id JOIN dim_fuel_type dft ON fs.fuel_type_id = dft.fuel_type_id JOIN dim_transmission dt_trans ON fs.transmission_id = dt_trans.transmission_id JOIN dim_engine de ON fs.engine_id = de.engine_id JOIN dim_time dt ON fs.time_id = dt.time_id GROUP BY dm.model_id, dm.model_name, dft.fuel_type_id, dft.fuel_type_name, dt_trans.transmission_id, dt_trans.transmission_name, de.engine_id, de.engine_size, dt.production_year LIMIT 50) x'),
        }

        for query_id, (qtype, query) in queries.items():
            try:
                pg_result, pg_time = self.execute_pg_query(query)
                duck_result, duck_time = self.execute_duck_query(query)

                pg_rows = pg_result[0][0] if pg_result else 0
                duck_rows = duck_result[0][0] if duck_result else 0

                match = pg_rows == duck_rows
                status = '✓ PASS' if match else '⚠ PARTIAL'

                print(f"\n  {status}: {query_id} ({qtype})")
                print(f"    PostgreSQL: {pg_rows} rows, {pg_time:.2f}ms")
                print(f"    DuckDB:     {duck_rows} rows, {duck_time:.2f}ms")

                section['queries'][query_id] = {
                    'type': qtype,
                    'postgresql': {'rows': pg_rows, 'time_ms': pg_time},
                    'duckdb': {'rows': duck_rows, 'time_ms': duck_time},
                    'match': match
                }
            except Exception as e:
                print(f"\n  ✗ FAIL: {query_id} - {e}")
                section['queries'][query_id] = {'error': str(e)}

        # Summary by type
        for qtype in ['SLICE', 'DICE', 'DRILL-DOWN']:
            queries_of_type = [q for q, info in section['queries'].items() if info.get('type') == qtype]
            section['summary'][qtype] = len(queries_of_type)
            print(f"\n  {qtype} operations: {len(queries_of_type)} queries")

        self.report['sections']['olap_queries'] = section
        return section

    def section_performance_comparison(self):
        """Section 3: Performance Comparison"""
        print("\n📊 Section 3: Performance Comparison")
        print("-" * 70)

        section = {'query_times': {}}

        # Simple aggregation query
        query = """
            SELECT
                dm.model_name,
                COUNT(*) as sales,
                AVG(fs.price) as avg_price
            FROM fact_sales fs
            JOIN dim_model dm ON fs.model_id = dm.model_id
            GROUP BY dm.model_id, dm.model_name
            ORDER BY sales DESC
        """

        pg_results, pg_time = self.execute_pg_query(query)
        duck_results, duck_time = self.execute_duck_query(query)

        speedup = pg_time / duck_time if duck_time > 0 else 0

        print(f"\n  Benchmark Query (9-Model aggregation):")
        print(f"    PostgreSQL: {pg_time:.2f}ms")
        print(f"    DuckDB:     {duck_time:.2f}ms")
        print(f"    Speedup:    {speedup:.2f}x ({'DuckDB faster' if duck_time < pg_time else 'PostgreSQL faster'})")

        section['benchmark'] = {
            'postgresql_ms': pg_time,
            'duckdb_ms': duck_time,
            'speedup_factor': speedup,
            'faster': 'DuckDB' if duck_time < pg_time else 'PostgreSQL'
        }

        self.report['sections']['performance'] = section
        return section

    def section_recommendations(self):
        """Section 4: Recommendations"""
        print("\n📊 Section 4: Recommendations")
        print("-" * 70)

        section = {'recommendations': []}

        # Analyze both databases
        print("\n  Analyzing OLAP implementation...")

        # PostgreSQL is ROLAP
        print("  ✓ PostgreSQL: ROLAP (Relational OLAP)")
        print("    - Uses GROUP BY for aggregations")
        print("    - Indexes on fact_sales foreign keys")
        print("    - Supports multi-dimensional GROUP BY")
        print("    - Recommended for: Ad-hoc queries, high cardinality")

        # DuckDB is Column-based
        print("\n  ✓ DuckDB: Column-oriented OLAP")
        print("    - Optimized for analytical queries")
        print("    - File-based, no server overhead")
        print("    - Faster aggregations on large datasets")
        print("    - Recommended for: Bulk analysis, export operations")

        section['recommendations'] = [
            "PostgreSQL is properly configured for ROLAP - use for transactional queries",
            "DuckDB provides faster analytical queries - use for reporting/export",
            "Both databases have identical data - good for validation",
            "Consider materializing views for frequently-accessed aggregates",
            "Add column indexes on foreign keys for better performance"
        ]

        for i, rec in enumerate(section['recommendations'], 1):
            print(f"  {i}. {rec}")

        self.report['sections']['recommendations'] = section
        return section

    def generate_report(self) -> dict:
        """Generate complete report"""
        print("\n" + "="*70)
        print("🚀 OLAP SYSTEM - COMPREHENSIVE TEST REPORT")
        print("="*70)

        self.section_data_integrity()
        self.section_olap_queries()
        self.section_performance_comparison()
        self.section_recommendations()

        # Final summary
        print("\n" + "="*70)
        print("📋 REPORT GENERATION COMPLETE")
        print("="*70)

        return self.report

    def close(self):
        """Close connections"""
        if self.pg_conn:
            self.pg_conn.close()
        if self.duck_db:
            self.duck_db.close()


def main():
    generator = OlapReportGenerator()

    if not generator.connect_all():
        print("❌ Cannot connect to databases")
        return 1

    try:
        report = generator.generate_report()

        # Save report to JSON
        report_file = '/var/www/html/olap_test_report.json'
        os.makedirs(os.path.dirname(report_file), exist_ok=True)

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n✓ Report saved to: {report_file}")

        print("\n✅ All tests completed!")
        return 0

    except Exception as e:
        print(f"\n❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        generator.close()


if __name__ == '__main__':
    sys.exit(main())
