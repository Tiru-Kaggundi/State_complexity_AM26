"""
Combine state ECI with income and poverty into one table for plotting.

Inputs : data/processed/state_eci_am26.csv                 (scripts/compute_state_eci.py)
         data/reference/rbi/rbi_t19_nsdp_per_capita_current.csv
         data/reference/rbi/rbi_t10_mpi.csv               (scripts/fetch_rbi_handbook.py)
Output : data/processed/state_panel_am26.csv

Choices
  - Income: per capita Net State Domestic Product (NSDP), current prices, 2023-24
    (RBI Handbook Table 19). RBI does not publish GSDP per capita.
  - Gujarat has no 2023-24 figure (latest is 2022-23). It is extrapolated one year
    using its average annual growth over the previous five years
    (2017-18 to 2022-23, compound rate). Flagged in `nsdp_note`.
  - Poverty: MPI headcount ratio (%), NFHS-5 (2019-21), NITI Aayog National MPI
    2023, as reproduced in RBI Handbook Table 10.
  - `in_main_plot`: FY26 exports of at least US$ 1 billion.

Run from the repo root:  python scripts/build_state_panel.py
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
RBI = ROOT / "data" / "reference" / "rbi"

NSDP_YEAR = "2023-24"
GROWTH_FROM, GROWTH_TO = "2017-18", "2022-23"   # five years of growth
MPI_ROUND = "NFHS-5 (2019-21)"
MAIN_PLOT_MIN_EXPORT_USD = 1e9


def key(name: str) -> str:
    """Normalise state names so RBI and DGCI&S spellings match."""
    s = name.lower().replace("&", "and").replace("*", "")
    return re.sub(r"[^a-z]", "", s)


def nsdp_per_capita(states: pd.Series) -> pd.DataFrame:
    t = pd.read_csv(RBI / "rbi_t19_nsdp_per_capita_current.csv")
    t["k"] = t["state_rbi"].map(key)
    wide = t.pivot_table(index="k", columns="year", values="value")
    out = pd.DataFrame({"k": states.map(key)})
    out["nsdp_pc_inr"] = out["k"].map(wide[NSDP_YEAR])
    out["nsdp_year"] = np.where(out["nsdp_pc_inr"].notna(), NSDP_YEAR, None)
    out["nsdp_note"] = None

    # Extrapolate states missing NSDP_YEAR but with the growth window available
    for i, k in out.loc[out["nsdp_pc_inr"].isna(), "k"].items():
        if k not in wide.index:
            continue
        a, b = wide.at[k, GROWTH_FROM], wide.at[k, GROWTH_TO]
        if pd.notna(a) and pd.notna(b) and NSDP_YEAR > GROWTH_TO:
            g = (b / a) ** (1 / 5) - 1
            out.at[i, "nsdp_pc_inr"] = round(b * (1 + g))
            out.at[i, "nsdp_year"] = f"{NSDP_YEAR} (est.)"
            out.at[i, "nsdp_note"] = (
                f"{GROWTH_TO} value Rs {b:,.0f} grown one year at {g:.1%}, "
                f"its average annual growth {GROWTH_FROM} to {GROWTH_TO}"
            )
    return out.drop(columns="k")


def mpi_headcount(states: pd.Series) -> pd.Series:
    t = pd.read_csv(RBI / "rbi_t10_mpi.csv")
    t = t[(t["round"] == MPI_ROUND) & t["measure"].str.startswith("Headcount")]
    lookup = dict(zip(t["state_rbi"].map(key), t["value"]))
    return states.map(key).map(lookup)


def main() -> None:
    p = pd.read_csv(PROC / "state_eci_am26.csv")
    p = pd.concat([p, nsdp_per_capita(p["state"])], axis=1)
    p["mpi_hcr_pct"] = mpi_headcount(p["state"])
    p["in_main_plot"] = p["export_usd"] >= MAIN_PLOT_MIN_EXPORT_USD
    p.to_csv(PROC / "state_panel_am26.csv", index=False)

    print(p[["state", "export_usd", "eci", "nsdp_pc_inr", "nsdp_year", "mpi_hcr_pct", "in_main_plot"]]
          .to_string(index=False, float_format=lambda v: f"{v:,.3f}"))
    for _, r in p[p["nsdp_note"].notna()].iterrows():
        print(f"Note, {r.state}: {r.nsdp_note}")
    print("No NSDP:", ", ".join(p.loc[p.nsdp_pc_inr.isna(), "state"]) or "none")
    print("No MPI:", ", ".join(p.loc[p.mpi_hcr_pct.isna(), "state"]) or "none")


if __name__ == "__main__":
    main()
