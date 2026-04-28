#!/usr/bin/env python3
"""
BMW Sales Data Loader
Loads CSV data into PostgreSQL and DuckDB with dimension extraction
"""

import csv
import sys
import os
from typing import Dict, Set, Tuple
import psycopg2
from psycopg2.extras import execute_batch
import duckdb


class DataLoader:
    """Load BMW sales data from CSV into OLAP databases"""

    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.pg_conn = None
        self.duck_db = None

        # Data for dimensions
        self.models: Set[str] = set()
        self.fuel_types: Set[str] = set()
        self.transmissions: Set[str] = set()
        self.engine_sizes: Set[float] = set()
        self.years: Set[int] = set()

        # Sales records
        self.sales_data: list = []

    def connect_databases(self) -> bool:
        """Connect to both PostgreSQL and DuckDB"""
        try:
            # PostgreSQL
            self.pg_conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'postgres'),
                port=os.getenv('DB_PORT', '5432'),
                database=os.getenv('DB_NAME', 'bmw_sales'),
                user=os.getenv('DB_USER', 'bmw_user'),
                password=os.getenv('DB_PASS', 'bmw_password')
            )
            print("✓ PostgreSQL connected")

            # DuckDB
            duckdb_path = os.getenv('DUCKDB_PATH', '/var/www/html/db/olap.duckdb')
            self.duck_db = duckdb.connect(duckdb_path)
            print(f"✓ DuckDB connected: {duckdb_path}")

            return True
        except Exception as e:
            print(f"✗ Connection error: {e}")
            return False

    def read_csv(self) -> bool:
        """Read CSV and extract dimension values and sales records"""
        try:
            print(f"\n📖 Reading CSV: {self.csv_path}")

            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0

                for row in reader:
                    # Extract dimensions
                    model = row['model'].strip()
                    fuel_type = row['fuelType'].strip()
                    transmission = row['transmission'].strip()

                    # Handle missing engine size with default
                    try:
                        engine_size = float(row['engineSize']) if row['engineSize'].strip() else 0.0
                    except (ValueError, KeyError):
                        engine_size = 0.0

                    year = int(row['year'])

                    self.models.add(model)
                    self.fuel_types.add(fuel_type)
                    self.transmissions.add(transmission)
                    self.engine_sizes.add(engine_size)
                    self.years.add(year)

                    # Store sales record
                    self.sales_data.append({
                        'model': model,
                        'year': year,
                        'price': int(row['price']),
                        'transmission': transmission,
                        'mileage': int(row['mileage']),
                        'fuel_type': fuel_type,
                        'tax': int(row['tax']),
                        'mpg': float(row['mpg']),
                        'engine_size': engine_size
                    })

                    count += 1
                    if count % 1000 == 0:
                        print(f"  Read {count} records...")

            print(f"\n✓ CSV loaded: {count} records")
            print(f"  Models: {len(self.models)}")
            print(f"  Fuel types: {len(self.fuel_types)}")
            print(f"  Transmissions: {len(self.transmissions)}")
            print(f"  Engine sizes: {len(self.engine_sizes)}")
            print(f"  Years: {len(self.years)} (min={min(self.years)}, max={max(self.years)})")

            return True
        except Exception as e:
            print(f"✗ CSV read error: {e}")
            return False

    def load_postgresql(self) -> bool:
        """Load data into PostgreSQL"""
        try:
            print("\n📥 Loading data into PostgreSQL...")
            cursor = self.pg_conn.cursor()

            # Load dimensions
            self._load_pg_dimensions(cursor)

            # Get dimension IDs
            model_map = self._get_pg_id_map(cursor, 'dim_model', 'model_name')
            fuel_map = self._get_pg_id_map(cursor, 'dim_fuel_type', 'fuel_type_name')
            trans_map = self._get_pg_id_map(cursor, 'dim_transmission', 'transmission_name')
            engine_map = self._get_pg_id_map(cursor, 'dim_engine', 'engine_size')
            year_map = self._get_pg_id_map(cursor, 'dim_time', 'production_year')

            # Load facts
            facts = []
            skipped = 0
            for sale in self.sales_data:
                model_id = model_map.get(sale['model'])
                year_id = year_map.get(sale['year'])
                fuel_id = fuel_map.get(sale['fuel_type'])
                trans_id = trans_map.get(sale['transmission'])
                engine_id = engine_map.get(sale['engine_size'])

                # Skip records with missing foreign keys
                if not all([model_id, year_id, fuel_id, trans_id, engine_id]):
                    skipped += 1
                    continue

                facts.append((
                    model_id,
                    year_id,
                    fuel_id,
                    trans_id,
                    engine_id,
                    sale['price'],
                    sale['tax'],
                    sale['mileage'],
                    sale['mpg']
                ))

            execute_batch(cursor, """
                INSERT INTO fact_sales
                (model_id, time_id, fuel_type_id, transmission_id, engine_id, price, tax, mileage, mpg)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, facts, page_size=500)

            if skipped > 0:
                print(f"  (Skipped {skipped} records with missing dimensions)")

            self.pg_conn.commit()

            # Count
            cursor.execute("SELECT COUNT(*) FROM fact_sales")
            count = cursor.fetchone()[0]
            print(f"✓ PostgreSQL: {count} sales records loaded")

            cursor.close()
            return True
        except Exception as e:
            print(f"✗ PostgreSQL load error: {e}")
            self.pg_conn.rollback()
            return False

    def load_duckdb(self) -> bool:
        """Load data into DuckDB"""
        try:
            print("\n📥 Loading data into DuckDB...")

            # Load dimensions
            self._load_duck_dimensions()

            # Get dimension IDs
            model_map = self._get_duck_id_map('dim_model', 'model_name')
            fuel_map = self._get_duck_id_map('dim_fuel_type', 'fuel_type_name')
            trans_map = self._get_duck_id_map('dim_transmission', 'transmission_name')
            engine_map = self._get_duck_id_map('dim_engine', 'engine_size')
            year_map = self._get_duck_id_map('dim_time', 'production_year')

            # Prepare facts
            facts = []
            skipped = 0
            sale_id = 1
            for sale in self.sales_data:
                model_id = model_map.get(sale['model'])
                year_id = year_map.get(sale['year'])
                fuel_id = fuel_map.get(sale['fuel_type'])
                trans_id = trans_map.get(sale['transmission'])
                engine_id = engine_map.get(sale['engine_size'])

                # Skip records with missing foreign keys
                if not all([model_id, year_id, fuel_id, trans_id, engine_id]):
                    skipped += 1
                    continue

                facts.append((
                    sale_id,
                    model_id,
                    year_id,
                    fuel_id,
                    trans_id,
                    engine_id,
                    sale['price'],
                    sale['tax'],
                    sale['mileage'],
                    sale['mpg']
                ))
                sale_id += 1

            # Insert facts
            for fact in facts:
                self.duck_db.execute("""
                    INSERT INTO fact_sales
                    (sale_id, model_id, time_id, fuel_type_id, transmission_id, engine_id, price, tax, mileage, mpg)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, fact)

            if skipped > 0:
                print(f"  (Skipped {skipped} records with missing dimensions)")

            # Count
            result = self.duck_db.execute("SELECT COUNT(*) FROM fact_sales").fetchall()
            count = result[0][0] if result else 0
            print(f"✓ DuckDB: {count} sales records loaded")

            return True
        except Exception as e:
            print(f"✗ DuckDB load error: {e}")
            return False

    def _load_pg_dimensions(self, cursor):
        """Load dimension tables into PostgreSQL"""
        # Models
        for model in sorted(self.models):
            cursor.execute(
                "INSERT INTO dim_model (model_name) VALUES (%s) ON CONFLICT DO NOTHING",
                (model,)
            )

        # Fuel types
        for fuel in sorted(self.fuel_types):
            cursor.execute(
                "INSERT INTO dim_fuel_type (fuel_type_name) VALUES (%s) ON CONFLICT DO NOTHING",
                (fuel,)
            )

        # Transmissions
        for trans in sorted(self.transmissions):
            cursor.execute(
                "INSERT INTO dim_transmission (transmission_name) VALUES (%s) ON CONFLICT DO NOTHING",
                (trans,)
            )

        # Engine sizes
        for engine in sorted(self.engine_sizes):
            cursor.execute(
                "INSERT INTO dim_engine (engine_size) VALUES (%s) ON CONFLICT DO NOTHING",
                (engine,)
            )

        # Time dimension
        min_year = min(self.years)
        max_year = max(self.years)

        for year in range(min_year, max_year + 1):
            decade = (year // 10) * 10
            cursor.execute(
                "INSERT INTO dim_time (production_year, decade) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (year, decade)
            )

        self.pg_conn.commit()
        print("  ✓ Dimensions loaded into PostgreSQL")

    def _load_duck_dimensions(self):
        """Load dimension tables into DuckDB"""
        # Models
        for idx, model in enumerate(sorted(self.models), 1):
            self.duck_db.execute(
                "INSERT INTO dim_model (model_id, model_name) VALUES (?, ?)",
                [idx, model]
            )

        # Fuel types
        for idx, fuel in enumerate(sorted(self.fuel_types), 1):
            self.duck_db.execute(
                "INSERT INTO dim_fuel_type (fuel_type_id, fuel_type_name) VALUES (?, ?)",
                [idx, fuel]
            )

        # Transmissions
        for idx, trans in enumerate(sorted(self.transmissions), 1):
            self.duck_db.execute(
                "INSERT INTO dim_transmission (transmission_id, transmission_name) VALUES (?, ?)",
                [idx, trans]
            )

        # Engine sizes
        for idx, engine in enumerate(sorted(self.engine_sizes), 1):
            self.duck_db.execute(
                "INSERT INTO dim_engine (engine_id, engine_size) VALUES (?, ?)",
                [idx, engine]
            )

        # Time dimension
        min_year = min(self.years)
        max_year = max(self.years)
        idx = 1
        for year in range(min_year, max_year + 1):
            decade = (year // 10) * 10
            self.duck_db.execute(
                "INSERT INTO dim_time (time_id, production_year, decade) VALUES (?, ?, ?)",
                [idx, year, decade]
            )
            idx += 1

        print("  ✓ Dimensions loaded into DuckDB")

    def _get_pg_id_map(self, cursor, table: str, column: str) -> Dict:
        """Get mapping of value -> ID from PostgreSQL"""
        cursor.execute(f"SELECT {column}, {table.replace('dim_', '')}_id FROM {table}")
        return {row[0]: row[1] for row in cursor.fetchall()}

    def _get_duck_id_map(self, table: str, column: str) -> Dict:
        """Get mapping of value -> ID from DuckDB"""
        id_col = table.replace('dim_', '') + '_id'
        result = self.duck_db.execute(f"SELECT {column}, {id_col} FROM {table}").fetchall()
        return {row[0]: row[1] for row in result}

    def show_stats(self):
        """Display final statistics"""
        print("\n📊 Final Statistics")
        print("=" * 50)

        try:
            if self.pg_conn:
                cursor = self.pg_conn.cursor()
                cursor.execute("""
                    SELECT
                        (SELECT COUNT(*) FROM dim_model) as models,
                        (SELECT COUNT(*) FROM dim_fuel_type) as fuel_types,
                        (SELECT COUNT(*) FROM dim_transmission) as transmissions,
                        (SELECT COUNT(*) FROM dim_engine) as engines,
                        (SELECT COUNT(*) FROM dim_time) as times,
                        (SELECT COUNT(*) FROM fact_sales) as facts
                """)
                row = cursor.fetchone()

                print(f"PostgreSQL:")
                print(f"  Models: {row[0]}")
                print(f"  Fuel types: {row[1]}")
                print(f"  Transmissions: {row[2]}")
                print(f"  Engine sizes: {row[3]}")
                print(f"  Time periods: {row[4]}")
                print(f"  Sales records: {row[5]:,}")

                cursor.close()

            if self.duck_db:
                result = self.duck_db.execute("""
                    SELECT
                        (SELECT COUNT(*) FROM dim_model) as models,
                        (SELECT COUNT(*) FROM dim_fuel_type) as fuel_types,
                        (SELECT COUNT(*) FROM dim_transmission) as transmissions,
                        (SELECT COUNT(*) FROM dim_engine) as engines,
                        (SELECT COUNT(*) FROM dim_time) as times,
                        (SELECT COUNT(*) FROM fact_sales) as facts
                """).fetchall()
                row = result[0] if result else None

                if row:
                    print(f"\nDuckDB:")
                    print(f"  Models: {row[0]}")
                    print(f"  Fuel types: {row[1]}")
                    print(f"  Transmissions: {row[2]}")
                    print(f"  Engine sizes: {row[3]}")
                    print(f"  Time periods: {row[4]}")
                    print(f"  Sales records: {row[5]:,}")
        except Exception as e:
            print(f"Error retrieving stats: {e}")

        print("=" * 50)

    def close(self):
        """Close database connections"""
        if self.pg_conn:
            self.pg_conn.close()
        if self.duck_db:
            self.duck_db.close()


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: load_bmw_data.py <csv_path>")
        print("Example: load_bmw_data.py /var/www/data/bmw.csv")
        sys.exit(1)

    csv_path = sys.argv[1]

    if not os.path.exists(csv_path):
        print(f"✗ CSV file not found: {csv_path}")
        sys.exit(1)

    loader = DataLoader(csv_path)

    try:
        # Connect
        if not loader.connect_databases():
            sys.exit(1)

        # Read CSV
        if not loader.read_csv():
            sys.exit(1)

        # Load PostgreSQL
        if not loader.load_postgresql():
            sys.exit(1)

        # Load DuckDB
        if not loader.load_duckdb():
            sys.exit(1)

        # Show stats
        loader.show_stats()

        print("\n✓ Data loading completed successfully!")

    except KeyboardInterrupt:
        print("\n⚠️  Loading interrupted by user")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)
    finally:
        loader.close()


if __name__ == '__main__':
    main()
