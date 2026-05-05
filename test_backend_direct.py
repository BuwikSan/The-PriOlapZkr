#!/usr/bin/env python3
import os
os.environ['DUCKDB_PATH'] = '/var/www/html/db/olap.duckdb'
os.environ['DB_HOST'] = 'postgres'
os.environ['DB_PORT'] = '5432'
os.environ['DB_NAME'] = 'bmw_olap'
os.environ['DB_USER'] = 'bmw_user'
os.environ['DB_PASS'] = 'bmw_password'

import sys
sys.path.insert(0, '/var/www/src')
from olap.olap_backend import OlapBackend

backend = OlapBackend()
result = backend.execute_query_by_id('q1', 'duckdb')
print(f'Status: {result.get("status")}')
print(f'Rows: {result.get("rows_returned")}')
print(f'Time: {result.get("execution_time_ms")} ms')
if result.get('results'):
    print(f'First result: {result["results"][0]}')
else:
    print(f'ERROR: {result.get("error", "No error message")}')
