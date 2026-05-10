"""
Test de qc_metrics.py sur 5 cas BraTS-GLI.
Valide la stabilite et estime le temps total.
"""
from pathlib import Path
import time
import pandas as pd
from qc_metrics import calculer_metriques_sujet

base = Path(r"C:\Users\yaman\data\brats\data\BraTS-GLI\ASNR-MICCAI-BraTS2023-GLI-Challenge-TrainingData")

# Lire les 5 premiers cas du manifest
with open("cas_brats_selectionnes.txt", "r") as f:
    cas_list = [line.strip() for line in f if line.strip() and not line.startswith("#")]

cas_test = cas_list[:5]
print(f"=== TEST QC METRICS sur {len(cas_test)} cas ===\n")

resultats = []
t_total = time.time()

for i, cas_id in enumerate(cas_test, 1):
    cas_dir = base / cas_id
    chemin_t1 = cas_dir / f"{cas_id}-t1n.nii.gz"
    chemin_seg = cas_dir / f"{cas_id}-seg.nii.gz"
    
    print(f"[{i}/{len(cas_test)}] {cas_id}...", end=" ", flush=True)
    
    t0 = time.time()
    try:
        r = calculer_metriques_sujet(chemin_t1, chemin_seg, sujet_id=cas_id)
        resultats.append(r)
        print(f"OK ({time.time()-t0:.1f}s)")
    except Exception as e:
        print(f"ERREUR : {e}")

duree = time.time() - t_total
print(f"\nDuree totale : {duree:.1f}s ({duree/len(cas_test):.1f}s par cas)")
print(f"Estimation 130 cas : {duree/len(cas_test)*130/60:.1f} minutes")

# Resume des resultats
df = pd.DataFrame(resultats)
print(f"\n--- Resume statistique (cerveau entier) ---")
cols = ['snr_cerveau', 'entropie_cerveau', 'gradient_cerveau', 'cv_bruit_cerveau']
print(df[cols].describe().round(3))

print(f"\n--- Volumes tumoraux ---")
print(df[['sujet_id', 'volume_tumeur_voxels']].to_string(index=False))

# Sauvegarder pour comparaison
df.to_csv("test_5_cas_resultats.csv", index=False)
print(f"\nResultats sauvegardes : test_5_cas_resultats.csv")
