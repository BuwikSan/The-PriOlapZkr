# Discussion Points & TBD Topics

This file tracks topics that need deeper discussion in future sessions.

---

## 1. SSL/HTTPS Strategy

**✅ DECIDED**:
- **SSL Method**: Cloudflare SSL proxying (automatic cert management)
- **Renewal**: Automatic (Cloudflare handles)
- **Caching**: Default Cloudflare settings, no caching for PHP/dynamic content
- **Development**: HTTP on localhost (no SSL needed)
- **Production**: Cloudflare A record + Full SSL mode

**Implementation**:
1. Add A record in Cloudflare dashboard → home server IP
2. Enable "Full SSL" in Cloudflare SSL/TLS settings
3. Wait 24-48h for DNS propagation
4. Certificate automatically renews

**Cloudflare DNS Propagation**:
- After adding A record, DNS spreads globally (24-48 hours)
- You can check status: `nslookup yourdomain.com`
- SSL cert provisioned automatically by Cloudflare

**Page Rules & Caching**:
- Don't cache: `/login.php`, `/crypto.php`, `/olap.php` (dynamic content)
- Cache: Static assets (CSS, images) for 1 hour
- Keep default settings initially, optimize later

**To-Do After Server Setup**:
- [ ] Step-by-step tutorial for Cloudflare setup (will create later)
- [ ] Test from external network after deployment

**Session**: ✅ Completed (Planning Session 1)

---






## 2. Kyber Cryptography Implementation Language

**✅ DECIDED: Python**

**Rationale**:
- Easy integration with existing Python OLAP backend
- Rapid development and testing
- Dependency management via `requirements.txt` in Docker
- Acceptable performance for educational/demo purposes
- Consistent tech stack (no need for Go/C++ wrappers)
- Hill cipher already in Python → keep same language

**Implementation Details**:
- Both Hill and Kyber will be in `project/crypto_backend.py`
- Library: liboqs-python (NIST-approved Kyber wrapper) or custom implementation
- Functions: `keygen_kyber()`, `encrypt_kyber()`, `decrypt_kyber()`, `keygen_hill()`, etc.
- All called via PHP wrapper in `www/` directory

**Performance Note**: 
- Python is slower than Go/C++, but acceptable for:
  - Small text inputs (crypto is fast enough for UI responsiveness)
  - Home lab educational project
  - Can optimize later if needed

**Docker Integration**:
- Add `liboqs-python` (or similar) to `requirements.txt`
- No compilation step needed (pure Python)
- Single image handles both OLAP + Crypto

**Session**: ✅ Completed (Planning Session 1)

---

## 3. Authentication System Details

**✅ DECIDED: Educational Demo Only (No Real Login System)**

**Why This Approach**:
- Simpler codebase (you can explain every line to your lecturer)
- Fulfills Cryptology class requirement (demonstrate hashing)
- Avoids unnecessary complexity
- Focuses on learning, not production features

**New Subpage**: `crypto_hashing.php` (under Cryptography section)

**Demonstrates**:
1. **Password hashing workflow**:
   - User enters password
   - System generates hash (bcrypt/Argon2)
   - Shows hash output
   - Shows comparison process

2. **Why hashing matters**:
   - One-way function (can't reverse)
   - Salt prevents rainbow tables
   - Time cost prevents brute force

3. **Code qualities**:
   - Simple: ~10-15 lines per function
   - Well-commented: Every line explained
   - No frameworks or helpers
   - Demonstrable to examiner line-by-line

**Example Code**:
```php
function hash_password($password) {
    // Generate hash using bcrypt algorithm with cost 12
    return password_hash($password, PASSWORD_BCRYPT, ['cost' => 12]);
}

function verify_password($password, $hash) {
    // Compare plaintext password with stored hash
    return password_verify($password, $hash);
}
```

**Website Access**: 
- No login required
- All pages publicly accessible
- Demo page shows hashing examples (interactive)

**Files to create**:
- `www/crypto_hashing.php` - Demo UI and explanation
- `www/includes/hashing_helpers.php` - Simple hashing functions (max 20 lines)

**Session**: ✅ Completed (Planning Session 1)

---

## 4. OLAP Query Builder Specification

**✅ DECIDED: Use Existing Query Set from `olap_comparison.py`**

**Query Categories** (9 pre-built queries total):

### SLICE Queries (Filter by 1 Dimension)
1. **SLICE 1**: Year 2017 prices (grouped by model × fuel type)
   - Metrics: sales count, avg/min/max price, avg mpg, avg mileage
   - Varies: Year parameter

2. **SLICE 2**: Diesel vs 2010s decade
   - Metrics: sales count, avg price, avg mpg, avg tax
   - Varies: Decade + fuel type

3. **SLICE 3**: Premium petrol (price > 30k)
   - Metrics: sales count, avg price, avg mpg
   - Varies: Price threshold

### DICE Queries (Multi-Dimension Filtering + TOP)
4. **DICE 1**: Top 15 most expensive combinations (min 5 sales)
   - Dimensions: model, year, engine size, fuel type, transmission
   - Metrics: sales count, avg price, avg mpg
   - Features: HAVING clause (min threshold), ORDER BY + LIMIT

5. **DICE 2**: Top 10 cheapest (min 10 sales)
   - Dimensions: model, year, engine size, fuel type, transmission
   - Metrics: sales count, avg price, min/max price

6. **DICE 3**: Best price/MPG ratio (2010+)
   - Dimensions: model, year, fuel type
   - Metrics: sales count, avg price, avg mpg, calculated price/mpg
   - Features: Calculated column, WHERE clause (year >= 2010)

### DRILL-DOWN Queries (Hierarchical Aggregation)
7. **DRILL-DOWN 1**: Models (1 aggregation level)
   - Grouped by: model only
   - Metrics: sales count, avg price, avg mpg

8. **DRILL-DOWN 2**: Model + Year (2 levels)
   - Grouped by: model, year
   - Metrics: sales count, avg price, min/max price, avg mpg

9. **DRILL-DOWN 3**: Model + Year + Engine + Fuel (4 levels - complex)
   - Grouped by: model, year, engine size, fuel type
   - Metrics: sales count, avg price, avg mpg, avg tax

**UI Implementation**:
- Dropdown selector: Show all 9 queries by name
- Some queries allow custom parameters (year, threshold, min count, etc.)
- Results displayed as HTML table
- Timing comparison: PostgreSQL vs DuckDB execution time (in ms)
- Display: Query name, results table, timing metrics, speedup factor

**Backend**:
- Python: `OLAPComparison` class from `project/olap_comparison.py`
- Timing: `execute_pg()` and `execute_duck()` measure query execution (average of 3 runs)
- PHP wrapper: Call Python backend, parse JSON results, display in table

**Code Structure**:
```
www/olap.php
├── Dropdown with 9 query options
├── Optional: Parameter input fields (for queries that support it)
├── Submit button (calls PHP backend)
└── Results display
    ├── Query executed
    ├── Results table (paginated if large)
    ├── PostgreSQL time: XXX ms
    ├── DuckDB time: XXX ms
    └── Speedup: X.XXx faster

project/olap_backend.py
└── Python functions to run each query on both DBs
```

**Exam-Ready Explanation**:
- Each query demonstrates OLAP operations: SLICE, DICE, DRILL-DOWN
- Timing comparison shows real performance difference
- Simple enough to explain each query's purpose in 2-3 sentences

**Session**: ✅ Completed (Planning Session 1)

---

## 5. Cryptography UI/UX Details

**Current Plan**: Text input, encrypt/decrypt, with documentation

**Questions for Discussion**:

### Hill Cipher
- Key matrix size: fixed (3x3) or user-selectable (2x2, 3x3, 4x4)?
- Key generation: show as matrix or numbers?
- Constraint handling for non-invertible keys?
- Plaintext padding strategy for block size?

### Kyber
- Key size options: 512, 768, 1024?
- Display public key and ciphertext as hex or base64?
- Shared secret length and usage?
- Performance expectations?

### Both
- Input validation feedback (real-time or on submit)?
- Error messages clarity and detail?
- Documentation:
  - Where should it appear (below form, separate section)?
  - Mathematical rigor level?
  - Include examples and visualizations?

**Session**: Key component discussion (Cryptography)

---

## 6. Machine Learning Placeholder

**Current Plan**: Empty subpage for future expansion

**Questions for Discussion**:
- What ML functionality is envisioned?
- Timeline for development?
- Should placeholder page have content (description, roadmap)?

**Session**: Later (Phase 2+), or when ML requirements clarified

---

## 7. Data Pipeline & CSV Synchronization

**✅ DECIDED: One-Time Load, Read-Only**

**Approach**:
- Load BMW.csv into PostgreSQL and DuckDB (one-time)
- Data persists in Docker volumes
- No validation, no duplicate handling, no backup/recovery needed
- Replication from DataGrip setup into Docker

**Process**:
1. Export schema from DataGrip → `docker/postgres/init.sql`
2. Export data and import into PostgreSQL container on startup
3. Replicate same data into DuckDB file
4. Both DBs remain read-only after initial load

**Implementation**:
- Docker: `docker-compose` with volume mounts
- PostgreSQL: Load SQL dump on container init
- DuckDB: Load from CSV or replicate from PostgreSQL
- No continuous sync needed

**Session**: ✅ Completed (Planning Session 1)

---

## 8. Performance & Resource Constraints

**✅ DECIDED: Single User, No Limits, Both DBs Equal**

**Setup**:
- Single user (you) - no connection pooling needed
- No query result limits
- No max row constraints
- No resource monitoring/alerting
- Both DBs treated as equal comparison targets (not primary/secondary)
- No load testing needed

**Optimization Level**: Keep it simple, no premature optimization

**DB Strategy**:
- Every query runs on BOTH databases
- Compare execution time and results
- Both are "correct" - they just process differently
- No sharding, caching, or special tuning

**Session**: ✅ Completed (Planning Session 1)

---

## 9. User Input Constraints & Validation

**✅ DECIDED: Premade Queries with Column Selection**

**Approach**:
- Pre-built queries (9 OLAP queries from earlier decision)
- Users select which **columns to include** in results
- Python backend generates dynamic queries based on column selection
- No free-form SQL input
- No validation complexity

**Implementation**:
- Checkboxes/toggles for columns: `model`, `year`, `engineSize`, `fuelType`, `transmission`, `price`, `mpg`, etc.
- Python builds SELECT clause dynamically
- Parameterized queries (prevent injection)
- No complexity - just string building with validation

**Cryptography**:
- Keep text input simple
- No special validation (user's responsibility)
- No file uploads
- No length limits

**Session**: ✅ Completed (Planning Session 1)

---

## 10. Cloudflare Integration & Security

**Questions for Discussion**:
- Should certain endpoints bypass Cloudflare (API, auth)?
- Rate limiting for API calls?
- Bot protection/CAPTCHA needed?
- Access controls (country blocking, IPs)?
- Do we need Cloudflare Tunnel or direct DNS A record?

**Session**: Deployment phase or security review

---

## 11. Code Documentation & Maintainability

**✅ DECIDED: Minimal Comments, Detailed Docstrings, READMEs + API Docs**

**Comment Philosophy**:
- **Simple inline comments**: Only explain "why", not "what"
- **Detailed docstrings**: Every function has full docstring
  - Format: Describe purpose, args, returns, example usage
  - Python style: Google/NumPy format
  - PHP: PHPDoc format

**Documentation Files**:
- **README files**: One per major component
  - `www/README.md` - Frontend structure
  - `project/README.md` - Backend (OLAP + Crypto)
  - `docker/README.md` - Docker setup
- **API Docs**: Document all Python functions
  - Input parameters
  - Output format
  - Example calls
- **Config files**: `config.php` for settings
  - DB connections
  - Paths
  - Thresholds

**Example (Good)**:
```python
def execute_pg(self, query: str, num_runs: int = 3) -> Tuple[pd.DataFrame, float]:
    """
    Execute query on PostgreSQL database and measure execution time.
    
    Args:
        query: SQL query string to execute
        num_runs: Number of times to run (default: 3 for averaging)
    
    Returns:
        Tuple[pd.DataFrame, float]: Query results and average execution time (ms)
    
    Example:
        df, time_ms = comp.execute_pg("SELECT * FROM fact_sales LIMIT 10")
        print(f"Query took {time_ms:.2f} ms")
    """
```

**Session**: ✅ Completed (Planning Session 1)

---

## 12. Testing & Quality Assurance

**✅ DECIDED: Unit Tests Now, Rest Later**

**Implementation**:
- **Unit tests**: YES, create now for Python backend
  - Test each query runs without errors
  - Test OLAP comparison logic
  - Test crypto functions (encrypt → decrypt → original)
  - Framework: `pytest` (simple, no overhead)

- **Integration tests**: LATER (post-deployment)
- **Manual testing**: LATER (post-launch)
- **Performance testing**: LATER (after working version)
- **Browser compatibility**: LATER (after full feature set)

**Test File Location**: `project/test_olap.py` and `project/test_crypto.py`

**Coverage Target**: 80%+ of backend functions

**How to Run**:
```bash
pytest project/ -v
```

**Session**: ✅ Completed (Planning Session 1)

---

## Quick Reference: Decision Matrix

| Topic | Priority | Urgency | Assigned Session |
|-------|----------|---------|------------------|
| SSL/HTTPS Strategy | Medium | Phase 1 | ✅ Completed |
| Kyber Language | High | Phase 3 | ✅ Completed |
| Auth Details | Medium | Phase 5 | ✅ Completed |
| OLAP Queries | High | Phase 2-3 | ✅ Completed |
| Crypto UI/UX | High | Phase 4 | Key Component (Crypto) |
| ML Placeholder | Low | Phase 6+ | Later |
| Data Pipeline | High | Phase 2 | ✅ Completed |
| Resource Planning | Medium | Phase 1-2 | ✅ Completed |
| Input Constraints | Medium | Phase 3-4 | ✅ Completed |
| Cloudflare Setup | Medium | Phase 6 | Deployment |
| Code Docs | Low | Throughout | ✅ Completed |
| Testing | Low | Phase 6 | ✅ Completed (unit tests now, rest later) |

---

## Session Checklist

**Completed (Planning Session 1) - 11 of 12 Points**:
- ✅ Hardware specs confirmed
- ✅ Component architecture decided
- ✅ Tech stack finalized
- ✅ SSL/HTTPS Strategy: Cloudflare (production) + HTTP localhost (dev)
- ✅ Kyber Language: Python
- ✅ Authentication: Educational demo (no real login, hashing subpage)
- ✅ OLAP Query Specification: 9 queries (SLICE, DICE, DRILL-DOWN)
- ✅ Data Pipeline: One-time load, read-only, no validation
- ✅ Performance & Resources: Single user, no limits, equal DBs
- ✅ Input Constraints: Column selection toggles, dynamic queries
- ✅ Code Documentation: Comments + docstrings + READMEs + API docs + config
- ✅ Testing: Unit tests now (pytest), rest later
- ✅ Development plan created

**Still Open**:
- [ ] **Point 5 (Crypto UI/UX)**: Hill cipher, Kyber, hashing demo interfaces
- [ ] **Point 6 (ML Placeholder)**: Blank page, nothing else needed
- [ ] **Point 10 (Cloudflare)**: Tutorial after server setup

**Upcoming Sessions**:
- [ ] **Key Component 1**: OLAP & Data Mining (Finalize schema, test queries)
- [ ] **Key Component 2**: Cryptography (Hill Cipher, Kyber, Hashing demo interfaces)
- [ ] **Implementation Session**: Docker setup, PHP pages, Integration, Unit tests
- [ ] (Optional) **Key Component 3**: Machine Learning expansion
