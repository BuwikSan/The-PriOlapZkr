"""
Database Configuration & Connection Management
Unified interface for PostgreSQL and DuckDB access
"""

import psycopg2
import duckdb
import os
from typing import Optional


# ============================================================================
# CONFIGURATION
# ============================================================================

# PostgreSQL Configuration
PG_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'bmw_olap'),
    'user': os.getenv('DB_USER', 'bmw_user'),
    'password': os.getenv('DB_PASSWORD', 'bmw_password'),
}

# DuckDB Configuration
DUCKDB_PATH = os.getenv('DUCKDB_PATH', '/var/www/db/olap.duckdb')


# ============================================================================
# DATABASE MANAGER (Singleton Pattern)
# ============================================================================

class DatabaseManager:
    """
    Unified interface for database connections.
    Implements connection pooling and error handling.
    """
    
    _pg_conn: Optional[psycopg2.extensions.connection] = None
    _duck_conn: Optional[duckdb.DuckDBPyConnection] = None
    
    @staticmethod
    def get_postgresql() -> psycopg2.extensions.connection:
        """Get PostgreSQL connection (create if needed)"""
        try:
            if DatabaseManager._pg_conn is None or DatabaseManager._pg_conn.closed:
                DatabaseManager._pg_conn = psycopg2.connect(**PG_CONFIG)
                print("✓ PostgreSQL connected")
            return DatabaseManager._pg_conn
        except Exception as e:
            print(f"✗ PostgreSQL error: {e}")
            raise
    
    @staticmethod
    def get_duckdb() -> duckdb.DuckDBPyConnection:
        """Get DuckDB connection (create if needed)"""
        try:
            if DatabaseManager._duck_conn is None:
                DatabaseManager._duck_conn = duckdb.connect(DUCKDB_PATH)
                print(f"✓ DuckDB connected: {DUCKDB_PATH}")
            return DatabaseManager._duck_conn
        except Exception as e:
            print(f"✗ DuckDB error: {e}")
            raise
    
    @staticmethod
    def close_all():
        """Close all connections"""
        if DatabaseManager._pg_conn and not DatabaseManager._pg_conn.closed:
            DatabaseManager._pg_conn.close()
            print("✓ PostgreSQL closed")
        
        if DatabaseManager._duck_conn:
            DatabaseManager._duck_conn.close()
            print("✓ DuckDB closed")


# ============================================================================
# WRAPPER CLASSES
# ============================================================================

class PostgreSQLOLAP:
    """PostgreSQL connection wrapper for OLAP queries"""
    
    def __init__(self):
        self.conn = DatabaseManager.get_postgresql()
    
    def execute_query(self, query: str) -> list:
        """Execute query and return results as list of dicts"""
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(query)
        return cursor.fetchall()
    
    def execute_scalar(self, query: str):
        """Execute query and return first value"""
        cursor = self.conn.cursor()
        cursor.execute(query)
        return cursor.fetchone()[0]
    
    def close(self):
        self.conn.close()


class DuckDBANALYTICS:
    """DuckDB connection wrapper for fast analytics"""
    
    def __init__(self):
        self.conn = DatabaseManager.get_duckdb()
    
    def execute_query(self, query: str):
        """Execute query and return results as list of tuples"""
        return self.conn.execute(query).fetchall()
    
    def execute_fetch_df(self, query: str):
        """Execute query and return Pandas DataFrame"""
        return self.conn.execute(query).fetchdf()
    
    def execute_fetch_arrow(self, query: str):
        """Execute query and return PyArrow Table"""
        return self.conn.execute(query).fetch_arrow_table()
    
    def get_table_schema(self, table_name: str) -> dict:
        """Get table schema (column names + types)"""
        query = f"DESCRIBE {table_name}"
        results = self.conn.execute(query).fetchall()
        return {row[0]: row[1] for row in results}
    
    def close(self):
        self.conn.close()


if __name__ == '__main__':
    # Test connections
    print("Testing database connections...")
    
    # PostgreSQL
    try:
        pg = PostgreSQLOLAP()
        count = pg.execute_scalar("SELECT COUNT(*) FROM fact_sales")
        print(f"✓ PostgreSQL: {count} records in fact_sales")
    except Exception as e:
        print(f"✗ PostgreSQL failed: {e}")
    
    # DuckDB
    try:
        duck = DuckDBANALYTICS()
        results = duck.execute_query("SELECT COUNT(*) as count FROM fact_sales")
        print(f"✓ DuckDB: {results[0][0]} records in fact_sales")
    except Exception as e:
        print(f"✗ DuckDB failed: {e}")
    
    DatabaseManager.close_all()
