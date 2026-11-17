"""
Collapse CEPII BACI (HS 2022 codes) bilateral trade into exports by country x HS6 x year.

Input : data/external/baci/BACI_HS22_Y{year}_V202601.csv   (exporter x importer x product)
        data/external/baci/country_codes_V202601.csv
        Download: https://www.cepii.fr/DATA_DOWNLOAD/baci/data/BACI_HS22_V202601.zip
Output: data/processed/baci_hs22_exports_country_hs6.csv.gz
        columns: year, iso3, hs6, export_usd  (BACI reports thousand USD; converted to USD)

Uses DuckDB so the ~1 GB of CSVs never has to fit in memory.

Run from the repo root:  python scripts/aggregate_baci.py
"""

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
BACI = ROOT / "data" / "external" / "baci"
VERSION = "V202601"
YEARS = [2022, 2023, 2024]
OUT = ROOT / "data" / "processed" / "baci_hs22_exports_country_hs6.csv.gz"


def main() -> None:
    files = [BACI / f"BACI_HS22_Y{y}_{VERSION}.csv" for y in YEARS]
    missing = [f.name for f in files if not f.exists()]
    if missing:
        raise FileNotFoundError(f"Missing BACI files {missing}; unzip BACI_HS22_{VERSION}.zip into {BACI}")

    con = duckdb.connect()
    file_list = ", ".join(f"'{f}'" for f in files)
    con.execute(f"""
        CREATE TABLE flows AS
        SELECT t AS year, i, LPAD(CAST(k AS VARCHAR), 6, '0') AS hs6, v
        FROM read_csv([{file_list}], header = true,
                      columns = {{'t': 'INTEGER', 'i': 'INTEGER', 'j': 'INTEGER',
                                  'k': 'VARCHAR', 'v': 'DOUBLE', 'q': 'VARCHAR'}})
    """)
    con.execute(f"""
        CREATE TABLE countries AS
        SELECT * FROM read_csv('{BACI / f"country_codes_{VERSION}.csv"}', header = true)
    """)

    n_flows, world = con.execute("SELECT COUNT(*), SUM(v) / 1e6 FROM flows").fetchone()
    print(f"Bilateral flows: {n_flows:,}; world trade over {len(YEARS)} years: US$ {world:,.0f} bn")

    unmatched = con.execute("""
        SELECT COUNT(DISTINCT i) FROM flows f
        LEFT JOIN countries c ON f.i = c.country_code WHERE c.country_code IS NULL
    """).fetchone()[0]
    if unmatched:
        raise ValueError(f"{unmatched} exporter codes not in the country table")

    con.execute(f"""
        COPY (
            SELECT f.year, c.country_iso3 AS iso3, f.hs6, ROUND(SUM(f.v) * 1000) AS export_usd
            FROM flows f JOIN countries c ON f.i = c.country_code
            GROUP BY f.year, c.country_iso3, f.hs6
            ORDER BY f.year, iso3, f.hs6
        ) TO '{OUT}' (HEADER, COMPRESSION gzip)
    """)

    summary = con.execute(f"""
        SELECT year, COUNT(DISTINCT iso3), COUNT(DISTINCT hs6), SUM(export_usd) / 1e9, COUNT(*)
        FROM read_csv('{OUT}') GROUP BY year ORDER BY year
    """).fetchall()
    print(f"Wrote {OUT.relative_to(ROOT)}")
    for y, nc, np_, tot, rows in summary:
        print(f"  {y}: {nc} exporters, {np_:,} HS6 products, US$ {tot:,.0f} bn, {rows:,} rows")


if __name__ == "__main__":
    main()
