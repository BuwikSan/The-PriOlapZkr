<?php
/**
 * Authentication & Hashing Page
 */
include __DIR__ . '/../includes/auth_demo.php';

$demoCredentials = AuthDemo::getDemoCredentials();
?>

<div class="container">
    <h1>Hashování & Autentifikace</h1>

    <p>
        Hashování a autentifikace jsou kritické pro zabezpečení aplikací.
        Níže si můžete vyzkoušet procesy registrace a přihlášení s pomocí bcrypt.
    </p>

    <div class="tab-menu">
        <button class="tab-button active" onclick="switchTab('login')">Přihlášení</button>
        <button class="tab-button" onclick="switchTab('register')">Registrace</button>
        <button class="tab-button" onclick="switchTab('credentials')">Demo Pověření</button>
    </div>

    <!-- LOGIN TAB -->
    <div id="login-tab" class="content-area active">
        <div class="section">
            <h3>🔑 Přihlášení</h3>

            <div class="description">
                <strong>Jak funguje ověřování:</strong>
                <ol style="margin-left: 1.5rem; margin-top: 0.5rem; color: var(--text-secondary);">
                    <li>Uživatel zadá heslo</li>
                    <li>Heslo se porovná s uloženým bcrypt hashem pomocí <code>password_verify()</code></li>
                    <li>Algoritmus bezpečně porovnává bez dešifrování (jednosměrná funkce)</li>
                    <li>Heslo během přenosu musí být chráněno TLS/SSL (HTTPS)</li>
                </ol>
            </div>

            <form id="loginForm" class="section" onsubmit="submitLogin(event)">
                <div class="form-group">
                    <label for="loginUsername">Uživatelské jméno:</label>
                    <input type="text" id="loginUsername" placeholder="Zadejte jméno" required>
                </div>

                <div class="form-group">
                    <label for="loginPassword">Heslo:</label>
                    <input type="password" id="loginPassword" placeholder="Zadejte heslo" required>
                </div>

                <div class="form-group">
                    <button type="submit" class="btn">▶ Přihlásit se</button>
                </div>
            </form>

            <div id="loginResult" class="hidden">
                <div class="section" style="background-color: rgba(0, 204, 102, 0.1);">
                    <h4 style="color: var(--success);">Výsledek přihlášení</h4>
                    <p id="loginMessage"></p>
                    <div id="loginDetail" class="result-box"></div>
                </div>
            </div>

            <div class="info-box">
                <strong>💡 Tip pro testování:</strong><br>
                Zkuste uživatele: <code>demo_user</code> nebo <code>test_account</code>
            </div>
        </div>
    </div>

    <!-- REGISTER TAB -->
    <div id="register-tab" class="content-area">
        <div class="section">
            <h3>✍️ Registrace</h3>

            <div class="description">
                <strong>Bezpečné ukládání heš:</strong>
                <ol style="margin-left: 1.5rem; margin-top: 0.5rem; color: var(--text-secondary);">
                    <li>Uživatel zadá nové heslo</li>
                    <li>Heslo se zahešuje pomocí bcrypt s náhodným salt (HMAC-SHA512)</li>
                    <li>Hash se uloží do databáze (heslo nikdy není uloženo v plaintext!)</li>
                    <li>Hash má vestavěný salt a je pokaždé unikátní i pro stejné heslo</li>
                    <li>Náklady (cost=12) zpomalují útok brute-force</li>
                </ol>
            </div>

            <form id="registerForm" class="section" onsubmit="submitRegister(event)">
                <div class="form-group">
                    <label for="regUsername">Uživatelské jméno:</label>
                    <input type="text" id="regUsername" placeholder="Zvolte uživatelské jméno" required>
                </div>

                <div class="form-group">
                    <label for="regEmail">Email:</label>
                    <input type="email" id="regEmail" placeholder="Zadejte email" required>
                </div>

                <div class="form-group">
                    <label for="regPassword">Heslo:</label>
                    <input type="password" id="regPassword" placeholder="Minimálně 8 znaků" required>
                </div>

                <div class="form-group">
                    <label for="regPasswordConfirm">Potvrďte heslo:</label>
                    <input type="password" id="regPasswordConfirm" placeholder="Zopakujte heslo" required>
                </div>

                <div class="form-group">
                    <button type="submit" class="btn">✓ Zaregistrovat se</button>
                </div>
            </form>

            <div id="registerResult" class="hidden">
                <div class="section" style="background-color: rgba(0, 204, 102, 0.1);">
                    <h4 style="color: var(--success);">Výsledek registrace</h4>
                    <p id="registerMessage"></p>
                    <div id="registerDetail" class="result-box"></div>
                </div>
            </div>
        </div>
    </div>

    <!-- CREDENTIALS TAB -->
    <div id="credentials-tab" class="content-area">
        <div class="section">
            <h3>👥 Demo Uživatelé</h3>

            <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">
                Níže jsou demo účty pro testování přihlášení. V produkci by tato pověření nebyla veřejně dostupná.
            </p>

            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Uživatelské jméno</th>
                        <th>Email</th>
                        <th>Hash Prefix</th>
                        <th>Vytvořeno</th>
                    </tr>
                </thead>
                <tbody>
                    <?php
                    foreach ($demoCredentials as $cred) {
                        echo "<tr>";
                        echo "<td>#{$cred['id']}</td>";
                        echo "<td><code>{$cred['username']}</code></td>";
                        echo "<td>{$cred['email']}</td>";
                        echo "<td><small>" . substr($cred['password_hash'], 0, 20) . "...</small></td>";
                        echo "<td>{$cred['created_at']}</td>";
                        echo "</tr>";
                    }
                    ?>
                </tbody>
            </table>

            <div class="warning-box" style="margin-top: 1.5rem;">
                <strong>⚠️ Poznámka:</strong> Toto je demo prostředí.
                Uživatelé zde nejsou skutečně ověřeni.
                V produkci by se používala databáze a TLS/SSL zabezpečení.
            </div>
        </div>
    </div>

    <div class="section mt-3">
        <h3>📚 O Hašování a Autentifikaci</h3>

        <h4>Bcrypt - Hašovací Algoritmus</h4>
        <div class="description">
            Bcrypt je adaptivní hašovací funkce založená na Blowfish šifře.
            Má vestavěný salt a umožňuje zvýšení nákladů (cost factor) bez změny hashů.
            To znamená, že se postupem času, jak se počítače zrychlují, lze zvyšovat náklady.
        </div>

        <h4>Přihlášení vs Registrace</h4>
        <table>
            <thead>
                <tr>
                    <th>Aspekt</th>
                    <th>Přihlášení</th>
                    <th>Registrace</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>Účel</strong></td>
                    <td>Ověřit existujícího uživatele</td>
                    <td>Vytvořit nový účet</td>
                </tr>
                <tr>
                    <td><strong>Heslo</strong></td>
                    <td>Porovnávno s hashem</td>
                    <td>Zašifrováno a uloženo</td>
                </tr>
                <tr>
                    <td><strong>Rychlost</strong></td>
                    <td>Pomalejší (ověření je drahé)</td>
                    <td>Stejně pomalá (bezpečnost)</td>
                </tr>
                <tr>
                    <td><strong>Chyba</strong></td>
                    <td>"Špatné jméno nebo heslo"</td>
                    <td>"Hesla se neshodují"</td>
                </tr>
                <tr>
                    <td><strong>Datové tabulky</strong></td>
                    <td>Čtení z existujících dat</td>
                    <td>Zápis do nových řádků</td>
                </tr>
            </tbody>
        </table>

        <h4 style="margin-top: 1.5rem;">Bezpečnostní Best Practices</h4>
        <div class="description">
            <ul style="margin-left: 1.5rem; color: var(--text-secondary);">
                <li>✓ Vždy přenášejte hesla přes HTTPS (nikdy HTTP)</li>
                <li>✓ Nikdy neukládejte hesla v plaintext</li>
                <li>✓ Používejte adaptivní hašovací funkce (bcrypt, argon2)</li>
                <li>✓ Implementujte rate limiting při přihlášení (ochrana brute-force)</li>
                <li>✓ Přidejte CSRF ochranu na formuláře</li>
                <li>✓ Logujte neúspěšné pokusy o přihlášení</li>
                <li>✓ Zvažte dvoustupňové ověřování (2FA)</li>
            </ul>
        </div>
    </div>
</div>

<script>
function switchTab(tab) {
    document.getElementById('login-tab').classList.remove('active');
    document.getElementById('register-tab').classList.remove('active');
    document.getElementById('credentials-tab').classList.remove('active');

    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));

    document.getElementById(tab + '-tab').classList.add('active');
    event.target.classList.add('active');
}

function submitLogin(e) {
    e.preventDefault();

    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    // Simulace
    setTimeout(() => {
        const resultDiv = document.getElementById('loginResult');
        const messageDiv = document.getElementById('loginMessage');
        const detailDiv = document.getElementById('loginDetail');

        messageDiv.textContent = `Ověřování uživatele: ${username}`;
        detailDiv.innerHTML = `Heslo by bylo porovnáno s uloženým bcrypt hashem.<br>
            <br>
            <strong>Proces:</strong><br>
            1. Vyhledán uživatel v databázi<br>
            2. Zadané heslo zahešováno<br>
            3. Porovnáno s uloženým hashem<br>
            4. Výsledek ověřen s cost=12 (pomalejší = bezpečnější)<br>
            <br>
            <span class="text-accent">ℹ️ (Toto je demo, bez reálného ověření)</span>`;

        resultDiv.classList.remove('hidden');
    }, 500);
}

function submitRegister(e) {
    e.preventDefault();

    const username = document.getElementById('regUsername').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    const passwordConfirm = document.getElementById('regPasswordConfirm').value;

    if (password !== passwordConfirm) {
        document.getElementById('registerDetail').innerHTML =
            '<span class="text-error">✗ Chyba: Hesla se neshodují</span>';
        document.getElementById('registerResult').classList.remove('hidden');
        return;
    }

    if (password.length < 8) {
        document.getElementById('registerDetail').innerHTML =
            '<span class="text-error">✗ Chyba: Heslo musí mít alespoň 8 znaků</span>';
        document.getElementById('registerResult').classList.remove('hidden');
        return;
    }

    setTimeout(() => {
        const resultDiv = document.getElementById('registerResult');
        const messageDiv = document.getElementById('registerMessage');
        const detailDiv = document.getElementById('registerDetail');

        messageDiv.textContent = `Registrace uživatele: ${username}`;

        // Generuj fake hash
        const fakeHash = '$2y$12$' + Math.random().toString(36).substring(2, 25);

        detailDiv.innerHTML = `<strong>Nový účet vytvořen</strong><br>
            <br>
            Username: <code>${username}</code><br>
            Email: <code>${email}</code><br>
            <br>
            <strong>Bcrypt Hash:</strong><br>
            <code style="word-break: break-all; display: block; margin-top: 0.5rem;">
            ${fakeHash}...
            </code><br>
            <br>
            <span class="text-success">✓ Heslo zahešováno a uloženo do databáze</span><br>
            <span class="text-secondary">(Cost=12, s náhodným salt)</span>`;

        resultDiv.classList.remove('hidden');
    }, 800);
}
</script>
