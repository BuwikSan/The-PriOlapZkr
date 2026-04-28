<?php
/**
 * Cryptography API Endpoint
 * Handles Hill cipher and Kyber encryption/decryption
 */

header('Content-Type: application/json');

// Include backend wrapper
include __DIR__ . '/../includes/crypto_wrapper.php';

// Get action and parameters
$action = $_GET['action'] ?? $_POST['action'] ?? 'info';
$cipher = strtolower($_GET['cipher'] ?? $_POST['cipher'] ?? 'hill');
$text = $_GET['text'] ?? $_POST['text'] ?? '';

// Error response helper
function errorJson($message, $code = 400) {
    http_response_code($code);
    echo json_encode([
        'error' => $message,
        'timestamp' => date('Y-m-d H:i:s')
    ]);
    exit;
}

try {
    if ($action === 'encrypt') {
        if (!$text) {
            errorJson('Text parameter required for encryption', 400);
        }

        if ($cipher === 'hill') {
            $result = CryptoWrapper::hillEncrypt($text);
            echo json_encode([
                'action' => 'encrypt',
                'cipher' => 'hill',
                'status' => $result['success'] ? 'success' : 'error',
                'input' => $text,
                'output' => $result['result'],
                'timestamp' => date('Y-m-d H:i:s')
            ]);
        } else if ($cipher === 'kyber') {
            errorJson('Kyber encryption not yet implemented', 501);
        } else {
            errorJson('Unknown cipher: ' . $cipher, 400);
        }
    }
    elseif ($action === 'decrypt') {
        if (!$text) {
            errorJson('Text parameter required for decryption', 400);
        }

        if ($cipher === 'hill') {
            $result = CryptoWrapper::hillDecrypt($text);
            echo json_encode([
                'action' => 'decrypt',
                'cipher' => 'hill',
                'status' => $result['success'] ? 'success' : 'error',
                'input' => $text,
                'output' => $result['result'],
                'timestamp' => date('Y-m-d H:i:s')
            ]);
        } else if ($cipher === 'kyber') {
            errorJson('Kyber decryption not yet implemented', 501);
        } else {
            errorJson('Unknown cipher: ' . $cipher, 400);
        }
    }
    elseif ($action === 'info') {
        $info = CryptoWrapper::getCipherInfo($cipher);
        if ($info) {
            echo json_encode([
                'cipher' => $cipher,
                'info' => $info
            ]);
        } else {
            errorJson('Unknown cipher: ' . $cipher, 400);
        }
    }
    else {
        errorJson('Unknown action: ' . $action, 400);
    }

} catch (Exception $e) {
    errorJson('Backend error: ' . $e->getMessage(), 500);
}
?>
