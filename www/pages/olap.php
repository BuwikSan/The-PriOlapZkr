<?php
/**
 * OLAP Showcase Page
 */
include __DIR__ . '/../includes/olap_wrapper.php';
?>

<div class="container">
    <h1>OLAP Showcase</h1>

    <p>
        Online Analytical Processing (OLAP) umožňuje rychlou analýzu velkých datových sadů.
        Níže si můžete vybrat různé typy analytických dotazů a porovnat výkon mezi PostgreSQL a DuckDB.
    </p>

    <div class="section">
        <h3>📋 Dostupné Dotazy</h3>

        <div class="form-group">
            <label for="querySelect">Vyberte dotaz:</label>
            <select id="querySelect" onchange="loadQuery()">
                <option value="">-- Vyberte OLAP dotaz --</option>
                <?php
                $queries = OlapWrapper::getAvailableQueries();
                foreach ($queries as $q) {
                    echo "<option value='{$q['id']}'>[{$q['type']}] {$q['name']}</option>";
                }
                ?>
            </select>
        </div>

        <div class="form-group">
            <label for="dbSelect">Porovnat s databází:</label>
            <div style="display: flex; gap: 1rem;">
                <label>
                    <input type="checkbox" name="dbCompare" value="postgres" checked>
                    PostgreSQL
                </label>
                <label>
                    <input type="checkbox" name="dbCompare" value="duckdb" checked>
                    DuckDB
                </label>
            </div>
        </div>

        <button onclick="executeQuery()">▶ Spustit Dotaz</button>
        <label style="margin-left: 1rem;">
            <input type="checkbox" id="compareCheckbox" checked>
            Porovnat s DuckDB
        </label>
    </div>

    <div id="resultsContainer" class="hidden">
        <div class="section">
            <h3>⚡ Výsledky</h3>

            <div id="pgResults" class="section" style="background-color: rgba(0, 102, 204, 0.1);">
                <h4 style="color: #0066cc;">PostgreSQL</h4>
                <p><strong>Čas zpracování:</strong> <span id="pgTime">-</span> ms</p>
                <p><strong>Počet řádků:</strong> <span id="pgRows">-</span></p>
                <p id="pgStatus" class="text-secondary">Čekání na data...</p>
                <div id="pgResultBox" class="result-box"></div>
            </div>

            <div id="duckResults" class="section hidden" style="background-color: rgba(204, 102, 0, 0.1);">
                <h4 style="color: #cc6600;">DuckDB</h4>
                <p><strong>Čas zpracování:</strong> <span id="duckTime">-</span> ms</p>
                <p><strong>Počet řádků:</strong> <span id="duckRows">-</span></p>
                <p id="duckStatus" class="text-secondary">Čekání na data...</p>
                <div id="duckResultBox" class="result-box"></div>
            </div>

            <div id="comparison" class="section hidden">
                <h4>📊 Porovnání Výkonu</h4>
                <p><strong>Rychlejší databáze:</strong> <span id="faster">-</span></p>
                <p><strong>Zrychlení:</strong> <span id="speedup">-</span>x</p>
            </div>
        </div>
    </div>    <div class="section mt-3">
        <h3>📐 Schéma Datového Skladu</h3>

        <?php
        $schema = OlapWrapper::getSchemaInfo();
        ?>

        <h4>Hvězdicové Schéma (Star Schema)</h4>
        <p>
            <strong>Faktová Tabulka:</strong> <code>fact_sales</code> (10,566 prodejních záznamů)<br>
            Centrální faktová tabulka obsahuje prodejní transakce BMW s referencemi na dimenzionální tabulky.
        </p>

        <h4>Dimenzionální Tabulky:</h4>
        <table>
            <thead>
                <tr>
                    <th>Tabulka</th>
                    <th>Primární Klíč</th>
                    <th>Sloupce</th>
                    <th>Počet Záznamů</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><code>dim_model</code></td>
                    <td>model_id</td>
                    <td>model_id, model_name</td>
                    <td>25 modelů</td>
                </tr>
                <tr>
                    <td><code>dim_time</code></td>
                    <td>time_id</td>
                    <td>time_id, production_year, decade</td>
                    <td>27 let</td>
                </tr>
                <tr>
                    <td><code>dim_fuel_type</code></td>
                    <td>fuel_type_id</td>
                    <td>fuel_type_id, fuel_type_name</td>
                    <td>5 typů paliva</td>
                </tr>
                <tr>
                    <td><code>dim_transmission</code></td>
                    <td>transmission_id</td>
                    <td>transmission_id, transmission_name</td>
                    <td>5 typů převodovky</td>
                </tr>
                <tr>
                    <td><code>dim_engine</code></td>
                    <td>engine_id</td>
                    <td>engine_id, engine_size</td>
                    <td>18 velikostí motorů</td>
                </tr>
            </tbody>
        </table>

        <h4>Faktová Tabulka - Sloupce Měr</h4>
        <p style="color: var(--text-secondary);">
            <code>sale_id</code> (PK) | <code>model_id</code> (FK) | <code>time_id</code> (FK) | <code>fuel_type_id</code> (FK) | <code>transmission_id</code> (FK) | <code>engine_id</code> (FK) | <code>price</code> | <code>tax</code> | <code>mileage</code> | <code>mpg</code>
        </p>
    </div>

    <div class="description">
        <strong>🔍 OLAP Operace:</strong>
        <ul style="margin-left: 1.5rem; margin-top: 0.5rem;">
            <li><strong>SLICE:</strong> Vybírá podmnožinu dat fixováním jedné dimenze</li>
            <li><strong>DICE:</strong> Vybírá podmnožinu dat fixováním více dimenzí</li>
            <li><strong>DRILL-DOWN:</strong> Jde ze shrnutých dat k podrobnostem</li>
        </ul>
    </div>
</div>

<script>
function loadQuery() {
    const queryId = document.getElementById('querySelect').value;
    document.getElementById('resultsContainer').classList.add('hidden');
}

function executeQuery() {
    const queryId = document.getElementById('querySelect').value;
    const compareCheckbox = document.getElementById('compareCheckbox').checked;

    console.log('=== EXECUTE QUERY START ===');
    console.log('queryId:', queryId);
    console.log('compareCheckbox:', compareCheckbox);

    if (!queryId) {
        alert('Prosím, vyberte dotaz');
        return;
    }

    document.getElementById('resultsContainer').classList.remove('hidden');

    // Show/hide DuckDB results based on checkbox
    if (compareCheckbox) {
        document.getElementById('duckResults').classList.remove('hidden');
        document.getElementById('comparison').classList.remove('hidden');
    } else {
        document.getElementById('duckResults').classList.add('hidden');
        document.getElementById('comparison').classList.add('hidden');
    }

    // Show loading status
    document.getElementById('pgStatus').textContent = 'Načítání...';
    document.getElementById('pgResultBox').innerHTML = '';
    if (compareCheckbox) {
        document.getElementById('duckStatus').textContent = 'Načítání...';
        document.getElementById('duckResultBox').innerHTML = '';
    }

    // Build the URL (absolute path starting with /)
    let url = '/api/olap.php?';
    if (compareCheckbox) {
        url += 'action=compare&query_id=' + encodeURIComponent(queryId);
    } else {
        url += 'action=execute&query_id=' + encodeURIComponent(queryId) + '&db=postgres';
    }

    // TEST: Use test endpoint for debugging - UNCOMMENT TO DEBUG
    // url = '/api/test_response.php';

    console.log('Fetching:', url);

    // Fetch from PHP wrapper
    fetch(url)
        .then(response => {
            console.log('Response status:', response.status);
            console.log('Response statusText:', response.statusText);
            if (!response.ok) {
                throw new Error('HTTP ' + response.status + ' ' + response.statusText);
            }
            return response.text();
        })
        .then(text => {
            console.log('Response text length:', text.length);
            console.log('Response text (first 300 chars):', text.substring(0, 300));
            try {
                const data = JSON.parse(text);
                console.log('Parsed data keys:', Object.keys(data));
                console.log('Parsed data:', data);
                if (compareCheckbox) {
                    console.log('Calling displayCompareResults');
                    displayCompareResults(data);
                } else {
                    console.log('Calling displaySingleResults');
                    displaySingleResults(data);
                }
            } catch (e) {
                console.error('JSON parse error:', e);
                console.error('Error parsing:', text);
                document.getElementById('pgStatus').textContent = '❌ Chyba: ' + e.message;
            }
        })
        .catch(error => {
            console.error('Fetch error:', error);
            console.error('Error stack:', error.stack);
            document.getElementById('pgStatus').textContent = '❌ Chyba: ' + error.message;
            if (compareCheckbox) {
                document.getElementById('duckStatus').textContent = '❌ Chyba: ' + error.message;
            }
        });
}

function displaySingleResults(data) {
    // Single database result - data is directly the response (not wrapped)
    console.log('displaySingleResults data:', data);

    // If response has 'error' key, show error
    if (data.error) {
        document.getElementById('pgStatus').textContent = '❌ Chyba: ' + data.error;
        return;
    }

    const pg = data;
    document.getElementById('pgTime').textContent = pg.execution_time_ms?.toFixed(2) || '-';
    document.getElementById('pgRows').textContent = pg.rows_returned || '0';
    document.getElementById('pgStatus').textContent =
        pg.rows_returned > 0 ? '✓ Úspěšně zpracováno' : '⚠️ Žádné výsledky';

    if (pg.results && pg.results.length > 0) {
        document.getElementById('pgResultBox').innerHTML = formatResults(pg.results);
    } else {
        document.getElementById('pgResultBox').innerHTML = '<p>Žádné výsledky</p>';
    }
}

function displayCompareResults(data) {
    // Display PostgreSQL results
    if (data.postgres) {
        const pg = data.postgres;
        document.getElementById('pgTime').textContent = pg.execution_time_ms?.toFixed(2) || '-';
        document.getElementById('pgRows').textContent = pg.rows_returned || '0';
        document.getElementById('pgStatus').textContent =
            pg.rows_returned > 0 ? '✓ Úspěšně zpracováno' : '⚠️ Žádné výsledky';
        document.getElementById('pgResultBox').innerHTML = formatResults(pg.results);
    }

    // Display DuckDB results
    if (data.duckdb) {
        const duck = data.duckdb;
        document.getElementById('duckTime').textContent = duck.execution_time_ms?.toFixed(2) || '-';
        document.getElementById('duckRows').textContent = duck.rows_returned || '0';
        document.getElementById('duckStatus').textContent =
            duck.rows_returned > 0 ? '✓ Úspěšně zpracováno' : '⚠️ Žádné výsledky';
        document.getElementById('duckResultBox').innerHTML = formatResults(duck.results);
    }

    // Display comparison
    if (data.comparison) {
        const comp = data.comparison;
        document.getElementById('faster').textContent = comp.faster_database || '-';
        document.getElementById('speedup').textContent = (comp.speedup_factor || 0).toFixed(2) + 'x';
    }
}

function formatResults(results) {
    if (!results || results.length === 0) {
        return '<em>Žádné výsledky</em>';
    }

    // Show first 5 rows as formatted table
    let html = '<table style="font-size: 0.9em; width: 100%; margin-top: 0.5rem;">';

    // Headers
    const keys = Object.keys(results[0]);
    html += '<thead><tr>';
    keys.forEach(k => html += '<th style="padding: 0.3rem; text-align: left;">' + k + '</th>');
    html += '</tr></thead>';

    // Rows
    html += '<tbody>';
    results.slice(0, 5).forEach(row => {
        html += '<tr>';
        keys.forEach(k => {
            const val = row[k];
            let display = val;
            if (typeof val === 'number') display = val.toLocaleString('cs-CZ');
            html += '<td style="padding: 0.3rem; border-bottom: 1px solid #404040;">' + display + '</td>';
        });
        html += '</tr>';
    });
    html += '</tbody>';
    html += '</table>';

    if (results.length > 5) {
        html += '<em style="color: #888; font-size: 0.8em; display: block; margin-top: 0.5rem;">... + ' + (results.length - 5) + ' více řádků</em>';
    }

    return html;
}
</script>
