#!/usr/bin/env python3
"""
Diagnostika - zkontroluj celý setup
"""

import os
import sys
import subprocess
from pathlib import Path

def check_env_vars():
    """Zkontroluj environment variables"""
    print("\n" + "="*60)
    print("📋 Environment Variables")
    print("="*60)

    env_vars = {
        'DUCKDB_PATH': '/var/www/db/olap.duckdb',
        'DB_HOST': 'postgres',
        'DB_PORT': '5432',
        'DB_NAME': 'bmw_olap',
        'DB_USER': 'bmw_user',
        'DB_PASS': '(hidden)',
    }

    for var, default in env_vars.items():
        val = os.getenv(var, default)
        if var == 'DB_PASS':
            val = '(hidden)'
        status = "✓" if os.getenv(var) or var in ['DB_PASS'] else "?"
        print(f"{status} {var:20} = {val}")

def check_files():
    """Zkontroluj jestli existují důležité soubory"""
    print("\n" + "="*60)
    print("📁 Files")
    print("="*60)

    base = Path(__file__).parent.parent
    files = {
        'olap_backend.py': 'OLAP engine',
        'init.sql': 'PostgreSQL schema',
        'init_duckdb.sql': 'DuckDB schema',
        'load_bmw_data.py': 'Data loader',
    }

    for fname, desc in files.items():
        fpath = base / fname
        exists = "✓" if fpath.exists() else "✗"
        size = f"({fpath.stat().st_size} bytes)" if fpath.exists() else "(missing)"
        print(f"{exists} {fname:25} {desc:20} {size}")

    # Check DuckDB file
    duckdb_path = os.getenv('DUCKDB_PATH', '/var/www/db/olap.duckdb')
    if Path(duckdb_path).exists():
        size = Path(duckdb_path).stat().st_size
        print(f"✓ {'olap.duckdb':25} (database)          ({size} bytes)")
    else:
        print(f"✗ {'olap.duckdb':25} (database)          (missing)")

def check_python():
    """Zkontroluj Python a móduly"""
    print("\n" + "="*60)
    print("🐍 Python & Modules")
    print("="*60)

    print(f"✓ Python: {sys.version}")

    modules = ['psycopg2', 'duckdb', 'pandas', 'numpy', 'json']

    for mod in modules:
        try:
            __import__(mod)
            print(f"✓ {mod:15} installed")
        except ImportError:
            print(f"✗ {mod:15} MISSING")

def check_databases():
    """Zkontroluj připojení k DB"""
    print("\n" + "="*60)
    print("🗄️  Databases")
    print("="*60)

    # PostgreSQL
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'postgres'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'bmw_olap'),
            user=os.getenv('DB_USER', 'bmw_user'),
            password=os.getenv('DB_PASS', 'bmw_password')
        )
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM fact_sales")
        count = cursor.fetchone()[0]
        print(f"✓ PostgreSQL connected ({count} records in fact_sales)")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"✗ PostgreSQL: {e}")

    # DuckDB
    try:
        import duckdb
        db_path = os.getenv('DUCKDB_PATH', '/var/www/db/olap.duckdb')
        conn = duckdb.connect(db_path)
        result = conn.execute("SELECT COUNT(*) FROM fact_sales").fetchall()
        count = result[0][0]
        print(f"✓ DuckDB connected ({count} records in fact_sales)")
        conn.close()
    except Exception as e:
        print(f"✗ DuckDB: {e}")

def check_api():
    """Zkontroluj API endpoint"""
    print("\n" + "="*60)
    print("🌐 API Endpoint")
    print("="*60)

    api_url = "http://localhost/api/olap.php?action=list"

    try:
        result = subprocess.run(
            ['curl', '-s', api_url],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            try:
                import json
                data = json.loads(result.stdout)
                print(f"✓ API accessible ({len(data)} queries returned)")
            except:
                print(f"✗ API returned invalid JSON")
        else:
            print(f"✗ curl failed: {result.returncode}")
    except Exception as e:
        print(f"✗ Cannot reach API: {e}")

def main():
    print("\n" + "="*60)
    print("BMW OLAP - System Diagnostics")
    print("="*60)

    check_env_vars()
    check_files()
    check_python()
    check_databases()
    check_api()

    print("\n" + "="*60)
    print("✅ Diagnostic Complete")
    print("="*60)

if __name__ == '__main__':
    main()
