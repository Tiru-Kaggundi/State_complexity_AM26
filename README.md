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
- [x] HS6 PCI from BACI HS22, validated against OEC
  (see `outputs/validation/pci_hs6_validation.md`)
- [x] State RCA and ECI at HS6, all 36 states/UTs kept (`data/processed/state_eci_am26.csv`)
- [x] RBI Handbook tables downloaded: MPI (Table 10), per capita NSDP (Table 19), GSDP (Table 21)
- [x] State panel: ECI + per capita NSDP 2023-24 + MPI headcount 2019-21 (`data/processed/state_panel_am26.csv`)
- [x] Plots (`outputs/figures/`), fit statistics in `outputs/figures/fit_stats.md`

## Layout

```
data/
  raw/dgcis_am26/          DGCI&S downloads, unmodified (7 parts)
  reference/               lookup tables (state name mapping)
  processed/               clean outputs produced by scripts/
  external/                large downloads such as BACI (not committed)
scripts/
  clean_dgcis_am26.py      raw .xls -> tidy CSV, with validation checks
  fetch_oec_reference.py   OEC PCI/ECI (HS 2022, HS6 and HS4) for validation
  aggregate_baci.py        BACI bilateral flows -> exports by country x HS6 x year
  complexity.py            RCA, Hidalgo-Hausmann ECI/PCI, HS6 code alignment
  compute_pci_hs6.py       HS6 PCI and country ECI + validation report
  compute_state_eci.py     state RCA at HS6 and state ECI (mean PCI of RCA >= 1 products)
  fetch_rbi_handbook.py    RBI Handbook of Statistics on Indian States: MPI, NSDP, GSDP
  build_state_panel.py     one table per state: ECI, income, poverty, plot flags
  plot_state_eci.py        the four charts + fit statistics
outputs/
  validation/              validation reports
  figures/                 plots
```

## Reproduce

```bash
pip install -r requirements.txt
python scripts/clean_dgcis_am26.py

# HS6 PCI: download BACI HS22 (about 300 MB zip, 1.1 GB unzipped) once
mkdir -p data/external/baci && cd data/external/baci
curl -LO https://www.cepii.fr/DATA_DOWNLOAD/baci/data/BACI_HS22_V202601.zip
unzip BACI_HS22_V202601.zip && cd ../../..
python scripts/fetch_oec_reference.py
python scripts/aggregate_baci.py
python scripts/compute_pci_hs6.py
python scripts/compute_state_eci.py
python scripts/fetch_rbi_handbook.py
python scripts/build_state_panel.py
python scripts/plot_state_eci.py
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

## HS6 product complexity (PCI)

Built from CEPII BACI, HS 2022 codes, version 202601 (years 2022-2024).

- **Exports**: averaged over 2022-2024 by country and HS6.
- **Countries**: the 130 in OEC's HS22 HS6 ECI ranking in all three years
  (OEC has already removed small and unreliable reporters).
- **Products**: 4,673 HS6 lines with average world trade of at least US$ 100 M.
- **Method**: RCA >= 1, then the Hidalgo-Hausmann eigenvector method
  (`scripts/complexity.py`); PCI and ECI are z-scores.

Validation (full report in `outputs/validation/pci_hs6_validation.md`):

| check | result |
|---|---|
| Same method on OEC's own 2024 sample vs OEC 2024 PCI | r = 0.96 |
| Our 2022-24 PCI vs OEC's 2022-24 average PCI | r = 0.99 |
| Our country ECI vs OEC ECI | r = 0.997; Japan, Switzerland, Taiwan, Germany, Korea on top; India 40th of 130 |
| Our HS6 PCI averaged up to HS4 vs OEC HS4 PCI | r = 0.96 |
| Share of India's FY26 state exports with a PCI | 99.6% |

BACI and OEC merge all petroleum oils (2710.12, 2710.19) into one code, 271000;
India's data keeps them separate (US$ 49 bn, mostly Gujarat). Codes without a
PCI are therefore mapped to their heading's "xxxx00" code (`align_hs6`).

Outputs:

- `data/processed/pci_hs6.csv`: `hs6, hs4, description, pci, ubiquity, world_trade_usd, oec_pci_2022_24`
- `data/processed/eci_countries_hs6.csv`: country ECI, diversity, rank, OEC ECI
- `data/processed/baci_hs22_exports_country_hs6.csv.gz`: BACI collapsed to
  year x country x HS6 (`export_usd`), so the PCI can be recomputed without the
  large download. BACI is published under the Etalab Open Licence 2.0
  (Gaulier and Zignago, 2010, CEPII Working Paper 2010-23).

## State ECI, income and poverty

- **State ECI** (`data/processed/state_eci_am26.csv`): RCA of each state against
  India's total at HS6; ECI = mean world PCI of products with RCA >= 1. All 36
  states/UTs are kept. Small exporters rest on few products (`n_products_rca`),
  e.g. Lakshadweep 1, Ladakh 3, several north-eastern states 10-40.
- **Income**: per capita NSDP, current prices, 2023-24 (RBI Handbook Table 19).
  RBI does not publish GSDP per capita, and the Handbook has no population table.
  Gujarat has no 2023-24 value: its 2022-23 value (Rs 272,451) is grown one year
  at 9.0%, its average annual growth 2017-18 to 2022-23, giving Rs 297,010.
  No NSDP is published for Lakshadweep or Dadra and Nagar Haveli and Daman and Diu.
- **Poverty**: MPI headcount ratio, NFHS-5 (2019-21), NITI Aayog National MPI
  2023 (RBI Handbook Table 10).

| chart | states shown | R² |
|---|---|---|
| `main_eci_vs_nsdp.png` | exports >= US$ 1 bn (21 with NSDP) | 0.45 |
| `main_eci_vs_mpi.png` | exports >= US$ 1 bn (22) | 0.21 |
| `full_eci_vs_nsdp.png` | all with NSDP (34) | 0.19 |
| `full_eci_vs_mpi.png` | all (36) | 0.15 |

The equation and R² are printed on a chart only when R² >= 0.4 (currently only
the main income chart). Colours use one ECI scale across all charts.
