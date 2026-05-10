from pathlib import Path

base = Path(r"C:\Users\yaman\data\brats\data\BraTS-GLI\ASNR-MICCAI-BraTS2023-GLI-Challenge-TrainingData")

print("=== VALIDATION BraTS-GLI TrainingData (FULL) ===\n")

cas_dirs = sorted([d for d in base.iterdir() if d.is_dir() and d.name.startswith("BraTS-GLI-")])
print(f"Total cas disponibles : {len(cas_dirs)}")

suffixes = ["-t1n.nii.gz", "-seg.nii.gz"]  # On verifie juste T1n + seg pour le run

cas_complets = []
cas_incomplets = []

for cas in cas_dirs:
    manquants = []
    for suf in suffixes:
        f = cas / (cas.name + suf)
        if not f.exists():
            manquants.append(suf)
    
    if not manquants:
        cas_complets.append(cas.name)
    else:
        cas_incomplets.append((cas.name, manquants))

print(f"Cas COMPLETS (t1n + seg) : {len(cas_complets)}")
print(f"Cas INCOMPLETS           : {len(cas_incomplets)}")

if cas_incomplets:
    print("\nCas incomplets :")
    for nom, miss in cas_incomplets[:20]:
        print(f"  - {nom} : manque {miss}")
    if len(cas_incomplets) > 20:
        print(f"  ... et {len(cas_incomplets)-20} autres")

# Sauvegarder le manifest complet
liste_path = Path("cas_brats_full.txt")
with open(liste_path, "w", encoding="utf-8") as f:
    f.write(f"# Base : {base}\n")
    for nom in cas_complets:
        f.write(nom + "\n")

print(f"\n=> Manifest sauvegarde : {liste_path.absolute()}")
print(f"=> {len(cas_complets)} cas pretsa traiter")
