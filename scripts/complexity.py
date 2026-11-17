"""
Economic complexity calculations shared by the scripts in this repo.

Notation: X[c, p] = exports of place c in product p.
  RCA[c, p] = (X[c,p] / X[c,.]) / (X[.,p] / X[.,.])
  M[c, p]   = 1 if RCA >= 1 else 0
  diversity k_c = sum_p M[c,p];  ubiquity k_p = sum_c M[c,p]

Hidalgo-Hausmann ECI is the eigenvector for the second-largest eigenvalue of
  M~ = D^-1 M U^-1 M'      (D = diag(k_c), U = diag(k_p))
We solve the equivalent symmetric matrix S = D^-1/2 M U^-1 M' D^-1/2 (same
eigenvalues; ECI = D^-1/2 x eigenvector), which is numerically stable.
PCI is then the average ECI of the places that export the product:
  PCI_p = (1 / k_p) sum_c M[c,p] ECI_c
which equals the eigenvector of the product matrix U^-1 M' D^-1 M.
Both are returned as z-scores; the sign is set so ECI rises with diversity.
"""

import numpy as np
import pandas as pd


def rca_matrix(X: pd.DataFrame) -> pd.DataFrame:
    """X: places (rows) x products (columns) of export values."""
    share_in_place = X.div(X.sum(axis=1), axis=0)
    share_in_world = X.sum(axis=0) / X.values.sum()
    return share_in_place.div(share_in_world, axis=1)


def binary_m(X: pd.DataFrame, threshold: float = 1.0) -> pd.DataFrame:
    """M[c,p] = 1 if RCA >= threshold. Drops all-zero rows/columns until none remain."""
    M = (rca_matrix(X) >= threshold).astype(float)
    while True:
        keep_r = M.sum(axis=1) > 0
        keep_c = M.sum(axis=0) > 0
        if keep_r.all() and keep_c.all():
            return M
        M = M.loc[keep_r, keep_c]


def zscore(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std(ddof=0)


def eci_pci(M: pd.DataFrame) -> tuple[pd.Series, pd.Series, dict]:
    """Return (ECI by place, PCI by product, diagnostics) from a 0/1 matrix."""
    m = M.values
    kc = m.sum(axis=1)
    kp = m.sum(axis=0)
    d = 1.0 / np.sqrt(kc)
    S = (d[:, None] * m) @ np.diag(1.0 / kp) @ (m.T * d[None, :])
    vals, vecs = np.linalg.eigh(S)            # ascending order
    order = np.argsort(vals)[::-1]
    v2 = vecs[:, order[1]]
    eci = d * v2                              # back to the M~ eigenvector
    if np.corrcoef(eci, kc)[0, 1] < 0:        # sign: more diverse -> higher ECI
        eci = -eci
    pci = (m.T @ eci) / kp
    eci_s = zscore(pd.Series(eci, index=M.index, name="eci"))
    pci_s = zscore(pd.Series(pci, index=M.columns, name="pci"))
    diag = {
        "eigenvalue_1": float(vals[order[0]]),
        "eigenvalue_2": float(vals[order[1]]),
        "eigenvalue_3": float(vals[order[2]]),
        "n_places": M.shape[0],
        "n_products": M.shape[1],
        "corr_eci_diversity": float(np.corrcoef(eci, kc)[0, 1]),
    }
    return eci_s, pci_s, diag


def mean_pci_eci(M: pd.DataFrame, pci: pd.Series, min_products: int = 1) -> pd.DataFrame:
    """Sub-national ECI: mean PCI of products with M = 1 (PCI held fixed from world data)."""
    common = M.columns.intersection(pci.index)
    m = M[common]
    n = m.sum(axis=1)
    eci = (m @ pci[common]) / n
    eci[n < min_products] = np.nan
    return pd.DataFrame({"eci": eci, "n_products_rca": n.astype(int)})


def align_hs6(codes: pd.Series, available: set) -> pd.Series:
    """
    Map national HS6 codes to the codes that have a PCI.

    BACI (and OEC) merge some headings into one "xxxx00" code, e.g. all of
    petroleum oils 2710.12/2710.19 -> 271000. A code that is not available is
    mapped to its heading's "xxxx00" code if that exists, otherwise NaN.
    """
    codes = codes.astype(str).str.zfill(6)
    heading = codes.str[:4] + "00"
    out = codes.where(codes.isin(available))
    return out.fillna(heading.where(heading.isin(available)))
