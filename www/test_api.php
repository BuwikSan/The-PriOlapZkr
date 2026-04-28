<?php
/**
 * Test OLAP API endpoints
 */
header('Content-Type: application/json');

$base_url = 'http://localhost';

// Test 1: List queries
echo "🧪 TEST 1: List queries\n";
$response = @file_get_contents("$base_url/api/olap.php?action=list");
if ($response) {
    $data = json_decode($response, true);
    echo "✓ Got " . count($data['queries'] ?? []) . " queries\n";
} else {
    echo "✗ Failed to connect\n";
}

// Test 2: Execute query on PostgreSQL
echo "\n🧪 TEST 2: Execute q1 on PostgreSQL\n";
$response = @file_get_contents("$base_url/api/olap.php?action=execute&query_id=q1&db=postgres");
if ($response) {
    $data = json_decode($response, true);
    if ($data['status'] === 'success') {
        echo "✓ Query successful: " . $data['execution_time_ms'] . "ms, " . $data['rows_returned'] . " rows\n";
    } else {
        echo "✗ Query failed: " . ($data['error'] ?? $data['status']) . "\n";
    }
} else {
    echo "✗ Failed to connect\n";
}

// Test 3: Execute query on DuckDB
echo "\n🧪 TEST 3: Execute q1 on DuckDB\n";
$response = @file_get_contents("$base_url/api/olap.php?action=execute&query_id=q1&db=duckdb");
if ($response) {
    $data = json_decode($response, true);
    if ($data['status'] === 'success') {
        echo "✓ Query successful: " . $data['execution_time_ms'] . "ms, " . $data['rows_returned'] . " rows\n";
    } else {
        echo "✗ Query failed: " . ($data['error'] ?? $data['status']) . "\n";
    }
} else {
    echo "✗ Failed to connect\n";
}

// Test 4: Compare queries
echo "\n🧪 TEST 4: Compare q1\n";
$response = @file_get_contents("$base_url/api/olap.php?action=compare&query_id=q1");
if ($response) {
    $data = json_decode($response, true);
    if (!isset($data['error'])) {
        echo "✓ Compare successful\n";
        echo "  PostgreSQL: " . $data['postgres']['execution_time_ms'] . "ms\n";
        echo "  DuckDB: " . $data['duckdb']['execution_time_ms'] . "ms\n";
        echo "  Speedup: " . $data['comparison']['speedup_factor'] . "x\n";
    } else {
        echo "✗ Compare failed: " . $data['error'] . "\n";
    }
} else {
    echo "✗ Failed to connect\n";
}

echo "\n✅ Test Complete\n";
?>
