"""
Inspection statistique du CSV produit par run_qc_full.py.
Valide la qualite des donnees avant calibration et application.
"""
import pandas as pd
import numpy as np
from pathlib import Path

csv_path = Path("brats_full_metrics.csv")
df = pd.read_csv(csv_path)

print(f"=== INSPECTION : {csv_path} ===\n")
print(f"Nombre de cas : {len(df)}")
print(f"Nombre de colonnes : {len(df.columns)}")
print(f"\nColonnes : {list(df.columns)}\n")

# Verifier les NaN
print("=== Valeurs manquantes (NaN) par colonne ===")
nan_counts = df.isna().sum()
nan_summary = nan_counts[nan_counts > 0]
if len(nan_summary) > 0:
    print(nan_summary.to_string())
else:
    print("Aucune valeur manquante !")

# Cas sans tumeur detectee
sans_tumeur = (df['volume_tumeur_voxels'] == 0).sum()
print(f"\nCas sans tumeur detectee : {sans_tumeur}")

# Statistiques sur les 4 metriques x 3 regions
print("\n=== Statistiques descriptives - Cerveau entier ===")
cols_cerveau = ['snr_cerveau', 'entropie_cerveau', 'gradient_cerveau', 'cv_bruit_cerveau']
print(df[cols_cerveau].describe().round(3))

print("\n=== Statistiques descriptives - Tissu sain ===")
cols_sain = ['snr_sain', 'entropie_sain', 'gradient_sain', 'cv_bruit_sain']
print(df[cols_sain].describe().round(3))

print("\n=== Statistiques descriptives - Zone tumorale ===")
cols_tumeur = ['snr_tumeur', 'entropie_tumeur', 'gradient_tumeur', 'cv_bruit_tumeur']
print(df[cols_tumeur].describe().round(3))

# Volumes tumoraux
print("\n=== Distribution des volumes tumoraux (voxels = mm3) ===")
vol = df['volume_tumeur_voxels']
print(f"  Min     : {vol.min():>10,}")
print(f"  Q25     : {vol.quantile(0.25):>10,.0f}")
print(f"  Mediane : {vol.median():>10,.0f}")
print(f"  Q75     : {vol.quantile(0.75):>10,.0f}")
print(f"  Max     : {vol.max():>10,}")
print(f"  Moyenne : {vol.mean():>10,.0f}")

# Volumes en pourcentage du cerveau
df['pct_tumeur'] = 100 * df['volume_tumeur_voxels'] / df['volume_cerveau_voxels']
print(f"\n=== Pourcentage tumeur / cerveau ===")
print(f"  Mediane : {df['pct_tumeur'].median():.2f}%")
print(f"  Min-Max : {df['pct_tumeur'].min():.2f}% - {df['pct_tumeur'].max():.2f}%")

# Verifications de coherence sur l'ensemble
print("\n=== Verifications de coherence scientifique (sur 1251 cas) ===")
n_snr_ok = (df['snr_sain'] > df['snr_tumeur']).sum()
n_ent_ok = (df['entropie_tumeur'] > df['entropie_sain']).sum()
print(f"  SNR sain > SNR tumeur     : {n_snr_ok}/{len(df)} ({100*n_snr_ok/len(df):.1f}%)")
print(f"  Entropie tumeur > sain    : {n_ent_ok}/{len(df)} ({100*n_ent_ok/len(df):.1f}%)")

# Detection rapide d'outliers extremes
print("\n=== Detection rapide d'outliers (z-score > 3) ===")
for col in cols_cerveau:
    z = np.abs((df[col] - df[col].mean()) / df[col].std())
    n_out = (z > 3).sum()
    print(f"  {col:25s} : {n_out} cas extremes (|z| > 3)")

print(f"\n=> CSV pret pour calibration et application")
