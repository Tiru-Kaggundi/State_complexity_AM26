"""
Download reference data from the OEC public API (no token needed).

Used to choose the country sample and to validate our own PCI/ECI:
  - PCI, HS6, HS 2022 codes, 2022-2024     -> benchmark for our HS6 PCI
  - ECI, HS6, HS 2022 codes, 2022-2024     -> benchmark for our country ECI, and
                                              the list of countries OEC keeps after
                                              its population/export filters
  - PCI, HS4, HS 2022 codes, 2022-2024     -> HS4 fallback / comparison

Output: data/reference/oec/*.csv

Run from the repo root:  python scripts/fetch_oec_reference.py
"""

import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "reference" / "oec"
API = "https://api-v2.oec.world/tesseract/data.jsonrecords"
PAGE = 10_000


def get_with_retry(params: dict, tries: int = 5) -> dict:
    """The OEC API sometimes returns 500s or times out; retry with backoff."""
    for attempt in range(1, tries + 1):
        try:
            r = requests.get(API, params=params, timeout=180)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            if attempt == tries:
                raise
            wait = 10 * attempt
            print(f"  {e.__class__.__name__}; retrying in {wait}s ({attempt}/{tries})")
            time.sleep(wait)


def fetch(params: dict) -> pd.DataFrame:
    rows, offset = [], 0
    while True:
        p = dict(params, limit=f"{PAGE},{offset}")
        js = get_with_retry(p)
        rows += js["data"]
        total = js["page"]["total"]
        offset += PAGE
        if offset >= total:
            break
    return pd.DataFrame(rows)


def iso3(country_id: pd.Series) -> pd.Series:
    # OEC country ids look like "asind" (continent + ISO3)
    return country_id.str[-3:].str.upper()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    pci6 = fetch({"cube": "complexity_pci_a_hs22_hs6", "drilldowns": "HS6 Official,Year", "measures": "PCI"})
    pci6 = pci6.rename(columns={"HS6 Official ID": "hs6", "HS6 Official": "description", "Year": "year", "PCI": "pci"})
    pci6["hs6"] = pci6["hs6"].astype(str).str.zfill(6)
    pci6[["hs6", "description", "year", "pci"]].to_csv(OUT / "oec_pci_hs22_hs6.csv", index=False)
    print(f"PCI HS6: {len(pci6):,} rows, years {sorted(pci6.year.unique())}")

    pci4 = fetch({"cube": "complexity_pci_a_hs22_hs4", "drilldowns": "HS4 Official,Year", "measures": "PCI"})
    pci4 = pci4.rename(columns={"HS4 Official ID": "hs4", "HS4 Official": "description", "Year": "year", "PCI": "pci"})
    pci4["hs4"] = pci4["hs4"].astype(str).str.zfill(4)
    pci4[["hs4", "description", "year", "pci"]].to_csv(OUT / "oec_pci_hs22_hs4.csv", index=False)
    print(f"PCI HS4: {len(pci4):,} rows")

    eci = fetch({"cube": "complexity_eci_a_hs22_hs6", "drilldowns": "Country Official,Year", "measures": "ECI"})
    eci = eci.rename(columns={"Country Official": "country", "Year": "year", "ECI": "eci"})
    eci["iso3"] = iso3(eci["Country Official ID"])
    eci[["iso3", "country", "year", "eci"]].to_csv(OUT / "oec_eci_hs22_hs6.csv", index=False)
    print(f"ECI HS6: {len(eci):,} rows")


if __name__ == "__main__":
    main()
