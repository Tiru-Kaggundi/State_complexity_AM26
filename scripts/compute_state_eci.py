"""
State-level economic complexity (ECI) for FY26 at HS6.

Inputs : data/processed/state_hs6_exports_am26.csv   (scripts/clean_dgcis_am26.py)
         data/processed/pci_hs6.csv                  (scripts/compute_pci_hs6.py)
Output : data/processed/state_eci_am26.csv
         data/processed/state_products_rca_am26.csv  (state x product RCA, for inspection)

Steps
  1. Drop exports with no state of origin ("Unspecified").
  2. Map each HS6 code to a code that has a PCI (codes BACI merges, such as
     2710.12/2710.19, go to their heading's "xxxx00" code). The ~0.4% of export
     value with no PCI is dropped.
  3. Drop state x product rows below US$ 1,000 (noise; same rule as the AM25 run).
  4. RCA of each state against India's total (states are compared with each other).
  5. State ECI = mean world PCI of the products where the state has RCA >= 1
     (OEC's approach for sub-national regions). Every state and UT is kept,
     however few products it exports, so every reader can find their state;
     n_products_rca shows how many products each value rests on.
  6. eci_std = ECI standardised across states (mean 0, sd 1).

Run from the repo root:  python scripts/compute_state_eci.py
"""

from pathlib import Path

import pandas as pd

from complexity import align_hs6, binary_m, mean_pci_eci, rca_matrix

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
MIN_ROW_USD = 1_000


def main() -> None:
    st = pd.read_csv(PROC / "state_hs6_exports_am26.csv", dtype={"hs6": str, "hs4": str, "hs2": str})
    pci = pd.read_csv(PROC / "pci_hs6.csv", dtype={"hs6": str}).set_index("hs6")["pci"]

    st = st[st["type"] != "Unspecified"].copy()
    total_by_state = st.groupby(["state", "type"])["export_usd"].sum()

    st["pci_code"] = align_hs6(st["hs6"], set(pci.index))
    covered = st.dropna(subset=["pci_code"])
    coverage = covered.groupby("state")["export_usd"].sum() / total_by_state.droplevel("type")

    X = covered.groupby(["state", "pci_code"])["export_usd"].sum().astype(float)
    X = X[X >= MIN_ROW_USD].unstack(fill_value=0.0)

    rca = rca_matrix(X)
    M = binary_m(X)
    eci = mean_pci_eci(M, pci)

    out = (
        total_by_state.rename("export_usd").reset_index()
        .merge(eci, left_on="state", right_index=True, how="left")
    )
    out["n_products_exported"] = out["state"].map((X > 0).sum(axis=1)).fillna(0).astype(int)
    out["pci_coverage"] = out["state"].map(coverage).round(4)
    out["eci_std"] = (out["eci"] - out["eci"].mean()) / out["eci"].std(ddof=0)
    out = out.sort_values("eci", ascending=False)[
        ["state", "type", "export_usd", "n_products_exported", "n_products_rca",
         "eci", "eci_std", "pci_coverage"]
    ]
    out.to_csv(PROC / "state_eci_am26.csv", index=False)

    long = rca.stack().rename("rca").reset_index()
    long = long[long["rca"] > 0].rename(columns={"pci_code": "hs6"})
    long["pci"] = long["hs6"].map(pci)
    long["export_usd"] = [X.at[s, h] for s, h in zip(long["state"], long["hs6"])]
    long.round({"rca": 4, "pci": 4}).to_csv(PROC / "state_products_rca_am26.csv", index=False)

    print(f"States/UTs: {len(out)}; products used: {X.shape[1]:,}")
    show = out.assign(export_bn=(out["export_usd"] / 1e9).round(2))[
        ["state", "export_bn", "n_products_exported", "n_products_rca", "eci", "eci_std", "pci_coverage"]
    ]
    print(show.to_string(index=False, float_format=lambda v: f"{v:.3f}"))


if __name__ == "__main__":
    main()
