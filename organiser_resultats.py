"""
Organise les fichiers existants pour le pipeline final.
- Copie brats_full_metrics.csv vers brats_metriques.csv (alias)
- Verifie la presence des seuils calibres
- Affiche un recap de l'etat du pipeline
"""
import shutil
from pathlib import Path
import json
import pandas as pd

# Verifier les seuils calibres
seuils_path = Path("results_calibration/seuils_calibres.json")
if seuils_path.exists():
    size = seuils_path.stat().st_size
    with open(seuils_path) as f:
        seuils = json.load(f)
    print(f"OK seuils_calibres.json ({size} octets, {len(seuils)} metriques)")
else:
    print(f"ERREUR : {seuils_path} introuvable")

# Verifier metriques BraTS full
brats_full = Path("brats_full_metrics.csv")
if brats_full.exists():
    df = pd.read_csv(brats_full)
    print(f"OK brats_full_metrics.csv ({len(df)} cas, {len(df.columns)} colonnes)")
    
    # Creer l'alias attendu par le pipeline
    alias = Path("brats_metriques.csv")
    if not alias.exists():
        shutil.copy(brats_full, alias)
        print(f"OK Alias cree : {alias}")
    else:
        print(f"OK Alias existe deja : {alias}")
else:
    print(f"ERREUR : {brats_full} introuvable")

# Verifier metriques calibration
calib_metrics = Path("results_calibration/calibration_metriques.csv")
if calib_metrics.exists():
    df_cal = pd.read_csv(calib_metrics)
    print(f"OK calibration_metriques.csv ({len(df_cal)} sujets)")
else:
    print(f"ERREUR : {calib_metrics} introuvable")

# Resume des colonnes pour preparer comparaison.py
print("\n=== Colonnes brats_metriques.csv ===")
df = pd.read_csv("brats_metriques.csv")
print(list(df.columns))

print("\n=== Colonnes calibration_metriques.csv ===")
df_cal = pd.read_csv("results_calibration/calibration_metriques.csv")
print(list(df_cal.columns))

print("\n=== Metriques disponibles dans seuils_calibres.json ===")
print(list(seuils.keys()))

print("\n=> Pret pour comparaison.py")
