# Homelab Website Development Plan

## Project Overview
A self-hosted vanilla PHP website featuring:
- **OLAP & Data Mining**: Compare DuckDB vs PostgreSQL with BMW dataset
- **Cryptography**: Hill cipher + Kyber cipher (post-quantum) with encrypt/decrypt tools
- **Machine Learning**: Placeholder for future expansion

**Architecture**: Vanilla HTML/CSS/PHP frontend + Python backend via Docker, Cloudflare domain

---

## Project Structure

```
src/
├── crypto/
│   ├── crypto_backend.py (interface for PHP, aggregates all crypto functions)
│   ├── HashingPrev/
│   │   ├── hashing_backend.py (password hashing demo interface)
│   │   └── methods/ (hashing logic)
│   ├── HillC/
│   │   ├── Hcypher.py (Hill cipher implementation)
│   │   └── methods/ (Hill cipher logic)
│   └── KyberC/
│       ├── Kcypher.py (Kyber cipher implementation)
│       └── methods/ (Kyber logic)
├── olap/
│   ├── olap_backend.py (interface for PHP, exposes OLAP queries)
│   └── methods/
│       └── olap_class.py (OLAP query implementation)
www/
├── index.php (entry point)
├── dashboard.php (main hub)
├── olap.php (OLAP interface)
├── crypto.php (Cryptography tools interface)
├── hash_preview.php (Login hash demo)
├── ml.php (placeholder)
├── includes/
│   ├── config.php (database & env config)
│   ├── olap_wrapper.php (PHP↔Python bridge for OLAP)
│   └── crypto_wrapper.php (PHP↔Python bridge for Crypto)
└── styles/
    └── main.css (dark theme)
```

---

## Development Phase Plan

### Phase 0: Docker & Database Infrastructure

**Status**: ✅ PRIORITIZED FIRST

**Goal**: Complete Docker setup with all databases before any development

**Components**:
1. **Dockerfile** (✅ exists): PHP 8.2 + Apache + ODBC for DuckDB
2. **docker-compose.yml** (✅ exists): Web service configuration
3. **Add PostgreSQL service**: For OLAP data comparison
4. **Add DuckDB service**: For OLAP data comparison (or file-based in web container)
5. **Add Credentials DB**: Lightweight DuckDB/SQLite for login preview

**Databases**:
- **PostgreSQL**: BMW OLAP comparison data (Production RDBMS)
- **DuckDB #1**: BMW OLAP comparison data (Columnar analytics engine)
- **DuckDB #2** (or SQLite): Credentials table for hash_preview.php (username + password_hash)

**Action Items**:
- [ ] Update docker-compose.yml with PostgreSQL service
- [ ] Add volume mappings for data persistence
- [ ] Create docker/postgres/init.sql (schema export)
- [ ] Add Python requirements.txt to Dockerfile
- [ ] Test Docker setup locally on Windows



---

### Phase 1: Backend Interface Layer (Python Stubs)

**Status**: ⏳ BEFORE ANY WEBDEV

**Goal**: Define Python↔PHP protocol without implementing logic

**Purpose**: 
- PHP webpages will have working structure before backend is ready
- Backend interface is frozen before frontend dev starts
- Clear separation of concerns

**Components to Create**:

1. **`src/olap/olap_backend.py`** (stub/interface):
   ```python
   # Stub functions with signatures - logic to be filled in Phase 5
   def execute_slice_query(query_id):
       """Execute SLICE query, return JSON"""
       return {"query": "slice_1", "pg_time": 0, "duck_time": 0, "results": []}
   
   def execute_dice_query(query_id):
       """Execute DICE query, return JSON"""
       return {"query": "dice_1", "pg_time": 0, "duck_time": 0, "results": []}
   
   def execute_drilldown_query(query_id):
       """Execute DRILL-DOWN query, return JSON"""
       return {"query": "dd_1", "pg_time": 0, "duck_time": 0, "results": []}
   
   def get_available_columns():
       """Return list of columns for checkbox selection"""
       return []
   
   def build_dynamic_query(query_id, selected_columns):
       """Build SELECT clause from columns"""
       return ""
   ```

2. **`src/crypto/crypto_backend.py`** (stub/interface):
   ```python
   # Stub functions for Hill Cipher
   def encrypt_hill(plaintext, key):
       return {"ciphertext": "", "key": key}
   
   def decrypt_hill(ciphertext, key):
       return {"plaintext": "", "key": key}
   
   def generate_key_hill(size):
       return [[1, 0], [0, 1]]  # Identity matrix stub
   
   # Stub functions for Kyber
   def keygen_kyber():
       return {"public_key": "", "private_key": ""}
   
   def encrypt_kyber(plaintext, public_key):
       return {"ciphertext": "", "shared_secret": ""}
   
   def decrypt_kyber(ciphertext, private_key):
       return {"plaintext": "", "shared_secret": ""}
   
   # Stub functions for Hashing Demo
   def hash_password(password):
       return ""
   
   def verify_password(password, hash_value):
       return True
   ```

**Action Items**:
- [ ] Create skeleton `src/olap/olap_backend.py` with function signatures
- [ ] Create skeleton `src/crypto/crypto_backend.py` with function signatures
- [ ] Document expected JSON format (input/output)
- [ ] Update docker/requirements.txt with all dependencies

---

### Phase 2: Frontend Development (PHP Pages & Styling)

**Status**: ⏳ AFTER BACKEND INTERFACE

**Goal**: All PHP pages functional, calling backend stubs, UI complete before data loads

**Structure**:
```
www/
├── index.php → redirects to dashboard.php
├── dashboard.php (main hub, navigation)
├── olap.php (query interface, calls stub backend)
├── crypto.php (cipher tools interface, calls stub backend)
├── hash_preview.php (login demo, calls stub backend)
├── ml.php (placeholder)
├── includes/
│   ├── config.php (env vars, DB settings)
│   ├── olap_wrapper.php (shell_exec to Python backend)
│   └── crypto_wrapper.php (shell_exec to Python backend)
└── styles/
    └── main.css (dark theme, reusable components)
```

**Components**:

1. **`www/dashboard.php`** (hub):
   - Navigation to OLAP, Crypto, ML, Hash Demo
   - Project description
   - Dark theme template

2. **`www/olap.php`** (OLAP interface):
   - Dropdown: select from 9 queries (SLICE, DICE, DRILL-DOWN)
   - Checkboxes: select columns
   - Submit: calls `includes/olap_wrapper.php`
   - Display: results table, timing comparison, query explanation
   - Handles JSON response from backend

3. **`www/crypto.php`** (Cryptography interface):
   - Section 1: Hill Cipher (plaintext input, ciphertext output)
   - Section 2: Kyber Cipher (plaintext input, ciphertext output)
   - Section 3: Password Hashing (plaintext input, hash output)
   - Each section calls backend stub

4. **`www/hash_preview.php`** (Login hash demo):
   - Form: username + password input
   - Button: "Verify Login"
   - Display: verification result
   - Show: credentials table (all test entries)
   - Explanation: how hashing works

5. **`www/includes/olap_wrapper.php`** (bridge):
   ```php
   $query_id = $_POST['query_id'];
   $columns = $_POST['columns'] ?? [];
   $result = shell_exec("python src/olap/olap_backend.py " . escapeshellarg(json_encode($query_id, $columns)));
   echo json_decode($result);
   ```

6. **`www/includes/crypto_wrapper.php`** (bridge):
   ```php
   $operation = $_POST['operation'];  // 'encrypt_hill', 'decrypt_kyber', 'hash_pwd'
   $payload = $_POST['data'] ?? {};
   $result = shell_exec("python src/crypto/crypto_backend.py " . escapeshellarg(json_encode($operation, $payload)));
   echo json_decode($result);
   ```

7. **`www/styles/main.css`** (dark theme):
   - Dark background: #1a1a1a
   - Light text: #e0e0e0
   - Reusable components: forms, tables, buttons, navigation
   - Grid/Flexbox layout

8. **`www/includes/config.php`** (configuration):
   ```php
   define('DB_HOST', getenv('DB_HOST') ?: 'localhost');
   define('DB_USER', getenv('DB_USER') ?: 'root');
   define('DB_PASS', getenv('DB_PASS') ?: '');
   define('DB_NAME', getenv('DB_NAME') ?: 'bmw');
   define('PYTHON_PATH', '/usr/bin/python3');
   ```

**Action Items**:
- [ ] Create all PHP files with stubs
- [ ] Create CSS with dark theme
- [ ] Test locally: pages load, backend calls work (stubs return data)
- [ ] Verify form handling, JSON responses

---

### Phase 3: Database Population - OLAP Data

**Status**: ⏳ AFTER PAGES EXIST

**Goal**: Load BMW data into PostgreSQL and DuckDB

**Process**:
1. Export schema from DataGrip → `docker/postgres/init.sql`
2. PostgreSQL boots and loads schema
3. Load CSV data into PostgreSQL:
   - `project/bmw.csv` → PostgreSQL via bulk import
   - `docker/postgres/load_data.sql`
4. Verify PostgreSQL has data
5. Replicate to DuckDB:
   - Query PostgreSQL from Python
   - Create DuckDB tables
   - Populate from PostgreSQL results
6. Verify both DBs have identical data
7. Test: Basic queries on both DBs return same results

**Action Items**:
- [ ] Export schema from DataGrip → `docker/postgres/init.sql`
- [ ] Create `docker/postgres/load_data.sql` (bulk import script)
- [ ] Test Docker PostgreSQL startup with schema + data
- [ ] Create Python script to replicate PostgreSQL → DuckDB
- [ ] Verify data equivalence

---

### Phase 4: Hashing Demo Implementation

**Status**: ⏳ AFTER PAGES EXIST, BEFORE CRYPTO

**Goal**: Functional login preview with real password hashing

**Components**:
1. **`src/crypto/HashingPrev/hashing_backend.py`**:
   ```python
   import bcrypt
   
   def hash_password(password):
       return bcrypt.hashpw(password.encode(), bcrypt.gensalt(12))
   
   def verify_password(password, hash_value):
       return bcrypt.checkpw(password.encode(), hash_value)
   
   def get_all_credentials():
       # Return all test credentials from DB
       return [{"username": "user1", "hash": "..."}, ...]
   ```

2. **Database**: 
   - DuckDB credentials table: `credentials (username, password_hash)`
   - Pre-populated: user1/password123, user2/secretpass

3. **`www/hash_preview.php`** logic:
   - Accept form POST
   - Call backend to verify
   - Show: result + all credentials in DB

**Action Items**:
- [ ] Implement `src/crypto/HashingPrev/hashing_backend.py`
- [ ] Populate credentials DB with test users
- [ ] Update `www/hash_preview.php` to call real backend
- [ ] Show credentials table on page

---

### Phase 5: Cryptography Implementation

**Status**: ⏳ AFTER HASHING

**Goal**: Hill Cipher + Kyber Cipher fully working

**Components**:

1. **Hill Cipher**:
   - Move logic from `src/crypto/HillC/Hcypher.py` → `src/crypto/methods/` or methods/
   - Expose via `src/crypto/crypto_backend.py`:
     - `encrypt_hill(plaintext, key_matrix)`
     - `decrypt_hill(ciphertext, key_matrix)`
     - `generate_key_hill(size)`

2. **Kyber Cipher**:
   - Move logic from `src/crypto/KyberC/Kcypher.py` → `src/crypto/methods/`
   - Expose via `src/crypto/crypto_backend.py`:
     - `keygen_kyber()`
     - `encrypt_kyber(plaintext, public_key)`
     - `decrypt_kyber(ciphertext, private_key)`
   - Library: liboqs-python or custom Kyber implementation

3. **Integration**:
   - `src/crypto/crypto_backend.py` aggregates all functions
   - PHP pages `www/crypto.php` call backend via `www/includes/crypto_wrapper.php`

**Action Items**:
- [ ] Integrate Hill Cipher implementation
- [ ] Integrate Kyber implementation
- [ ] Update `src/crypto/crypto_backend.py` with real functions
- [ ] Test: encryption → decryption chain works
- [ ] Update `www/crypto.php` to display results

---

### Phase 6: OLAP Implementation

**Status**: ⏳ AFTER CRYPTO

**Goal**: 9 OLAP queries fully working on both databases

**Queries** (from existing code):

**SLICE Queries** (1 dimension filtering):
- Diesel vehicles in 2010s
- Premium petrol (price > 30k)

**DICE Queries** (multi-dimension + ranking):
- Top 15 most expensive combinations (min 5 sales)
- Top 10 cheapest (min 10 sales)
- Best price/MPG ratio (2010+)

**DRILL-DOWN Queries** (hierarchical aggregation):
- Model aggregation (1 level)
- Model + Year (2 levels)
- Model + Year + Engine + Fuel (4 levels)

**Implementation**:
1. Refactor existing `olap_class.py` logic
2. Implement in `src/olap/methods/olap_class.py`
3. Expose via `src/olap/olap_backend.py`:
   - `execute_query(query_id, columns_list)`
   - `execute_pg()`, `execute_duck()` (internal)
   - `compare_results()` (timing + validation)
4. Return JSON: `{query, pg_time, duck_time, speedup, results}`

**Column Selection**:
- `get_available_columns()` → list for checkboxes
- `build_dynamic_select(columns)` → parameterized query

**Features**:
- Time measurement: average of 3 runs
- Both DBs execution + comparison
- Results validation
- JSON output

**Action Items**:
- [ ] Implement SLICE queries
- [ ] Implement DICE queries
- [ ] Implement DRILL-DOWN queries
- [ ] Add column selection + dynamic SQL
- [ ] Test: Same results on both DBs
- [ ] Update `www/olap.php` to display results + timing

---

### Phase 7: Unit Tests

**Status**: ⏳ AFTER IMPLEMENTATIONS

**Framework**: pytest

**Test Files**:
1. **`project/test_olap.py`**:
   - Test each 9 queries runs without error
   - Verify result structure
   - Compare DuckDB vs PostgreSQL results

2. **`project/test_crypto.py`**:
   - Hill cipher: encrypt → decrypt = original
   - Kyber: keygen → encrypt → decrypt chain
   - Hashing: hash → verify logic

**Coverage**: 80%+ for backend functions

**Run**: `pytest project/ -v`

**Action Items**:
- [ ] Create test files
- [ ] Write 9 OLAP query tests
- [ ] Write crypto function tests
- [ ] Verify 80% coverage
- [ ] All tests pass before deployment

---

### Phase 8: Infrastructure Deployment (Linux Server)

**Status**: ⏳ FINAL (after all software complete)

**Goal**: Deploy on Debian 12 home server

**Steps**:
1. Provision Linux server (Debian 12 netinstall)
2. Install Docker + Docker Compose
3. Clone repository
4. `docker-compose up -d`
5. Access via Cloudflare tunnel or DNS A record
6. Enable Cloudflare SSL

**Configuration**:
- Environment variables for production
- Cloudflare tunnel token (if using tunnel)
- Firewall rules (only 80/443 exposed)

**Testing**:
- Verify services running: `docker ps`
- Test pages accessibility
- Test database connections
- Verify performance

**Action Items**:
- [ ] Provision Debian 12 server
- [ ] Install Docker
- [ ] Deploy docker-compose
- [ ] Configure Cloudflare
- [ ] Test from external network





---

## Code Philosophy & Best Practices

### Code Style
- **No frameworks**: Plain PHP/Python, no Laravel/Symfony/etc
- **Compact code**: Avoid unnecessary variable declarations, single-line functions okay
- **Clear storage**: Variables you DO use must be readable and self-documenting
- **Error handling**: Simple try/catch, clear error messages
- **Explainable**: Every line must be defendable to an examiner

### PHP Example (Preferred):
```php
<?php
// Direct return, no unnecessary intermediate variables
function hash_password($pass) { 
    return password_hash($pass, PASSWORD_BCRYPT, ['cost' => 12]);
}

function verify_password($pass, $hash) { 
    return password_verify($pass, $hash);
}

// Clear variable names when storing for reuse
$user_id = get_user_id($username);
$is_valid = verify_password($password, $stored_hash);
?>
```

### Python Example:
```python
def encrypt_hill(plaintext, key_matrix):
    """Encrypt plaintext using Hill cipher with key matrix"""
    return result_ciphertext

def decrypt_hill(ciphertext, key_inverse):
    """Decrypt using inverse key matrix"""
    return plaintext
```

---

## Technology Stack
| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | HTML5 + CSS3 + PHP 8.2 | Dark theme, minimal, vanilla |
| Backend (Compute) | Python 3.10+ | OLAP, cryptography |
| OLAP DB #1 | PostgreSQL 15 | Comparison database |
| OLAP DB #2 | DuckDB | Columnar analytics database |
| Credentials DB | DuckDB (file-based) | Login demo credentials |
| Containerization | Docker + Docker Compose | Local dev + production |
| Server OS | Debian 12 | Production deployment |

---

## Development Timeline & Effort Estimate

| Phase | Task | Duration | Status |
|-------|------|----------|--------|
| **Phase 0** | Docker + PostgreSQL + DuckDB setup | 2-3 hrs | ⏳ Next |
| **Phase 1** | Backend interface stubs (olap + crypto) | 1-2 hrs | ⏳ After 0 |
| **Phase 2** | Frontend pages (all PHP + CSS) | 3-4 hrs | ⏳ After 1 |
| **Phase 3** | Database population (BMW OLAP data) | 1-2 hrs | ⏳ After 2 |
| **Phase 4** | Hashing demo implementation | 1 hr | ⏳ After 3 |
| **Phase 5** | Cryptography (Hill + Kyber) | 3-4 hrs | ⏳ After 4 |
| **Phase 6** | OLAP queries (9 queries) | 2-3 hrs | ⏳ After 5 |
| **Phase 7** | Unit tests (OLAP + Crypto) | 1-2 hrs | ⏳ After 6 |
| **Phase 8** | Linux server setup + deployment | 2-3 hrs | ⏳ Final |
| | **TOTAL** | **16-24 hours** | |

**Key Dependency Chain**:
```
Phase 0 (Docker)
  ↓
Phase 1 (Backend stubs) + Phase 2 (Frontend) [parallel]
  ↓
Phase 3 (DB data)
  ↓
Phase 4 (Hashing)
  ↓
Phase 5 (Crypto)
  ↓
Phase 6 (OLAP)
  ↓
Phase 7 (Tests)
  ↓
Phase 8 (Deployment)
```

---

## Current Project State

**✅ Completed**:
- Directory structure created (`src/crypto/`, `src/olap/`, `www/`)
- Dockerfile created (PHP 8.2 + Apache + ODBC for DuckDB)
- docker-compose.yml created (web + tunnel services)
- Backend modules exist (empty):  - `src/olap/olap_backend.py`
  - `src/crypto/crypto_backend.py`
  - `src/crypto/HashingPrev/hashing_backend.py`
- Cipher implementations exist (not integrated):
  - `src/crypto/HillC/Hcypher.py`
  - `src/crypto/KyberC/Kcypher.py`
- OLAP class exists (not in Phase 1):
  - `src/olap/methods/olap_class.py`
- www/index.php exists (placeholder)
- Docker infrastructure docs created

**⏳ Next Immediate Tasks** (Phase 0):
1. Add PostgreSQL service to docker-compose.yml
2. Create docker/postgres/init.sql (schema export)
3. Add Python requirements.txt
4. Test Docker setup on Windows

**❌ Not Started**:
- Backend interfaces (Phase 1)
- Frontend pages (Phase 2)
- Database population (Phase 3)
- Everything beyond

---

## Migration Notes from Old Plan

**Changes from Previous Plan**:
- Phase 0 is **now first** (was last)
- Backend **stubs created before** frontend (was after)
- Frontend pages **call empty backends** initially
- Database population **after pages exist** (was before)
- Crypto hashing **separated from auth system** (no session system)
- Clearer separation: **protocol definition** → **interface** → **implementation**

**Rationale**:
- Allows parallel frontend + backend work
- Pages work with stub data immediately
- Backend interface frozen before frontend dev
- Avoids rework due to protocol changes
