#!/usr/bin/env python3
"""
OLAP Backend - BMW Sales Analytics
Supports both PostgreSQL and DuckDB with query timing and comparison
"""

import json
import sys
import time
import os
from typing import Dict, List, Any, Tuple
import psycopg2
import duckdb
from psycopg2.extras import RealDictCursor


class OlapBackend:
    """OLAP query engine for BMW sales data"""

    def __init__(self):
        self.pg_conn = None
        self.duck_db = None
        self.pg_connected = False
        self.duck_connected = False

    def connect_postgres(self) -> bool:
        """Connect to PostgreSQL database"""
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
            self.pg_connected = False
            print(f"PG Error: {e}", file=sys.stderr)
            return False

    def connect_duckdb(self, db_path: str = None) -> bool:
        """Connect to DuckDB database"""
        try:
            # Use env var first, then default
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

            # Convert to list of dicts
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

            # Get column names
            columns = [desc[0] for desc in self.duck_db.description]

            # Convert to list of dicts
            data = [dict(zip(columns, row)) for row in result]
            return data, elapsed_ms, len(data)
        except Exception as e:
            print(f"DuckDB Query Error: {e}", file=sys.stderr)
            return [], 0.0, 0

    # ========== SLICE QUERIES ==========

    def query_sales_by_model(self, db: str = 'postgres') -> Dict[str, Any]:
        """Q1: SLICE - Total sales and avg price by model (all years)"""
        query = """
            SELECT
                dm.model_name as model,
                COUNT(fs.sale_id) as total_sales,
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price,
                SUM(fs.price) as total_revenue,
                ROUND(AVG(fs.mpg)::NUMERIC, 2) as avg_mpg
            FROM fact_sales fs
            JOIN dim_model dm ON fs.model_id = dm.model_id
            GROUP BY dm.model_name
            ORDER BY total_sales DESC
            LIMIT 15
        """

        results, timing, count = self._execute_query(query, db)
        return self._format_response(
            query_id='q1',
            name='Sales by Model (SLICE)',
            query_type='SLICE',
            db=db,
            results=results,
            timing=timing,
            count=count
        )

    def query_sales_by_year(self, db: str = 'postgres') -> Dict[str, Any]:
        """Q2: SLICE - Total sales by production year"""
        query = """
            SELECT
                dt.production_year as year,
                COUNT(fs.sale_id) as total_sales,
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price,
                SUM(fs.price) as total_revenue
            FROM fact_sales fs
            JOIN dim_time dt ON fs.time_id = dt.time_id
            GROUP BY dt.production_year
            ORDER BY dt.production_year DESC
        """

        results, timing, count = self._execute_query(query, db)
        return self._format_response(
            query_id='q2',
            name='Sales by Year (SLICE)',
            query_type='SLICE',
            db=db,
            results=results,
            timing=timing,
            count=count
        )

    def query_top_models_by_revenue(self, db: str = 'postgres') -> Dict[str, Any]:
        """Q3: SLICE - Top 10 models by total revenue"""
        query = """
            SELECT
                dm.model_name as model,
                COUNT(fs.sale_id) as sales_count,
                SUM(fs.price) as total_revenue,
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price
            FROM fact_sales fs
            JOIN dim_model dm ON fs.model_id = dm.model_id
            GROUP BY dm.model_name
            ORDER BY total_revenue DESC
            LIMIT 10
        """

        results, timing, count = self._execute_query(query, db)
        return self._format_response(
            query_id='q3',
            name='Top 10 Models by Revenue (SLICE)',
            query_type='SLICE',
            db=db,
            results=results,
            timing=timing,
            count=count
        )

    # ========== DICE QUERIES ==========

    def query_sales_by_fuel_transmission(self, db: str = 'postgres') -> Dict[str, Any]:
        """Q4: DICE - Sales cross-tab by fuel type and transmission"""
        query = """
            SELECT
                dft.fuel_type_name as fuel_type,
                dt_trans.transmission_name as transmission,
                COUNT(fs.sale_id) as sales_count,
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price,
                ROUND(AVG(fs.mpg)::NUMERIC, 2) as avg_mpg
            FROM fact_sales fs
            JOIN dim_fuel_type dft ON fs.fuel_type_id = dft.fuel_type_id
            JOIN dim_transmission dt_trans ON fs.transmission_id = dt_trans.transmission_id
            GROUP BY dft.fuel_type_name, dt_trans.transmission_name
            ORDER BY sales_count DESC
        """

        results, timing, count = self._execute_query(query, db)
        return self._format_response(
            query_id='q4',
            name='Sales by Fuel Type & Transmission (DICE)',
            query_type='DICE',
            db=db,
            results=results,
            timing=timing,
            count=count
        )

    def query_premium_segment_analysis(self, db: str = 'postgres') -> Dict[str, Any]:
        """Q5: DICE - Premium vs Budget segments by model"""
        query = """
            SELECT
                dm.model_name as model,
                CASE
                    WHEN fs.price > 15000 THEN 'Premium'
                    WHEN fs.price > 10000 THEN 'Mid-Range'
                    ELSE 'Budget'
                END as segment,
                COUNT(fs.sale_id) as sales_count,
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price,
                ROUND(AVG(fs.mpg)::NUMERIC, 2) as avg_mpg
            FROM fact_sales fs
            JOIN dim_model dm ON fs.model_id = dm.model_id
            GROUP BY dm.model_name, segment
            ORDER BY model, avg_price DESC
            LIMIT 20
        """

        results, timing, count = self._execute_query(query, db)
        return self._format_response(
            query_id='q5',
            name='Premium Segment Analysis (DICE)',
            query_type='DICE',
            db=db,
            results=results,
            timing=timing,
            count=count
        )

    def query_engine_performance_analysis(self, db: str = 'postgres') -> Dict[str, Any]:
        """Q6: DICE - Engine size vs MPG correlation"""
        query = """
            SELECT
                de.engine_size,
                COUNT(fs.sale_id) as sales_count,
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price,
                ROUND(AVG(fs.mpg)::NUMERIC, 2) as avg_mpg,
                ROUND(AVG(fs.mileage)::NUMERIC, 2) as avg_mileage
            FROM fact_sales fs
            JOIN dim_engine de ON fs.engine_id = de.engine_id
            GROUP BY de.engine_size
            ORDER BY de.engine_size
        """

        results, timing, count = self._execute_query(query, db)
        return self._format_response(
            query_id='q6',
            name='Engine Performance Analysis (DICE)',
            query_type='DICE',
            db=db,
            results=results,
            timing=timing,
            count=count
        )

    # ========== DRILL-DOWN QUERIES ==========

    def query_model_detail_analysis(self, db: str = 'postgres') -> Dict[str, Any]:
        """Q7: DRILL-DOWN - Model -> Fuel Type -> Transmission details"""
        query = """
            SELECT
                dm.model_name as model,
                dft.fuel_type_name as fuel_type,
                dt_trans.transmission_name as transmission,
                COUNT(fs.sale_id) as sales_count,
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price,
                ROUND(AVG(fs.mpg)::NUMERIC, 2) as avg_mpg,
                MIN(fs.price) as min_price,
                MAX(fs.price) as max_price
            FROM fact_sales fs
            JOIN dim_model dm ON fs.model_id = dm.model_id
            JOIN dim_fuel_type dft ON fs.fuel_type_id = dft.fuel_type_id
            JOIN dim_transmission dt_trans ON fs.transmission_id = dt_trans.transmission_id
            GROUP BY dm.model_name, dft.fuel_type_name, dt_trans.transmission_name
            ORDER BY model, sales_count DESC
            LIMIT 30
        """

        results, timing, count = self._execute_query(query, db)
        return self._format_response(
            query_id='q7',
            name='Model Detail Drill-Down (DRILL-DOWN)',
            query_type='DRILL-DOWN',
            db=db,
            results=results,
            timing=timing,
            count=count
        )

    def query_temporal_analysis(self, db: str = 'postgres') -> Dict[str, Any]:
        """Q8: DRILL-DOWN - Year -> Model -> Segment hierarchy"""
        query = """
            SELECT
                dt.decade,
                dt.production_year as year,
                dm.model_name as model,
                COUNT(fs.sale_id) as sales_count,
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price,
                SUM(fs.price) as total_revenue
            FROM fact_sales fs
            JOIN dim_time dt ON fs.time_id = dt.time_id
            JOIN dim_model dm ON fs.model_id = dm.model_id
            GROUP BY dt.decade, dt.production_year, dm.model_name
            ORDER BY dt.decade DESC, dt.production_year DESC, sales_count DESC
            LIMIT 40
        """

        results, timing, count = self._execute_query(query, db)
        return self._format_response(
            query_id='q8',
            name='Temporal Analysis Drill-Down (DRILL-DOWN)',
            query_type='DRILL-DOWN',
            db=db,
            results=results,
            timing=timing,
            count=count
        )

    def query_complete_hierarchy(self, db: str = 'postgres') -> Dict[str, Any]:
        """Q9: DRILL-DOWN - Complete hierarchy with all dimensions"""
        query = """
            SELECT
                dm.model_name as model,
                dft.fuel_type_name as fuel_type,
                dt_trans.transmission_name as transmission,
                de.engine_size as engine,
                dt.production_year as year,
                COUNT(fs.sale_id) as sales_count,
                ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price,
                ROUND(AVG(fs.mileage)::NUMERIC, 2) as avg_mileage,
                ROUND(AVG(fs.mpg)::NUMERIC, 2) as avg_mpg
            FROM fact_sales fs
            JOIN dim_model dm ON fs.model_id = dm.model_id
            JOIN dim_fuel_type dft ON fs.fuel_type_id = dft.fuel_type_id
            JOIN dim_transmission dt_trans ON fs.transmission_id = dt_trans.transmission_id
            JOIN dim_engine de ON fs.engine_id = de.engine_id
            JOIN dim_time dt ON fs.time_id = dt.time_id
            GROUP BY dm.model_name, dft.fuel_type_name, dt_trans.transmission_name,
                     de.engine_size, dt.production_year
            ORDER BY sales_count DESC
            LIMIT 50
        """

        results, timing, count = self._execute_query(query, db)
        return self._format_response(
            query_id='q9',
            name='Complete Hierarchy Analysis (DRILL-DOWN)',
            query_type='DRILL-DOWN',
            db=db,
            results=results,
            timing=timing,
            count=count
        )

    # ========== HELPER METHODS ==========

    def _execute_query(self, query: str, db: str) -> Tuple[List[Dict], float, int]:
        """Execute query on specified database"""
        if db == 'duckdb':
            return self.execute_duck_query(query)
        else:
            return self.execute_pg_query(query)

    def _format_response(self, query_id: str, name: str, query_type: str,
                        db: str, results: List[Dict], timing: float, count: int) -> Dict[str, Any]:
        """Format standardized response"""
        return {
            'query_id': query_id,
            'name': name,
            'type': query_type,
            'database': db,
            'execution_time_ms': round(timing, 2),
            'rows_returned': count,
            'status': 'success' if count > 0 else 'no_results',
            'results': results
        }

    def get_query_list(self) -> List[Dict[str, str]]:
        """Get available queries"""
        return [
            {'id': 'q1', 'name': 'Sales by Model', 'type': 'SLICE', 'method': 'query_sales_by_model'},
            {'id': 'q2', 'name': 'Sales by Year', 'type': 'SLICE', 'method': 'query_sales_by_year'},
            {'id': 'q3', 'name': 'Top 10 Models by Revenue', 'type': 'SLICE', 'method': 'query_top_models_by_revenue'},
            {'id': 'q4', 'name': 'Sales by Fuel & Transmission', 'type': 'DICE', 'method': 'query_sales_by_fuel_transmission'},
            {'id': 'q5', 'name': 'Premium Segment Analysis', 'type': 'DICE', 'method': 'query_premium_segment_analysis'},
            {'id': 'q6', 'name': 'Engine Performance Analysis', 'type': 'DICE', 'method': 'query_engine_performance_analysis'},
            {'id': 'q7', 'name': 'Model Detail Drill-Down', 'type': 'DRILL-DOWN', 'method': 'query_model_detail_analysis'},
            {'id': 'q8', 'name': 'Temporal Drill-Down', 'type': 'DRILL-DOWN', 'method': 'query_temporal_analysis'},
            {'id': 'q9', 'name': 'Complete Hierarchy', 'type': 'DRILL-DOWN', 'method': 'query_complete_hierarchy'},
        ]

    def execute_query_by_id(self, query_id: str, db: str = 'postgres') -> Dict[str, Any]:
        """Execute query by ID and return results"""
        queries = {
            'q1': self.query_sales_by_model,
            'q2': self.query_sales_by_year,
            'q3': self.query_top_models_by_revenue,
            'q4': self.query_sales_by_fuel_transmission,
            'q5': self.query_premium_segment_analysis,
            'q6': self.query_engine_performance_analysis,
            'q7': self.query_model_detail_analysis,
            'q8': self.query_temporal_analysis,
            'q9': self.query_complete_hierarchy,
        }

        if query_id not in queries:
            return {'error': f'Unknown query: {query_id}'}

        return queries[query_id](db)

    def compare_query_performance(self, query_id: str) -> Dict[str, Any]:
        """Execute query on both databases and compare"""
        pg_result = self.execute_query_by_id(query_id, 'postgres')
        duck_result = self.execute_query_by_id(query_id, 'duckdb')

        pg_time = pg_result.get('execution_time_ms', 0)
        duck_time = duck_result.get('execution_time_ms', 0)

        speedup = pg_time / duck_time if duck_time > 0 else 0
        faster = 'DuckDB' if duck_time < pg_time else 'PostgreSQL'

        return {
            'query_id': query_id,
            'postgres': pg_result,
            'duckdb': duck_result,
            'comparison': {
                'faster_database': faster,
                'speedup_factor': round(speedup, 2),
                'time_difference_ms': round(abs(pg_time - duck_time), 2)
            }
        }

    def close(self):
        """Close database connections"""
        if self.pg_conn:
            self.pg_conn.close()
        if self.duck_db:
            self.duck_db.close()


def main():
    """CLI interface for OLAP backend"""
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: olap_backend.py <action> [args]'}))
        return

    action = sys.argv[1]
    backend = OlapBackend()

    try:
        if action == 'list_queries':
            result = backend.get_query_list()

        elif action == 'execute_query':
            if len(sys.argv) < 3:
                result = {'error': 'Missing query_id'}
            else:
                query_id = sys.argv[2]
                db = sys.argv[3] if len(sys.argv) > 3 else 'postgres'
                result = backend.execute_query_by_id(query_id, db)

        elif action == 'compare':
            if len(sys.argv) < 3:
                result = {'error': 'Missing query_id'}
            else:
                query_id = sys.argv[2]
                result = backend.compare_query_performance(query_id)

        else:
            result = {'error': f'Unknown action: {action}'}

        print(json.dumps(result, indent=2, default=str))

    finally:
        backend.close()


if __name__ == '__main__':
    main()
