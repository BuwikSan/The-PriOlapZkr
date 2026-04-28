#!/usr/bin/env python3
"""Quick init script for BMW databases"""
import psycopg2
import duckdb
import os

print("[1] Initializing PostgreSQL...")
try:
    conn = psycopg2.connect(host='postgres', database='bmw_olap', user='bmw_user', password='bmw_password')
    cur = conn.cursor()
    with open('/var/www/src/olap/init.sql') as f:
        for stmt in f.read().split(';'):
            stmt = stmt.strip()
            if stmt:
                cur.execute(stmt)
    conn.commit()
    cur.close()
    conn.close()
    print("✓ PostgreSQL schema initialized")
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)

print("[2] Initializing DuckDB...")
try:
    os.makedirs('/var/www/html/db', exist_ok=True)
    db = duckdb.connect('/var/www/html/db/olap.duckdb')
    with open('/var/www/src/olap/init_duckdb.sql') as f:
        for stmt in f.read().split(';'):
            stmt = stmt.strip()
            if stmt:
                try:
                    db.execute(stmt)
                except Exception as e:
                    # Some statements might fail in DuckDB, that's OK
                    if 'already exists' not in str(e).lower():
                        print(f"  Note: {e}")
    db.close()
    print("✓ DuckDB schema initialized")
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)

print("✓ All done")
