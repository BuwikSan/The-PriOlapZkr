<?php
include '/var/www/html/includes/olap_wrapper.php';

echo "Testing OlapWrapper directly:\n\n";

echo "1. Get Available Queries:\n";
$queries = OlapWrapper::getAvailableQueries();
echo json_encode($queries, JSON_PRETTY_PRINT) . "\n\n";

echo "2. Execute Q1 on PostgreSQL:\n";
$result = OlapWrapper::executeQuery('q1', 'postgres');
echo json_encode($result, JSON_PRETTY_PRINT) . "\n\n";

echo "3. Execute Q1 on DuckDB:\n";
$result = OlapWrapper::executeQuery('q1', 'duckdb');
echo json_encode($result, JSON_PRETTY_PRINT) . "\n\n";

echo "4. Compare Q1:\n";
$result = OlapWrapper::comparePerformance('q1');
echo json_encode($result, JSON_PRETTY_PRINT) . "\n\n";
?>
