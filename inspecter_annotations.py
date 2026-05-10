"""
Inspection du fichier quality_annotations.tsv.
Identifie les sujets necessaires pour la calibration ds000030.
"""
import pandas as pd
from pathlib import Path

tsv = Path("quality_annotations.tsv")
df = pd.read_csv(tsv, sep='\t')

print(f"=== INSPECTION quality_annotations.tsv ===\n")
print(f"Nombre de lignes  : {len(df)}")
print(f"Colonnes          : {list(df.columns)}\n")

print("--- Apercu (5 premieres lignes) ---")
print(df.head().to_string())

print("\n--- Distribution des labels ---")
if 'quality_label' in df.columns:
    print(df['quality_label'].value_counts())

print("\n--- Statistiques par label ---")
if 'quality_rating' in df.columns:
    print(df.groupby('quality_label')['quality_rating'].describe())

print("\n--- Exemple de chemin nifti_path ---")
if 'nifti_path' in df.columns:
    for p in df['nifti_path'].head(5):
        print(f"  {p}")

# Sauvegarder la liste des sujets
print(f"\n--- Liste des sujets uniques ---")
if 'participant_id' in df.columns:
    sujets = df['participant_id'].unique()
    print(f"Total : {len(sujets)} sujets")
    print(f"Premier : {sujets[0]}")
    print(f"Dernier : {sujets[-1]}")
    
    # Sauvegarder
    with open("sujets_calibration_ids.txt", "w") as f:
        for s in sujets:
            f.write(s + "\n")
    print(f"\nIDs sauvegardes : sujets_calibration_ids.txt")
