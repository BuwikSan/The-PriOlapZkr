<?php
/**
 * Introduction Page
 */
?>

<div class="container">
    <h1>Vítejte na BMW OLAP & Cryptography Platform</h1>

    <p>
        Tato platforma představuje integraci moderních technologií pro datovou analýzu a kryptografii.
        Procházejte jednotlivé sekce a objevte, jak fungují online analytické zpracování (OLAP) a šifrování.
    </p>

    <div class="grid-2">
        <div class="section">
            <h3>📊 OLAP Showcase</h3>
            <p>
                Prohlédněte si demonstraci Online Analytical Processing nad datasetem BMW prodejů.
                Porovnávejte výkon PostgreSQL a DuckDB databází, sledujte doby zpracování různých typů dotazů.
            </p>
            <p><strong>Procesy:</strong> SLICE, DICE, DRILL-DOWN</p>
            <a href="index.php?page=olap" class="btn">Otevřít OLAP →</a>
        </div>

        <div class="section">
            <h3>🔐 Kryptografie</h3>
            <p>
                Prozkoumejte tradiční Hill cipher a moderní post-kvantový algoritmus Kyber.
                Šifrujte a dešifrujte texty, porovnávejte bezpečnostní charakteristiky obou přístupů.
            </p>
            <p><strong>Algoritmy:</strong> Hill Cipher, Kyber (Module-LWE)</p>
            <a href="index.php?page=crypto" class="btn">Otevřít Šifrování →</a>
        </div>

        <div class="section">
            <h3>🔑 Hashování & Autentifikace</h3>
            <p>
                Experimentujte s hašovacími funkcemi a procesy autentifikace.
                Pochopte rozdíl mezi registrací (bezpečné ukládání heš) a přihlášením (ověřování).
            </p>
            <p><strong>Technologie:</strong> Bcrypt, Secure Hashing</p>
            <a href="index.php?page=auth" class="btn">Otevřít Hashování →</a>
        </div>

        <div class="section">
            <h3>💻 Technologický Stack</h3>
            <p>
                <strong>Frontend:</strong> PHP 8.2, HTML5, CSS3 Vanilla<br>
                <strong>Backend:</strong> Python 3, PostgreSQL 15, DuckDB<br>
                <strong>Kontejnerizace:</strong> Docker, Docker Compose<br>
                <strong>Bezpečnost:</strong> SSH Key Auth, UFW Firewall
            </p>
        </div>
    </div>

    <div class="section mt-3">
        <h3>📚 O Projektu</h3>
        <p>
            Tento projekt je edukační platformou demonstrující:
        </p>
        <ul style="margin-left: 2rem; color: var(--text-secondary);">
            <li><strong>OLAP analýzu:</strong> Porovnání tradičních a moderních datových skladů</li>
            <li><strong>Kryptografii:</strong> Od klasických metod k post-kvantovému šifrování</li>
            <li><strong>Infrastrukturu:</strong> Docker, Kubernetes-ready deployment</li>
            <li><strong>Bezpečnost:</strong> Ověřené praktiky pro produkční nasazení</li>
        </ul>
    </div>

    <div class="info-box">
        <strong>ℹ️ Poznámka:</strong> Toto je bezpečné testovací prostředí.
        Všechny šifrované zprávy a autentifikační procesy jsou demonstrační a neuchovávají žádná skutečná data.
    </div>
</div>
