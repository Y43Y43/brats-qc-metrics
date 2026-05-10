"""
Telechargement cible des 50 sujets ds000030 pour la calibration.
On telecharge UNIQUEMENT les fichiers T1w listes dans quality_annotations.tsv.
"""
import openneuro as on
from pathlib import Path
import pandas as pd
import time

# Configuration
DATASET = "ds000030"
TARGET_DIR = Path(r"C:\Users\yaman\data\ds000030")
TARGET_DIR.mkdir(parents=True, exist_ok=True)

# Lire le TSV pour avoir la liste exacte des sujets
df = pd.read_csv("quality_annotations.tsv", sep='\t')
sujets = df['participant_id'].unique().tolist()

print(f"=== TELECHARGEMENT CIBLE ds000030 ===\n")
print(f"Dataset       : {DATASET}")
print(f"Destination   : {TARGET_DIR}")
print(f"Nombre sujets : {len(sujets)}")
print(f"Premier       : {sujets[0]}")
print(f"Dernier       : {sujets[-1]}\n")

# Construire la liste des patterns include
# Pour chaque sujet, on prend uniquement le T1w
include_patterns = []
for sub in sujets:
    include_patterns.append(f"{sub}/anat/{sub}_T1w.nii.gz")
    include_patterns.append(f"{sub}/anat/{sub}_T1w.json")  # metadata BIDS

print(f"Patterns include : {len(include_patterns)} fichiers cibles")
print(f"Exemples :")
for p in include_patterns[:4]:
    print(f"  - {p}")
print(f"  ...\n")

# Lancer le telechargement
print("Demarrage du telechargement (peut prendre 5-15 min)...\n")
t0 = time.time()

try:
    on.download(
        dataset=DATASET,
        target_dir=str(TARGET_DIR),
        include=include_patterns,
    )
    duree = time.time() - t0
    print(f"\n=== TELECHARGEMENT TERMINE ===")
    print(f"Duree : {duree/60:.1f} minutes")
    print(f"Destination : {TARGET_DIR}")
except Exception as e:
    print(f"\nERREUR : {e}")
    print(f"Duree avant erreur : {(time.time()-t0)/60:.1f} min")
