"""
Wrapper pour executer comparaison.py avec les chemins Windows.
"""
from pathlib import Path
import shutil
import comparaison_win as comp

# Patcher le chemin RESULTS_DIR
comp.RESULTS_DIR = Path("results_calibration")

# S'assurer que les fichiers necessaires sont au bon endroit
fichiers_requis = {
    "brats_metriques.csv": "brats_metriques.csv",
    "calibration_metriques.csv": "results_calibration/calibration_metriques.csv",
    "seuils_calibres.json": "results_calibration/seuils_calibres.json",
}

# Le wrapper attend tout dans RESULTS_DIR
# On copie/symlink brats_metriques.csv si pas deja dedans
src_brats = Path("brats_metriques.csv")
dst_brats = comp.RESULTS_DIR / "brats_metriques.csv"
if src_brats.exists() and not dst_brats.exists():
    shutil.copy(src_brats, dst_brats)
    print(f"OK Copie : {src_brats} -> {dst_brats}")

print(f"=== CHEMINS PATCHES ===")
print(f"RESULTS_DIR : {comp.RESULTS_DIR}")
for f in ["brats_metriques.csv", "calibration_metriques.csv", "seuils_calibres.json"]:
    p = comp.RESULTS_DIR / f
    print(f"  {f:30s} : {'OK' if p.exists() else 'MANQUANT'} ({p})")
print()

# Lancer la comparaison
df_outliers, rapport, df_comp = comp.main()

print(f"\n=> Comparaison terminee.")
print(f"=> Resultats dans : {comp.RESULTS_DIR.absolute()}")
