"""
Download state tables from the RBI Handbook of Statistics on Indian States
(2024-25 edition, released December 2025).

  Table 10: State-wise Poverty Estimates - Multi-dimensional Poverty Index
            (NITI Aayog National MPI 2023; NFHS-4 2015-16 and NFHS-5 2019-21)
  Table 19: Per Capita Net State Domestic Product, current prices (Rs)
  Table 21: Gross State Domestic Product, current prices (Rs lakh)

RBI's Excel links sit behind a bot check, but each table page also carries
the table as HTML, which is what this script reads.
Page list: https://rbi.org.in/Scripts/AnnualPublications.aspx?head=Handbook+of+Statistics+on+Indian+States

Output: data/reference/rbi/*.csv (long format: state, year/round, value)

Run from the repo root:  python scripts/fetch_rbi_handbook.py
"""

import io
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "reference" / "rbi"
PAGE = "https://rbi.org.in/Scripts/PublicationsView.aspx?id={}"
TABLES = {
    "mpi": 23459,               # Table 10
    "nsdp_per_capita": 23468,   # Table 19
    "gsdp": 23470,              # Table 21
}


def get(url: str, tries: int = 4) -> str:
    for attempt in range(1, tries + 1):
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=90)
            r.raise_for_status()
            return r.text
        except requests.RequestException:
            if attempt == tries:
                raise
            time.sleep(5 * attempt)


def year_tables(html: str) -> pd.DataFrame:
    """Tables 19/21 are split into two HTML tables by year range; stitch them."""
    parts = []
    for t in pd.read_html(io.StringIO(html)):
        if t.shape[0] < 30:
            continue
        hdr = t.index[t.iloc[:, 0].astype(str).str.contains("State/Union Territory")][-1]
        years = t.iloc[hdr, 1:].astype(str).tolist()
        body = t.iloc[hdr + 1:].copy()
        body = body[~body.iloc[:, 0].astype(str).str.contains("Not Available|Source|Note", case=False)]
        body.columns = ["state_rbi"] + years
        parts.append(body.melt(id_vars="state_rbi", var_name="year", value_name="value"))
    df = pd.concat(parts, ignore_index=True)
    df["value"] = pd.to_numeric(df["value"].astype(str).str.replace(",", ""), errors="coerce")
    return df.drop_duplicates(["state_rbi", "year"])


def mpi_table(html: str) -> pd.DataFrame:
    t = max(pd.read_html(io.StringIO(html)), key=len)
    rounds, measures = t.iloc[0, 1:].tolist(), t.iloc[1, 1:].tolist()
    body = t.iloc[2:].copy()
    body = body[~body.iloc[:, 0].astype(str).str.startswith("NFHS:")]
    body.columns = ["state_rbi"] + [f"{r}|{m}" for r, m in zip(rounds, measures)]
    long = body.melt(id_vars="state_rbi", var_name="key", value_name="value")
    long[["round", "measure"]] = long["key"].str.split("|", expand=True)
    long["measure"] = long["measure"].str.replace(r"\s+", " ", regex=True).str.strip()
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    return long[["state_rbi", "round", "measure", "value"]]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    mpi = mpi_table(get(PAGE.format(TABLES["mpi"])))
    mpi.to_csv(OUT / "rbi_t10_mpi.csv", index=False)
    print(f"MPI: {mpi.state_rbi.nunique()} states/UTs, rounds {sorted(mpi['round'].unique())}")
    for name, file in [("nsdp_per_capita", "rbi_t19_nsdp_per_capita_current.csv"),
                       ("gsdp", "rbi_t21_gsdp_current.csv")]:
        df = year_tables(get(PAGE.format(TABLES[name])))
        df.to_csv(OUT / file, index=False)
        print(f"{name}: {df.state_rbi.nunique()} states/UTs, years {df.year.min()} to {df.year.max()}")


if __name__ == "__main__":
    main()
