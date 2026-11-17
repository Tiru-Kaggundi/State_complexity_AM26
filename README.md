# State complexity, FY26 (AM26)

Economic complexity of Indian states from FY2025-26 export data, and how it
relates to income (GSDP per capita) and poverty (NITI Aayog MPI).

This updates the analysis behind the Indian Westerlies post
[Why Some Indian States Are Richer Than Others](https://indianwesterlies.substack.com/p/why-some-indian-states-are-richer),
which used FY25 data at HS4. This version uses FY26 data at **HS6**.

## Method (planned)

1. **State exports**: DGCI&S state-of-origin exports, April 2025 to March 2026,
   state x HS6 (ITC-HS, HS 2022 basis).
2. **Product complexity (PCI) at HS6**: computed from world trade in
   CEPII BACI (HS22 edition), using the Hidalgo-Hausmann eigenvector method on
   the country x product RCA matrix, with standard filters for small countries
   and products. Fallback if HS6 does not work well: OEC PCI at HS4.
3. **State ECI**: RCA of each state against India's total; state ECI is the
   mean PCI of the HS6 products where the state has RCA >= 1 (the OEC approach
   for sub-national regions).
4. **Plots**: state ECI against log GSDP per capita and MPI headcount ratio,
   bubbles sized by exports, with and without small NE states/UTs.

## Status

- [x] Raw data added and cleaned (`data/processed/state_hs6_exports_am26.csv`)
- [ ] HS6 PCI from BACI HS22
- [ ] State RCA and ECI
- [ ] GSDP and MPI inputs
- [ ] Plots

## Layout

```
data/
  raw/dgcis_am26/          DGCI&S downloads, unmodified (7 parts)
  reference/               lookup tables (state name mapping)
  processed/               clean outputs produced by scripts/
  external/                large downloads such as BACI (not committed)
scripts/
  clean_dgcis_am26.py      raw .xls -> tidy CSV, with validation checks
outputs/figures/           plots
```

## Reproduce

```bash
pip install -r requirements.txt
python scripts/clean_dgcis_am26.py
```

## Data: `data/processed/state_hs6_exports_am26.csv`

One row per state x HS6 product (67,188 rows, 37 states/UTs, 5,216 HS6 codes,
total about US$ 441.5 bn).

| column | meaning |
|---|---|
| `fy` | financial year, `2025-26` |
| `state` | standardised state/UT name |
| `type` | `State`, `UT`, or `Unspecified` (exports with no state of origin, about US$ 4.3 bn) |
| `state_raw` | name as it appears in the DGCI&S file |
| `hs2`, `hs4`, `hs6` | HS code at 2, 4 and 6 digits (text, leading zeros kept) |
| `description` | DGCI&S commodity description, whitespace cleaned (the portal cuts these at about 60 characters) |
| `export_usd`, `export_inr` | exports April 2025 to March 2026, in US$ and rupees |

The DGCI&S download also reports March 2026 on its own in separate columns.
Those are dropped: the April-March columns already include March. Checks:
full-year total US$ 441.5 bn (₹ 39.0 lakh crore); March alone was US$ 38.9 bn.

Known quirks kept as-is: 75 rows show US$ 0 with a small positive rupee value
(rounding in the source).

`data/processed/state_totals_am26.csv` has one row per state with total
exports and the number of HS6 and HS4 products exported.
