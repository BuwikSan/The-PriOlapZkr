#!/usr/bin/env python3
"""
Benchmark: Standard vs Advanced OLAP Operations
Compares performance and results between:
- Standard Mode: Basic GROUP BY queries
- Advanced Mode: GROUPING SETS, ROLLUP, CUBE queries
"""

import sys
import os
import time
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import RealDictCursor


class BenchmarkComparison:
    """Compare standard vs advanced OLAP operations"""

    def __init__(self):
        self.pg_conn = None

    def connect(self) -> bool:
        """Connect to PostgreSQL"""
        try:
            self.pg_conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'postgres'),
                port=os.getenv('DB_PORT', '5432'),
                database=os.getenv('DB_NAME', 'bmw_olap'),
                user=os.getenv('DB_USER', 'bmw_user'),
                password=os.getenv('DB_PASS', 'bmw_password')
            )
            return True
        except Exception as e:
            print(f"Connection Error: {e}")
            return False

    def execute_query(self, query: str) -> tuple:
        """Execute query and return results with timing"""
        cursor = self.pg_conn.cursor(cursor_factory=RealDictCursor)
        start = time.time()
        cursor.execute(query)
        results = cursor.fetchall()
        elapsed_ms = (time.time() - start) * 1000
        cursor.close()
        return [dict(row) for row in results], elapsed_ms

    def benchmark_standard_queries(self):
        """Benchmark 3 standard queries"""
        print("\n" + "="*70)
        print("📊 STANDARD MODE - Basic GROUP BY Queries")
        print("="*70)

        queries = {
            'q1_std': {
                'name': 'Sales by Model',
                'query': """
                    SELECT dm.model_name as model, COUNT(*) as sales_count
                    FROM fact_sales fs
                    JOIN dim_model dm ON fs.model_id = dm.model_id
                    GROUP BY dm.model_id, dm.model_name
                    ORDER BY sales_count DESC
                    LIMIT 15
                """
            },
            'q2_std': {
                'name': 'Sales by Fuel Type',
                'query': """
                    SELECT dft.fuel_type_name, COUNT(*) as sales_count,
                           AVG(fs.price) as avg_price
                    FROM fact_sales fs
                    JOIN dim_fuel_type dft ON fs.fuel_type_id = dft.fuel_type_id
                    GROUP BY dft.fuel_type_id, dft.fuel_type_name
                    ORDER BY sales_count DESC
                """
            },
            'q3_std': {
                'name': 'Sales by Year',
                'query': """
                    SELECT dt.production_year, COUNT(*) as sales_count,
                           SUM(fs.price) as total_revenue
                    FROM fact_sales fs
                    JOIN dim_time dt ON fs.time_id = dt.time_id
                    GROUP BY dt.production_year
                    ORDER BY dt.production_year DESC
                """
            }
        }

        results = {}
        for query_id, query_info in queries.items():
            print(f"\n📌 {query_id}: {query_info['name']}")
            data, timing = self.execute_query(query_info['query'])
            print(f"   Rows: {len(data)}, Time: {timing:.2f}ms")
            results[query_id] = {'rows': len(data), 'time_ms': timing}

        return results

    def benchmark_advanced_queries(self):
        """Benchmark 3 advanced queries using GROUPING SETS, ROLLUP, CUBE"""
        print("\n" + "="*70)
        print("⚡ ADVANCED MODE - GROUPING SETS, ROLLUP, CUBE Queries")
        print("="*70)

        queries = {
            'q1_adv': {
                'name': 'ROLLUP: Temporal Hierarchy (Decade → Year → Model)',
                'query': """
                    SELECT dt.decade, dt.production_year, dm.model_name,
                           COUNT(*) as sales_count, SUM(fs.price) as revenue,
                           GROUPING(dt.decade) as d_total,
                           GROUPING(dt.production_year) as y_total,
                           GROUPING(dm.model_name) as m_total
                    FROM fact_sales fs
                    JOIN dim_time dt ON fs.time_id = dt.time_id
                    JOIN dim_model dm ON fs.model_id = dm.model_id
                    GROUP BY ROLLUP (dt.decade, dt.production_year, dm.model_name)
                    ORDER BY dt.decade DESC, dt.production_year DESC
                    LIMIT 100
                """
            },
            'q2_adv': {
                'name': 'CUBE: Model × Fuel × Transmission (8 combinations)',
                'query': """
                    SELECT COALESCE(dm.model_name, 'ALL') as model,
                           COALESCE(dft.fuel_type_name, 'ALL') as fuel,
                           COALESCE(dt_trans.transmission_name, 'ALL') as trans,
                           COUNT(*) as sales_count, AVG(fs.price) as avg_price,
                           GROUPING(dm.model_name) as m_total,
                           GROUPING(dft.fuel_type_name) as f_total,
                           GROUPING(dt_trans.transmission_name) as t_total
                    FROM fact_sales fs
                    JOIN dim_model dm ON fs.model_id = dm.model_id
                    JOIN dim_fuel_type dft ON fs.fuel_type_id = dft.fuel_type_id
                    JOIN dim_transmission dt_trans ON fs.transmission_id = dt_trans.transmission_id
                    GROUP BY CUBE (dm.model_name, dft.fuel_type_name, dt_trans.transmission_name)
                    LIMIT 150
                """
            },
            'q3_adv': {
                'name': 'GROUPING SETS: Selective Combinations',
                'query': """
                    SELECT COALESCE(dm.model_name, 'TOTAL') as model,
                           COALESCE(dft.fuel_type_name, 'ALL') as fuel,
                           COALESCE(dt.production_year::TEXT, 'ALL') as year,
                           COUNT(*) as sales_count, SUM(fs.price) as revenue
                    FROM fact_sales fs
                    JOIN dim_model dm ON fs.model_id = dm.model_id
                    JOIN dim_fuel_type dft ON fs.fuel_type_id = dft.fuel_type_id
                    JOIN dim_time dt ON fs.time_id = dt.time_id
                    GROUP BY GROUPING SETS (
                        (dm.model_name, dft.fuel_type_name, dt.production_year),
                        (dm.model_name, dft.fuel_type_name),
                        (dt.production_year),
                        ()
                    )
                    ORDER BY sales_count DESC
                    LIMIT 100
                """
            }
        }

        results = {}
        for query_id, query_info in queries.items():
            print(f"\n📌 {query_id}: {query_info['name']}")
            data, timing = self.execute_query(query_info['query'])
            print(f"   Rows: {len(data)}, Time: {timing:.2f}ms")
            results[query_id] = {'rows': len(data), 'time_ms': timing}

        return results

    def run_benchmark(self):
        """Run full benchmark comparison"""
        print("\n" + "="*70)
        print("🚀 OLAP Operations Benchmark - Standard vs Advanced")
        print("="*70)

        if not self.connect():
            print("❌ Cannot connect to PostgreSQL")
            return

        std_results = self.benchmark_standard_queries()
        adv_results = self.benchmark_advanced_queries()

        # Summary
        print("\n" + "="*70)
        print("📋 BENCHMARK SUMMARY")
        print("="*70)

        std_total_time = sum(r['time_ms'] for r in std_results.values())
        adv_total_time = sum(r['time_ms'] for r in adv_results.values())

        print(f"\nStandard Mode (3 basic queries):")
        print(f"  Total time: {std_total_time:.2f}ms")
        print(f"  Avg time:   {std_total_time/3:.2f}ms per query")
        print(f"  Total rows: {sum(r['rows'] for r in std_results.values())}")

        print(f"\nAdvanced Mode (3 advanced queries):")
        print(f"  Total time: {adv_total_time:.2f}ms")
        print(f"  Avg time:   {adv_total_time/3:.2f}ms per query")
        print(f"  Total rows: {sum(r['rows'] for r in adv_results.values())}")

        speedup = std_total_time / adv_total_time if adv_total_time > 0 else 0
        efficiency = ((std_total_time - adv_total_time) / std_total_time * 100) if std_total_time > 0 else 0

        print(f"\n⚡ Advanced Mode Performance:")
        print(f"  Speedup:    {speedup:.2f}x")
        print(f"  Efficiency: {efficiency:.1f}% faster")

        print(f"\n💡 Additional Data from Advanced Mode:")
        print(f"  Advanced queries return MORE analytical data in single query")
        print(f"  Standard: 3 separate queries × N database calls")
        print(f"  Advanced: 3 queries × 1 database call (hierarchical aggregations)")

        self.close()

    def close(self):
        """Close connection"""
        if self.pg_conn:
            self.pg_conn.close()


def main():
    benchmark = BenchmarkComparison()
    benchmark.run_benchmark()


if __name__ == '__main__':
    main()
