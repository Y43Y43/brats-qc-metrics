"""
Wrapper pour executer visualisations.py avec :
- Chemins Windows
- Adaptation pour 1251 cas (sous-echantillonnage des figures denses)
"""
from pathlib import Path
import shutil
import pandas as pd
import visualisations_win as viz

# Patcher les chemins
viz.RESULTS_DIR = Path("results_calibration")
viz.FIGURES_DIR = Path("figures_full")
viz.FIGURES_DIR.mkdir(parents=True, exist_ok=True)

print(f"=== CHEMINS PATCHES ===")
print(f"RESULTS_DIR : {viz.RESULTS_DIR}")
print(f"FIGURES_DIR : {viz.FIGURES_DIR}\n")

# Charger les donnees normalement
df_calib, df_brats, df_outliers, df_rapport, seuils = viz.charger_donnees()
print(f"Charges : {len(df_calib)} calib, {len(df_brats)} BraTS\n")

# === FIG 1 : OK avec 1251 cas ===
print("Generation des figures...")
viz.fig1_boxplots_comparaison(df_calib, df_brats, seuils)

# === FIG 2 : OK (utilise seulement calibration) ===
viz.fig2_boxplots_par_qualite(df_calib)

# === FIG 3 : SOUS-ECHANTILLONNAGE pour heatmap lisible ===
# Top 25 outliers + bottom 25 = 50 cas representatifs
df_outliers_sorted = df_outliers.merge(
    df_rapport[['sujet_id', 'n_outliers_zscore']], on='sujet_id'
).sort_values('n_outliers_zscore', ascending=False)

top_outliers = df_outliers_sorted.head(25)
bottom_outliers = df_outliers_sorted.tail(25)
df_outliers_sample = pd.concat([top_outliers, bottom_outliers]).drop(
    columns=['n_outliers_zscore']
).reset_index(drop=True)

print(f"  Heatmap : echantillon de {len(df_outliers_sample)} cas (25 top + 25 bottom)")
viz.fig3_heatmap_zscores(df_outliers_sample, seuils)

# === FIG 4 : OK mais visualisation amelioree dans le code original ===
viz.fig4_scatter_snr_gradient(df_calib, df_brats, seuils)

# === FIG 5 : Top 50 outliers seulement pour le barplot ===
df_rapport_top = df_rapport.head(50).copy()
print(f"  Barplot outliers : top 50 cas (sur {len(df_rapport)})")
viz.fig5_resume_outliers(df_rapport_top)

# === FIG 6 : OK avec 1251 cas (boxplots robustes) ===
viz.fig6_distributions_regions(df_brats)

# Lister les fichiers generes
print(f"\n=== Fichiers generes dans {viz.FIGURES_DIR} ===")
for f in sorted(viz.FIGURES_DIR.glob('*.png')):
    size_kb = f.stat().st_size / 1024
    print(f"  - {f.name} ({size_kb:.0f} KB)")

print("\n=> Visualisations terminees.")
