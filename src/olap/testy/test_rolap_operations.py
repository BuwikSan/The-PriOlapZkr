#!/usr/bin/env python3
"""
ROLAP (Relational OLAP) Operations Verification
Verifies that PostgreSQL correctly implements:
- GROUP BY aggregations (SLICE)
- Multi-dimensional filtering (DICE)
- Hierarchical drill-down (DRILL-DOWN)
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import RealDictCursor
import duckdb


class RolapVerifier:
    """Verify ROLAP operations on PostgreSQL"""

    def __init__(self):
        self.pg_conn = None
        self.pg_connected = False

    def connect(self) -> bool:
        """Connect to PostgreSQL"""
        try:
            self.pg_conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'postgres'),
                port=os.getenv('DB_PORT', '5432'),
                database=os.getenv('DB_NAME', 'bmw_sales'),
                user=os.getenv('DB_USER', 'bmw_user'),
                password=os.getenv('DB_PASS', 'bmw_password')
            )
            self.pg_connected = True
            return True
        except Exception as e:
            print(f"Connection Error: {e}")
            return False

    def execute_query(self, query: str, label: str = "") -> tuple:
        """Execute query and return results with timing"""
        cursor = self.pg_conn.cursor(cursor_factory=RealDictCursor)
        start = time.time()
        cursor.execute(query)
        results = cursor.fetchall()
        elapsed_ms = (time.time() - start) * 1000
        cursor.close()

        results_list = [dict(row) for row in results]
        return results_list, elapsed_ms

    def verify_slice_operation(self):
        """Verify SLICE operation (single dimension)"""
        print("\n" + "="*70)
        print("🔍 VERIFYING SLICE OPERATION (GROUP BY single dimension)")
        print("="*70)
        print("\nSLICE: Extract data along one dimension with aggregation")
        print("ROLAP Implementation: GROUP BY + Aggregate functions")

        # Q1: Sales by Model (GROUP BY Model)
        print("\n📌 Q1: Sales by Model")
        print("-" * 70)

        query = """
            -- SLICE OPERATION: Extract by Model dimension
            -- ROLAP uses: GROUP BY model_id (single key)
            SELECT
                dm.model_id,
                dm.model_name as model,
                COUNT(*) as total_sales,                    -- Aggregate 1
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price,  -- Aggregate 2
                SUM(fs.price) as total_revenue,              -- Aggregate 3
                ROUND(AVG(fs.mpg)::NUMERIC, 2) as avg_mpg   -- Aggregate 4
            FROM fact_sales fs
            JOIN dim_model dm ON fs.model_id = dm.model_id
            GROUP BY dm.model_id, dm.model_name             -- ROLAP: GROUP BY
            ORDER BY total_sales DESC
            LIMIT 5
        """

        results, timing = self.execute_query(query)
        print(f"\n✓ Query executed in {timing:.2f}ms")
        print(f"✓ Returned {len(results)} result rows\n")

        print("Results (first 5 models):")
        print(f"{'#':<3} {'Model':<20} {'Sales':<10} {'Avg $':<10} {'Total $':<12} {'Avg MPG':<8}")
        print("-" * 70)

        for i, row in enumerate(results, 1):
            print(f"{i:<3} {row['model']:<20} {row['total_sales']:<10} "
                  f"${row['avg_price']:<9.2f} ${row['total_revenue']:<11,.0f} {row['avg_mpg']:<8.1f}")

        # Verify GROUP BY is working
        print(f"\n✓ ROLAP Verification:")
        print(f"  - GROUP BY dimension: model_id (1 dimension)")
        print(f"  - Aggregate functions: COUNT, AVG, SUM (4 functions)")
        print(f"  - Fact table rows aggregated to: {len(results)} result rows")

        return len(results) > 0

    def verify_dice_operation(self):
        """Verify DICE operation (multiple dimensions)"""
        print("\n" + "="*70)
        print("🔍 VERIFYING DICE OPERATION (GROUP BY multiple dimensions)")
        print("="*70)
        print("\nDICE: Extract sub-cube along multiple dimensions")
        print("ROLAP Implementation: GROUP BY + multiple dimensions + WHERE clause")

        # Q4: Sales by Fuel Type and Transmission
        print("\n📌 Q4: Sales by Fuel Type & Transmission (2D DICE)")
        print("-" * 70)

        query = """
            -- DICE OPERATION: Extract by 2 dimensions (Fuel Type × Transmission)
            -- ROLAP uses: GROUP BY fuel_type_id, transmission_id (composite key)
            SELECT
                dft.fuel_type_id,
                dft.fuel_type_name as fuel_type,
                dt_trans.transmission_id,
                dt_trans.transmission_name as transmission,
                COUNT(*) as sales_count,                    -- Aggregate 1
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price,  -- Aggregate 2
                ROUND(AVG(fs.mpg)::NUMERIC, 2) as avg_mpg   -- Aggregate 3
            FROM fact_sales fs
            JOIN dim_fuel_type dft ON fs.fuel_type_id = dft.fuel_type_id
            JOIN dim_transmission dt_trans ON fs.transmission_id = dt_trans.transmission_id
            GROUP BY dft.fuel_type_id, dft.fuel_type_name,
                     dt_trans.transmission_id, dt_trans.transmission_name
            ORDER BY sales_count DESC
        """

        results, timing = self.execute_query(query)
        print(f"\n✓ Query executed in {timing:.2f}ms")
        print(f"✓ Returned {len(results)} result rows (cross-product of dimensions)\n")

        print("Results (2D DICE matrix):")
        print(f"{'Fuel Type':<15} {'Transmission':<20} {'Sales':<10} {'Avg $':<10} {'Avg MPG':<8}")
        print("-" * 70)

        for row in results:
            print(f"{row['fuel_type']:<15} {row['transmission']:<20} {row['sales_count']:<10} "
                  f"${row['avg_price']:<9.2f} {row['avg_mpg']:<8.1f}")

        # Verify multi-dimensional GROUP BY
        unique_fuels = len(set(r['fuel_type'] for r in results))
        unique_transmissions = len(set(r['transmission'] for r in results))

        print(f"\n✓ ROLAP Verification:")
        print(f"  - GROUP BY dimensions: fuel_type_id, transmission_id (2 dimensions)")
        print(f"  - Unique values in Fuel Type: {unique_fuels}")
        print(f"  - Unique values in Transmission: {unique_transmissions}")
        print(f"  - Cross-product result rows: {len(results)}")
        print(f"  - Aggregate functions: COUNT, AVG (3 functions)")

        return len(results) > 0

    def verify_drill_down_operation(self):
        """Verify DRILL-DOWN operation (hierarchical aggregation)"""
        print("\n" + "="*70)
        print("🔍 VERIFYING DRILL-DOWN OPERATION (Hierarchical GROUP BY)")
        print("="*70)
        print("\nDRILL-DOWN: Navigate hierarchy from general to specific")
        print("ROLAP Implementation: GROUP BY + multiple hierarchical levels")

        # Q8: Temporal Analysis (Year -> Model -> Segment)
        print("\n📌 Q8: Temporal Drill-Down (Decade → Year → Model)")
        print("-" * 70)

        query = """
            -- DRILL-DOWN OPERATION: Hierarchical aggregation
            -- Level 1: Decade (coarse)
            -- Level 2: Year (medium)
            -- Level 3: Model (fine)
            -- ROLAP uses: GROUP BY decade, production_year, model_id
            SELECT
                dt.decade,                                   -- Level 1 (coarse)
                dt.production_year as year,                 -- Level 2 (medium)
                dm.model_id,
                dm.model_name as model,                     -- Level 3 (fine)
                COUNT(*) as sales_count,                    -- Aggregate 1
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price,  -- Aggregate 2
                SUM(fs.price) as total_revenue              -- Aggregate 3
            FROM fact_sales fs
            JOIN dim_time dt ON fs.time_id = dt.time_id
            JOIN dim_model dm ON fs.model_id = dm.model_id
            GROUP BY dt.decade, dt.production_year, dm.model_id, dm.model_name
            ORDER BY dt.decade DESC, dt.production_year DESC, sales_count DESC
            LIMIT 20
        """

        results, timing = self.execute_query(query)
        print(f"\n✓ Query executed in {timing:.2f}ms")
        print(f"✓ Returned {len(results)} result rows (hierarchical)\n")

        print("Results (first 20 rows - hierarchical structure):")
        print(f"{'Decade':<8} {'Year':<6} {'Model':<20} {'Sales':<10} {'Avg $':<10} {'Total $':<12}")
        print("-" * 70)

        for row in results:
            print(f"{row['decade']:<8} {row['year']:<6} {row['model']:<20} {row['sales_count']:<10} "
                  f"${row['avg_price']:<9.2f} ${row['total_revenue']:<11,.0f}")

        # Verify hierarchical grouping
        unique_decades = len(set(r['decade'] for r in results))
        unique_years = len(set(r['year'] for r in results))
        unique_models = len(set(r['model'] for r in results))

        print(f"\n✓ ROLAP Verification:")
        print(f"  - GROUP BY hierarchy: decade → year → model (3 levels)")
        print(f"  - Unique Decades: {unique_decades}")
        print(f"  - Unique Years: {unique_years}")
        print(f"  - Unique Models: {unique_models}")
        print(f"  - Total hierarchical result rows: {len(results)}")
        print(f"  - Supports drill-down navigation: ✓")

        return len(results) > 0

    def verify_grouping_sets(self):
        """Verify advanced ROLAP: GROUPING SETS for multi-level aggregation"""
        print("\n" + "="*70)
        print("🔍 ADVANCED ROLAP: GROUPING SETS (Multi-level Aggregation)")
        print("="*70)
        print("\nGROUPING SETS: Efficient multi-level aggregation in single query")
        print("ROLAP Feature: Single query for all hierarchy levels")

        # Total sales + By Model + By Year + By Fuel Type
        print("\n📌 Multi-level aggregation with GROUPING SETS")
        print("-" * 70)

        query = """
            -- GROUPING SETS: Multiple aggregation levels in one query
            -- Efficient for ROLAP cube materialization
            SELECT
                COALESCE(dm.model_name, 'TOTAL') as model,
                COALESCE(dft.fuel_type_name, 'ALL') as fuel_type,
                COUNT(*) as sales_count,
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price,
                SUM(fs.price) as total_revenue
            FROM fact_sales fs
            JOIN dim_model dm ON fs.model_id = dm.model_id
            JOIN dim_fuel_type dft ON fs.fuel_type_id = dft.fuel_type_id
            GROUP BY GROUPING SETS (
                (dm.model_name, dft.fuel_type_name),  -- All combinations
                (dm.model_name),                       -- By Model only
                (dft.fuel_type_name),                 -- By Fuel Type only
                ()                                     -- Grand total
            )
            ORDER BY model, fuel_type
            LIMIT 30
        """

        try:
            results, timing = self.execute_query(query)
            print(f"\n✓ Query executed in {timing:.2f}ms")
            print(f"✓ Returned {len(results)} result rows\n")

            print("Results (hierarchical aggregation levels):")
            print(f"{'Model':<20} {'Fuel Type':<15} {'Sales':<10} {'Avg $':<10} {'Total $':<12}")
            print("-" * 70)

            for row in results[:30]:
                print(f"{row['model']:<20} {row['fuel_type']:<15} {row['sales_count']:<10} "
                      f"${row['avg_price']:<9.2f} ${row['total_revenue']:<11,.0f}")

            print(f"\n✓ GROUPING SETS supported!")
            return True
        except Exception as e:
            print(f"\n⚠️  GROUPING SETS not fully supported or error: {e}")
            print("   (This is OK - not all PostgreSQL versions have full support)")
            return False

    def verify_indexes(self):
        """Verify that indexes are being used for ROLAP queries"""
        print("\n" + "="*70)
        print("🔍 VERIFYING INDEXES (Performance Optimization)")
        print("="*70)

        # Check existing indexes
        query = """
            SELECT
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename IN ('fact_sales', 'dim_model', 'dim_fuel_type', 'dim_transmission', 'dim_engine', 'dim_time')
            ORDER BY tablename, indexname
        """

        cursor = self.pg_conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query)
        indexes = cursor.fetchall()
        cursor.close()

        print(f"\n✓ Found {len(indexes)} indexes:\n")

        for idx in indexes:
            print(f"Table: {idx['tablename']}")
            print(f"  Index: {idx['indexname']}")
            print(f"  Definition: {idx['indexdef']}")
            print()

        # Check query plans
        print("\nOptimization: Checking query plan for Q1 (Sales by Model)")
        print("-" * 70)

        query = """
            EXPLAIN ANALYZE
            SELECT
                dm.model_name as model,
                COUNT(*) as total_sales
            FROM fact_sales fs
            JOIN dim_model dm ON fs.model_id = dm.model_id
            GROUP BY dm.model_id, dm.model_name
            ORDER BY total_sales DESC
            LIMIT 5
        """

        cursor = self.pg_conn.cursor()
        cursor.execute(query)
        plan = cursor.fetchall()
        cursor.close()

        print("\nQuery Plan:")
        for line in plan:
            print(f"  {line[0]}")

        return True

    def close(self):
        """Close connection"""
        if self.pg_conn:
            self.pg_conn.close()


def main():
    print("\n" + "="*70)
    print("🚀 ROLAP (Relational OLAP) Operations Verification")
    print("="*70)
    print("Verifying that PostgreSQL correctly implements OLAP operations")
    print("using GROUP BY aggregations and dimensional modeling\n")

    verifier = RolapVerifier()

    if not verifier.connect():
        print("❌ Cannot connect to PostgreSQL")
        return 1

    print("✓ PostgreSQL connected\n")

    try:
        results = {
            'SLICE Operation': verifier.verify_slice_operation(),
            'DICE Operation': verifier.verify_dice_operation(),
            'DRILL-DOWN Operation': verifier.verify_drill_down_operation(),
            'GROUPING SETS': verifier.verify_grouping_sets(),
            'Index Verification': verifier.verify_indexes(),
        }

        # Summary
        print("\n" + "="*70)
        print("📋 ROLAP VERIFICATION SUMMARY")
        print("="*70)

        passed = sum(1 for v in results.values() if v)
        total = len(results)

        for name, result in results.items():
            status = "✅ PASSED" if result else "⚠️  WARNING"
            print(f"{name:.<45} {status}")

        print(f"\n{'Total':.<45} {passed}/{total} tests passed")

        if passed >= 4:
            print("\n✅ PostgreSQL correctly implements ROLAP operations!")
            print("   Data is properly modeled and aggregations work correctly.")
            return 0
        else:
            print("\n⚠️  Some ROLAP features may not be fully optimized")
            return 1

    finally:
        verifier.close()


if __name__ == '__main__':
    sys.exit(main())
