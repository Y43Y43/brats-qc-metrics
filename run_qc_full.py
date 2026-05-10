"""
Run complet du pipeline QC sur tous les cas BraTS-GLI TrainingData.
Sauvegarde incrementale toutes les 50 cas (securite anti-crash).
"""
from pathlib import Path
import time
import pandas as pd
from qc_metrics import calculer_metriques_sujet

# Configuration
base = Path(r"C:\Users\yaman\data\brats\data\BraTS-GLI\ASNR-MICCAI-BraTS2023-GLI-Challenge-TrainingData")
manifest_path = Path("cas_brats_full.txt")
output_csv = Path("brats_full_metrics.csv")
checkpoint_every = 50  # Sauvegarde tous les 50 cas

# Lire le manifeste
with open(manifest_path, "r", encoding="utf-8") as f:
    cas_list = [line.strip() for line in f if line.strip() and not line.startswith("#")]

n_total = len(cas_list)
print(f"=== RUN COMPLET QC - {n_total} cas ===")
print(f"Estimation : {n_total * 2.4 / 60:.1f} minutes\n")

# Reprendre depuis un run interrompu si checkpoint existe
deja_traites = set()
resultats = []
if output_csv.exists():
    df_existant = pd.read_csv(output_csv)
    deja_traites = set(df_existant['sujet_id'].tolist())
    resultats = df_existant.to_dict('records')
    print(f"Reprise : {len(deja_traites)} cas deja traites, repris depuis {output_csv}\n")

t_start = time.time()
errors = []

for i, cas_id in enumerate(cas_list, 1):
    if cas_id in deja_traites:
        continue
    
    cas_dir = base / cas_id
    chemin_t1 = cas_dir / f"{cas_id}-t1n.nii.gz"
    chemin_seg = cas_dir / f"{cas_id}-seg.nii.gz"
    
    t0 = time.time()
    try:
        r = calculer_metriques_sujet(chemin_t1, chemin_seg, sujet_id=cas_id)
        resultats.append(r)
        duree_cas = time.time() - t0
        
        # Estimation temps restant
        n_traites = len(resultats)
        n_restant = n_total - n_traites
        duree_moyenne = (time.time() - t_start) / max(n_traites - len(deja_traites), 1)
        eta_min = n_restant * duree_moyenne / 60
        
        print(f"[{i}/{n_total}] {cas_id} OK ({duree_cas:.1f}s) | ETA: {eta_min:.1f}min", flush=True)
        
    except Exception as e:
        msg = f"ERREUR {cas_id}: {e}"
        print(f"[{i}/{n_total}] {msg}", flush=True)
        errors.append({'sujet_id': cas_id, 'erreur': str(e)})
    
    # Sauvegarde incrementale
    if i % checkpoint_every == 0:
        pd.DataFrame(resultats).to_csv(output_csv, index=False)
        print(f"  >> Checkpoint sauvegarde ({len(resultats)} cas) <<", flush=True)

# Sauvegarde finale
pd.DataFrame(resultats).to_csv(output_csv, index=False)
if errors:
    pd.DataFrame(errors).to_csv("brats_full_errors.csv", index=False)

duree_totale = time.time() - t_start
print(f"\n=== TERMINE ===")
print(f"Duree totale : {duree_totale/60:.1f} minutes")
print(f"Cas traites avec succes : {len(resultats)}")
print(f"Cas en erreur : {len(errors)}")
print(f"Resultats : {output_csv.absolute()}")
