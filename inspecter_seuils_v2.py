"""Comparaison des seuils v1 vs v2 (BraTS QC).

Auteur : Y43, doctorant en informatique cognitive (UQAM, DIC938R).
"""
import json
from pathlib import Path

p_v1 = Path("results_calibration/seuils_calibres.json")
p_v2 = Path("results_calibration/seuils_calibres_v2.json")

s_v1 = json.loads(p_v1.read_text())
s_v2 = json.loads(p_v2.read_text())

print("=== Comparaison seuils v1 vs v2 (ds000030, 20 sujets 'include') ===\n")
print(f"{'Metrique':22s} {'mu_v1':>10s} {'mu_v2':>10s} {'sigma_v1':>10s} {'sigma_v2':>10s} {'delta_mu_%':>12s}")
print("-" * 80)
metriques_communes = sorted(set(s_v1.keys()) & set(s_v2.keys()))
for m in metriques_communes:
    mu1, mu2 = s_v1[m]["moyenne"], s_v2[m]["moyenne"]
    si1, si2 = s_v1[m]["ecart_type"], s_v2[m]["ecart_type"]
    delta = 100 * (mu2 - mu1) / mu1 if mu1 != 0 else float("nan")
    print(f"{m:22s} {mu1:10.3f} {mu2:10.3f} {si1:10.3f} {si2:10.3f} {delta:+11.1f}%")

print("\n--- Nouvelle metrique v2 ---")
if "bruit_rim_std" in s_v2:
    s = s_v2["bruit_rim_std"]
    print(f"  bruit_rim_std : mu={s['moyenne']:.3f} sigma={s['ecart_type']:.3f}")
    print(f"  Plage z-score normale : [{s['z_low']:.3f}, {s['z_high']:.3f}]")
    print(f"  Plage percentiles     : [{s['p5']:.3f}, {s['p95']:.3f}]")

print("\n--- Seuils v2 detailles ---")
for m, s in s_v2.items():
    print(f"\n{m}:")
    print(f"  mu={s['moyenne']:.3f} | sigma={s['ecart_type']:.3f} | n={s['n']}")
    print(f"  z [{s['z_low']:.3f}, {s['z_high']:.3f}]  |  P5/P95 [{s['p5']:.3f}, {s['p95']:.3f}]")
