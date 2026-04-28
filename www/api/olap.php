<?php
/**
 * OLAP API Endpoint
 * Called via AJAX from olap.php
 * Returns JSON responses from Python backend
 */

header('Content-Type: application/json');

// Include backend wrapper
include __DIR__ . '/../includes/olap_wrapper.php';

// Get action and query_id from request
$action = $_GET['action'] ?? 'execute';
$queryId = $_GET['query_id'] ?? null;
$database = $_GET['db'] ?? 'postgres';

// Error response helper
function errorJson($message, $code = 400) {
    http_response_code($code);
    echo json_encode([
        'error' => $message,
        'timestamp' => date('Y-m-d H:i:s')
    ]);
    exit;
}

// Validate query_id for execute action only
if ($action === 'execute' && (!$queryId || !preg_match('/^q[1-9]$/', $queryId))) {
    errorJson('Invalid query_id', 400);
}

try {
    // Execute action
    if ($action === 'execute') {
        $result = OlapWrapper::executeQuery($queryId, $database);
        echo json_encode($result);
    }
    elseif ($action === 'compare') {
        $result = OlapWrapper::comparePerformance($queryId);
        echo json_encode($result);
    }
    elseif ($action === 'list') {
        $queries = OlapWrapper::getAvailableQueries();
        echo json_encode(['queries' => $queries]);
    }
    elseif ($action === 'schema') {
        $schema = OlapWrapper::getSchemaInfo();
        echo json_encode(['schema' => $schema]);
    }
    else {
        errorJson('Unknown action: ' . $action, 400);
    }

} catch (Exception $e) {
    errorJson('Backend error: ' . $e->getMessage(), 500);
}
?>
