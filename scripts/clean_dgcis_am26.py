"""
Clean the DGCI&S state-of-origin export files for FY26 (AM26) into one tidy CSV.

Input : data/raw/dgcis_am26/*.xls   (7 parts, sheet "NewData", as downloaded)
Output: data/processed/state_hs6_exports_am26.csv   (one row per state x HS6)
        data/processed/state_totals_am26.csv        (one row per state, for quick checks)

Problems in the raw files that this script fixes:
  - Row 1 is a report title; row 2 is the header.
  - Column names carry trailing spaces ("Hs Code ", "State ").
  - HS codes can lose leading zeros if read as numbers -> read as text, zero-pad to 6.
  - State names are upper case and some differ from other datasets
    (e.g. "DADRA,NH,DAMAN,DIU") -> mapped via data/reference/state_names.csv.
  - Commodity descriptions have stray/double spaces -> whitespace collapsed.
    (They are also cut at ~60 characters by the portal; that cannot be fixed here.)
  - Values are rupees and US dollars as text -> converted to integers.
  - The portal also reports the last month (March 2026) in separate columns.
    Only the April 2025 to March 2026 totals are kept; the March columns are
    used for one sanity check and then dropped.

The script stops with an error if any validation check fails.

Run from the repo root:  python scripts/clean_dgcis_am26.py
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "dgcis_am26"
STATE_MAP = ROOT / "data" / "reference" / "state_names.csv"
OUT_DIR = ROOT / "data" / "processed"

FY = "2025-26"

# Raw header (after stripping spaces) -> clean column name
COLUMNS = {
    "Hs Code": "hs6",
    "State": "state_raw",
    "Commodity Description": "description",
    "April, 25 To March, 26 Value(US $)": "export_usd",
    "April, 25 To March, 26 Value(INR)": "export_inr",
    "March, 26 Value(US $)": "mar26_export_usd",
    "March, 26 Value(INR)": "mar26_export_inr",
}
VALUE_COLS = ["export_usd", "export_inr"]          # kept in the output (full year)
MARCH_COLS = ["mar26_export_usd", "mar26_export_inr"]  # read for a check, then dropped


def read_raw() -> pd.DataFrame:
    files = sorted(RAW_DIR.glob("*.xls"))
    if not files:
        raise FileNotFoundError(f"No .xls files in {RAW_DIR}")
    parts = []
    for f in files:
        title = pd.read_excel(f, engine="xlrd", header=None, nrows=1).iloc[0, 0]
        if "Apr-2025 To Mar-2026" not in str(title):
            raise ValueError(f"{f.name}: unexpected period in title: {title!r}")
        df = pd.read_excel(f, engine="xlrd", header=1, dtype=str)
        df.columns = [c.strip() for c in df.columns]
        missing = set(COLUMNS) - set(df.columns)
        if missing:
            raise ValueError(f"{f.name}: missing columns {missing}")
        df["source_file"] = f.name
        parts.append(df)
        print(f"  read {f.name}: {len(df):,} rows")
    return pd.concat(parts, ignore_index=True)


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.rename(columns=COLUMNS)[list(COLUMNS.values())].copy()

    df["hs6"] = df["hs6"].str.strip().str.zfill(6)
    df["hs4"] = df["hs6"].str[:4]
    df["hs2"] = df["hs6"].str[:2]

    df["state_raw"] = df["state_raw"].str.strip()
    names = pd.read_csv(STATE_MAP, dtype=str)
    unmapped = set(df["state_raw"]) - set(names["state_raw"])
    if unmapped:
        raise ValueError(f"States missing from {STATE_MAP.name}: {sorted(unmapped)}")
    df = df.merge(names, on="state_raw", how="left")

    df["description"] = (
        df["description"].fillna("").str.replace(r"\s+", " ", regex=True).str.strip()
    )

    for c in VALUE_COLS + MARCH_COLS:
        df[c] = pd.to_numeric(df[c].str.strip(), errors="raise").astype("int64")

    df.insert(0, "fy", FY)
    cols = ["fy", "state", "type", "state_raw", "hs2", "hs4", "hs6", "description"]
    return df[cols + VALUE_COLS + MARCH_COLS].sort_values(["state", "hs6"]).reset_index(drop=True)


def validate(raw: pd.DataFrame, df: pd.DataFrame) -> None:
    checks = {}
    checks["row count unchanged"] = len(df) == len(raw)
    checks["no duplicate state x hs6"] = not df.duplicated(["state", "hs6"]).any()
    checks["hs6 is 6 digits"] = df["hs6"].str.fullmatch(r"\d{6}").all()
    checks["no missing state"] = df["state"].notna().all()
    checks["no negative values"] = (df[VALUE_COLS + MARCH_COLS] >= 0).all().all()
    for raw_col, col in COLUMNS.items():
        if col in VALUE_COLS + MARCH_COLS:
            raw_total = pd.to_numeric(raw[raw_col].str.strip()).sum()
            checks[f"total {col} matches raw"] = raw_total == df[col].sum()
    # Confirms the full-year column is cumulative and already includes March
    checks["March <= full year (USD)"] = (df["mar26_export_usd"] <= df["export_usd"]).all()
    checks["full-year total above US$ 400 bn"] = df["export_usd"].sum() > 400e9

    print("\nValidation:")
    for name, ok in checks.items():
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if not all(checks.values()):
        raise SystemExit("Validation failed; nothing written.")


def main() -> None:
    print(f"Reading {RAW_DIR.relative_to(ROOT)}")
    raw = read_raw()
    df = clean(raw)
    validate(raw, df)
    march_usd = df["mar26_export_usd"].sum()
    df = df.drop(columns=MARCH_COLS)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "state_hs6_exports_am26.csv"
    df.to_csv(out, index=False)

    totals = (
        df.groupby(["state", "type"], as_index=False)
        .agg(
            export_usd=("export_usd", "sum"),
            export_inr=("export_inr", "sum"),
            n_hs6=("hs6", "nunique"),
            n_hs4=("hs4", "nunique"),
        )
        .sort_values("export_usd", ascending=False)
    )
    totals.to_csv(OUT_DIR / "state_totals_am26.csv", index=False)

    print(f"\nWrote {out.relative_to(ROOT)}: {len(df):,} rows")
    print(f"  states/UTs: {df['state'].nunique()}  HS6: {df['hs6'].nunique():,}  HS4: {df['hs4'].nunique():,}")
    print(f"  total exports: US$ {df['export_usd'].sum() / 1e9:,.1f} bn")
    print(f"  (March 2026 alone was US$ {march_usd / 1e9:,.1f} bn; dropped, already inside the full year)")
    print(f"  rows with zero US$ but positive INR: {((df.export_usd == 0) & (df.export_inr > 0)).sum()}")


if __name__ == "__main__":
    main()
