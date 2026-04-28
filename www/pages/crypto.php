<?php
/**
 * Cryptography Page
 */
include __DIR__ . '/../includes/crypto_wrapper.php';

$hillInfo = CryptoWrapper::getCipherInfo('hill');
$kyberInfo = CryptoWrapper::getCipherInfo('kyber');
?>

<div class="container">
    <h1>Kryptografie & Šifrování</h1>

    <p>
        Prozkoumejte tradiční a moderní přístupy k šifrování.
        Hill cipher reprezentuje klasické symetrické šifrování, zatímco Kyber představuje budoucnost bezpečnosti post-kvantové éry.
    </p>

    <div class="tab-menu">
        <button class="tab-button active" onclick="switchTab('hill')">Hill Cipher</button>
        <button class="tab-button" onclick="switchTab('kyber')">Kyber (Post-Quantum)</button>
    </div>

    <!-- HILL CIPHER TAB -->
    <div id="hill-tab" class="content-area active">
        <div class="section">
            <h3><?php echo $hillInfo['name']; ?></h3>

            <div class="info-box">
                <strong>Typ:</strong> <?php echo $hillInfo['type']; ?><br>
                <strong>Velikost klíče:</strong> <?php echo $hillInfo['keySize']; ?><br>
                <strong>Velikost bloku:</strong> <?php echo $hillInfo['blockSize']; ?><br>
                <strong>Kola:</strong> <?php echo $hillInfo['rounds']; ?>
            </div>

            <div class="description">
                <strong>Popis:</strong><br>
                <?php echo $hillInfo['description']; ?>
                Algoritmus používá maticovou algebru nad abecedou 43 znaků (česká abeceda s diakritikou + mezera + tečka).
            </div>

            <div class="description">
                <strong>Jak funguje:</strong>
                <ul style="margin-left: 1.5rem; margin-top: 0.5rem; color: var(--text-secondary);">
                    <li>Vstupní text se převede na čísla dle abecedy (0-42)</li>
                    <li>Vznikne matice bloků (blok = řádek matice)</li>
                    <li>Každý blok se vynásobí šifrovací maticí modulo 43</li>
                    <li>Výsledná čísla se konvertují zpět na znaky</li>
                    <li>Dešifrování používá inverzní matici (mod 43)</li>
                </ul>
            </div>

            <div class="section">
                <h4>🔐 Hill Cipher Demo</h4>

                <div class="form-group">
                    <label for="hillInput">Vstupní Text (česky):</label>
                    <textarea id="hillInput" placeholder="Zadejte text k šifrování...">Ahoj Světe</textarea>
                </div>

                <div class="form-group">
                    <label>Operace:</label>
                    <div style="display: flex; gap: 1rem;">
                        <button onclick="hillEncrypt()" class="btn">🔒 Šifrovat</button>
                        <button onclick="hillDecrypt()" class="btn secondary">🔓 Dešifrovat</button>
                    </div>
                </div>

                <div class="form-group">
                    <label>Výsledek:</label>
                    <div id="hillOutput" class="result-box">Výsledek se bude zobrazovat zde...</div>
                </div>

                <div class="warning-box">
                    <strong>⚠️ Poznámka:</strong> Hill cipher je moderním pohledem již zastaralý a není vhodný
                    pro skutečné bezpečnostní účely. Je demonstrován zde pro edukační účely.
                </div>
            </div>
        </div>
    </div>

    <!-- KYBER TAB -->
    <div id="kyber-tab" class="content-area">
        <div class="section">
            <h3><?php echo $kyberInfo['name']; ?></h3>

            <div class="info-box">
                <strong>Typ:</strong> <?php echo $kyberInfo['type']; ?><br>
                <strong>Algoritmus:</strong> <?php echo $kyberInfo['algorithm']; ?><br>
                <strong>Ekvivalent:</strong> <?php echo $kyberInfo['nist_category']; ?><br>
                <strong>NIST Standardizace:</strong> ✓ Schváleno
            </div>

            <div class="description">
                <strong>Popis:</strong><br>
                <?php echo $kyberInfo['description']; ?>
                Kyber byl vybrán NIST jako standardní post-kvantový algoritmus v roce 2022
                a je již součástí mnoha bezpečnostních frameworků.
            </div>

            <div class="description">
                <strong>Proč post-kvantové šifrování?</strong>
                <ul style="margin-left: 1.5rem; margin-top: 0.5rem; color: var(--text-secondary);">
                    <li><strong>Hrozba kvantových počítačů:</strong> Dostatečně silný QC by mohl faktorizovat RSA a ECC</li>
                    <li><strong>Harvest Now, Decrypt Later:</strong> Útočník může nyní sbírat šifrované data a dešifrovat později</li>
                    <li><strong>Matematický základ:</strong> Kyber je založen na mřížkových problémech, které jsou odolné vůči QC</li>
                    <li><strong>Proizvedení:</strong> NIST doporučuje migrovat na PQC před faktickou hrozbou</li>
                </ul>
            </div>

            <div class="section">
                <h4>🔐 Kyber Demo</h4>

                <div class="info-box">
                    <strong>ℹ️ Status:</strong> Kyber implementace se právě připravuje.
                    Tato sekce bude brzy obsahovat interaktivní demo veřejného klíče (KEM),
                    sdílení tajemství a šifrování.
                </div>

                <div style="background-color: var(--bg-primary); border-left: 4px solid var(--warning); padding: 1rem; margin-top: 1rem; border-radius: 4px;">
                    <strong style="color: var(--warning);">🚧 Probíhá vývoj:</strong><br>
                    <p style="color: var(--text-secondary); margin-top: 0.5rem;">
                        Bude obsahovat:
                    </p>
                    <ul style="margin-left: 1.5rem; color: var(--text-secondary);">
                        <li>Generaci párů klíčů (Public/Private)</li>
                        <li>Encapsulation (vytvoření sdíleného tajemství)</li>
                        <li>Decapsulation (extrakce tajemství)</li>
                        <li>Vizualizaci klíčů a procesů</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>

    <div class="section mt-3">
        <h3>📊 Porovnání Algoritmů</h3>

        <table>
            <thead>
                <tr>
                    <th>Vlastnost</th>
                    <th>Hill Cipher</th>
                    <th>Kyber</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>Typ</strong></td>
                    <td>Symetrické blokové</td>
                    <td>Asymetrické (KEM)</td>
                </tr>
                <tr>
                    <td><strong>Matematika</strong></td>
                    <td>Lineární algebra (mod n)</td>
                    <td>Mřížkové problémy</td>
                </tr>
                <tr>
                    <td><strong>Bezpečnost</strong></td>
                    <td>Zastaralá ❌</td>
                    <td>Post-kvantová ✓</td>
                </tr>
                <tr>
                    <td><strong>Rychlost</strong></td>
                    <td>Velmi rychlá</td>
                    <td>Moderně rychlá</td>
                </tr>
                <tr>
                    <td><strong>Praktické použití</strong></td>
                    <td>Edukace, historie</td>
                    <td>Budoucnost, NIST standard</td>
                </tr>
                <tr>
                    <td><strong>Odolnost vůči QC</strong></td>
                    <td>Není ✗</td>
                    <td>Ano ✓</td>
                </tr>
            </tbody>
        </table>
    </div>
</div>

<script>
function switchTab(tab) {
    // Hide all tabs
    document.getElementById('hill-tab').classList.remove('active');
    document.getElementById('kyber-tab').classList.remove('active');

    // Remove active from all buttons
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));

    // Show selected tab
    document.getElementById(tab + '-tab').classList.add('active');
    event.target.classList.add('active');
}

function hillEncrypt() {
    const text = document.getElementById('hillInput').value;
    const output = document.getElementById('hillOutput');

    if (!text) {
        output.innerHTML = '<span class="text-error">Chyba: Zadejte text</span>';
        return;
    }

    // Simulace - v produkci by volala backend
    setTimeout(() => {
        output.innerHTML = '<span class="text-success">✓ Šifrování v procesu...</span><br>' +
            'Vstup: ' + text + '<br>' +
            'Výstup: [šifrovaný text] (backend se připravuje)';
        output.classList.add('success');
    }, 500);
}

function hillDecrypt() {
    const text = document.getElementById('hillInput').value;
    const output = document.getElementById('hillOutput');

    if (!text) {
        output.innerHTML = '<span class="text-error">Chyba: Zadejte šifrovaný text</span>';
        return;
    }

    // Simulace
    setTimeout(() => {
        output.innerHTML = '<span class="text-success">✓ Dešifrování v procesu...</span><br>' +
            'Vstup: ' + text + '<br>' +
            'Výstup: [dešifrovaný text] (backend se připravuje)';
        output.classList.add('success');
    }, 500);
}
</script>
