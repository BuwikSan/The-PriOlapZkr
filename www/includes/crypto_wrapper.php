<?php
/**
 * Cryptography Backend Wrapper
 * Interface to Hill cipher and Kyber (placeholder for Kyber)
 */

class CryptoWrapper {

    private static $pythonPath = '/usr/bin/python3';
    private static $hillPath = '/var/www/src/crypto/HillC';
    private static $kyberPath = '/var/www/src/crypto/KyberC';

    /**
     * Execute Hill cipher encryption
     */
    public static function hillEncrypt($text) {
        $cmd = sprintf(
            "%s -c 'import sys; sys.path.append(\"%s\"); from Hcypher import Hills_cypher; c = Hills_cypher(); print(c.cypher(\"%s\"))'",
            self::$pythonPath,
            self::$hillPath,
            addslashes($text)
        );

        $output = shell_exec($cmd);
        return [
            'success' => $output !== null,
            'result' => trim($output),
            'cipher' => 'Hill',
            'mode' => 'encrypt'
        ];
    }

    /**
     * Execute Hill cipher decryption
     */
    public static function hillDecrypt($text) {
        $cmd = sprintf(
            "%s -c 'import sys; sys.path.append(\"%s\"); from Hcypher import Hills_cypher; c = Hills_cypher(); print(c.decypher(\"%s\"))'",
            self::$pythonPath,
            self::$hillPath,
            addslashes($text)
        );

        $output = shell_exec($cmd);
        return [
            'success' => $output !== null,
            'result' => trim($output),
            'cipher' => 'Hill',
            'mode' => 'decrypt'
        ];
    }

    /**
     * Get cipher information
     */
    public static function getCipherInfo($cipher) {
        $info = [
            'hill' => [
                'name' => 'Hill Cipher',
                'type' => 'Symmetric Block Cipher',
                'keySize' => '43x43 matrix (mod 43)',
                'blockSize' => 'Variable',
                'rounds' => 'Multi-round support',
                'description' => 'Hill cipher implementation using linear algebra over Czech alphabet (43 characters).',
                'usage' => 'Educational demonstration of matrix-based encryption'
            ],
            'kyber' => [
                'name' => 'Kyber',
                'type' => 'Post-Quantum Asymmetric',
                'keySize' => '1024 bits',
                'algorithm' => 'Lattice-based (Module-LWE)',
                'nist_category' => 'Level 1 (AES-128 equivalent)',
                'description' => 'NIST-standardized post-quantum key encapsulation mechanism.',
                'status' => 'Implementation pending'
            ]
        ];

        return $info[strtolower($cipher)] ?? null;
    }
}
?>
