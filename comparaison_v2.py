"""Comparaison v2 BraTS vs ds000030 avec analyses statistiques avancees.

Ameliorations vs v1 :
  1. Test de Mann-Whitney U (non parametrique) entre distributions.
  2. Distance de Mahalanobis multivariee (resume 4 metriques en 1 score).
  3. Auto-calibration tumorale via distribution du tissu sain BraTS.
  4. Analyse de sensibilite des seuils de classification SUSPECT.

Auteur : Y43, doctorant en informatique cognitive (UQAM, DIC938R).

"Strength is what we have to count on. The weak have to rely on others."
   -- Rimuru Tempest
"""
from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial.distance import mahalanobis

RESULTS = Path("results_calibration")
BRATS_CSV = Path("brats_full_metrics_v2.csv")
CALIB_CSV = RESULTS / "calibration_metriques_v2.csv"
SEUILS_JSON = RESULTS / "seuils_calibres_v2.json"

METRIQUES_CERVEAU = ["snr_cerveau", "entropie_cerveau", "gradient_cerveau", "cv_bruit_cerveau"]


def charger() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    df_brats = pd.read_csv(BRATS_CSV)
    df_calib = pd.read_csv(CALIB_CSV)
    with open(SEUILS_JSON) as f:
        seuils = json.load(f)
    print(f"BraTS : {len(df_brats)} cas | Calib ds000030 : {len(df_calib)} sujets")
    return df_brats, df_calib, seuils


# --- Analyse 1 : Mann-Whitney U test ---
def test_mann_whitney(df_brats: pd.DataFrame, df_calib: pd.DataFrame) -> pd.DataFrame:
    print("\n=== 1. Test de Mann-Whitney U (BraTS vs ds000030) ===")
    rows = []
    for m in METRIQUES_CERVEAU:
        b = df_brats[m].dropna().values
        c = df_calib[m].dropna().values
        u, p = stats.mannwhitneyu(b, c, alternative="two-sided")
        # Taille d'effet : r = z / sqrt(N)
        n1, n2 = len(b), len(c)
        mean_u = n1 * n2 / 2
        std_u = np.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
        z = (u - mean_u) / std_u
        r = abs(z) / np.sqrt(n1 + n2)
        rows.append({
            "metrique": m,
            "median_brats": float(np.median(b)),
            "median_calib": float(np.median(c)),
            "U": float(u),
            "p_value": float(p),
            "taille_effet_r": float(r),
            "significatif": p < 0.001,
        })
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    return df


# --- Analyse 2 : Distance de Mahalanobis ---
def calcul_mahalanobis(df_brats: pd.DataFrame, df_calib: pd.DataFrame) -> pd.DataFrame:
    print("\n=== 2. Distance de Mahalanobis (BraTS vs centroide ds000030) ===")
    df_calib_ok = df_calib[df_calib.get("quality_label", "include") == "include"]
    X_calib = df_calib_ok[METRIQUES_CERVEAU].dropna().values
    mu = X_calib.mean(axis=0)
    cov = np.cov(X_calib, rowvar=False)
    inv_cov = np.linalg.pinv(cov)

    distances = []
    X_brats = df_brats[METRIQUES_CERVEAU].values
    for i, x in enumerate(X_brats):
        if np.any(np.isnan(x)):
            distances.append(np.nan)
            continue
        d = mahalanobis(x, mu, inv_cov)
        distances.append(float(d))

    df_brats["mahalanobis_d"] = distances
    # Seuil chi2 a 4 ddl (4 metriques) : p<0.001 -> sqrt(18.47)
    seuil_d = float(np.sqrt(stats.chi2.ppf(0.999, df=len(METRIQUES_CERVEAU))))
    df_brats["mahalanobis_outlier"] = df_brats["mahalanobis_d"] > seuil_d
    n_out = int(df_brats["mahalanobis_outlier"].sum())
    pct = 100 * n_out / len(df_brats)
    print(f"  Seuil chi2 (p<0.001, 4 ddl) : d > {seuil_d:.3f}")
    print(f"  Cas BraTS detectes outliers : {n_out}/{len(df_brats)} ({pct:.1f}%)")
    print(f"  Distance mediane BraTS      : {np.nanmedian(distances):.3f}")
    print(f"  Distance max BraTS          : {np.nanmax(distances):.3f}")
    return df_brats


# --- Analyse 3 : Auto-calibration tumorale ---
def auto_calibration_tumeur(df_brats: pd.DataFrame) -> pd.DataFrame:
    print("\n=== 3. Auto-calibration tumorale (reference: tissu sain BraTS) ===")
    paires = [
        ("snr_tumeur", "snr_sain"),
        ("entropie_tumeur", "entropie_sain"),
        ("gradient_tumeur", "gradient_sain"),
        ("cv_bruit_tumeur", "cv_bruit_sain"),
    ]
    rows = []
    for tum, sain in paires:
        ref = df_brats[sain].dropna().values
        mu, sigma = ref.mean(), ref.std(ddof=1)
        z = (df_brats[tum] - mu) / sigma
        df_brats[f"{tum}_z_auto"] = z
        rows.append({
            "metrique_tumeur": tum,
            "ref_sain_mu": float(mu),
            "ref_sain_sigma": float(sigma),
            "z_mediane": float(np.nanmedian(z)),
            "n_outliers_z>2": int((np.abs(z) > 2).sum()),
            "n_outliers_z>3": int((np.abs(z) > 3).sum()),
        })
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    return df_brats


# --- Analyse 4 : Sensibilite des seuils SUSPECT ---
def sensibilite_seuils(df_brats: pd.DataFrame, seuils: dict) -> pd.DataFrame:
    print("\n=== 4. Sensibilite du seuil de statut SUSPECT ===")
    cols_z = []
    for m in METRIQUES_CERVEAU:
        if m not in seuils:
            continue
        s = seuils[m]
        z = (df_brats[m] - s["moyenne"]) / s["ecart_type"]
        df_brats[f"{m}_z"] = z
        df_brats[f"{m}_outlier_z"] = (np.abs(z) > 2)
        cols_z.append(f"{m}_outlier_z")
    df_brats["n_outliers_cerveau"] = df_brats[cols_z].sum(axis=1)

    rows = []
    for k in range(0, 5):
        n_suspect = int((df_brats["n_outliers_cerveau"] >= k).sum())
        rows.append({
            "seuil_outliers_min": k,
            "n_cas_suspects": n_suspect,
            "pct": 100 * n_suspect / len(df_brats),
        })
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    return df


def main():
    df_brats, df_calib, seuils = charger()
    df_mw = test_mann_whitney(df_brats, df_calib)
    df_brats = calcul_mahalanobis(df_brats, df_calib)
    df_auto = auto_calibration_tumeur(df_brats)
    df_sens = sensibilite_seuils(df_brats, seuils)

    # Sauvegardes
    df_mw.to_csv(RESULTS / "mann_whitney_v2.csv", index=False)
    df_brats.to_csv(RESULTS / "brats_outliers_v2.csv", index=False)
    df_sens.to_csv(RESULTS / "sensibilite_seuils_v2.csv", index=False)
    print("\n=== Sauvegardes ===")
    print(f"  {RESULTS/'mann_whitney_v2.csv'}")
    print(f"  {RESULTS/'brats_outliers_v2.csv'}")
    print(f"  {RESULTS/'sensibilite_seuils_v2.csv'}")
    return df_brats, df_mw, df_sens


if __name__ == "__main__":
    main()
