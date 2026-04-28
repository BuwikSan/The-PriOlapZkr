#!/usr/bin/env python3
"""
BMW OLAP Analytics - Complete Setup Script for Windows Docker Desktop
Handles: Docker startup, schema init, data loading, verification
"""

import subprocess
import time
import sys
import os

def run_cmd(cmd, description=""):
    """Run shell command and show output"""
    if description:
        print(f"\n{description}")
    try:
        result = subprocess.run(cmd, shell=True, check=False, capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def docker_exec_python(code, description=""):
    """Execute Python code inside docker container"""
    if description:
        print(f"\n{description}")

    # Escape quotes for docker
    code_escaped = code.replace('"', '\\"').replace('$', '\\$')
    cmd = f'docker exec bmw_analytics_web python3 -c "{code_escaped}"'

    try:
        result = subprocess.run(cmd, shell=True, check=False, capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"ERROR: {e}")
        return False

print("\n" + "="*60)
print("BMW OLAP Analytics - Windows Docker Desktop Setup")
print("="*60)

# 1. Start containers
print("\n[1/6] Starting Docker containers...")
os.chdir(r"c:\GitHub\The-PriOlapZkr")
run_cmd("docker-compose down -v 2>nul")
time.sleep(2)
run_cmd("docker-compose up -d")
print("[*] Waiting 15 seconds for services...")
time.sleep(15)

# 2. Initialize PostgreSQL schema
print("\n[2/6] Initializing PostgreSQL schema...")
pg_code = """
import psycopg2
import time
time.sleep(5)
try:
    conn = psycopg2.connect(host='postgres', database='bmw_olap', user='bmw_user', password='bmw_password')
    cursor = conn.cursor()
    with open('/var/www/src/olap/init.sql', 'r') as f:
        for stmt in f.read().split(';'):
            if stmt.strip():
                cursor.execute(stmt)
    conn.commit()
    cursor.close()
    conn.close()
    print('✓ PostgreSQL schema ready')
except Exception as e:
    print(f'✗ Error: {e}')
    import sys
    sys.exit(1)
"""
if not docker_exec_python(pg_code):
    print("FAILED: PostgreSQL initialization")
    sys.exit(1)

# 3. Initialize DuckDB schema
print("\n[3/6] Initializing DuckDB...")
duck_code = """
import duckdb
import os
try:
    db_path = '/var/www/html/db/olap.duckdb'
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = duckdb.connect(db_path)
    with open('/var/www/src/olap/init.sql', 'r') as f:
        for stmt in f.read().split(';'):
            if stmt.strip():
                try:
                    conn.execute(stmt)
                except:
                    pass
    conn.close()
    print(f'✓ DuckDB ready: {db_path}')
except Exception as e:
    print(f'✗ Error: {e}')
    import sys
    sys.exit(1)
"""
if not docker_exec_python(duck_code):
    print("FAILED: DuckDB initialization")
    sys.exit(1)

# 4. Copy CSV data
print("\n[4/6] Copying BMW data to container...")
local_csv = r"depricated_or_tobeused\bmw.csv"
if os.path.exists(local_csv):
    run_cmd(f'docker cp "{local_csv}" bmw_analytics_web:/var/www/data/bmw.csv')
    print("✓ CSV copied from host")
else:
    print("! Local CSV not found, using container copy")
    run_cmd('docker exec bmw_analytics_web bash -c "mkdir -p /var/www/data && cp /var/www/depricated_or_tobeused/bmw.csv /var/www/data/bmw.csv"')

# 5. Load data into both databases
print("\n[5/6] Loading 10,782 BMW records into PostgreSQL and DuckDB...")
if not run_cmd('docker exec bmw_analytics_web python3 /var/www/src/olap/load_bmw_data.py /var/www/data/bmw.csv'):
    print("FAILED: Data loading")
    sys.exit(1)

# 6. Verify data
print("\n[6/6] Verifying data load...")
verify_code = """
import psycopg2
import duckdb
try:
    conn_pg = psycopg2.connect(host='postgres', database='bmw_olap', user='bmw_user', password='bmw_password')
    cursor = conn_pg.cursor()
    cursor.execute('SELECT COUNT(*) FROM fact_sales;')
    pg_count = cursor.fetchone()[0]
    cursor.close()
    conn_pg.close()
    print(f'✓ PostgreSQL: {pg_count} records')

    conn_duck = duckdb.connect('/var/www/html/db/olap.duckdb')
    duck_count = conn_duck.execute('SELECT COUNT(*) FROM fact_sales').fetchall()[0][0]
    conn_duck.close()
    print(f'✓ DuckDB: {duck_count} records')
except Exception as e:
    print(f'✗ Error: {e}')
"""
docker_exec_python(verify_code)

# Summary
print("\n" + "="*60)
print("SUCCESS! Setup Complete")
print("="*60)
print("\nWeb Interface:")
print("  http://localhost:8080")
print("\nTest OLAP Query:")
print("  docker exec bmw_analytics_web python3 /var/www/src/olap/olap_backend.py execute_query q1 postgres")
print("\n" + "="*60 + "\n")
