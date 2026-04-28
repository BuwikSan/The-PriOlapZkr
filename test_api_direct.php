<?php
// Direct test of API endpoint
header('Content-Type: text/plain');

include __DIR__ . '/www/includes/olap_wrapper.php';

echo "=== Testing OlapWrapper::executeQuery ===\n";
echo "Query: q1, Database: postgres\n";
echo "---\n";

$result = OlapWrapper::executeQuery('q1', 'postgres');

echo "Response structure:\n";
print_r($result);

echo "\n=== JSON output ===\n";
echo json_encode($result, JSON_PRETTY_PRINT);
?>
