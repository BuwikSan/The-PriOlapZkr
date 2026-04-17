# Homelab Website Development Plan

## Project Overview
A self-hosted vanilla PHP website featuring:
- **OLAP & Data Mining**: Compare DuckDB vs PostgreSQL with BMW dataset
- **Cryptography**: Hill cipher + Kyber cipher (post-quantum) with encrypt/decrypt tools
- **Machine Learning**: Placeholder for future expansion

**Architecture**: Vanilla HTML/CSS/PHP frontend + Python backend via Docker, Cloudflare domain

---


## Phase 0: Infrastructure setup (will pobably be last to be done)

### 0.1 Linux Distro Selection
- **✅ CHOSEN**: Debian 12
- **Rationale**: Minimal footprint, stable packages, better RAM efficiency (8GB resource optimization)
- **Server Specs**: 4-core CPU, 8GB DDR3 RAM
- **Setup**: Netinstall (minimal) + SSH + Docker only (no desktop environment)


## Phase 1: Docker Setup


### 1.1 Docker Compose Architecture
```
homelab-website/
├── docker-compose.yml
├── Dockerfile (PHP+web server)
├── services/
│   ├── postgres/ (OLAP DB)
│   ├── duckdb/ (OLAP DB)
│   └── python-backend/ (compute engine)
├── www/ (PHP frontend)
└── data/ (CSV, database files)
```

**Containers**:
1. **PHP/Web** (`Dockerfile`): Apache/Nginx + PHP 8.1+
2. **PostgreSQL**: Port 5432 (internal)
3. **DuckDB**: File-based (shared volume)
4. **Python Backend**: Python 3.10+ with cryptography libraries



## Phase 2: Database Setup & Data Pipeline

### 2.1 Data Ingestion (One-Time Load)
- Source: `bmw.csv` (already structured in DataGrip)
- **Process**:
  1. Export schema from DataGrip → `docker/postgres/init.sql`
  2. PostgreSQL container loads schema on startup
  3. Load CSV data into PostgreSQL
  4. Replicate data into DuckDB (file-based)
  5. Both DBs remain read-only after load


### 2.2 Schema Persistence
- Data stored in Docker volumes
- Volumes persist between container restarts
- No continuous sync or validation needed
- No backup/recovery procedures (one-time reference data)


### 2.3 Database Strategy
- **PostgreSQL**: Traditional OLAP structure, normalized schema
- **DuckDB**: Columnar format for analytical queries
- **Both treated equally**: Every query runs on both for comparison
- No primary/secondary relationship
- No caching, sharding, or special optimization

---

## Phase 3: Backend Development (Python)



### 3.1 OLAP Query Engine
**Location**: `src/olap/olap_backend.py` (refactor from existing `olap_comparison.py`)

**9 Pre-Built Queries** (from your existing code):

**SLICE Queries (1 dimension filtering)**:
- Diesel vehicles in 2010s decade
- Premium petrol (price > 30k)

**DICE Queries (multi-dimension + ranking)**:
- Top 15 most expensive combinations (min 5 sales)
- Top 10 cheapest (min 10 sales)
- Best price/MPG ratio (calculated column, 2010+)

**DRILL-DOWN Queries (hierarchical aggregation)**:
- Model-only aggregation (1 level)
- Model + Year (2 levels)
- Model + Year + Engine + Fuel (4 levels)

**Features**:
- Time measurement: Average of 3 runs for each query
- Both DuckDB and PostgreSQL execution
- Results comparison: speedup factor, row counts, validation
- JSON output to PHP wrapper

**Interface**: Python functions → PHP calls via `shell_exec()` or subprocess wrapper

**Code Style**:
- Existing `OLAPComparison` class structure (keep it)
- Simple functions: `execute_pg()`, `execute_duck()`, `compare_query()`
- Comments for each query type
- Return: Execution time, rows affected, speedup ratio





### 3.2 Cryptography Backend
**Location**: `src/crypto/crypto_backend.py` (new)

#### Hill Cipher (existing)
- Move existing Python implementation
- Functions: `encrypt_hill()`, `decrypt_hill()`, `generate_key_hill()`
- Input validation: key matrix invertibility, plaintext constraints
- Return: ciphertext, key, metadata

#### Kyber Implementation (Python)
- **Library**: liboqs-python (NIST-approved Kyber wrapper) or custom implementation
- Functions: `keygen_kyber()`, `encrypt_kyber()`, `decrypt_kyber()`
- Constraints: Standard NIST parameters
- Return: ciphertext, public key, shared secret
- **Note**: Same language as Hill cipher for consistency and simplicity

### 3.3 Backend-Frontend Bridge
- Generate temporary session files with results
- Or direct output in JSON format
- PHP calls Python via `shell_exec()` or subprocess (safe wrapper)

---




## Phase 4: Frontend Development (PHP + HTML/CSS)

### 4.1 Page Structure (Desktop-only, Dark Mode, Simple Design)
```


dashboard.php (main hub)
├── Brief welcome message
├── Navigation menu
│   ├── OLAP Queries
│   ├── Cryptography Tools
│   └── Machine Learning
└── Project description

olap.php (publicly accessible)
├── Query selector dropdown (9 queries)
├── Column selection checkboxes
├── Run button
├── Results table
├── Timing comparison (PostgreSQL vs DuckDB)
└── Query explanation

crypto.php (publicly accessible)
├── Section 1: Hill Cipher (input, output, explanation)
├── Section 2: Kyber Cipher (input, output, explanation)
└── Section 3: Password Hashing Demo (Educational)
    └── Additional hashing examples

hash_preview.php (hash verification demo - entry point)
├── Username & password input
├── Submit button (verify credentials)
├── Result display (success or failure)
├── Credentials table (all entries stored in db to see how it is stored in practice)
└── Explanation (how hashing works)
```
**All pages publicly accessible** - No sessions or protection needed



### 4.2 Code Philosophy & Simplicity

**Critical Requirement**: Every line must be explainable to an examiner.

**Code principles**:
- **No frameworks**: Plain PHP, no Laravel/Symfony/etc
- **Compact code**: Avoid unnecessary variable declarations, single-line functions are fine
- **Clear storage**: Variables you DO use must be readable and self-documenting
- **One thing per file**: `olap.php`, `crypto.php`, keep concerns separated
- **Error handling**: Simple try/catch, clear error messages

**Example - PREFERRED** (compact, no wasted variables):
```php
<?php
// Direct return, no unnecessary intermediate variables
function hash_password($pass) { 
    return password_hash($pass, PASSWORD_BCRYPT, ['cost' => 12]);
}

// Stored variables are clear when used
function verify_password($pass, $hash) { 
    return password_verify($pass, $hash);
}

// Clear variable names when storing values for reuse
$user_id = get_user_id($username);
$is_valid = verify_password($password, $stored_hash);
?>
```

**Philosophy**: Avoid intermediate variables like `$temp` if you can return directly. But when storing values, use names that clearly explain their purpose.

### 4.3 Styling Strategy
- **Single CSS file**: `styles/main.css`
- **Dark theme**: #1a1a1a background, light gray text
- **Components**: Forms, tables, buttons (minimal, reusable)
- **No frameworks**: Pure CSS Grid/Flexbox
- **Comments in CSS**: Explain layout sections

### 4.4 Form Validation & Input Handling

**OLAP Queries**:
- Dropdown: Select from 9 pre-built queries
- Checkboxes: Select which columns to display
- Python builds dynamic SELECT clause based on choices
- Parameterized queries (prevent SQL injection)
- No validation complexity - just column string building

**Cryptography**:
- Text input: No special validation (only interacts with php or python, if command is passed, it will be simply treated as another string + I have limited cypher alphabet for the hill cypher)
- 1000 char length limit
- No file uploads
- Plain text only

**Hashing Demo**:
- Username and Password input: (basic sanitization)
- Show plaintext, hash, and comparison visualization

---

## Phase 5: Authentication Demo & Form

**Status**: ✅ Educational Hash Verification Demo

**Scope** (Simplified):
- HTML form: username + password input
- Verify credentials against lightweight DB
- Display: success or failure message
- Show hashing process demonstration
- NO session management, NO protected pages
- All pages remain publicly accessible

**Database** (Lightweight):
- SQLite or DuckDB with `credentials` table (second duckdb database would be probably best)
- Table: `credentials (username, password_hash)`
- Pre-populate with test users
  - Example: user1 / password123
  - Example: user2 / secretpass

**Form Page** (`www/login.php`):
1. HTML form: text input (username), password input
2. Submit button (POST)
3. Process form:
   - Get username from query
   - Fetch hash from DB
   - Compare passwords using `password_verify()`
   - Display result

**Code Structure** (Simple):
```php
// www/includes/auth_demo.php (~25 lines)
function get_password_hash($username) {
    // Query credentials table for username
    // Return stored hash or false
}

function verify_credentials($username, $password) {
    // Get hash from DB
    // Use password_verify() for comparison
    // Return true/false
}

// www/login.php (~40 lines)
$result = null;
if ($_POST) {
    $username = $_POST['username'];
    $password = $_POST['password'];
    
    if (verify_credentials($username, $password)) {
        $result = "✓ Login successful!";
    } else {
        $result = "✗ Invalid credentials";
    }
}
?>
<form method="POST">
    <input type="text" name="username" required>
    <input type="password" name="password" required>
    <button>Verify Login</button>
</form>
<?php if ($result): ?>
    <p><?php echo $result; ?></p>
<?php endif; ?>
```

**Requirements Met**:
- ✅ HTML form for data input
- ✅ Database storage (credentials table)
- ✅ Read from database (query for username)
- ✅ Display data (show verification result)
- ✅ Explainable (simple hashing logic)

---


## Phase 6: Documentation & Testing

### 6.1 Code Documentation

**Inline Comments** (simple, explain "why"):
```php
// Check if password matches the stored hash
if (password_verify($input, $stored_hash)) {
    // User is authenticated
}
```

**Docstrings** (detailed for every function):
```python
def execute_pg(self, query: str, num_runs: int = 3) -> Tuple[pd.DataFrame, float]:
    """
    Execute query on PostgreSQL and measure execution time.
    
    Args:
        query: SQL query string to execute
        num_runs: Number of executions for averaging (default: 3)
    
    Returns:
        Tuple[pd.DataFrame, float]: Query results and avg execution time (ms)
    """
```

**README Files**:
- `www/README.md` - Frontend structure, page descriptions
- `project/README.md` - Backend OLAP and crypto functions
- `docker/README.md` - Docker setup, container management

**API Documentation**:
- Document all Python functions in `project/` with examples
- Include input/output examples
- List available queries and column options

**Config Files**:
- `www/includes/config.php` - DB credentials, settings, paths
- Environment variables for sensitive data

### 6.2 Unit Testing

**Framework**: `pytest` (Python)

**Test Files**:
- `project/test_olap.py` - Test OLAPComparison class
  - Verify each query runs without errors
  - Check result structure (columns, types)
  - Verify DuckDB vs PostgreSQL results match
  
- `project/test_crypto.py` - Test cryptography functions
  - Hill cipher: encrypt → decrypt → matches original
  - Kyber: keygen → encrypt → decrypt chain
  - Hashing: hash generation, verification

**Coverage**: Target 80%+ for backend functions

**Run Tests**:
```bash
pytest project/ -v
```

**Tests are required before deployment.**

### 6.3 Later Testing (Post-Launch)
- Integration tests (Docker + all services)
- Manual testing / QA procedures
- Performance benchmarking
- Browser compatibility (desktop only)

---

## File Structure (Updated)
```
c:\GitHub\OLAP-a-DM/
├── DEVELOPMENT_PLAN.md (this file)
├── DISCUSSION_POINTS.md (TBD topics)
├── docker-compose.yml
├── Dockerfile
├── docker/
│   ├── postgres/
│   │   └── init.sql
│   ├── duckdb/
│   └── python/
│       ├── requirements.txt
│       ├── olap_backend.py
│       └── crypto_backend.py
├── www/
│   ├── login.php (hash verification demo - entry point)
│   ├── dashboard.php (main hub)
│   ├── olap.php (OLAP queries)
│   ├── crypto.php (Crypto tools)
│   ├── ml.php (placeholder)
│   ├── styles/
│   │   └── main.css (one file, dark theme)
│   ├── includes/
│   │   ├── config.php (DB config, settings)
│   │   ├── auth_demo.php (hash verification functions)
│   │   ├── olap_wrapper.php (calls Python backend)
│   │   └── crypto_wrapper.php (calls Python backend)
│   └── assets/ (images if any)
├── project/
│   ├── olap_backend.py (9 OLAP queries)
│   ├── crypto_backend.py (Hill + Kyber + hashing)
│   ├── test_olap.py (unit tests)
│   ├── test_crypto.py (unit tests)
│   ├── bmw.csv
│   └── existing files...
└── data/
    ├── postgres_volume/
    └── duckdb_volume/
```

---

## Technology Stack Summary
| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | HTML5 + CSS3 | Dark theme, minimal, responsive to code changes |
| Backend (Web) | PHP 8.1+ | Form handling, session management |
| Compute | Python 3.10+ | OLAP queries, cryptography algorithms |
| OLAP DB #1 | PostgreSQL 15 | Traditional RDBMS comparison |
| OLAP DB #2 | DuckDB | Columnar, analytical engine comparison |
| Containerization | Docker + Docker Compose | Multi-service orchestration |
| Server | Ubuntu 22.04 or Debian 12 | Linux, Docker-ready |
| Domain | Cloudflare DNS | SSL proxying, DDoS protection |

---

## Phase 7: Deployment & Production Setup

### 7.1 Docker Build & Deploy (Windows - Local Development)
```bash
docker-compose up -d
```
Access: `http://localhost`

### 7.2 Docker Deploy (Linux Server - Production)
```bash
docker-compose up -d
```
Access: Via Cloudflare domain (after DNS setup)

### 7.3 Cloudflare Integration (Post-Server Setup)
- Add A record → home server IP
- Enable "Full SSL" in Cloudflare SSL/TLS settings
- Wait 24-48h for DNS propagation
- SSL cert automatically renewed by Cloudflare
- *(Tutorial to be written once server is ready)*

---

## Development Phases Timeline
1. **Phase 1**: Infrastructure setup (1-2 hrs)
2. **Phase 2**: Database schema & data load (1-2 hrs)
3. **Phase 3**: Python backends (OLAP + Crypto) (3-4 hrs)
4. **Phase 4**: PHP frontend & styling (2-3 hrs)
5. **Phase 5**: Login demo form (hash verification) (1 hr)
6. **Phase 6**: Documentation & unit tests (2-3 hrs)
7. **Phase 7**: Docker deployment & testing (1-2 hrs)

**Total Estimate**: 11-17 hours (sequential)

**Implementation**: 
- Start on Windows with Docker Desktop
- Test locally at `http://localhost`
- Deploy to Linux server
- Point Cloudflare domain to server IP
