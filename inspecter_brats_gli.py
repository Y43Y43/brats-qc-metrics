from pathlib import Path

base = Path(r"C:\Users\yaman\data\brats\data\BraTS-GLI")

print(f"Inspection de : {base}\n")

# Niveau 1 : contenu direct
items_n1 = sorted(list(base.iterdir()))
print(f"Niveau 1 - {len(items_n1)} elements :")
for item in items_n1[:10]:
    type_str = "DIR " if item.is_dir() else "FILE"
    print(f"  [{type_str}] {item.name}")
if len(items_n1) > 10:
    print(f"  ... et {len(items_n1)-10} autres")

# Niveau 2 : si le premier element est un dossier, on l'explore
print()
premier_dir = next((i for i in items_n1 if i.is_dir()), None)
if premier_dir:
    items_n2 = sorted(list(premier_dir.iterdir()))
    print(f"Niveau 2 (dans {premier_dir.name}) - {len(items_n2)} elements :")
    for item in items_n2[:10]:
        type_str = "DIR " if item.is_dir() else "FILE"
        print(f"  [{type_str}] {item.name}")
    if len(items_n2) > 10:
        print(f"  ... et {len(items_n2)-10} autres")

# Recherche recursive de fichiers .nii.gz pour trouver le bon niveau
print("\nRecherche d'un fichier .nii.gz pour identifier la hierarchie :")
nii_files = list(base.rglob("*.nii.gz"))
if nii_files:
    exemple = nii_files[0]
    print(f"  Exemple trouve : {exemple}")
    print(f"  Dossier parent : {exemple.parent}")
    print(f"  Profondeur depuis BraTS-GLI : {len(exemple.relative_to(base).parts)}")
