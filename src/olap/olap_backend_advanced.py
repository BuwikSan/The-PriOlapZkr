#!/usr/bin/env python3
"""
OLAP Backend - Advanced PostgreSQL Operations
Uses GROUPING SETS, ROLLUP, CUBE for optimized hierarchical aggregations
"""

import json
import sys
import time
import os
from typing import Dict, List, Any, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
import duckdb


class AdvancedOlapBackend:
    """Advanced OLAP query engine using GROUPING SETS, ROLLUP, CUBE"""

    # Configuration: use_advanced = True for PostgreSQL optimizations
    USE_ADVANCED = True  # Switch this to enable/disable advanced operations

    def __init__(self, use_advanced: bool = True):
        self.pg_conn = None
        self.duck_db = None
        self.pg_connected = False
        self.duck_connected = False
        self.use_advanced = use_advanced

        if use_advanced:
            print("⚡ Advanced OLAP Mode ENABLED (GROUPING SETS, ROLLUP, CUBE)")
        else:
            print("📊 Standard OLAP Mode (basic GROUP BY)")

    def connect_postgres(self) -> bool:
        """Connect to PostgreSQL database"""
        try:
            self.pg_conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'postgres'),
                port=os.getenv('DB_PORT', '5432'),
                database=os.getenv('DB_NAME', 'bmw_olap'),
                user=os.getenv('DB_USER', 'bmw_user'),
                password=os.getenv('DB_PASS', 'bmw_password')
            )
            self.pg_connected = True
            return True
        except Exception as e:
            self.pg_connected = False
            print(f"PG Error: {e}", file=sys.stderr)
            return False

    def connect_duckdb(self, db_path: str = None) -> bool:
        """Connect to DuckDB database"""
        try:
            if db_path is None:
                db_path = os.getenv('DUCKDB_PATH', '/var/www/html/db/olap.duckdb')
            self.duck_db = duckdb.connect(db_path)
            self.duck_connected = True
            return True
        except Exception as e:
            self.duck_connected = False
            print(f"DuckDB Error: {e}", file=sys.stderr)
            return False

    def execute_pg_query(self, query: str) -> Tuple[List[Dict], float, int]:
        """Execute query on PostgreSQL and return results with timing"""
        if not self.pg_connected:
            if not self.connect_postgres():
                return [], 0.0, 0

        try:
            cursor = self.pg_conn.cursor(cursor_factory=RealDictCursor)
            start = time.time()
            cursor.execute(query)
            results = cursor.fetchall()
            elapsed_ms = (time.time() - start) * 1000
            cursor.close()

            data = [dict(row) for row in results]
            return data, elapsed_ms, len(data)
        except Exception as e:
            print(f"PG Query Error: {e}", file=sys.stderr)
            return [], 0.0, 0

    def execute_duck_query(self, query: str) -> Tuple[List[Dict], float, int]:
        """Execute query on DuckDB and return results with timing"""
        if not self.duck_connected:
            if not self.connect_duckdb():
                return [], 0.0, 0

        try:
            start = time.time()
            result = self.duck_db.execute(query).fetchall()
            elapsed_ms = (time.time() - start) * 1000

            columns = [desc[0] for desc in self.duck_db.description]
            data = [dict(zip(columns, row)) for row in result]
            return data, elapsed_ms, len(data)
        except Exception as e:
            print(f"DuckDB Query Error: {e}", file=sys.stderr)
            return [], 0.0, 0

    # ========== ADVANCED QUERIES - GROUPING SETS / ROLLUP / CUBE ==========

    def query_sales_hierarchy_rollup(self, db: str = 'postgres') -> Dict[str, Any]:
        """
        Q1 ADVANCED: Temporal Hierarchy with ROLLUP
        Generates: (Decade, Year, Model) → (Decade, Year) → (Decade) → Total
        """
        query = """
            SELECT
                dt.decade,
                dt.production_year as year,
                dm.model_name as model,
                COUNT(*) as sales_count,
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price,
                SUM(fs.price) as total_revenue,
                GROUPING(dt.decade) as decade_is_total,
                GROUPING(dt.production_year) as year_is_total,
                GROUPING(dm.model_name) as model_is_total
            FROM fact_sales fs
            JOIN dim_time dt ON fs.time_id = dt.time_id
            JOIN dim_model dm ON fs.model_id = dm.model_id
            GROUP BY ROLLUP (dt.decade, dt.production_year, dm.model_name)
            ORDER BY dt.decade DESC, dt.production_year DESC, sales_count DESC
            LIMIT 100
        """

        results, timing, count = self.execute_pg_query(query)
        return self._format_response(
            query_id='q1_adv',
            name='Temporal Hierarchy (ROLLUP - All Levels)',
            query_type='ROLLUP',
            db=db,
            results=results,
            timing=timing,
            count=count
        )

    def query_sales_cube_all_dimensions(self, db: str = 'postgres') -> Dict[str, Any]:
        """
        Q2 ADVANCED: Complete CUBE across 3 dimensions
        Generates all 8 possible combinations:
        (Model, Fuel, Transmission), (Model, Fuel), (Model, Transmission),
        (Fuel, Transmission), (Model), (Fuel), (Transmission), Total
        """
        query = """
            SELECT
                COALESCE(dm.model_name, 'ALL MODELS') as model,
                COALESCE(dft.fuel_type_name, 'ALL FUELS') as fuel_type,
                COALESCE(dt_trans.transmission_name, 'ALL TRANS') as transmission,
                COUNT(*) as sales_count,
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price,
                SUM(fs.price) as total_revenue,
                GROUPING(dm.model_name) as model_is_total,
                GROUPING(dft.fuel_type_name) as fuel_is_total,
                GROUPING(dt_trans.transmission_name) as trans_is_total,
                GROUPING_ID(dm.model_name, dft.fuel_type_name, dt_trans.transmission_name) as grouping_id
            FROM fact_sales fs
            JOIN dim_model dm ON fs.model_id = dm.model_id
            JOIN dim_fuel_type dft ON fs.fuel_type_id = dft.fuel_type_id
            JOIN dim_transmission dt_trans ON fs.transmission_id = dt_trans.transmission_id
            GROUP BY CUBE (dm.model_name, dft.fuel_type_name, dt_trans.transmission_name)
            ORDER BY grouping_id, sales_count DESC
            LIMIT 150
        """

        results, timing, count = self.execute_pg_query(query)
        return self._format_response(
            query_id='q2_adv',
            name='3D CUBE (All Dimension Combinations)',
            query_type='CUBE',
            db=db,
            results=results,
            timing=timing,
            count=count
        )

    def query_sales_grouping_sets_model_fuel_year(self, db: str = 'postgres') -> Dict[str, Any]:
        """
        Q3 ADVANCED: GROUPING SETS - Specific combinations only
        Returns only selected grouping combinations (more efficient than CUBE):
        (Model, Fuel, Year), (Model, Fuel), (Year), Total
        """
        query = """
            SELECT
                COALESCE(dm.model_name, 'TOTAL') as model,
                COALESCE(dft.fuel_type_name, 'ALL') as fuel_type,
                COALESCE(dt.production_year::TEXT, 'ALL') as year,
                COUNT(*) as sales_count,
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price,
                SUM(fs.price) as total_revenue,
                GROUPING(dm.model_name, dft.fuel_type_name, dt.production_year) as grouping_level
            FROM fact_sales fs
            JOIN dim_model dm ON fs.model_id = dm.model_id
            JOIN dim_fuel_type dft ON fs.fuel_type_id = dft.fuel_type_id
            JOIN dim_time dt ON fs.time_id = dt.time_id
            GROUP BY GROUPING SETS (
                (dm.model_name, dft.fuel_type_name, dt.production_year),  -- Full detail
                (dm.model_name, dft.fuel_type_name),                       -- By Model & Fuel
                (dt.production_year),                                      -- By Year only
                ()                                                          -- Grand Total
            )
            ORDER BY grouping_level, sales_count DESC
            LIMIT 100
        """

        results, timing, count = self.execute_pg_query(query)
        return self._format_response(
            query_id='q3_adv',
            name='GROUPING SETS (Selective Combinations)',
            query_type='GROUPING_SETS',
            db=db,
            results=results,
            timing=timing,
            count=count
        )

    def query_sales_rollup_by_fuel_engine(self, db: str = 'postgres') -> Dict[str, Any]:
        """
        Q4 ADVANCED: ROLLUP by Fuel Type and Engine Size
        Generates: (Fuel, Engine) → (Fuel) → Total
        Useful for analyzing fuel type effectiveness across engine sizes
        """
        query = """
            SELECT
                COALESCE(dft.fuel_type_name, 'TOTAL') as fuel_type,
                COALESCE(de.engine_size::TEXT, 'ALL') as engine_size,
                COUNT(*) as sales_count,
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price,
                ROUND(AVG(fs.mpg)::NUMERIC, 2) as avg_mpg,
                SUM(fs.price) as total_revenue,
                GROUPING(dft.fuel_type_name) as fuel_is_total,
                GROUPING(de.engine_size) as engine_is_total
            FROM fact_sales fs
            JOIN dim_fuel_type dft ON fs.fuel_type_id = dft.fuel_type_id
            JOIN dim_engine de ON fs.engine_id = de.engine_id
            GROUP BY ROLLUP (dft.fuel_type_name, de.engine_size)
            ORDER BY fuel_type, engine_size DESC
        """

        results, timing, count = self.execute_pg_query(query)
        return self._format_response(
            query_id='q4_adv',
            name='ROLLUP: Fuel Type → Engine Size',
            query_type='ROLLUP',
            db=db,
            results=results,
            timing=timing,
            count=count
        )

    def query_sales_cube_model_price_segment(self, db: str = 'postgres') -> Dict[str, Any]:
        """
        Q5 ADVANCED: CUBE with calculated dimension (Price Segment)
        Generates all combinations of: (Model, Segment, Transmission)
        Where Segment is derived: Premium/Mid-Range/Budget
        """
        query = """
            SELECT
                COALESCE(dm.model_name, 'ALL') as model,
                COALESCE(
                    CASE WHEN fs.price > 15000 THEN 'Premium'
                         WHEN fs.price > 10000 THEN 'Mid-Range'
                         ELSE 'Budget'
                    END, 'ALL'
                ) as segment,
                COALESCE(dt_trans.transmission_name, 'ALL') as transmission,
                COUNT(*) as sales_count,
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price,
                ROUND(AVG(fs.mpg)::NUMERIC, 2) as avg_mpg,
                GROUPING_ID(
                    dm.model_name,
                    CASE WHEN fs.price > 15000 THEN 'Premium'
                         WHEN fs.price > 10000 THEN 'Mid-Range'
                         ELSE 'Budget'
                    END,
                    dt_trans.transmission_name
                ) as grouping_id
            FROM fact_sales fs
            JOIN dim_model dm ON fs.model_id = dm.model_id
            JOIN dim_transmission dt_trans ON fs.transmission_id = dt_trans.transmission_id
            GROUP BY CUBE (
                dm.model_name,
                CASE WHEN fs.price > 15000 THEN 'Premium'
                     WHEN fs.price > 10000 THEN 'Mid-Range'
                     ELSE 'Budget'
                END,
                dt_trans.transmission_name
            )
            ORDER BY grouping_id, sales_count DESC
            LIMIT 100
        """

        results, timing, count = self.execute_pg_query(query)
        return self._format_response(
            query_id='q5_adv',
            name='CUBE: Model × Segment × Transmission',
            query_type='CUBE',
            db=db,
            results=results,
            timing=timing,
            count=count
        )

    def query_sales_multidimensional_analysis(self, db: str = 'postgres') -> Dict[str, Any]:
        """
        Q6 ADVANCED: Multi-dimensional Analysis with GROUPING SETS
        Analyzes sales from 4 different analytical perspectives:
        1. Model + Fuel Type breakdown
        2. Year + Engine Size breakdown
        3. Transmission analysis
        4. Grand Total
        """
        query = """
            SELECT
                COALESCE(dm.model_name, 'TOTAL') as model,
                COALESCE(dft.fuel_type_name, 'ALL') as fuel_type,
                COALESCE(dt.production_year::TEXT, 'ALL') as year,
                COALESCE(de.engine_size::TEXT, 'ALL') as engine_size,
                COUNT(*) as sales_count,
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price,
                SUM(fs.price) as total_revenue,
                GROUPING(dm.model_name, dft.fuel_type_name, dt.production_year, de.engine_size) as level
            FROM fact_sales fs
            JOIN dim_model dm ON fs.model_id = dm.model_id
            JOIN dim_fuel_type dft ON fs.fuel_type_id = dft.fuel_type_id
            JOIN dim_time dt ON fs.time_id = dt.time_id
            JOIN dim_engine de ON fs.engine_id = de.engine_id
            GROUP BY GROUPING SETS (
                (dm.model_name, dft.fuel_type_name),
                (dt.production_year, de.engine_size),
                (dt.production_year),
                ()
            )
            ORDER BY level, sales_count DESC
            LIMIT 100
        """

        results, timing, count = self.execute_pg_query(query)
        return self._format_response(
            query_id='q6_adv',
            name='GROUPING SETS: Multi-Dimensional Analysis',
            query_type='GROUPING_SETS',
            db=db,
            results=results,
            timing=timing,
            count=count
        )

    # ========== HELPER METHODS ==========

    def _format_response(self, query_id: str, name: str, query_type: str,
                        db: str, results: List[Dict], timing: float, count: int) -> Dict[str, Any]:
        """Format standardized response"""
        return {
            'query_id': query_id,
            'name': name,
            'type': query_type,
            'database': db,
            'advanced': self.use_advanced,
            'execution_time_ms': round(timing, 2),
            'rows_returned': count,
            'status': 'success' if count > 0 else 'no_results',
            'results': results
        }

    def get_advanced_query_list(self) -> List[Dict[str, str]]:
        """Get available advanced queries"""
        return [
            {'id': 'q1_adv', 'name': 'Temporal Hierarchy', 'type': 'ROLLUP', 'method': 'query_sales_hierarchy_rollup'},
            {'id': 'q2_adv', 'name': '3D CUBE Analysis', 'type': 'CUBE', 'method': 'query_sales_cube_all_dimensions'},
            {'id': 'q3_adv', 'name': 'Selective GROUPING SETS', 'type': 'GROUPING_SETS', 'method': 'query_sales_grouping_sets_model_fuel_year'},
            {'id': 'q4_adv', 'name': 'Fuel-Engine ROLLUP', 'type': 'ROLLUP', 'method': 'query_sales_rollup_by_fuel_engine'},
            {'id': 'q5_adv', 'name': 'Segment CUBE', 'type': 'CUBE', 'method': 'query_sales_cube_model_price_segment'},
            {'id': 'q6_adv', 'name': 'Multi-Dimensional SETS', 'type': 'GROUPING_SETS', 'method': 'query_sales_multidimensional_analysis'},
        ]

    def execute_query_by_id(self, query_id: str, db: str = 'postgres') -> Dict[str, Any]:
        """Execute advanced query by ID"""
        queries = {
            'q1_adv': self.query_sales_hierarchy_rollup,
            'q2_adv': self.query_sales_cube_all_dimensions,
            'q3_adv': self.query_sales_grouping_sets_model_fuel_year,
            'q4_adv': self.query_sales_rollup_by_fuel_engine,
            'q5_adv': self.query_sales_cube_model_price_segment,
            'q6_adv': self.query_sales_multidimensional_analysis,
        }

        if query_id not in queries:
            return {'error': f'Unknown query: {query_id}'}

        return queries[query_id](db)

    def compare_all_queries(self) -> Dict[str, Any]:
        """Execute all 6 advanced queries and return comparison"""
        results = {
            'postgresql': {},
            'duckdb': {},
            'comparison': {}
        }

        for query_id in ['q1_adv', 'q2_adv', 'q3_adv', 'q4_adv', 'q5_adv', 'q6_adv']:
            pg_result = self.execute_query_by_id(query_id, 'postgres')
            duck_result = self.execute_query_by_id(query_id, 'duckdb')

            results['postgresql'][query_id] = pg_result
            results['duckdb'][query_id] = duck_result

            pg_time = pg_result.get('execution_time_ms', 0)
            duck_time = duck_result.get('execution_time_ms', 0)

            speedup = pg_time / duck_time if duck_time > 0 else 0
            faster = 'DuckDB' if duck_time < pg_time else 'PostgreSQL'

            results['comparison'][query_id] = {
                'faster_database': faster,
                'speedup_factor': round(speedup, 2),
                'time_difference_ms': round(abs(pg_time - duck_time), 2)
            }

        return results

    def close(self):
        """Close database connections"""
        if self.pg_conn:
            self.pg_conn.close()
        if self.duck_db:
            self.duck_db.close()


def main():
    """CLI interface for Advanced OLAP backend"""
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: olap_backend_advanced.py <action> [args]'}))
        return

    action = sys.argv[1]

    # Create backend with advanced mode enabled
    backend = AdvancedOlapBackend(use_advanced=True)

    try:
        if action == 'list_queries':
            result = backend.get_advanced_query_list()

        elif action == 'execute_query':
            if len(sys.argv) < 3:
                result = {'error': 'Missing query_id'}
            else:
                query_id = sys.argv[2]
                db = sys.argv[3] if len(sys.argv) > 3 else 'postgres'
                result = backend.execute_query_by_id(query_id, db)

        elif action == 'compare':
            result = backend.compare_all_queries()

        else:
            result = {'error': f'Unknown action: {action}'}

        print(json.dumps(result, indent=2, default=str))

    finally:
        backend.close()


if __name__ == '__main__':
    main()
