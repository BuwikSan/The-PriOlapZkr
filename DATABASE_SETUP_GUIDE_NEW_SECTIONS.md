## Python Integration

### Directory Structure

```
src/
├── db/
│   ├── sync_duckdb.py          # PostgreSQL → DuckDB replication
│   └── db_config.py            # Connection pooling + constants
├── olap/
│   ├── query_builder.py        # Dynamic query construction
│   ├── comparison.py           # PostgreSQL vs DuckDB comparison
│   └── olap_queries.py         # Pre-built SLICE/DICE/DRILL-DOWN queries
└── web/
    └── search_api.py           # REST API for web frontend
```

### Database Connection Management

**File**: `src/db/db_config.py`
```python
import psycopg2
import duckdb
import os

# PostgreSQL
PG_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'bmw_olap'),
    'user': os.getenv('DB_USER', 'bmw_user'),
    'password': os.getenv('DB_PASSWORD', 'bmw_password'),
}

# DuckDB
DUCKDB_PATH = os.getenv('DUCKDB_PATH', '/var/www/db/olap.duckdb')

class DatabaseManager:
    """Unified interface for both databases"""
    
    @staticmethod
    def get_postgresql():
        return psycopg2.connect(**PG_CONFIG)
    
    @staticmethod
    def get_duckdb():
        return duckdb.connect(DUCKDB_PATH)
```

### Web Application Integration

**Two Use Cases**:

1. **Search/Filtering** (www/search.php)
   - Uses DuckDB only (fast, in-process)
   - Dynamic filters via dropdowns (checkboxes for multi-select)
   - Real-time results update
   - No performance overhead

2. **Comparison** (www/compare.php)
   - Compares PostgreSQL vs DuckDB on same queries
   - Executes both 3 times (for averaging)
   - Shows timing + accuracy verification
   - Used for benchmarking and validation

---

## OLAP Query Framework

### Query Types (ODM Requirements)

Per [ODMpožadavky.txt](ODMpožadavky.txt):

**1. SLICE Queries** (1-dimensional filtering):
- Aktivní rok (e.g., 2017)
- Diesel v dekádě 2010s
- Premium benzín (cena > 30 000)

**2. DICE Queries** (multi-dimensional + ranking):
- Top 15 nejdražších kombinací (min. 5 prodejů)
- Top 10 nejlevnějších vozidel (min. 10 prodejů)
- Nejlepší poměr cena/MPG (od 2010+)

**3. DRILL-DOWN Queries** (hierarchická agregace):
- Model (1 úroveň)
- Model + Rok (2 úrovně)
- Model + Rok + Engine + Palivo (4 úrovně)

### Unified Query Builder Architecture

**File**: `src/olap/query_builder.py`

```python
from typing import List, Dict, Optional
from enum import Enum

class QueryType(Enum):
    SLICE = "slice"
    DICE = "dice"
    DRILLDOWN = "drill_down"

class OLAPQueryBuilder:
    """
    Dynamic SQL generator for Slice, Dice, and Drill-Down queries.
    Supports both PostgreSQL and DuckDB with identical SQL syntax.
    """
    
    def __init__(self, query_type: QueryType, db_engine: str = 'duckdb'):
        """
        Args:
            query_type: Type of query (SLICE, DICE, DRILLDOWN)
            db_engine: 'postgres' or 'duckdb'
        """
        self.query_type = query_type
        self.db_engine = db_engine
        self.filters = {}  # {dimension: [value_ids]}
        self.group_by = []  # Columns to aggregate by
        self.measures = ['COUNT(*) as count']  # Aggregations
        self.having = None  # Optional HAVING clause
        self.limit = None  # TOP N
        self.order_by = 'count DESC'
    
    def add_filter(self, dimension: str, values: List[int]):
        """
        Add dimension filter.
        
        Example:
            builder.add_filter('fuel_type_id', [1, 2])  # Diesel OR Petrol
            builder.add_filter('transmission_id', [1])  # Automatic only
        """
        self.filters[dimension] = values
    
    def add_aggregation(self, measure: str):
        """
        Add measure to SELECT clause.
        
        Example:
            builder.add_aggregation('AVG(fs.price) as avg_price')
            builder.add_aggregation('MIN(fs.price) as min_price')
        """
        self.measures.append(measure)
    
    def add_group_by(self, *columns):
        """
        Add grouping dimensions.
        
        Example:
            builder.add_group_by('dm.model_name')  # SLICE by model
            builder.add_group_by('dm.model_name', 'dt.production_year')  # DRILL-DOWN
        """
        self.group_by.extend(columns)
    
    def set_having(self, clause: str):
        """Set HAVING clause for result filtering."""
        self.having = clause
    
    def set_limit(self, n: int):
        """Limit result set to top N rows."""
        self.limit = n
    
    def set_order_by(self, clause: str):
        """Set ORDER BY clause."""
        self.order_by = clause
    
    def build(self) -> str:
        """
        Generate SQL query.
        
        Returns:
            Complete SQL string ready to execute.
        """
        
        # Base SELECT
        measures_str = ', '.join(self.measures)
        group_by_str = ', '.join(self.group_by) if self.group_by else '*'
        
        sql = f"SELECT {measures_str}, {group_by_str}\nFROM fact_sales fs\n"
        
        # Joins (based on filters + group_by)
        joins = self._build_joins()
        if joins:
            sql += joins + "\n"
        
        # WHERE clause (filters)
        where = self._build_where()
        if where:
            sql += f"WHERE {where}\n"
        
        # GROUP BY
        if self.group_by:
            sql += f"GROUP BY {group_by_str}\n"
        
        # HAVING
        if self.having:
            sql += f"HAVING {self.having}\n"
        
        # ORDER BY
        sql += f"ORDER BY {self.order_by}\n"
        
        # LIMIT
        if self.limit:
            sql += f"LIMIT {self.limit}"
        
        return sql
    
    def _build_joins(self) -> str:
        """Build JOIN clauses based on filters and group_by."""
        joins = []
        
        join_map = {
            'fuel_type_id': 'JOIN dim_fuel_type dft ON fs.fuel_type_id = dft.fuel_type_id',
            'transmission_id': 'JOIN dim_transmission dtr ON fs.transmission_id = dtr.transmission_id',
            'engine_id': 'JOIN dim_engine de ON fs.engine_id = de.engine_id',
            'model_id': 'JOIN dim_model dm ON fs.model_id = dm.model_id',
            'time_id': 'JOIN dim_time dt ON fs.time_id = dt.time_id',
        }
        
        # Add joins for filtered dimensions
        for dim, _ in self.filters.items():
            if dim in join_map:
                joins.append(join_map[dim])
        
        # Add joins for grouped dimensions
        group_by_str = ' '.join(self.group_by)
        for dim, join_clause in join_map.items():
            if dim in group_by_str and join_clause not in joins:
                joins.append(join_clause)
        
        return '\n'.join(joins)
    
    def _build_where(self) -> str:
        """Build WHERE clause from filters."""
        conditions = []
        
        where_map = {
            'fuel_type_id': 'dft.fuel_type_id IN ({})',
            'transmission_id': 'dtr.transmission_id IN ({})',
            'engine_id': 'de.engine_id IN ({})',
            'model_id': 'dm.model_id IN ({})',
            'time_id': 'dt.time_id IN ({})',
        }
        
        for dim, values in self.filters.items():
            if dim in where_map and values:
                values_str = ','.join(map(str, values))
                conditions.append(where_map[dim].format(values_str))
        
        return ' AND '.join(conditions)


# Pre-built Query Patterns

class SliceQueries:
    """Pre-built SLICE queries from ODMpožadavky.txt"""
    
    @staticmethod
    def year_2017(db_engine='duckdb'):
        builder = OLAPQueryBuilder(QueryType.SLICE, db_engine)
        builder.add_filter('time_id', [22])  # 2017 (adjust based on actual IDs)
        builder.add_group_by('dm.model_name')
        builder.add_aggregation('AVG(fs.price) as avg_price')
        builder.add_aggregation('COUNT(*) as sales_count')
        builder.set_order_by('avg_price DESC')
        return builder.build()
    
    @staticmethod
    def diesel_2010s(db_engine='duckdb'):
        builder = OLAPQueryBuilder(QueryType.SLICE, db_engine)
        builder.add_filter('fuel_type_id', [1])  # Diesel
        builder.add_group_by('dm.model_name', 'dt.decade')
        builder.add_aggregation('COUNT(*) as sales_count')
        builder.add_aggregation('AVG(fs.price) as avg_price')
        builder.set_order_by('avg_price DESC')
        return builder.build()
    
    @staticmethod
    def premium_petrol(db_engine='duckdb'):
        """Petrol vehicles price > 30,000"""
        builder = OLAPQueryBuilder(QueryType.SLICE, db_engine)
        builder.add_filter('fuel_type_id', [2])  # Petrol
        builder.add_group_by('dm.model_name')
        builder.add_aggregation('AVG(fs.price) as avg_price')
        builder.add_aggregation('COUNT(*) as sales_count')
        builder.set_having('AVG(fs.price) > 30000')
        builder.set_order_by('avg_price DESC')
        return builder.build()


class DiceQueries:
    """Pre-built DICE queries from ODMpožadavky.txt"""
    
    @staticmethod
    def top_15_expensive(db_engine='duckdb'):
        """Top 15 most expensive combinations (min 5 sales)"""
        builder = OLAPQueryBuilder(QueryType.DICE, db_engine)
        builder.add_group_by(
            'dm.model_name',
            'dft.fuel_type_name',
            'dtr.transmission_name',
            'de.engine_size'
        )
        builder.add_aggregation('AVG(fs.price) as avg_price')
        builder.add_aggregation('COUNT(*) as sales_count')
        builder.set_having('COUNT(*) >= 5')
        builder.set_limit(15)
        builder.set_order_by('avg_price DESC')
        return builder.build()
    
    @staticmethod
    def top_10_cheapest(db_engine='duckdb'):
        """Top 10 cheapest vehicles (min 10 sales)"""
        builder = OLAPQueryBuilder(QueryType.DICE, db_engine)
        builder.add_group_by('dm.model_name', 'dft.fuel_type_name')
        builder.add_aggregation('AVG(fs.price) as avg_price')
        builder.add_aggregation('COUNT(*) as sales_count')
        builder.set_having('COUNT(*) >= 10')
        builder.set_limit(10)
        builder.set_order_by('avg_price ASC')
        return builder.build()
    
    @staticmethod
    def best_price_mpg_ratio(db_engine='duckdb'):
        """Best price/MPG ratio (2010 onwards)"""
        builder = OLAPQueryBuilder(QueryType.DICE, db_engine)
        builder.add_group_by('dm.model_name', 'dft.fuel_type_name')
        builder.add_aggregation('AVG(fs.price) as avg_price')
        builder.add_aggregation('AVG(fs.mpg) as avg_mpg')
        builder.add_aggregation('(AVG(fs.price) / AVG(fs.mpg)) as ratio')
        builder.set_limit(20)
        builder.set_order_by('ratio ASC')
        return builder.build()


class DrillDownQueries:
    """Pre-built DRILL-DOWN queries from ODMpožadavky.txt"""
    
    @staticmethod
    def models_only(db_engine='duckdb'):
        """Level 1: Only models"""
        builder = OLAPQueryBuilder(QueryType.DRILLDOWN, db_engine)
        builder.add_group_by('dm.model_name')
        builder.add_aggregation('COUNT(*) as sales_count')
        builder.add_aggregation('AVG(fs.price) as avg_price')
        builder.set_order_by('sales_count DESC')
        return builder.build()
    
    @staticmethod
    def model_year(db_engine='duckdb'):
        """Level 2: Model + Year"""
        builder = OLAPQueryBuilder(QueryType.DRILLDOWN, db_engine)
        builder.add_group_by('dm.model_name', 'dt.production_year')
        builder.add_aggregation('COUNT(*) as sales_count')
        builder.add_aggregation('AVG(fs.price) as avg_price')
        builder.set_order_by('dm.model_name, dt.production_year DESC')
        return builder.build()
    
    @staticmethod
    def model_year_engine_fuel(db_engine='duckdb'):
        """Level 4: Model + Year + Engine + Fuel"""
        builder = OLAPQueryBuilder(QueryType.DRILLDOWN, db_engine)
        builder.add_group_by(
            'dm.model_name',
            'dt.production_year',
            'de.engine_size',
            'dft.fuel_type_name'
        )
        builder.add_aggregation('COUNT(*) as sales_count')
        builder.add_aggregation('AVG(fs.price) as avg_price')
        builder.set_order_by('dm.model_name, dt.production_year DESC')
        return builder.build()
```

---

## Docker Deployment

### Docker Compose Full Configuration

**File**: `docker-compose.yml`

```yaml
version: '3.9'

services:
  postgres:
    image: postgres:15-alpine
    container_name: bmw_postgres_db
    restart: unless-stopped
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: bmw_olap
      POSTGRES_USER: bmw_user
      POSTGRES_PASSWORD: bmw_password
      TZ: Europe/Prague
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/01-init.sql
      - ./docker/postgres/load_data.sql:/docker-entrypoint-initdb.d/02-load_data.sql
      - ./db:/tmp/db
      - ./depricated_or_tobeused/bmw.csv:/tmp/bmw.csv
    networks:
      - bmw_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U bmw_user -d bmw_olap"]
      interval: 10s
      timeout: 5s
      retries: 5

  php:
    image: php:8.1-apache
    container_name: bmw_php_app
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./www:/var/www/html
      - ./db:/var/www/db
      - ./src:/var/www/src
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: bmw_olap
      DB_USER: bmw_user
      DB_PASSWORD: bmw_password
      DUCKDB_PATH: /var/www/db/olap.duckdb
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - bmw_network

  python:
    image: python:3.11-slim
    container_name: bmw_python_worker
    restart: unless-stopped
    volumes:
      - ./src:/app/src
      - ./db:/app/db
    environment:
      DB_HOST: postgres
      DUCKDB_PATH: /app/db/olap.duckdb
    working_dir: /app
    command: python src/db/sync_duckdb.py
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - bmw_network

volumes:
  postgres_data:

networks:
  bmw_network:
    driver: bridge
```

### Building & Running

```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f postgres
docker-compose logs -f php
docker-compose logs -f python

# Access applications
# Web: http://localhost/search.php
# Compare: http://localhost/compare.php

# PostgreSQL CLI
docker exec -it bmw_postgres_db psql -U bmw_user -d bmw_olap

# Stop all
docker-compose down
```

### Deployment to Linux Server

**Option 1: Transfer volumes**
```bash
# On development PC
docker-compose down
tar -czf bmw_db_backup.tar.gz postgres_data/ db/

# On Linux server
tar -xzf bmw_db_backup.tar.gz
docker-compose up -d
```

**Option 2: Rebuild on server (cleaner)**
```bash
# Clone repository
git clone <repo>
cd OLAP-a-DM

# Start fresh
docker-compose up -d
# Database initializes automatically from init.sql + load_data.sql
```

