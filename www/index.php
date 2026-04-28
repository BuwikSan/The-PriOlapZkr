<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BMW OLAP & Crypto Dashboard</title>
    <link rel="stylesheet" href="styles/main.css">
</head>
<body>
    <?php
    // Simple routing
    $page = isset($_GET['page']) ? $_GET['page'] : 'intro';
    $validPages = ['intro', 'olap', 'crypto', 'auth'];
    $page = in_array($page, $validPages) ? $page : 'intro';
    ?>

    <header>
        <h1>🚗 BMW OLAP & Cryptography Platform</h1>
    </header>

    <nav>
        <a href="index.php?page=intro" class="<?php echo $page === 'intro' ? 'active' : ''; ?>">Úvodní stránka</a>
        <a href="index.php?page=olap" class="<?php echo $page === 'olap' ? 'active' : ''; ?>">OLAP Showcase</a>
        <a href="index.php?page=crypto" class="<?php echo $page === 'crypto' ? 'active' : ''; ?>">Šifrování</a>
        <a href="index.php?page=auth" class="<?php echo $page === 'auth' ? 'active' : ''; ?>">Hashování & Auth</a>
    </nav>

    <main>
        <?php
        switch ($page) {
            case 'intro':
                include 'pages/intro.php';
                break;
            case 'olap':
                include 'pages/olap.php';
                break;
            case 'crypto':
                include 'pages/crypto.php';
                break;
            case 'auth':
                include 'pages/auth.php';
                break;
        }
        ?>
    </main>

    <footer>
        <p>&copy; 2024 BMW OLAP & Cryptography Platform | Educational Project</p>
    </footer>
</body>
</html>