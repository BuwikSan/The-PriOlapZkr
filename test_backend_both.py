#!/usr/bin/env python3
import os
import subprocess
import json

# Set environment variables
env = {
    'DB_HOST': 'postgres',
    'DB_PORT': '5432',
    'DB_NAME': 'bmw_olap',
    'DB_USER': 'bmw_user',
    'DB_PASS': 'bmw_password',
    'DUCKDB_PATH': '/var/www/html/db/olap.duckdb',
}

# Merge with current env
full_env = os.environ.copy()
full_env.update(env)

# Test both databases
for db in ['postgres', 'duckdb']:
    print(f"\n{'='*60}")
    print(f"Testing: {db.upper()}")
    print(f"{'='*60}")
    
    cmd = [
        'python3',
        '/var/www/src/olap/olap_backend.py',
        'execute_query',
        'q1',
        db
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, env=full_env)

    if result.stdout:
        try:
            data = json.loads(result.stdout)
            print(f"✓ Status: {data.get('status')}")
            print(f"  Rows: {data.get('rows_returned')}")
            print(f"  Time: {data.get('execution_time_ms')} ms")
            
            if data.get('results'):
                print(f"\n  First 2 results:")
                for row in data['results'][:2]:
                    print(f"    {row}")
        except json.JSONDecodeError as e:
            print(f"✗ Failed to parse JSON: {e}")
            print(f"  Output: {result.stdout[:200]}")
    else:
        print(f"✗ No output")
    
    if result.stderr:
        print(f"\n  Debug info: {result.stderr[:200]}")
