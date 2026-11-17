"""
Compute product complexity (PCI) at HS6 from world trade (BACI, HS 2022 codes),
and validate it against OEC's published HS6 PCI/ECI.

Inputs : data/processed/baci_hs22_exports_country_hs6.csv.gz   (scripts/aggregate_baci.py)
         data/reference/oec/*.csv                             (scripts/fetch_oec_reference.py)
         data/external/baci/product_codes_HS22_V202601.csv     (product descriptions)
Outputs: data/processed/pci_hs6.csv              main PCI used for the states
         data/processed/eci_countries_hs6.csv    country ECI from the same run
         outputs/validation/pci_hs6_validation.md

Main specification
  - Exports averaged over 2022-2024 (smooths one-off shipments).
  - Countries: those in OEC's HS22 HS6 ECI ranking in all three years (OEC has
    already removed small and unreliable reporters).
  - Products: HS6 lines with average world trade (in that country sample) of at
    least US$ 100 million; this approximates OEC's product set.
  - RCA >= 1, Hidalgo-Hausmann eigenvector method (see complexity.py).

Method check
  Recompute 2024 with OEC's exact 2024 countries and products and compare with
  OEC's 2024 PCI and ECI. If the method matches, correlations should be near 1.

Run from the repo root:  python scripts/compute_pci_hs6.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

from complexity import align_hs6, binary_m, eci_pci

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
OEC = ROOT / "data" / "reference" / "oec"
BACI = ROOT / "data" / "external" / "baci"
REPORT = ROOT / "outputs" / "validation" / "pci_hs6_validation.md"

YEARS = [2022, 2023, 2024]
MIN_WORLD_TRADE_USD = 100e6
BACI_TO_OEC_ISO3 = {"S19": "TWN"}  # BACI codes Taiwan as "Other Asia, nes"

# HS6 lines worth eyeballing (India-relevant splits within one HS4)
SPOTLIGHT = {
    "710210": "Diamonds, unsorted",
    "710221": "Diamonds, industrial, unworked",
    "710231": "Diamonds, non-industrial, unworked (rough)",
    "710239": "Diamonds, non-industrial, worked (cut & polished)",
    "300410": "Medicaments with penicillins",
    "300490": "Other medicaments, retail packs",
    "851713": "Smartphones",
    "851762": "Network equipment (switching/routing)",
    "271000": "Petroleum oils, not crude (BACI/OEC merge all of 2710 here)",
    "100630": "Rice, semi/wholly milled",
    "620520": "Men's cotton shirts",
}


def load() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series]:
    b = pd.read_csv(PROC / "baci_hs22_exports_country_hs6.csv.gz", dtype={"hs6": str})
    b["iso3"] = b["iso3"].replace(BACI_TO_OEC_ISO3)
    o_pci = pd.read_csv(OEC / "oec_pci_hs22_hs6.csv", dtype={"hs6": str})
    o_eci = pd.read_csv(OEC / "oec_eci_hs22_hs6.csv")
    desc = pd.read_csv(BACI / "product_codes_HS22_V202601.csv", dtype={"code": str})
    desc = desc.set_index(desc["code"].str.zfill(6))["description"]
    return b, o_pci, o_eci, desc


def matrix(b: pd.DataFrame, years: list[int], countries: set, products: set | None) -> pd.DataFrame:
    sub = b[b["year"].isin(years) & b["iso3"].isin(countries)]
    X = sub.pivot_table(index="iso3", columns="hs6", values="export_usd", aggfunc="sum", fill_value=0.0)
    X = X / len(years)  # average per year
    if products is not None:
        X = X.reindex(columns=sorted(products), fill_value=0.0)
    return X


def corr(a: pd.Series, b: pd.Series) -> tuple[float, float, int]:
    j = pd.concat([a, b], axis=1, join="inner").dropna()
    return j.iloc[:, 0].corr(j.iloc[:, 1]), j.iloc[:, 0].corr(j.iloc[:, 1], method="spearman"), len(j)


def main() -> None:
    b, o_pci, o_eci, desc = load()
    lines = ["# HS6 PCI validation", ""]

    # ---- 1. Method check: OEC's own 2024 sample -------------------------------
    y = 2024
    c24 = set(o_eci.loc[o_eci.year == y, "iso3"])
    p24 = set(o_pci.loc[o_pci.year == y, "hs6"])
    M = binary_m(matrix(b, [y], c24, p24))
    eci24, pci24, diag24 = eci_pci(M)
    r_p, s_p, n_p = corr(pci24, o_pci[o_pci.year == y].set_index("hs6")["pci"])
    r_e, s_e, n_e = corr(eci24, o_eci[o_eci.year == y].set_index("iso3")["eci"])
    lines += [
        "## 1. Method check (2024, OEC's countries and products)",
        "",
        f"Matrix: {diag24['n_places']} countries x {diag24['n_products']:,} products.",
        "",
        "| compared with OEC 2024 | Pearson | Spearman | n |",
        "|---|---|---|---|",
        f"| PCI (HS6) | {r_p:.3f} | {s_p:.3f} | {n_p:,} |",
        f"| ECI (countries) | {r_e:.3f} | {s_e:.3f} | {n_e} |",
        "",
    ]
    print(f"Method check 2024: PCI r={r_p:.3f} (rho {s_p:.3f}), ECI r={r_e:.3f} (rho {s_e:.3f})")

    # ---- 2. Main specification: 2022-24 average -------------------------------
    countries = set.intersection(*[set(o_eci.loc[o_eci.year == yy, "iso3"]) for yy in YEARS])
    X = matrix(b, YEARS, countries, None)
    world = X.sum(axis=0)
    X = X.loc[:, world >= MIN_WORLD_TRADE_USD]
    M = binary_m(X)
    eci, pci, diag = eci_pci(M)

    oec_avg = o_pci.groupby("hs6")["pci"].mean()
    oec_eci_avg = o_eci.groupby("iso3")["eci"].mean()
    r_p2, s_p2, n_p2 = corr(pci, oec_avg)
    r_e2, s_e2, n_e2 = corr(eci, oec_eci_avg)
    print(f"Main spec: {diag['n_places']} countries x {diag['n_products']:,} products; "
          f"PCI vs OEC avg r={r_p2:.3f}, ECI r={r_e2:.3f}")

    out = pd.DataFrame({
        "hs6": pci.index,
        "description": desc.reindex(pci.index).values,
        "pci": pci.values,
        "ubiquity": M.sum(axis=0).reindex(pci.index).astype(int).values,
        "world_trade_usd": world.reindex(pci.index).round().values,
        "oec_pci_2022_24": oec_avg.reindex(pci.index).values,
    }).sort_values("pci", ascending=False)
    out.insert(1, "hs4", out["hs6"].str[:4])
    out.to_csv(PROC / "pci_hs6.csv", index=False)

    ce = pd.DataFrame({
        "iso3": eci.index,
        "eci": eci.values,
        "diversity": M.sum(axis=1).reindex(eci.index).astype(int).values,
        "oec_eci_2022_24": oec_eci_avg.reindex(eci.index).values,
    }).sort_values("eci", ascending=False)
    ce["rank"] = np.arange(1, len(ce) + 1)
    ce.to_csv(PROC / "eci_countries_hs6.csv", index=False)

    lines += [
        "## 2. Main specification (2022-24 average)",
        "",
        f"Countries: {diag['n_places']} (in OEC's ranking all three years). "
        f"Products: {diag['n_products']:,} HS6 lines with average world trade >= US$ "
        f"{MIN_WORLD_TRADE_USD / 1e6:.0f} M. Eigenvalues: "
        f"{diag['eigenvalue_1']:.3f}, {diag['eigenvalue_2']:.3f}, {diag['eigenvalue_3']:.3f}.",
        "",
        "| compared with OEC (2022-24 mean) | Pearson | Spearman | n |",
        "|---|---|---|---|",
        f"| PCI (HS6) | {r_p2:.3f} | {s_p2:.3f} | {n_p2:,} |",
        f"| ECI (countries) | {r_e2:.3f} | {s_e2:.3f} | {n_e2} |",
        "",
    ]

    # ---- 3. HS4 consistency: export-weighted HS6 PCI vs OEC HS4 PCI -----------
    o4 = pd.read_csv(OEC / "oec_pci_hs22_hs4.csv", dtype={"hs4": str}).groupby("hs4")["pci"].mean()
    w = out.dropna(subset=["world_trade_usd"])
    agg4 = w.groupby("hs4").apply(lambda g: np.average(g["pci"], weights=g["world_trade_usd"]), include_groups=False)
    r4, s4, n4 = corr(agg4, o4)
    lines += [
        "## 3. Consistency with OEC HS4 PCI",
        "",
        f"Trade-weighted mean of our HS6 PCI within each HS4 vs OEC HS4 PCI: "
        f"Pearson {r4:.3f}, Spearman {s4:.3f}, n = {n4:,}.",
        "",
    ]
    print(f"HS4 consistency: r={r4:.3f}")

    # ---- 4. Country ranking ---------------------------------------------------
    names = o_eci.drop_duplicates("iso3").set_index("iso3")["country"]
    def ctable(df):
        rows = ["| rank | country | our ECI | OEC ECI | diversity |", "|---|---|---|---|---|"]
        for _, r in df.iterrows():
            rows.append(f"| {r['rank']} | {names.get(r.iso3, r.iso3)} | {r.eci:.2f} | {r.oec_eci_2022_24:.2f} | {r.diversity} |")
        return rows
    ind = ce[ce.iso3 == "IND"]
    lines += ["## 4. Country ECI", "", "Top 10:", ""] + ctable(ce.head(10)) + ["", "Bottom 5:", ""] + ctable(ce.tail(5))
    lines += ["", f"India: rank {int(ind['rank'].iloc[0])} of {len(ce)}, ECI {ind.eci.iloc[0]:.2f} "
              f"(OEC {ind.oec_eci_2022_24.iloc[0]:.2f}).", ""]

    # ---- 5. Product ranking ---------------------------------------------------
    def ptable(df):
        rows = ["| HS6 | product | PCI | OEC PCI | ubiquity |", "|---|---|---|---|---|"]
        for _, r in df.iterrows():
            o = "" if pd.isna(r.oec_pci_2022_24) else f"{r.oec_pci_2022_24:.2f}"
            rows.append(f"| {r.hs6} | {str(r.description)[:70]} | {r.pci:.2f} | {o} | {int(r.ubiquity)} |")
        return rows
    lines += ["## 5. Products", "", "Most complex 15:", ""] + ptable(out.head(15))
    lines += ["", "Least complex 15:", ""] + ptable(out.tail(15))
    spot = out.set_index("hs6").reindex(list(SPOTLIGHT)).reset_index()
    spot["description"] = [SPOTLIGHT[h] for h in spot["hs6"]]
    lines += ["", "Spotlight (India-relevant HS6 splits):", ""] + ptable(spot.dropna(subset=["pci"]))
    missing = [h for h in SPOTLIGHT if h not in set(out.hs6)]
    if missing:
        lines += ["", f"Not in the product set (below the trade cut-off or not traded): {', '.join(missing)}"]

    # ---- 6. Coverage of India's FY26 state exports ----------------------------
    st = pd.read_csv(PROC / "state_hs6_exports_am26.csv", dtype={"hs6": str})
    st = st[st["type"] != "Unspecified"].copy()
    st["direct"] = st["hs6"].isin(set(out.hs6))
    st["pci_code"] = align_hs6(st["hs6"], set(out.hs6))
    tot = st["export_usd"].sum()
    direct = st.loc[st["direct"], "export_usd"].sum() / tot
    mapped = st.loc[st["pci_code"].notna(), "export_usd"].sum() / tot
    via_heading = st[st["pci_code"].notna() & ~st["direct"]]
    heads = via_heading.groupby("pci_code")["export_usd"].sum().sort_values(ascending=False) / 1e9
    unm = (st[st["pci_code"].isna()].groupby(["hs6", "description"])["export_usd"].sum()
           .sort_values(ascending=False).head(10) / 1e9)
    by_state = st.assign(v=st["export_usd"].where(st["pci_code"].notna(), 0)).groupby("state")[["v", "export_usd"]].sum()
    by_state["share"] = by_state["v"] / by_state["export_usd"]
    low = by_state[by_state["export_usd"] > 1e8].sort_values("share").head(5)
    lines += [
        "", "## 6. Coverage of India's FY26 state exports (excluding 'Unspecified')", "",
        f"- HS6 code has a PCI directly: {direct:.1%} of export value",
        f"- after mapping missing codes to their heading's 'xxxx00' code: {mapped:.1%}",
        "", "Headings matched through 'xxxx00' (US$ bn):", "",
    ] + [f"- {h}: {v:.1f}" for h, v in heads.head(10).items()] + [
        "", "Largest exports still without a PCI (US$ bn; small products below the trade cut-off):", "",
    ] + [f"- {h} {d[:50]}: {v:.2f}" for (h, d), v in unm.items()] + [
        "", "Lowest coverage among states with exports above US$ 100 M:", "",
    ] + [f"- {s_}: {r.share:.1%}" for s_, r in low.iterrows()]
    print(f"Coverage of state exports: direct {direct:.1%}, with heading mapping {mapped:.1%}")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {REPORT.relative_to(ROOT)}, {(PROC / 'pci_hs6.csv').relative_to(ROOT)}, "
          f"{(PROC / 'eci_countries_hs6.csv').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
