"""Run complet de qc_metrics_v2 sur les 1251 cas BraTS-GLI.

Auteur : Y43, doctorant en informatique cognitive (UQAM, DIC938R).
"""
from pathlib import Path
import time
import pandas as pd
from qc_metrics_v2 import calculer_metriques_sujet_v2

BASE = Path(r"C:\Users\yaman\data\brats\data\BraTS-GLI"
            r"\ASNR-MICCAI-BraTS2023-GLI-Challenge-TrainingData")
MANIFEST = Path("cas_brats_full.txt")
OUTPUT = Path("brats_full_metrics_v2.csv")
ERRORS = Path("brats_full_errors_v2.csv")
CHECKPOINT_EVERY = 50

with open(MANIFEST) as f:
    cas_list = [l.strip() for l in f if l.strip() and not l.startswith("#")]
print(f"Cas a traiter : {len(cas_list)}")

# Reprise sur checkpoint si CSV deja partiel
deja = set()
if OUTPUT.exists():
    df_part = pd.read_csv(OUTPUT)
    deja = set(df_part["sujet_id"].tolist())
    print(f"Reprise : {len(deja)} cas deja traites.")

resultats, erreurs = [], []
start = time.time()
for i, cid in enumerate(cas_list, 1):
    if cid in deja:
        continue
    cas_dir = BASE / cid
    t1 = cas_dir / f"{cid}-t1n.nii.gz"
    seg = cas_dir / f"{cid}-seg.nii.gz"
    t0 = time.time()
    try:
        r = calculer_metriques_sujet_v2(t1, seg if seg.exists() else None, sujet_id=cid)
        resultats.append(r)
        elapsed = time.time() - start
        eta = elapsed / max(1, len(resultats)) * (len(cas_list) - i) / 60
        print(f"[{i}/{len(cas_list)}] {cid} OK ({time.time()-t0:.1f}s) | ETA: {eta:.1f}min")
    except Exception as e:
        erreurs.append({"sujet_id": cid, "erreur": str(e)})
        print(f"[{i}/{len(cas_list)}] {cid} ERROR: {e}")

    if len(resultats) % CHECKPOINT_EVERY == 0 and resultats:
        df = pd.DataFrame(resultats)
        if deja and OUTPUT.exists():
            df_old = pd.read_csv(OUTPUT)
            df = pd.concat([df_old, df], ignore_index=True)
        df.to_csv(OUTPUT, index=False)
        print(f"  >> Checkpoint sauvegarde ({len(df)} cas) <<")

# Sauvegarde finale
if resultats:
    df = pd.DataFrame(resultats)
    if deja and OUTPUT.exists():
        df_old = pd.read_csv(OUTPUT)
        df = pd.concat([df_old, df], ignore_index=True)
    df.to_csv(OUTPUT, index=False)
if erreurs:
    pd.DataFrame(erreurs).to_csv(ERRORS, index=False)

duree = (time.time() - start) / 60
print(f"\n=== TERMINE ===")
print(f"Duree : {duree:.1f} min")
print(f"Cas traites avec succes : {len(resultats)}")
print(f"Cas en erreur           : {len(erreurs)}")
print(f"Resultats : {OUTPUT.absolute()}")
