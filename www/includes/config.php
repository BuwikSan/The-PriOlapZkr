<?php
/**
 * Configuration & Constants
 * Database credentials, paths, and app settings
 */

// Environment
define('ENV', getenv('ENV') ?: 'development');
define('DEBUG', ENV === 'development');

// Database - PostgreSQL
define('PG_HOST', getenv('DB_HOST') ?: 'postgres');
define('PG_PORT', getenv('DB_PORT') ?: '5432');
define('PG_DB', getenv('DB_NAME') ?: 'bmw_sales');
define('PG_USER', getenv('DB_USER') ?: 'bmw_user');
define('PG_PASS', getenv('DB_PASS') ?: 'bmw_password');

// Database - DuckDB
define('DUCKDB_PATH', '/var/www/html/db/olap.duckdb');

// Paths
define('BASE_URL', 'http://localhost:8080');
define('INCLUDES_DIR', __DIR__);
define('SRC_DIR', '/var/www/src');

// Crypto
define('CRYPTO_BACKEND_PATH', SRC_DIR . '/crypto');
define('OLAP_BACKEND_PATH', SRC_DIR . '/olap');

// Database Connection Function
function getPgConnection() {
    $dsn = sprintf(
        "pgsql:host=%s;port=%s;dbname=%s;user=%s;password=%s",
        PG_HOST,
        PG_PORT,
        PG_DB,
        PG_USER,
        PG_PASS
    );

    try {
        return new PDO($dsn);
    } catch (PDOException $e) {
        if (DEBUG) {
            die('Database Error: ' . $e->getMessage());
        }
        return null;
    }
}

// Error handler
function handleError($message, $type = 'error') {
    return [
        'status' => $type,
        'message' => $message,
        'timestamp' => date('Y-m-d H:i:s')
    ];
}

// Success response
function handleSuccess($data, $message = 'Success') {
    return [
        'status' => 'success',
        'message' => $message,
        'data' => $data,
        'timestamp' => date('Y-m-d H:i:s')
    ];
}
?>
