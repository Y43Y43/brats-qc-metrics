"""Recalibration ds000030 avec qc_metrics_v2.

Calcule les memes metriques v2 (avec masque rim) sur les 50 sujets
ds000030, puis derive les seuils z-score (mu +/- 2 sigma) et percentiles
(P5/P95) sur les sujets etiquetes "include" (qualite OK).

Auteur : Y43, doctorant en informatique cognitive (UQAM, DIC938R).
"""
from pathlib import Path
import json
import time
import numpy as np
import pandas as pd
from qc_metrics_v2 import calculer_metriques_sujet_v2

DS_DIR = Path(r"C:\Users\yaman\data\ds000030")
ANNOT = Path("quality_annotations.tsv")
OUTPUT_CSV = Path("results_calibration") / "calibration_metriques_v2.csv"
OUTPUT_JSON = Path("results_calibration") / "seuils_calibres_v2.json"
OUTPUT_CSV.parent.mkdir(exist_ok=True)

df_annot = pd.read_csv(ANNOT, sep="\t")
print(f"Sujets a traiter : {len(df_annot)}")

resultats = []
start = time.time()
for i, row in df_annot.iterrows():
    sub = row["participant_id"]
    t1 = DS_DIR / sub / "anat" / f"{sub}_T1w.nii.gz"
    if not t1.exists():
        print(f"[{i+1}/{len(df_annot)}] {sub} INTROUVABLE")
        continue
    t0 = time.time()
    try:
        r = calculer_metriques_sujet_v2(t1, None, sujet_id=sub)
        r["quality_label"] = row["quality_label"]
        r["quality_rating"] = row["quality_rating"]
        resultats.append(r)
        print(f"[{i+1}/{len(df_annot)}] {sub} ({row['quality_label']}) OK ({time.time()-t0:.1f}s)")
    except Exception as e:
        print(f"[{i+1}/{len(df_annot)}] {sub} ERROR: {e}")

df = pd.DataFrame(resultats)
df.to_csv(OUTPUT_CSV, index=False)
print(f"\nMetriques sauvegardees : {OUTPUT_CSV} ({len(df)} sujets)")

# Seuils derives uniquement sur sujets "include" (controles qualite OK)
df_ok = df[df["quality_label"] == "include"].copy()
print(f"\nDerivation des seuils sur {len(df_ok)} sujets 'include'.")

metriques = [
    "snr_cerveau", "entropie_cerveau", "gradient_cerveau", "cv_bruit_cerveau",
    "snr_sain", "entropie_sain", "gradient_sain", "cv_bruit_sain",
    "bruit_rim_std",
]
seuils = {}
for m in metriques:
    vals = df_ok[m].dropna().values
    if len(vals) < 5:
        continue
    mu, sigma = float(np.mean(vals)), float(np.std(vals, ddof=1))
    seuils[m] = {
        "moyenne": mu,
        "ecart_type": sigma,
        "z_low": mu - 2 * sigma,
        "z_high": mu + 2 * sigma,
        "p5": float(np.percentile(vals, 5)),
        "p95": float(np.percentile(vals, 95)),
        "n": int(len(vals)),
    }

with open(OUTPUT_JSON, "w") as f:
    json.dump(seuils, f, indent=2)
print(f"Seuils sauvegardes : {OUTPUT_JSON}")
print(f"Duree totale : {(time.time()-start)/60:.1f} min")
