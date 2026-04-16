# Homelab Website Development Plan

## Project Overview
A self-hosted vanilla PHP website featuring:
- **OLAP & Data Mining**: Compare DuckDB vs PostgreSQL with BMW dataset
- **Cryptography**: Hill cipher + Kyber cipher (post-quantum) with encrypt/decrypt tools
- **Machine Learning**: Placeholder for future expansion

**Architecture**: Vanilla HTML/CSS/PHP frontend + Python backend via Docker, Cloudflare domain

---

## Phase 1: Infrastructure & Environment Setup

### 1.1 Linux Distro Selection
- **Recommendation**: Ubuntu 22.04 LTS or Debian 12
- **Rationale**: Docker support, Hytale server compatibility, package ecosystem
- **Server Specs**: 4-core CPU, 8GB DDR3 RAM (resource optimization needed)

### 1.2 Docker Compose Architecture
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

### 1.3 SSL/HTTPS Setup

**Development (Windows + Docker Desktop)**:
- HTTP only on `localhost:80`
- No SSL certificates needed
- Direct access via browser

**Production (Linux Home Server)**:
- Cloudflare SSL proxying (automatic cert management)
- A record in Cloudflare → home server IP
- Full SSL mode in Cloudflare dashboard
- No manual renewal needed (Cloudflare handles it)
- *(See DISCUSSION_POINTS.md for detailed Cloudflare setup)*

---

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
**Location**: `project/olap_backend.py` (refactor from existing `olap_comparison.py`)

**9 Pre-Built Queries** (from your existing code):

**SLICE Queries (1 dimension filtering)**:
- Prices by year/fuel type (2017 data)
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
**Location**: `project/crypto_backend.py` (new)

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
index.php (home/welcome page)
├── dashboard.php (main hub with nav)
├── olap.php
│   ├── Query builder interface
│   ├── Results display (simple table)
│   ├── Execution time comparison (DuckDB vs PostgreSQL)
│   └── How it works explanation
├── crypto.php
│   ├── Section 1: Hill Cipher
│   │   ├── Input/output form
│   │   ├── Results display
│   │   └── Explanation (how it works)
│   ├── Section 2: Kyber Cipher
│   │   ├── Input/output form
│   │   ├── Results display
│   │   └── Explanation (how it works)
│   └── Section 3: Password Hashing Demo (Educational)
│       ├── Hash password demo
│       ├── Verify password demo
│       ├── Show hash output
│       └── Explanation (why hashing matters)
├── ml.php (placeholder - blank)
└── assets (CSS only)
```

**NO authentication system** - all pages publicly accessible

### 4.2 Code Philosophy & Simplicity

**Critical Requirement**: Every line must be explainable to an examiner.

**Code principles**:
- **No frameworks**: Plain PHP, no Laravel/Symfony/etc
- **No helpers**: Just standard PHP functions
- **Comments for every section**: Explain the "why", not the "what"
- **Consistent naming**: `$user`, `$password`, `$hash`, not abbreviations
- **One thing per file**: `olap.php`, `crypto.php`, keep concerns separated
- **No complex logic**: If/else preferred over ternary operators
- **Error handling**: Simple try/catch, clear error messages

**Example - GOOD**:
```php
<?php
// hash_password.php - Simple password hashing example

function hash_password($input_password) {
    // Use bcrypt algorithm with cost factor 12
    // Cost factor determines how long hashing takes (security vs speed)
    $hashed = password_hash($input_password, PASSWORD_BCRYPT, ['cost' => 12]);
    
    return $hashed;
}

function check_password($input_password, $stored_hash) {
    // Compare user-entered password with stored hash
    // Returns true if they match, false if not
    $is_valid = password_verify($input_password, $stored_hash);
    
    return $is_valid;
}
?>
```

**Example - BAD** (don't do this):
```php
<?php
function hp($p) { return password_hash($p, PASSWORD_BCRYPT); }
$valid = password_verify($p, $h) ? true : false;
// No comments, cryptic names, unreadable
?>
```

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
- Text input: No special validation
- No length limits
- No file uploads
- Plain text only

**Hashing Demo**:
- Password input: No validation
- Show plaintext, hash, and comparison visualization

---

## Phase 5: Authentication & User Management

**Status**: ✅ SIMPLIFIED - Educational Demo Only

**New Approach**: No actual login system. Instead, add an **educational cryptography subpage** demonstrating password hashing concepts.

**New Page**: `crypto_hashing.php`
- Demonstrates password hashing workflow
- Show plaintext password → hash → comparison
- Algorithms: bcrypt or Argon2 (simple example)
- Interactive demo: Users enter password, see hash generated, then verify attempt

**Educational Value** (for Cryptology Class):
- Shows why plaintext passwords are bad
- Demonstrates one-way hashing
- Shows salt usage
- Compares weak vs strong hashing

**Code Philosophy**: 
- **Super simple**: 10-15 lines per function, max
- **Well-commented**: Every line explained
- **No frameworks**: Plain PHP, no helpers
- **Example**: Show exact hash comparison logic

**Implementation**:
```php
// Example structure (simple)
function hash_password($password) {
    return password_hash($password, PASSWORD_BCRYPT);
}

function verify_password($password, $hash) {
    return password_verify($password, $hash);
}
```

**Files needed**:
- `www/crypto_hashing.php` - Demo page
- `www/includes/hashing_demo.php` - Simple hashing functions

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
│   ├── index.php (home page)
│   ├── dashboard.php (navigation hub)
│   ├── olap.php (OLAP queries)
│   ├── crypto.php (Hill cipher + Kyber cipher + Hashing demo)
│   ├── ml.php (placeholder)
│   ├── styles/
│   │   └── main.css (one file, dark theme)
│   ├── includes/
│   │   ├── config.php (DB config, paths)
│   │   ├── olap_wrapper.php (calls Python backend)
│   │   └── crypto_wrapper.php (calls Python backend)
│   └── assets/ (images, if any)
├── project/
│   ├── olap_backend.py (NEW)
│   ├── crypto_backend.py (NEW - Hill + Kyber)
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
5. **Phase 5**: Hashing demo page (1 hr)
6. **Phase 6**: Documentation & unit tests (2-3 hrs)
7. **Phase 7**: Docker deployment & testing (1-2 hrs)

**Total Estimate**: 11-17 hours (sequential)

**Then**: Windows development, then deploy to Linux server with Cloudflare DNS
