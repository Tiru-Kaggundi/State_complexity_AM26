"""
Plot state economic complexity (FY26, HS6) against income and poverty.

Input : data/processed/state_panel_am26.csv   (scripts/build_state_panel.py)
Output: outputs/figures/
          main_eci_vs_nsdp.png   states with FY26 exports >= US$ 1 bn, income on a log scale
          main_eci_vs_mpi.png    states with FY26 exports >= US$ 1 bn
          full_eci_vs_nsdp.png   every state/UT with data
          full_eci_vs_mpi.png    every state/UT with data
        outputs/figures/fit_stats.md   slopes, R^2 and residuals for the write-up

Style follows the earlier Indian Westerlies charts: 16:9 at 400 dpi, bubble area
proportional to FY26 exports, colour by ECI, fitted straight line. The equation
and R^2 are printed on a chart only when R^2 >= SHOW_FIT_MIN_R2; they are always
written to fit_stats.md.

Run from the repo root:  python scripts/plot_state_eci.py
"""

from pathlib import Path

import matplotlib
import matplotlib.colors
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator

try:
    from adjustText import adjust_text
except ImportError:  # labels still drawn, just not de-overlapped
    adjust_text = None

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data" / "processed" / "state_panel_am26.csv"
FIG = ROOT / "outputs" / "figures"

FIG_SIZE = (12, 6.75)       # 16:9
DPI = 400
AREA_PER_BN = 49            # points^2 per US$ bn of exports
MIN_AREA = 18
SHOW_FIT_MIN_R2 = 0.4
# One colour scale for every chart (ECI range of the large exporters), so a state
# keeps its colour across charts; values outside the range take the end colours.
COLOR_NORM = matplotlib.colors.Normalize(vmin=-0.45, vmax=0.3, clip=True)
SHORT_NAMES = {
    "Dadra and Nagar Haveli and Daman and Diu": "DNH & DD",
    "Andaman and Nicobar Islands": "Andaman & Nicobar",
    "Jammu and Kashmir": "J&K",
}

ECI_LABEL = "Economic Complexity Index (ECI), FY2025-26, HS6"
NSDP_LABEL = "Per capita NSDP, 2023-24 (₹, log scale)"
NSDP_LABEL_LINEAR = "Per capita NSDP, 2023-24 (₹)"
MPI_LABEL = "Multidimensional poverty: headcount ratio (%), 2019-21"

SOURCES = ("Sources: exports, DGCI&S (Apr 2025 to Mar 2026); product complexity computed at HS6 from "
           "CEPII BACI (2022-24); per capita NSDP (current prices) and MPI (NITI Aayog National MPI 2023, "
           "NFHS-5) from RBI Handbook of Statistics on Indian States.")


def fit(x: np.ndarray, y: np.ndarray) -> dict:
    slope, intercept = np.polyfit(x, y, 1)
    pred = slope * x + intercept
    resid = y - pred
    r2 = 1 - (resid ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return {"slope": slope, "intercept": intercept, "r2": r2,
            "resid_sd": resid / resid.std(ddof=1), "n": len(x)}


def rupees(v: float, _pos=None) -> str:
    return f"₹{v / 1e5:g} lakh" if v >= 1e5 else f"₹{v / 1e3:g}k"


def scatter(df: pd.DataFrame, y_col: str, out: Path, title: str, ylabel: str,
            notes: list[str], log_y: bool = False) -> dict:
    d = df.dropna(subset=["eci", y_col]).copy()
    x = d["eci"].to_numpy()
    y_raw = d[y_col].to_numpy()
    y_fit = np.log(y_raw) if log_y else y_raw
    f = fit(x, y_fit)
    d["resid_sd"] = f["resid_sd"]

    fig, ax = plt.subplots(figsize=FIG_SIZE)
    sizes = np.maximum(d["export_usd"].to_numpy() / 1e9 * AREA_PER_BN, MIN_AREA)
    sc = ax.scatter(x, y_raw, s=sizes, c=x, cmap="Spectral", norm=COLOR_NORM, alpha=0.78,
                    edgecolors="dimgrey", linewidths=0.5, zorder=3)

    xs = np.linspace(x.min(), x.max(), 100)
    ys = f["slope"] * xs + f["intercept"]
    ax.plot(xs, np.exp(ys) if log_y else ys, color="coral", lw=2, zorder=2)

    if log_y:
        ax.set_yscale("log")
        lo, hi = y_raw.min() / 1.15, y_raw.max() * 1.15
        ticks = [t for t in [5e4, 7.5e4, 1e5, 1.5e5, 2e5, 3e5, 4e5, 5e5, 6e5, 8e5] if lo <= t <= hi]
        ax.set_ylim(lo, hi)
        ax.yaxis.set_major_locator(FixedLocator(ticks))
        ax.yaxis.set_minor_locator(NullLocator())
        ax.yaxis.set_major_formatter(FuncFormatter(rupees))
    elif y_col == "nsdp_pc_inr":
        ax.yaxis.set_major_formatter(FuncFormatter(rupees))

    font = 9.5 if len(d) <= 25 else 8.5
    texts = [ax.text(xi, yi, SHORT_NAMES.get(s, s), fontsize=font, alpha=0.9, zorder=4)
             for xi, yi, s in zip(x, y_raw, d["state"])]
    if adjust_text is not None:
        fig.canvas.draw()
        adjust_text(texts, x=x, y=y_raw, ax=ax,
                    expand=(1.35, 1.7), force_text=(0.5, 0.9), force_static=(0.4, 0.7),
                    ensure_inside_axes=True, iter_lim=2000,
                    arrowprops=dict(arrowstyle="-", color="grey", lw=0.5))

    ref = 10
    ax.legend(handles=[ax.scatter([], [], s=ref * AREA_PER_BN, c="grey", alpha=0.5,
                                  edgecolors="dimgrey", label=f"US$ {ref} bn exports")],
              loc="lower right" if y_col == "nsdp_pc_inr" else "upper right",
              fontsize=9, frameon=True, labelspacing=1.5, borderpad=1)

    if f["r2"] >= SHOW_FIT_MIN_R2:
        lhs = "ln(NSDP pc)" if log_y else y_col
        ax.text(0.02, 0.97, f"{lhs} = {f['intercept']:.2f} {f['slope']:+.2f} × ECI\n$R^2$ = {f['r2']:.2f}",
                transform=ax.transAxes, va="top", fontsize=10,
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8))

    ax.set_xlabel(ECI_LABEL, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=16)
    ax.grid(True, alpha=0.3)
    ax.text(0.0, -0.13, "\n".join(notes + [SOURCES]), transform=ax.transAxes,
            fontsize=7.5, color="dimgrey", va="top", wrap=True)
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out.relative_to(ROOT)}  (n={f['n']}, R²={f['r2']:.3f})")
    f["data"] = d
    return f


def main() -> None:
    p = pd.read_csv(PANEL)
    main_df = p[p["in_main_plot"]]
    gj = p.loc[p["nsdp_note"].notna(), ["state", "nsdp_note"]]
    gj_note = [f"{r.state}: per capita NSDP for 2023-24 estimated ({r.nsdp_note})." for r in gj.itertuples()]
    main_note = "Shows states/UTs with exports of at least US$ 1 billion in FY2025-26; the full chart includes all."
    full_note = ("All states/UTs with data. Small exporters (e.g. Lakshadweep, Ladakh, the north-eastern states) "
                 "export few products, so their ECI is less reliable.")
    no_nsdp = ", ".join(p.loc[p["nsdp_pc_inr"].isna(), "state"])

    runs = {
        "main_eci_vs_nsdp": scatter(main_df, "nsdp_pc_inr", FIG / "main_eci_vs_nsdp.png",
                                    "Complexity vs income: Indian states", NSDP_LABEL,
                                    [main_note + f" No NSDP published for {no_nsdp}."] + gj_note, log_y=True),
        "main_eci_vs_mpi": scatter(main_df, "mpi_hcr_pct", FIG / "main_eci_vs_mpi.png",
                                   "Complexity vs poverty: Indian states", MPI_LABEL, [main_note]),
        "full_eci_vs_nsdp": scatter(p, "nsdp_pc_inr", FIG / "full_eci_vs_nsdp.png",
                                    "Complexity vs income: all states and UTs", NSDP_LABEL_LINEAR,
                                    [full_note + f" No NSDP published for {no_nsdp}."] + gj_note),
        "full_eci_vs_mpi": scatter(p, "mpi_hcr_pct", FIG / "full_eci_vs_mpi.png",
                                   "Complexity vs poverty: all states and UTs", MPI_LABEL, [full_note]),
    }

    lines = ["# Fit statistics (straight-line fits shown on the charts)", ""]
    for name, f in runs.items():
        lines += [f"## {name}", "", f"n = {f['n']}, slope = {f['slope']:.3f}, intercept = {f['intercept']:.3f}, "
                  f"R² = {f['r2']:.3f}"]
        if name == "main_eci_vs_nsdp":
            lines.append(f"A 0.1 rise in ECI goes with {np.exp(0.1 * f['slope']) - 1:.1%} higher per capita NSDP.")
        d = f["data"].sort_values("resid_sd")
        lines += ["", "Furthest below / above the line (residual in standard deviations):", ""]
        lines += [f"- {r.state}: {r.resid_sd:+.2f}" for r in pd.concat([d.head(3), d.tail(3)]).itertuples()]
        up = d[d["state"] == "Uttar Pradesh"]
        if len(up) and name.endswith("nsdp"):
            u = up.iloc[0]
            pred = f["slope"] * u.eci + f["intercept"]
            pred = np.exp(pred) if name.startswith("main") else pred
            lines.append(f"- Uttar Pradesh: actual ₹{u.nsdp_pc_inr:,.0f}, line predicts ₹{pred:,.0f} "
                         f"({pred / u.nsdp_pc_inr:.2f}x actual)")
        lines.append("")
    (FIG / "fit_stats.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
