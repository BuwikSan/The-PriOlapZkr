<?php
// Test OLAP API response
header('Content-Type: application/json');

// Test data - simulate what the backend should return
$test_response = [
    'query_id' => 'q1',
    'name' => 'Sales by Model (SLICE)',
    'type' => 'SLICE',
    'database' => 'postgres',
    'execution_time_ms' => 12.78,
    'rows_returned' => 15,
    'status' => 'success',
    'results' => [
        ['model' => '3 Series', 'total_sales' => 2429, 'avg_price' => 19946.35, 'total_revenue' => 48475625.00, 'avg_mpg' => 24.85],
        ['model' => '5 Series', 'total_sales' => 1858, 'avg_price' => 27758.12, 'total_revenue' => 51606583.00, 'avg_mpg' => 21.56],
        ['model' => '7 Series', 'total_sales' => 842, 'avg_price' => 31500.00, 'total_revenue' => 26529000.00, 'avg_mpg' => 19.23],
        ['model' => 'X1', 'total_sales' => 1234, 'avg_price' => 22500.00, 'total_revenue' => 27765000.00, 'avg_mpg' => 23.45],
        ['model' => 'X3', 'total_sales' => 987, 'avg_price' => 28900.00, 'total_revenue' => 28537300.00, 'avg_mpg' => 20.12],
    ]
];

echo json_encode($test_response, JSON_PRETTY_PRINT);
?>
