"""
Wrapper pour executer calibration.py avec les chemins Windows.
"""
import pandas as pd
from pathlib import Path
import calibration_win as calib

# Patcher les chemins
calib.CALIBRATION_DIR = Path(r"C:\Users\yaman\data\ds000030")
calib.ANNOTATIONS_FILE = Path("quality_annotations.tsv")
calib.RESULTS_DIR = Path("results_calibration")
calib.RESULTS_DIR.mkdir(parents=True, exist_ok=True)

print(f"=== CHEMINS PATCHES ===")
print(f"CALIBRATION_DIR  : {calib.CALIBRATION_DIR}")
print(f"ANNOTATIONS_FILE : {calib.ANNOTATIONS_FILE}")
print(f"RESULTS_DIR      : {calib.RESULTS_DIR}\n")

# Patcher la fonction preparer_liste_sujets_calibration
# pour gerer le prefixe "nifti/" du TSV
def preparer_liste_sujets_calibration_win():
    """Version adaptee : enleve le prefixe 'nifti/' du chemin."""
    annotations = pd.read_csv(calib.ANNOTATIONS_FILE, sep='\t')
    
    liste_sujets = []
    manquants = []
    for _, row in annotations.iterrows():
        sujet_id = row['participant_id']
        # Enlever le prefixe "nifti/" si present
        nifti_rel = row['nifti_path']
        if nifti_rel.startswith("nifti/"):
            nifti_rel = nifti_rel[len("nifti/"):]
        chemin_t1 = calib.CALIBRATION_DIR / nifti_rel
        
        if chemin_t1.exists():
            liste_sujets.append({
                'sujet_id': sujet_id,
                'chemin_t1': str(chemin_t1),
                'quality_label': row['quality_label'],
                'quality_rating': row['quality_rating']
            })
        else:
            manquants.append((sujet_id, str(chemin_t1)))
    
    if manquants:
        print(f"ATTENTION : {len(manquants)} sujets introuvables :")
        for sid, p in manquants[:5]:
            print(f"  - {sid} : {p}")
    
    return liste_sujets

# Remplacer la fonction d'origine
calib.preparer_liste_sujets_calibration = preparer_liste_sujets_calibration_win

# Lancer la calibration
df_metriques, seuils, df_eval = calib.main()

print(f"\n=> Calibration terminee.")
print(f"=> Seuils  : {calib.RESULTS_DIR / 'seuils_calibres.json'}")
print(f"=> Metriques : {calib.RESULTS_DIR / 'calibration_metriques.csv'}")
print(f"=> Evaluation : {calib.RESULTS_DIR / 'evaluation_seuils.csv'}")
