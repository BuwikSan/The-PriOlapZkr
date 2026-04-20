"""
OLAP Performance Comparison: PostgreSQL vs DuckDB
Porovnání výkonu stejných dotazů na dvou různých DBMS
"""

import time
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import duckdb
from typing import Literal, Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')


class OLAPComparison:
    """Třída pro porovnání výkonu OLAP dotazů"""

    def __init__(self, pg_host: str = "localhost", pg_port: int = 5432,
                 pg_db: str = "postgres", pg_user: str = "postgres",
                 pg_password: str = "Coconut12", duckdb_path: str = r"C:\Users\Administrator\DataGripProjects\RDBS databaze\identifier.db"):
        """
        Inicializace připojení na obě databáze

        Args:
            pg_host: PostgreSQL host
            pg_port: PostgreSQL port
            pg_db: PostgreSQL database
            pg_user: PostgreSQL user
            pg_password: PostgreSQL password
            duckdb_path: Cesta k DuckDB souboru
        """
        self.pg_conn = None
        self.duck_conn = None
        self.results = {}
        try:
            # PostgreSQL připojení
            self.pg_conn = psycopg2.connect(
                host=pg_host,
                port=pg_port,
                database=pg_db,
                user=pg_user,
                password=pg_password
            )
            print("✓ PostgreSQL připojeno")
        except Exception as e:
            print(f"✗ PostgreSQL chyba: {e}")

        try:
            # DuckDB připojení
            self.duck_conn = duckdb.connect(duckdb_path)
            print("✓ DuckDB připojeno")
        except Exception as e:
            print(f"✗ DuckDB chyba: {e}")

    def execute_pg(self, query: str, num_runs: int = 3) -> Tuple[pd.DataFrame, float]:
        """Spustí dotaz na PostgreSQL a změří čas"""
        if not self.pg_conn:
            return None, -1

        times = []
        df = None

        for _ in range(num_runs):
            start = time.time()
            try:
                df = pd.read_sql(query, self.pg_conn)
                elapsed = time.time() - start
                times.append(elapsed)
            except Exception as e:
                print(f"PostgreSQL error: {e}")
                return None, -1

        avg_time = sum(times) / len(times)
        return df, avg_time

    def execute_duck(self, query: str, num_runs: int = 3) -> Tuple[pd.DataFrame, float]:
        """Spustí dotaz na DuckDB a změří čas"""
        if not self.duck_conn:
            return None, -1

        times = []
        df = None

        for _ in range(num_runs):
            start = time.time()
            try:
                df = self.duck_conn.execute(query).df()
                elapsed = time.time() - start
                times.append(elapsed)
            except Exception as e:
                print(f"DuckDB error: {e}")
                return None, -1

        avg_time = sum(times) / len(times)
        return df, avg_time

    def compare_query(self, query_name: str, pg_query: str, duck_query: str,
                      num_runs: int = 3, verbose: bool = True) -> Dict:
        """
        Porovná výkon stejného dotazu na obou DBMS

        Args:
            query_name: Název dotazu
            pg_query: SQL dotaz pro PostgreSQL
            duck_query: SQL dotaz pro DuckDB
            num_runs: Kolik krát spustit dotaz (pro průměr)
            verbose: Tisknout výsledky

        Returns:
            Dict s výsledky a časy
        """
        print(f"\n{'='*70}")
        print(f"QUERY: {query_name}")
        print(f"{'='*70}")

        # PostgreSQL
        df_pg, time_pg = self.execute_pg(pg_query, num_runs)

        # DuckDB
        df_duck, time_duck = self.execute_duck(duck_query, num_runs)

        # Porovnání
        if df_pg is not None and df_duck is not None:
            # Normalizuj sloupce - PostgreSQL vrací camelCase, DuckDB lowercase
            df_pg_norm = df_pg.copy()
            df_duck_norm = df_duck.copy()

            # Přejmenuj DuckDB sloupce na stejné jméno jako PostgreSQL (case-insensitive match)
            pg_cols_lower = {col.lower(): col for col in df_pg_norm.columns}
            duck_rename = {col: pg_cols_lower.get(col.lower(), col) for col in df_duck_norm.columns}
            df_duck_norm = df_duck_norm.rename(columns=duck_rename)

            # Zaokrouhli numerické sloupce na 2 des. místa
            numeric_cols = df_pg_norm.select_dtypes(include=['float64', 'float32', 'int64', 'int32']).columns
            for col in numeric_cols:
                if col in df_pg_norm.columns:
                    df_pg_norm[col] = df_pg_norm[col].round(2)
                if col in df_duck_norm.columns:
                    df_duck_norm[col] = df_duck_norm[col].round(2)

            # Sortuj obě tabulky stejně aby byly v identickém pořadí
            # Sortujem podle všech sloupců
            all_cols = sorted(df_pg_norm.columns.tolist())
            df_pg_sorted = df_pg_norm.sort_values(by=all_cols, na_position='last').reset_index(drop=True)
            df_duck_sorted = df_duck_norm.sort_values(by=all_cols, na_position='last').reset_index(drop=True)

            # Teď porovnej
            are_equal = df_pg_sorted.equals(df_duck_sorted)
            speedup = time_pg / time_duck if time_duck > 0 else 0
        else:
            are_equal = False
            speedup = 0

        result = {
            'query_name': query_name,
            'pg_time_ms': time_pg * 1000,
            'duck_time_ms': time_duck * 1000,
            'speedup': speedup,
            'pg_rows': len(df_pg) if df_pg is not None else 0,
            'duck_rows': len(df_duck) if df_duck is not None else 0,
            'results_equal': are_equal,
            'pg_df': df_pg,
            'duck_df': df_duck
        }

        self.results[query_name] = result

        if verbose:
            print(f"PostgreSQL: {result['pg_time_ms']:.2f} ms ({result['pg_rows']} rows)")
            print(f"DuckDB:     {result['duck_time_ms']:.2f} ms ({result['duck_rows']} rows)")
            if speedup > 1:
                print(f"Speedup:    {speedup:.2f}x (DuckDB je {speedup:.2f}x RYCHLEJŠÍ)")
            elif speedup < 1:
                print(f"Speedup:    {1/speedup:.2f}x (PostgreSQL je {1/speedup:.2f}x RYCHLEJŠÍ)")
            else:
                print(f"Speedup:    1.00x (stejný čas)")
            print(f"Results Equal: {'✓ YES' if are_equal else '✗ NO'}")

        return result

    def close(self):
        """Zavře připojení"""
        if self.pg_conn:
            self.pg_conn.close()
        if self.duck_conn:
            self.duck_conn.close()


# ============================================================================
# SLICE QUERIES - Filtrování po jedné dimenzi
# ============================================================================

class SliceQueries:
    """SLICE operace - filtrování jedné dimenze"""

    @staticmethod
    def slice1_postgres() -> str:
        """SLICE 1: Ceny v roce 2017 (model × palivo)"""
        return """
        SELECT
            m.model,
            v.fuelType,
            COUNT(*) AS sales_count,
            ROUND(AVG(f.price)::numeric, 2) AS avg_price,
            MIN(f.price) AS min_price,
            MAX(f.price) AS max_price,
            ROUND(AVG(f.mpg)::numeric, 2) AS avg_mpg,
            ROUND(AVG(f.mileage)::numeric, 0) AS avg_mileage
        FROM Fact_Sales f
        JOIN Dim_Version v ON f.version_id = v.version_id
        JOIN Dim_Model m ON v.model_id = m.model_id
        JOIN Dim_Time t ON v.time_id = t.time_id
        WHERE t.year = 2017
        GROUP BY m.model, v.fuelType
        ORDER BY m.model, avg_price DESC
        """

    @staticmethod
    def slice1_duckdb() -> str:
        """SLICE 1: DuckDB verze"""
        return """
        SELECT
            m.model,
            v.fuelType,
            COUNT(*) AS sales_count,
            ROUND(AVG(f.price), 2) AS avg_price,
            MIN(f.price) AS min_price,
            MAX(f.price) AS max_price,
            ROUND(AVG(f.mpg), 2) AS avg_mpg,
            ROUND(AVG(f.mileage), 0) AS avg_mileage
        FROM Fact_Sales f
        JOIN Dim_Version v ON f.version_id = v.version_id
        JOIN Dim_Model m ON v.model_id = m.model_id
        JOIN Dim_Time t ON v.time_id = t.time_id
        WHERE t.year = 2017
        GROUP BY m.model, v.fuelType
        ORDER BY m.model, avg_price DESC
        """

    @staticmethod
    def slice2_postgres() -> str:
        """SLICE 2: Diesel v 2010s"""
        return """
        SELECT
            m.model,
            t.year,
            COUNT(*) AS sales_count,
            ROUND(AVG(f.price)::numeric, 2) AS avg_price,
            ROUND(AVG(f.mpg)::numeric, 2) AS avg_mpg,
            ROUND(AVG(f.tax)::numeric, 0) AS avg_tax
        FROM Fact_Sales f
        JOIN Dim_Version v ON f.version_id = v.version_id
        JOIN Dim_Model m ON v.model_id = m.model_id
        JOIN Dim_Time t ON v.time_id = t.time_id
        WHERE t.decade = 2010 AND v.fuelType = 'Diesel'
        GROUP BY m.model, t.year
        ORDER BY m.model, t.year DESC
        """

    @staticmethod
    def slice2_duckdb() -> str:
        """SLICE 2: DuckDB verze"""
        return """
        SELECT
            m.model,
            t.year,
            COUNT(*) AS sales_count,
            ROUND(AVG(f.price), 2) AS avg_price,
            ROUND(AVG(f.mpg), 2) AS avg_mpg,
            ROUND(AVG(f.tax), 0) AS avg_tax
        FROM Fact_Sales f
        JOIN Dim_Version v ON f.version_id = v.version_id
        JOIN Dim_Model m ON v.model_id = m.model_id
        JOIN Dim_Time t ON v.time_id = t.time_id
        WHERE t.decade = 2010 AND v.fuelType = 'Diesel'
        GROUP BY m.model, t.year
        ORDER BY m.model, t.year DESC
        """

    @staticmethod
    def slice3_postgres() -> str:
        """SLICE 3: Benzinová auta s vyšší cenou (premium segment)"""
        return """
        SELECT
            m.model,
            t.year,
            COUNT(*) AS sales_count,
            ROUND(AVG(f.price)::numeric, 2) AS avg_price,
            ROUND(AVG(f.mpg)::numeric, 2) AS avg_mpg
        FROM Fact_Sales f
        JOIN Dim_Version v ON f.version_id = v.version_id
        JOIN Dim_Model m ON v.model_id = m.model_id
        JOIN Dim_Time t ON v.time_id = t.time_id
        WHERE v.fuelType = 'Petrol' AND f.price > 30000
        GROUP BY m.model, t.year
        ORDER BY avg_price DESC
        """

    @staticmethod
    def slice3_duckdb() -> str:
        """SLICE 3: DuckDB verze"""
        return """
        SELECT
            m.model,
            t.year,
            COUNT(*) AS sales_count,
            ROUND(AVG(f.price), 2) AS avg_price,
            ROUND(AVG(f.mpg), 2) AS avg_mpg
        FROM Fact_Sales f
        JOIN Dim_Version v ON f.version_id = v.version_id
        JOIN Dim_Model m ON v.model_id = m.model_id
        JOIN Dim_Time t ON v.time_id = t.time_id
        WHERE v.fuelType = 'Petrol' AND f.price > 30000
        GROUP BY m.model, t.year
        ORDER BY avg_price DESC
        """


# ============================================================================
# DICE QUERIES - Filtrování více dimenzí + ranking
# ============================================================================

class DiceQueries:
    """DICE operace - komplexní filtrování + TOP ranking"""

    @staticmethod
    def dice1_postgres() -> str:
        """DICE 1: Top 15 nejdražších kombinací"""
        return """
        SELECT
            m.model,
            t.year,
            v.engineSize,
            v.fuelType,
            v.transmission,
            COUNT(*) AS sales_count,
            ROUND(AVG(f.price)::numeric, 2) AS avg_price,
            ROUND(AVG(f.mpg)::numeric, 2) AS avg_mpg
        FROM Fact_Sales f
        JOIN Dim_Version v ON f.version_id = v.version_id
        JOIN Dim_Model m ON v.model_id = m.model_id
        JOIN Dim_Time t ON v.time_id = t.time_id
        GROUP BY m.model, t.year, v.engineSize, v.fuelType, v.transmission
        HAVING COUNT(*) >= 5
        ORDER BY avg_price DESC
        LIMIT 15
        """

    @staticmethod
    def dice1_duckdb() -> str:
        """DICE 1: DuckDB verze"""
        return """
        SELECT
            m.model,
            t.year,
            v.engineSize,
            v.fuelType,
            v.transmission,
            COUNT(*) AS sales_count,
            ROUND(AVG(f.price), 2) AS avg_price,
            ROUND(AVG(f.mpg), 2) AS avg_mpg
        FROM Fact_Sales f
        JOIN Dim_Version v ON f.version_id = v.version_id
        JOIN Dim_Model m ON v.model_id = m.model_id
        JOIN Dim_Time t ON v.time_id = t.time_id
        GROUP BY m.model, t.year, v.engineSize, v.fuelType, v.transmission
        HAVING COUNT(*) >= 5
        ORDER BY avg_price DESC
        LIMIT 15
        """

    @staticmethod
    def dice2_postgres() -> str:
        """DICE 2: Top 10 nejlevnějších kombinací (prodejnost >= 10)"""
        return """
        SELECT
            m.model,
            t.year,
            v.engineSize,
            v.fuelType,
            v.transmission,
            COUNT(*) AS sales_count,
            ROUND(AVG(f.price)::numeric, 2) AS avg_price,
            MIN(f.price) AS min_price,
            MAX(f.price) AS max_price
        FROM Fact_Sales f
        JOIN Dim_Version v ON f.version_id = v.version_id
        JOIN Dim_Model m ON v.model_id = m.model_id
        JOIN Dim_Time t ON v.time_id = t.time_id
        GROUP BY m.model, t.year, v.engineSize, v.fuelType, v.transmission
        HAVING COUNT(*) >= 10
        ORDER BY avg_price ASC
        LIMIT 10
        """

    @staticmethod
    def dice2_duckdb() -> str:
        """DICE 2: DuckDB verze"""
        return """
        SELECT
            m.model,
            t.year,
            v.engineSize,
            v.fuelType,
            v.transmission,
            COUNT(*) AS sales_count,
            ROUND(AVG(f.price), 2) AS avg_price,
            MIN(f.price) AS min_price,
            MAX(f.price) AS max_price
        FROM Fact_Sales f
        JOIN Dim_Version v ON f.version_id = v.version_id
        JOIN Dim_Model m ON v.model_id = m.model_id
        JOIN Dim_Time t ON v.time_id = t.time_id
        GROUP BY m.model, t.year, v.engineSize, v.fuelType, v.transmission
        HAVING COUNT(*) >= 10
        ORDER BY avg_price ASC
        LIMIT 10
        """

    @staticmethod
    def dice3_postgres() -> str:
        """DICE 3: Model + Rok + Palivo - nejlepší poměr cena/MPG"""
        return """
        SELECT
            m.model,
            t.year,
            v.fuelType,
            COUNT(*) AS sales_count,
            ROUND(AVG(f.price)::numeric, 2) AS avg_price,
            ROUND(AVG(f.mpg)::numeric, 2) AS avg_mpg,
            ROUND((AVG(f.price) / NULLIF(AVG(f.mpg), 0))::numeric, 2) AS price_per_mpg
        FROM Fact_Sales f
        JOIN Dim_Version v ON f.version_id = v.version_id
        JOIN Dim_Model m ON v.model_id = m.model_id
        JOIN Dim_Time t ON v.time_id = t.time_id
        WHERE t.year >= 2010
        GROUP BY m.model, t.year, v.fuelType
        HAVING COUNT(*) >= 5
        ORDER BY price_per_mpg ASC
        LIMIT 20
        """

    @staticmethod
    def dice3_duckdb() -> str:
        """DICE 3: DuckDB verze"""
        return """
        SELECT
            m.model,
            t.year,
            v.fuelType,
            COUNT(*) AS sales_count,
            ROUND(AVG(f.price), 2) AS avg_price,
            ROUND(AVG(f.mpg), 2) AS avg_mpg,
            ROUND(AVG(f.price) / NULLIF(AVG(f.mpg), 0), 2) AS price_per_mpg
        FROM Fact_Sales f
        JOIN Dim_Version v ON f.version_id = v.version_id
        JOIN Dim_Model m ON v.model_id = m.model_id
        JOIN Dim_Time t ON v.time_id = t.time_id
        WHERE t.year >= 2010
        GROUP BY m.model, t.year, v.fuelType
        HAVING COUNT(*) >= 5
        ORDER BY price_per_mpg ASC
        LIMIT 20
        """


# ============================================================================
# DRILL-DOWN QUERIES - Hierarchická agregace na různých úrovních
# ============================================================================

class DrillDownQueries:
    """DRILL-DOWN operace - hierarchická agregace"""

    @staticmethod
    def drilldown1_postgres() -> str:
        """DRILL-DOWN 1: Jednoduchý - jen modely (1 úroveň agregace)"""
        return """
        SELECT
            'MODEL' AS level,
            m.model AS dimension,
            COUNT(*) AS sales_count,
            ROUND(AVG(f.price)::numeric, 2) AS avg_price,
            ROUND(AVG(f.mpg)::numeric, 2) AS avg_mpg
        FROM Fact_Sales f
        JOIN Dim_Version v ON f.version_id = v.version_id
        JOIN Dim_Model m ON v.model_id = m.model_id
        GROUP BY m.model
        ORDER BY avg_price DESC
        """

    @staticmethod
    def drilldown1_duckdb() -> str:
        """DRILL-DOWN 1: DuckDB verze"""
        return """
        SELECT
            'MODEL' AS level,
            m.model AS dimension,
            COUNT(*) AS sales_count,
            ROUND(AVG(f.price), 2) AS avg_price,
            ROUND(AVG(f.mpg), 2) AS avg_mpg
        FROM Fact_Sales f
        JOIN Dim_Version v ON f.version_id = v.version_id
        JOIN Dim_Model m ON v.model_id = m.model_id
        GROUP BY m.model
        ORDER BY avg_price DESC
        """

    @staticmethod
    def drilldown2_postgres() -> str:
        """DRILL-DOWN 2: Středně složitý - model + rok (2 úrovně)"""
        return """
        SELECT
            m.model,
            t.year,
            COUNT(*) AS sales_count,
            ROUND(AVG(f.price)::numeric, 2) AS avg_price,
            MIN(f.price) AS min_price,
            MAX(f.price) AS max_price,
            ROUND(AVG(f.mpg)::numeric, 2) AS avg_mpg
        FROM Fact_Sales f
        JOIN Dim_Version v ON f.version_id = v.version_id
        JOIN Dim_Model m ON v.model_id = m.model_id
        JOIN Dim_Time t ON v.time_id = t.time_id
        GROUP BY m.model, t.year
        ORDER BY m.model, t.year DESC
        """

    @staticmethod
    def drilldown2_duckdb() -> str:
        """DRILL-DOWN 2: DuckDB verze"""
        return """
        SELECT
            m.model,
            t.year,
            COUNT(*) AS sales_count,
            ROUND(AVG(f.price), 2) AS avg_price,
            MIN(f.price) AS min_price,
            MAX(f.price) AS max_price,
            ROUND(AVG(f.mpg), 2) AS avg_mpg
        FROM Fact_Sales f
        JOIN Dim_Version v ON f.version_id = v.version_id
        JOIN Dim_Model m ON v.model_id = m.model_id
        JOIN Dim_Time t ON v.time_id = t.time_id
        GROUP BY m.model, t.year
        ORDER BY m.model, t.year DESC
        """

    @staticmethod
    def drilldown3_postgres() -> str:
        """DRILL-DOWN 3: Složitý - model + rok + engine + palivo (4 úrovně)"""
        return """
        SELECT
            m.model,
            t.year,
            v.engineSize,
            v.fuelType,
            COUNT(*) AS sales_count,
            ROUND(AVG(f.price)::numeric, 2) AS avg_price,
            ROUND(AVG(f.mpg)::numeric, 2) AS avg_mpg,
            ROUND(AVG(f.tax)::numeric, 0) AS avg_tax
        FROM Fact_Sales f
        JOIN Dim_Version v ON f.version_id = v.version_id
        JOIN Dim_Model m ON v.model_id = m.model_id
        JOIN Dim_Time t ON v.time_id = t.time_id
        GROUP BY m.model, t.year, v.engineSize, v.fuelType
        ORDER BY m.model, t.year DESC, v.engineSize
        """

    @staticmethod
    def drilldown3_duckdb() -> str:
        """DRILL-DOWN 3: DuckDB verze"""
        return """
        SELECT
            m.model,
            t.year,
            v.engineSize,
            v.fuelType,
            COUNT(*) AS sales_count,
            ROUND(AVG(f.price), 2) AS avg_price,
            ROUND(AVG(f.mpg), 2) AS avg_mpg,
            ROUND(AVG(f.tax), 0) AS avg_tax
        FROM Fact_Sales f
        JOIN Dim_Version v ON f.version_id = v.version_id
        JOIN Dim_Model m ON v.model_id = m.model_id
        JOIN Dim_Time t ON v.time_id = t.time_id
        GROUP BY m.model, t.year, v.engineSize, v.fuelType
        ORDER BY m.model, t.year DESC, v.engineSize
        """


def main():
    """Testovací běh - všechny připravené queries"""
    # Inicializace
    comp = OLAPComparison(
        pg_host="localhost",
        pg_port=5432,
        pg_db="postgres",
        pg_user="postgres",
        pg_password="Coconut12",
        duckdb_path=r"C:\Users\Administrator\DataGripProjects\RDBS databaze\identifier.db"
    )

    # ========== SLICE QUERIES ==========
    print("\n" + "="*70)
    print("SLICE QUERIES - Filtrování jedné dimenze")
    print("="*70)

    comp.compare_query(
        "SLICE 1: Rok 2017",
        SliceQueries.slice1_postgres(),
        SliceQueries.slice1_duckdb()
    )

    comp.compare_query(
        "SLICE 2: Diesel v 2010s",
        SliceQueries.slice2_postgres(),
        SliceQueries.slice2_duckdb()
    )

    comp.compare_query(
        "SLICE 3: Benzín premium (cena > 30k)",
        SliceQueries.slice3_postgres(),
        SliceQueries.slice3_duckdb()
    )

    # ========== DICE QUERIES ==========
    print("\n" + "="*70)
    print("DICE QUERIES - Komplexní filtrování + TOP ranking")
    print("="*70)

    comp.compare_query(
        "DICE 1: Top 15 nejdražších kombinací (HAVING >= 5)",
        DiceQueries.dice1_postgres(),
        DiceQueries.dice1_duckdb()
    )

    comp.compare_query(
        "DICE 2: Top 10 nejlevnějších (HAVING >= 10)",
        DiceQueries.dice2_postgres(),
        DiceQueries.dice2_duckdb()
    )

    comp.compare_query(
        "DICE 3: Nejlepší poměr cena/MPG (2010+)",
        DiceQueries.dice3_postgres(),
        DiceQueries.dice3_duckdb()
    )

    # ========== DRILL-DOWN QUERIES ==========
    print("\n" + "="*70)
    print("DRILL-DOWN QUERIES - Hierarchická agregace")
    print("="*70)

    comp.compare_query(
        "DRILL-DOWN 1: Modely (1 úroveň)",
        DrillDownQueries.drilldown1_postgres(),
        DrillDownQueries.drilldown1_duckdb()
    )

    comp.compare_query(
        "DRILL-DOWN 2: Model + Rok (2 úrovně)",
        DrillDownQueries.drilldown2_postgres(),
        DrillDownQueries.drilldown2_duckdb()
    )

    comp.compare_query(
        "DRILL-DOWN 3: Model + Rok + Engine + Palivo (4 úrovně)",
        DrillDownQueries.drilldown3_postgres(),
        DrillDownQueries.drilldown3_duckdb()
    )

    # ========== SUMMARY ==========
    print("\n" + "="*110)
    print("SOUHRN VŠECH VÝSLEDKŮ (9 queries)")
    print("="*110)

    summary_data = []
    for v in comp.results.values():
        summary_data.append({
            'Query': v['query_name'],
            'PostgreSQL (ms)': v['pg_time_ms'],
            'DuckDB (ms)': v['duck_time_ms'],
            'Speedup': v['speedup'],
            'Equal': '✓' if v['results_equal'] else '✗'
        })

    # Custom tisk tabulky
    print(f"{'Query':<50} {'PostgreSQL':<15} {'DuckDB':<15} {'Speedup':<10} {'Equal':<8}")
    print("-"*110)
    for item in summary_data:
        query_name = item['Query'][:49]
        print(f"{query_name:<50} {item['PostgreSQL (ms)']:>10.2f} ms  {item['DuckDB (ms)']:>10.2f} ms  {item['Speedup']:>8.2f}x  {item['Equal']:>6}")

    # Statistika
    print("\n" + "="*110)
    print("STATISTIKA VÝKONU")
    print("="*110)

    speedups = []
    for v in comp.results.values():
        if v['speedup'] > 0:
            speedups.append(v['speedup'])

    if speedups:
        print(f"Průměrné zrychlení DuckDB: {sum(speedups) / len(speedups):.2f}x")
        print(f"Nejrychlejší query: {max(speedups):.2f}x")
        print(f"Nejpomalejší query: {min(speedups):.2f}x")
        print(f"Počet queries: {len(speedups)}")

    comp.close()


# ============================================================================
# PARAMETRIZOVANÉ QUERIES - CUSTOMIZABLE VSTUPNÍ PARAMETRY
# ============================================================================

class ParameterizedSliceQueries:
    """SLICE operace s úplnou kontrolou nad parametry"""

    @staticmethod
    def slice_postgres(dimensions: List[str], filters: Dict[str, any]) -> str:
        """
        SLICE query - libovolný počet dimenzí (1-5) s custom filtry

        Args:
            dimensions: Seznam dimenzí k agregaci (model, year, engineSize, fuelType, transmission)
            filters: Dict s WHERE podmínkami (key=sloupec, value=hodnota)

        Returns:
            SQL query string
        """
        # Validace
        valid_dims = {'model', 'year', 'decade', 'engineSize', 'fuelType', 'transmission'}
        for d in dimensions:
            if d not in valid_dims:
                raise ValueError(f"Neznámá dimenze: {d}")

        # Mapování dimenzí na tabulky
        select_cols = []
        join_tables = set()

        for dim in dimensions:
            if dim in ['model']:
                select_cols.append('m.model')
                join_tables.add('Dim_Model')
            elif dim in ['year', 'decade']:
                select_cols.append(f't.{dim}')
                join_tables.add('Dim_Time')
            elif dim in ['engineSize', 'fuelType', 'transmission']:
                select_cols.append(f'v.{dim}')
                join_tables.add('Dim_Version')

        # Base SELECT
        select_part = ', '.join(select_cols) + ', COUNT(*) AS sales_count, ROUND(AVG(f.price)::numeric, 2) AS avg_price, ROUND(AVG(f.mpg)::numeric, 2) AS avg_mpg'

        # FROM a JOINs
        from_part = "FROM Fact_Sales f JOIN Dim_Version v ON f.version_id = v.version_id"
        if 'Dim_Model' in join_tables:
            from_part += " JOIN Dim_Model m ON v.model_id = m.model_id"
        if 'Dim_Time' in join_tables:
            from_part += " JOIN Dim_Time t ON v.time_id = t.time_id"

        # WHERE clauses
        where_clauses = []
        for key, value in filters.items():
            if isinstance(value, str):
                where_clauses.append(f"{key} = '{value}'")
            else:
                where_clauses.append(f"{key} = {value}")

        where_part = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        # GROUP BY
        group_part = " GROUP BY " + ", ".join(select_cols)

        return f"SELECT {select_part} {from_part}{where_part}{group_part} ORDER BY avg_price DESC"

    @staticmethod
    def slice_duckdb(dimensions: List[str], filters: Dict[str, any]) -> str:
        """SLICE query pro DuckDB - stejná logika jako PostgreSQL verze"""
        valid_dims = {'model', 'year', 'decade', 'engineSize', 'fuelType', 'transmission'}
        for d in dimensions:
            if d not in valid_dims:
                raise ValueError(f"Neznámá dimenze: {d}")

        # Mapování dimenzí na tabulky
        select_cols = []
        join_tables = set()

        for dim in dimensions:
            if dim in ['model']:
                select_cols.append('m.model')
                join_tables.add('Dim_Model')
            elif dim in ['year', 'decade']:
                select_cols.append(f't.{dim}')
                join_tables.add('Dim_Time')
            elif dim in ['engineSize', 'fuelType', 'transmission']:
                select_cols.append(f'v.{dim}')
                join_tables.add('Dim_Version')

        # Base SELECT
        select_part = ', '.join(select_cols) + ', COUNT(*) AS sales_count, ROUND(AVG(f.price), 2) AS avg_price, ROUND(AVG(f.mpg), 2) AS avg_mpg'

        # FROM a JOINs
        from_part = "FROM Fact_Sales f JOIN Dim_Version v ON f.version_id = v.version_id"
        if 'Dim_Model' in join_tables:
            from_part += " JOIN Dim_Model m ON v.model_id = m.model_id"
        if 'Dim_Time' in join_tables:
            from_part += " JOIN Dim_Time t ON v.time_id = t.time_id"

        # WHERE clauses
        where_clauses = []
        for key, value in filters.items():
            if isinstance(value, str):
                where_clauses.append(f"{key} = '{value}'")
            else:
                where_clauses.append(f"{key} = {value}")

        where_part = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        # GROUP BY
        group_part = " GROUP BY " + ", ".join(select_cols)

        return f"SELECT {select_part} {from_part}{where_part}{group_part} ORDER BY avg_price DESC"


class ParameterizedDiceQueries:
    """DICE operace s úplnou kontrolou nad parametry"""

    @staticmethod
    def dice_postgres(dimensions: List[str], having_count: int = 5,
                     top_n: int = 15, order_by: str = "avg_price DESC",
                     filters: Dict[str, any] = None) -> str:
        """
        DICE query - multi-dimenzionální ranking

        Args:
            dimensions: Seznam dimenzí k agregaci
            having_count: Minimální počet prodejů (HAVING COUNT >= X)
            top_n: Kolik řádků vrátit (LIMIT)
            order_by: ORDER BY klauzule
            filters: WHERE podmínky (optional)

        Returns:
            SQL query string
        """
        valid_dims = {'model', 'year', 'engineSize', 'fuelType', 'transmission'}
        for d in dimensions:
            if d not in valid_dims:
                raise ValueError(f"Neznámá dimenze: {d}")

        # Mapování dimenzí
        select_cols = []
        join_tables = set()

        for dim in dimensions:
            if dim == 'model':
                select_cols.append('m.model')
                join_tables.add('Dim_Model')
            elif dim == 'year':
                select_cols.append('t.year')
                join_tables.add('Dim_Time')
            elif dim in ['engineSize', 'fuelType', 'transmission']:
                select_cols.append(f'v.{dim}')
                join_tables.add('Dim_Version')

        # Base SELECT
        select_part = ', '.join(select_cols) + ', COUNT(*) AS sales_count, ROUND(AVG(f.price)::numeric, 2) AS avg_price'

        # FROM a JOINs
        from_part = "FROM Fact_Sales f JOIN Dim_Version v ON f.version_id = v.version_id"
        if 'Dim_Model' in join_tables:
            from_part += " JOIN Dim_Model m ON v.model_id = m.model_id"
        if 'Dim_Time' in join_tables:
            from_part += " JOIN Dim_Time t ON v.time_id = t.time_id"

        # WHERE clauses
        where_part = ""
        if filters:
            where_clauses = []
            for key, value in filters.items():
                if isinstance(value, str):
                    where_clauses.append(f"{key} = '{value}'")
                else:
                    where_clauses.append(f"{key} = {value}")
            where_part = " WHERE " + " AND ".join(where_clauses)

        # GROUP BY
        group_part = " GROUP BY " + ", ".join(select_cols)

        # HAVING
        having_part = f" HAVING COUNT(*) >= {having_count}"

        # ORDER BY + LIMIT
        order_limit = f" ORDER BY {order_by} LIMIT {top_n}"

        return f"SELECT {select_part} {from_part}{where_part}{group_part}{having_part}{order_limit}"

    @staticmethod
    def dice_duckdb(dimensions: List[str], having_count: int = 5,
                   top_n: int = 15, order_by: str = "avg_price DESC",
                   filters: Dict[str, any] = None) -> str:
        """DICE query pro DuckDB - stejná logika"""
        valid_dims = {'model', 'year', 'engineSize', 'fuelType', 'transmission'}
        for d in dimensions:
            if d not in valid_dims:
                raise ValueError(f"Neznámá dimenze: {d}")

        # Mapování dimenzí
        select_cols = []
        join_tables = set()

        for dim in dimensions:
            if dim == 'model':
                select_cols.append('m.model')
                join_tables.add('Dim_Model')
            elif dim == 'year':
                select_cols.append('t.year')
                join_tables.add('Dim_Time')
            elif dim in ['engineSize', 'fuelType', 'transmission']:
                select_cols.append(f'v.{dim}')
                join_tables.add('Dim_Version')

        # Base SELECT
        select_part = ', '.join(select_cols) + ', COUNT(*) AS sales_count, ROUND(AVG(f.price), 2) AS avg_price'

        # FROM a JOINs
        from_part = "FROM Fact_Sales f JOIN Dim_Version v ON f.version_id = v.version_id"
        if 'Dim_Model' in join_tables:
            from_part += " JOIN Dim_Model m ON v.model_id = m.model_id"
        if 'Dim_Time' in join_tables:
            from_part += " JOIN Dim_Time t ON v.time_id = t.time_id"

        # WHERE clauses
        where_part = ""
        if filters:
            where_clauses = []
            for key, value in filters.items():
                if isinstance(value, str):
                    where_clauses.append(f"{key} = '{value}'")
                else:
                    where_clauses.append(f"{key} = {value}")
            where_part = " WHERE " + " AND ".join(where_clauses)

        # GROUP BY
        group_part = " GROUP BY " + ", ".join(select_cols)

        # HAVING
        having_part = f" HAVING COUNT(*) >= {having_count}"

        # ORDER BY + LIMIT
        order_limit = f" ORDER BY {order_by} LIMIT {top_n}"

        return f"SELECT {select_part} {from_part}{where_part}{group_part}{having_part}{order_limit}"


class ParameterizedDrillDownQueries:
    """DRILL-DOWN operace s úplnou kontrolou nad parametry"""

    @staticmethod
    def drilldown_postgres(dimensions: List[str],
                          top_n: int = None,
                          filters: Dict[str, any] = None) -> str:
        """
        DRILL-DOWN query - hierarchická agregace s libovolným počtem úrovní

        Args:
            dimensions: Seznam dimenzí v pořadí agregace (model -> year -> engineSize -> ...)
            top_n: Kolik řádků vrátit (LIMIT, optional)
            filters: WHERE podmínky (optional)

        Returns:
            SQL query string
        """
        valid_dims = {'model', 'year', 'engineSize', 'fuelType', 'transmission', 'decade'}
        for d in dimensions:
            if d not in valid_dims:
                raise ValueError(f"Neznámá dimenze: {d}")

        if not dimensions:
            raise ValueError("Musíš zadat alespoň jednu dimenzi")

        # Mapování dimenzí
        select_cols = []
        join_tables = set()

        for dim in dimensions:
            if dim == 'model':
                select_cols.append('m.model')
                join_tables.add('Dim_Model')
            elif dim in ['year', 'decade']:
                select_cols.append(f't.{dim}')
                join_tables.add('Dim_Time')
            elif dim in ['engineSize', 'fuelType', 'transmission']:
                select_cols.append(f'v.{dim}')
                join_tables.add('Dim_Version')

        # Base SELECT
        select_part = ', '.join(select_cols) + ', COUNT(*) AS sales_count, ROUND(AVG(f.price)::numeric, 2) AS avg_price, ROUND(AVG(f.mpg)::numeric, 2) AS avg_mpg'

        # FROM a JOINs
        from_part = "FROM Fact_Sales f JOIN Dim_Version v ON f.version_id = v.version_id"
        if 'Dim_Model' in join_tables:
            from_part += " JOIN Dim_Model m ON v.model_id = m.model_id"
        if 'Dim_Time' in join_tables:
            from_part += " JOIN Dim_Time t ON v.time_id = t.time_id"

        # WHERE clauses
        where_part = ""
        if filters:
            where_clauses = []
            for key, value in filters.items():
                if isinstance(value, str):
                    where_clauses.append(f"{key} = '{value}'")
                else:
                    where_clauses.append(f"{key} = {value}")
            where_part = " WHERE " + " AND ".join(where_clauses)

        # GROUP BY
        group_part = " GROUP BY " + ", ".join(select_cols)

        # ORDER BY
        order_part = " ORDER BY " + ", ".join(select_cols)

        # LIMIT (optional)
        limit_part = f" LIMIT {top_n}" if top_n else ""

        return f"SELECT {select_part} {from_part}{where_part}{group_part}{order_part}{limit_part}"

    @staticmethod
    def drilldown_duckdb(dimensions: List[str],
                        top_n: int = None,
                        filters: Dict[str, any] = None) -> str:
        """DRILL-DOWN query pro DuckDB - stejná logika"""
        valid_dims = {'model', 'year', 'engineSize', 'fuelType', 'transmission', 'decade'}
        for d in dimensions:
            if d not in valid_dims:
                raise ValueError(f"Neznámá dimenze: {d}")

        if not dimensions:
            raise ValueError("Musíš zadat alespoň jednu dimenzi")

        # Mapování dimenzí
        select_cols = []
        join_tables = set()

        for dim in dimensions:
            if dim == 'model':
                select_cols.append('m.model')
                join_tables.add('Dim_Model')
            elif dim in ['year', 'decade']:
                select_cols.append(f't.{dim}')
                join_tables.add('Dim_Time')
            elif dim in ['engineSize', 'fuelType', 'transmission']:
                select_cols.append(f'v.{dim}')
                join_tables.add('Dim_Version')

        # Base SELECT
        select_part = ', '.join(select_cols) + ', COUNT(*) AS sales_count, ROUND(AVG(f.price), 2) AS avg_price, ROUND(AVG(f.mpg), 2) AS avg_mpg'

        # FROM a JOINs
        from_part = "FROM Fact_Sales f JOIN Dim_Version v ON f.version_id = v.version_id"
        if 'Dim_Model' in join_tables:
            from_part += " JOIN Dim_Model m ON v.model_id = m.model_id"
        if 'Dim_Time' in join_tables:
            from_part += " JOIN Dim_Time t ON v.time_id = t.time_id"

        # WHERE clauses
        where_part = ""
        if filters:
            where_clauses = []
            for key, value in filters.items():
                if isinstance(value, str):
                    where_clauses.append(f"{key} = '{value}'")
                else:
                    where_clauses.append(f"{key} = {value}")
            where_part = " WHERE " + " AND ".join(where_clauses)

        # GROUP BY
        group_part = " GROUP BY " + ", ".join(select_cols)

        # ORDER BY
        order_part = " ORDER BY " + ", ".join(select_cols)

        # LIMIT (optional)
        limit_part = f" LIMIT {top_n}" if top_n else ""

        return f"SELECT {select_part} {from_part}{where_part}{group_part}{order_part}{limit_part}"


if __name__ == "__main__":
    main()
