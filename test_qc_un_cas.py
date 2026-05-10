"""
Test de qc_metrics.py sur un seul cas BraTS-GLI.
Valide l'installation et la coherence des resultats.
"""
from pathlib import Path
import time
from qc_metrics import calculer_metriques_sujet

# Premier cas valide
base = Path(r"C:\Users\yaman\data\brats\data\BraTS-GLI\ASNR-MICCAI-BraTS2023-GLI-Challenge-TrainingData")
cas_id = "BraTS-GLI-00000-000"
cas_dir = base / cas_id

chemin_t1 = cas_dir / f"{cas_id}-t1n.nii.gz"
chemin_seg = cas_dir / f"{cas_id}-seg.nii.gz"

print(f"=== TEST QC METRICS sur 1 cas ===\n")
print(f"Cas : {cas_id}")
print(f"T1n existe : {chemin_t1.exists()}")
print(f"Seg existe : {chemin_seg.exists()}\n")

t0 = time.time()
result = calculer_metriques_sujet(
    chemin_t1=chemin_t1,
    chemin_seg=chemin_seg,
    sujet_id=cas_id
)
duree = time.time() - t0

print(f"--- Resultats (calcul en {duree:.1f}s) ---")
for k, v in result.items():
    if isinstance(v, float):
        print(f"  {k:30s} : {v:.4f}")
    else:
        print(f"  {k:30s} : {v}")

print("\n--- Verifications de coherence ---")
# Le SNR du tissu sain devrait etre > SNR tumeur (signal plus stable)
if result['snr_sain'] > result['snr_tumeur']:
    print("  OK : SNR sain > SNR tumeur (attendu)")
else:
    print(f"  ATTENTION : SNR sain ({result['snr_sain']:.2f}) <= SNR tumeur ({result['snr_tumeur']:.2f})")

# L'entropie tumorale devrait etre >= entropie tissu sain (heterogeneite)
if result['entropie_tumeur'] >= result['entropie_sain']:
    print("  OK : Entropie tumeur >= entropie sain (attendu)")
else:
    print(f"  ATTENTION : Entropie tumeur ({result['entropie_tumeur']:.2f}) < entropie sain ({result['entropie_sain']:.2f})")

# Volume tumoral non nul
if result['volume_tumeur_voxels'] > 0:
    pct = 100 * result['volume_tumeur_voxels'] / result['volume_cerveau_voxels']
    print(f"  OK : Volume tumoral = {result['volume_tumeur_voxels']} voxels ({pct:.1f}% du cerveau)")
else:
    print("  ATTENTION : Volume tumoral nul")
