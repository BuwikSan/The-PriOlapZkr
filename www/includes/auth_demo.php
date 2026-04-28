<?php
/**
 * Authentication Demo Functions
 * Hash verification and credential checking (no real persistence yet)
 */

// Simple bcrypt wrapper for demo
class AuthDemo {

    public static function hashPassword($password) {
        return password_hash($password, PASSWORD_BCRYPT, ['cost' => 12]);
    }

    public static function verifyPassword($password, $hash) {
        return password_verify($password, $hash);
    }

    // Demo credentials (would come from database in production)
    public static function getDemoCredentials() {
        return [
            [
                'id' => 1,
                'username' => 'demo_user',
                'email' => 'demo@example.com',
                'password_hash' => '$2y$12$abcd1234efgh5678ijkl9012mnopqrst.uvwxyz',
                'created_at' => '2024-01-15'
            ],
            [
                'id' => 2,
                'username' => 'test_account',
                'email' => 'test@example.com',
                'password_hash' => '$2y$12$zyxwvuts9876rqpo5432mlkji.hgfedcba',
                'created_at' => '2024-01-20'
            ]
        ];
    }

    // Simulate login check
    public static function attemptLogin($username, $password) {
        $credentials = self::getDemoCredentials();

        foreach ($credentials as $cred) {
            if ($cred['username'] === $username) {
                // In real app, would verify hash
                return [
                    'success' => true,
                    'username' => $username,
                    'message' => 'Login would check password hash against stored bcrypt hash'
                ];
            }
        }

        return [
            'success' => false,
            'message' => 'Username not found in demo credentials'
        ];
    }

    // Simulate registration
    public static function attemptRegister($username, $email, $password, $password_confirm) {
        if ($password !== $password_confirm) {
            return [
                'success' => false,
                'message' => 'Passwords do not match'
            ];
        }

        if (strlen($password) < 8) {
            return [
                'success' => false,
                'message' => 'Password must be at least 8 characters'
            ];
        }

        $hash = self::hashPassword($password);

        return [
            'success' => true,
            'username' => $username,
            'email' => $email,
            'hash_demo' => substr($hash, 0, 20) . '...',
            'message' => 'Registration would create account with bcrypt hashed password'
        ];
    }
}
?>
