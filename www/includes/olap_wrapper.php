<?php
/**
 * OLAP Backend Wrapper
 * Interface to PostgreSQL and DuckDB for OLAP queries
 */

class OlapWrapper {

    private static $pythonPath = '/usr/bin/python3';
    private static $backendScript = '/var/www/src/olap/olap_backend.py';

    /**
     * Get list of available OLAP queries from Python backend
     */
    public static function getAvailableQueries() {
        $result = self::callBackend('list_queries');
        return $result ?? self::getDefaultQueries();
    }

    /**
     * Default query list (fallback)
     */
    private static function getDefaultQueries() {
        return [
            ['id' => 'q1', 'name' => 'Sales by Model', 'type' => 'SLICE'],
            ['id' => 'q2', 'name' => 'Sales by Year', 'type' => 'SLICE'],
            ['id' => 'q3', 'name' => 'Top 10 Models by Revenue', 'type' => 'SLICE'],
            ['id' => 'q4', 'name' => 'Sales by Fuel & Transmission', 'type' => 'DICE'],
            ['id' => 'q5', 'name' => 'Premium Segment Analysis', 'type' => 'DICE'],
            ['id' => 'q6', 'name' => 'Engine Performance Analysis', 'type' => 'DICE'],
            ['id' => 'q7', 'name' => 'Model Detail Drill-Down', 'type' => 'DRILL-DOWN'],
            ['id' => 'q8', 'name' => 'Temporal Drill-Down', 'type' => 'DRILL-DOWN'],
            ['id' => 'q9', 'name' => 'Complete Hierarchy', 'type' => 'DRILL-DOWN'],
        ];
    }

    /**
     * Execute specific OLAP query
     */
    public static function executeQuery($queryId, $database = 'postgres') {
        $result = self::callBackend('execute_query', [$queryId, $database]);

        if ($result === null) {
            return self::errorResponse("Failed to execute query $queryId on $database");
        }

        return $result;
    }

    /**
     * Compare query performance between PostgreSQL and DuckDB
     */
    public static function comparePerformance($queryId) {
        $result = self::callBackend('compare', [$queryId]);

        if ($result === null) {
            return self::errorResponse("Failed to compare performance for query $queryId");
        }

        return $result;
    }

    /**
     * Get OLAP schema information
     */
    public static function getSchemaInfo() {
        return [
            'databases' => [
                'postgresql' => [
                    'type' => 'Traditional OLAP',
                    'host' => 'postgres',
                    'port' => 5432,
                    'description' => 'Row-oriented relational database'
                ],
                'duckdb' => [
                    'type' => 'Analytical Database',
                    'path' => '/var/www/db/olap.duckdb',
                    'description' => 'Column-oriented embedded database, optimized for analytics'
                ]
            ],
            'star_schema' => [
                'fact_table' => 'fact_sales',
                'fact_columns' => ['sale_id', 'model_id', 'time_id', 'fuel_type_id',
                                   'transmission_id', 'engine_id', 'price', 'tax', 'mileage', 'mpg'],
                'dimensions' => [
                    'dim_model' => ['model_id', 'model_name'],
                    'dim_fuel_type' => ['fuel_type_id', 'fuel_type_name'],
                    'dim_transmission' => ['transmission_id', 'transmission_name'],
                    'dim_engine' => ['engine_id', 'engine_size'],
                    'dim_time' => ['time_id', 'production_year', 'decade']
                ],
                'total_records' => '~10,781 sales records'
            ]
        ];
    }

    /**
     * Call Python backend script
     */
    private static function callBackend($action, $args = []) {
        // Build command
        $cmd = escapeshellcmd(self::$pythonPath) . ' ' . escapeshellarg(self::$backendScript) . ' ' . escapeshellarg($action);

        foreach ($args as $arg) {
            $cmd .= ' ' . escapeshellarg($arg);
        }

        // Add error redirection
        $cmd .= ' 2>&1';

        // Execute
        $output = shell_exec($cmd);

        if ($output === null) {
            return null;
        }

        // Parse JSON response
        $result = json_decode(trim($output), true);

        // If JSON parsing failed, return error
        if ($result === null) {
            return [
                'error' => 'Failed to parse backend response',
                'raw_output' => $output
            ];
        }

        return $result;
    }

    /**
     * Format error response
     */
    private static function errorResponse($message) {
        return [
            'status' => 'error',
            'message' => $message,
            'execution_time_ms' => 0,
            'rows_returned' => 0,
            'results' => []
        ];
    }

    /**
     * Check if backend is available
     */
    public static function isBackendAvailable() {
        $output = shell_exec(escapeshellcmd(self::$pythonPath) . ' --version 2>&1');
        return $output !== null && strpos($output, 'Python') !== false;
    }
}
?>
