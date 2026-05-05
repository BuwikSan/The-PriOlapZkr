#!/usr/bin/env python3
import psycopg2
import os

# Connect
conn = psycopg2.connect(
    host='postgres',
    port='5432',
    database='bmw_olap',
    user='bmw_user',
    password='bmw_password'
)

cursor = conn.cursor()

# Test simple OLAP query
print("=== Testing OLAP Query ===\n")

cursor.execute("""
    SELECT
        dm.model_name,
        COUNT(*) as total_sales,
        ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price
    FROM fact_sales fs
    JOIN dim_model dm ON fs.model_id = dm.model_id
    GROUP BY dm.model_id, dm.model_name
    ORDER BY total_sales DESC
    LIMIT 5
""")

print("Model-based Sales (TOP 5):")
rows = cursor.fetchall()
print(f"Rows returned: {len(rows)}\n")
for row in rows:
    print(f"  {row[0]:20} | Sales: {row[1]:6} | Avg Price: ${row[2]:10}")

# Test with fuel type
print("\n\n=== Testing DICE Query ===\n")
cursor.execute("""
    SELECT
        dft.fuel_type_name,
        COUNT(*) as sales_count,
        ROUND(AVG(fs.price)::NUMERIC, 2) as avg_price
    FROM fact_sales fs
    JOIN dim_fuel_type dft ON fs.fuel_type_id = dft.fuel_type_id
    GROUP BY dft.fuel_type_id, dft.fuel_type_name
    ORDER BY sales_count DESC
""")

print("Sales by Fuel Type:")
rows = cursor.fetchall()
print(f"Rows returned: {len(rows)}\n")
for row in rows:
    print(f"  {row[0]:20} | Sales: {row[1]:6} | Avg Price: ${row[2]:10}")

cursor.close()
conn.close()

print("\n✓ OLAP queries working correctly!")
