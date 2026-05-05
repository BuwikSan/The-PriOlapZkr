#!/usr/bin/env python3
import sys
import os

os.environ['DB_HOST'] = 'postgres'
os.environ['DB_PORT'] = '5432'
os.environ['DB_NAME'] = 'bmw_olap'
os.environ['DB_USER'] = 'bmw_user'
os.environ['DB_PASS'] = 'bmw_password'
os.environ['DUCKDB_PATH'] = '/var/www/html/db/olap.duckdb'

sys.path.insert(0, '/var/www/src')
from olap.load_bmw_data import DataLoader

print("Starting data loader test...")
loader = DataLoader('/var/www/html/bmw.csv')

try:
    print("1. Connecting to databases...")
    if not loader.connect_databases():
        print("Connection failed!")
        sys.exit(1)
    
    print("2. Reading CSV...")
    if not loader.read_csv():
        print("CSV read failed!")
        sys.exit(1)
    
    print("3. Loading PostgreSQL...")
    r_pg = loader.load_postgresql()
    print(f"   Result: {r_pg}")
    
    print("4. Loading DuckDB...")
    r_duck = loader.load_duckdb()
    print(f"   Result: {r_duck}")
    
    if r_pg and r_duck:
        print("\n5. Showing final statistics...")
        loader.show_stats()
    else:
        print(f"Loading incomplete: PG={r_pg}, DuckDB={r_duck}")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    print("\nClosing connections...")
    loader.close()
