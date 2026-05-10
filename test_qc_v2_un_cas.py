"""Test rapide de qc_metrics_v2 sur un cas BraTS-GLI.

Auteur : Y43, doctorant en informatique cognitive (UQAM, DIC938R).
"""
from pathlib import Path
import time
from qc_metrics_v2 import calculer_metriques_sujet_v2

base = Path(r"C:\Users\yaman\data\brats\data\BraTS-GLI"
            r"\ASNR-MICCAI-BraTS2023-GLI-Challenge-TrainingData")
cas_id = "BraTS-GLI-00000-000"
cas_dir = base / cas_id

print("=== TEST QC METRICS v2 sur 1 cas ===\n")
t0 = time.time()
r = calculer_metriques_sujet_v2(
    chemin_t1=cas_dir / f"{cas_id}-t1n.nii.gz",
    chemin_seg=cas_dir / f"{cas_id}-seg.nii.gz",
    sujet_id=cas_id,
)
duree = time.time() - t0

print(f"--- Resultats v2 (calcul en {duree:.1f}s) ---")
for k, v in r.items():
    if isinstance(v, float):
        print(f"  {k:25s} : {v:.4f}")
    else:
        print(f"  {k:25s} : {v}")

print("\n--- Verifications de coherence ---")
ok1 = r["snr_sain"] > r["snr_tumeur"]
ok2 = r["entropie_tumeur"] >= r["entropie_sain"]
ok3 = r["bruit_rim_voxels"] > 1000
print(f"  SNR sain > SNR tumeur            : {'OK' if ok1 else 'KO'}")
print(f"  Entropie tumeur >= sain          : {'OK' if ok2 else 'KO'}")
print(f"  Bande rim > 1000 voxels          : {'OK' if ok3 else 'KO'}")

print("\n--- Comparaison v1 vs v2 (memes donnees) ---")
print(f"  cv_bruit_cerveau v2 (sur cerveau) : {r['cv_bruit_cerveau']:.4f}")
print(f"  bruit_rim_std (nouveau)           : {r['bruit_rim_std']:.4f}")
print(f"  Volume rim                        : {r['bruit_rim_voxels']} voxels")
