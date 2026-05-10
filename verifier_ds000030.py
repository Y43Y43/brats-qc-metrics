"""
Verification structure ds000030
"""
from pathlib import Path
import pandas as pd

TARGET_DIR = Path(r"C:\Users\yaman\data\ds000030")
df = pd.read_csv("quality_annotations.tsv", sep='\t')

print(f"=== VERIFICATION ds000030 ===\n")
print(f"Dossier : {TARGET_DIR}")
print(f"Existe  : {TARGET_DIR.exists()}\n")

# Lister les sous-dossiers sub-XXXXX
sub_dirs = sorted([d for d in TARGET_DIR.iterdir() if d.is_dir() and d.name.startswith("sub-")])
print(f"Sous-dossiers sub-* : {len(sub_dirs)}")

# Verifier la presence des T1w pour chaque sujet du TSV
sujets_attendus = df['participant_id'].tolist()
trouves = 0
manquants = []
total_size = 0

for sub in sujets_attendus:
    t1w = TARGET_DIR / sub / "anat" / f"{sub}_T1w.nii.gz"
    if t1w.exists():
        trouves += 1
        total_size += t1w.stat().st_size
    else:
        manquants.append(sub)

print(f"\nT1w trouves    : {trouves}/{len(sujets_attendus)}")
print(f"Taille totale  : {total_size/(1024**2):.1f} MB")

if manquants:
    print(f"\nT1w manquants  : {len(manquants)}")
    for m in manquants[:5]:
        print(f"  - {m}")

# Exemple de structure
if trouves > 0:
    exemple_sub = sujets_attendus[0]
    exemple_dir = TARGET_DIR / exemple_sub / "anat"
    print(f"\nStructure exemple ({exemple_sub}) :")
    for f in sorted(exemple_dir.iterdir()):
        size_mb = f.stat().st_size / (1024**2)
        print(f"  - {f.name} ({size_mb:.2f} MB)")

# Lister aussi les fichiers BIDS de premier niveau
print(f"\nFichiers BIDS racine :")
for f in sorted(TARGET_DIR.iterdir()):
    if f.is_file():
        print(f"  - {f.name}")

print(f"\n=> Pret pour la calibration : {trouves == 50}")
