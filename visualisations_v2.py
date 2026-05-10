"""Visualisations v2 BraTS QC - 6 figures pour le rapport IEEE.

Auteur : Y43, doctorant en informatique cognitive (UQAM, DIC938R).

"A picture worth a thousand metrics." -- adapte de Rimuru Tempest
"""
from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid", context="paper", font_scale=0.9)

# --- Chargement ---
RESULTS = Path("results_calibration")
FIGS = Path("figures_v2")
FIGS.mkdir(exist_ok=True)

df_brats = pd.read_csv("brats_full_metrics_v2.csv")
df_outliers = pd.read_csv(RESULTS / "brats_outliers_v2.csv")
df_calib = pd.read_csv(RESULTS / "calibration_metriques_v2.csv")
seuils = json.loads((RESULTS / "seuils_calibres_v2.json").read_text())

print(f"BraTS : {len(df_brats)} | Calib : {len(df_calib)} | Outliers : {len(df_outliers)}")

METRIQUES = ["snr_cerveau", "entropie_cerveau", "gradient_cerveau", "cv_bruit_cerveau"]
LABELS = {"snr_cerveau": "SNR", "entropie_cerveau": "Entropie",
          "gradient_cerveau": "Gradient", "cv_bruit_cerveau": "CV bruit"}


# --- Fig 1 : Boxplots comparaison BraTS vs ds000030 ---
def fig1():
    fig, axes = plt.subplots(1, 4, figsize=(14, 4))
    for ax, m in zip(axes, METRIQUES):
        data = pd.concat([
            pd.DataFrame({"Valeur": df_calib[m], "Dataset": "ds000030"}),
            pd.DataFrame({"Valeur": df_brats[m], "Dataset": "BraTS-GLI"}),
        ], ignore_index=True)
        sns.boxplot(data=data, x="Dataset", y="Valeur", hue="Dataset",
                    palette={"ds000030": "#2E86AB", "BraTS-GLI": "#E63946"},
                    legend=False, ax=ax)
        if m in seuils:
            ax.axhline(seuils[m]["z_low"], color="orange", ls="--", lw=1, label="z=±2 (calib)")
            ax.axhline(seuils[m]["z_high"], color="orange", ls="--", lw=1)
        ax.set_title(LABELS[m])
        ax.set_xlabel("")
    plt.suptitle("Fig. 1 - Distribution des metriques v2 : ds000030 (n=50) vs BraTS-GLI (n=1251)",
                 fontsize=11, y=1.02)
    plt.tight_layout()
    plt.savefig(FIGS / "fig1_boxplots_comparaison.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  fig1_boxplots_comparaison.png OK")


# --- Fig 2 : Boxplots par qualite ds000030 ---
def fig2():
    fig, axes = plt.subplots(1, 4, figsize=(14, 4))
    order = ["include", "uncertain", "exclude"]
    for ax, m in zip(axes, METRIQUES):
        sns.boxplot(data=df_calib, x="quality_label", y=m, hue="quality_label",
                    order=order, palette={"include": "#06A77D", "uncertain": "#F4A261",
                                          "exclude": "#E63946"}, legend=False, ax=ax)
        ax.set_title(LABELS[m])
        ax.set_xlabel("")
    plt.suptitle("Fig. 2 - Metriques v2 par etiquette qualite (ds000030, n=50)",
                 fontsize=11, y=1.02)
    plt.tight_layout()
    plt.savefig(FIGS / "fig2_boxplots_par_qualite.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  fig2_boxplots_par_qualite.png OK")


# --- Fig 3 : Heatmap z-scores top/bottom outliers ---
def fig3():
    cols_z = [f"{m}_z" for m in METRIQUES if f"{m}_z" in df_outliers.columns]
    if not cols_z:
        print("  fig3 SKIP (colonnes z manquantes)")
        return
    df_sorted = df_outliers.copy()
    df_sorted["z_total"] = df_sorted[cols_z].abs().sum(axis=1)
    top = df_sorted.nlargest(25, "z_total")
    bottom = df_sorted.nsmallest(25, "z_total")
    sample = pd.concat([top, bottom])
    mat = sample[cols_z].values
    labels = sample["sujet_id"].values
    fig, ax = plt.subplots(figsize=(8, 12))
    sns.heatmap(mat, yticklabels=labels, xticklabels=[LABELS[m] for m in METRIQUES],
                cmap="RdBu_r", center=0, vmin=-5, vmax=5, ax=ax, cbar_kws={"label": "z-score"})
    ax.set_title("Fig. 3 - Heatmap z-scores : 25 cas extremes + 25 cas typiques (BraTS)",
                 fontsize=10)
    plt.tight_layout()
    plt.savefig(FIGS / "fig3_heatmap_zscores.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  fig3_heatmap_zscores.png OK")


# --- Fig 4 : Scatter Mahalanobis vs SNR ---
def fig4():
    if "mahalanobis_d" not in df_outliers.columns:
        print("  fig4 SKIP (mahalanobis_d manquant)")
        return
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    axes[0].scatter(df_calib["snr_cerveau"], df_calib["gradient_cerveau"],
                    c="#2E86AB", s=30, alpha=0.7, label="ds000030")
    axes[0].scatter(df_outliers["snr_cerveau"], df_outliers["gradient_cerveau"],
                    c="#E63946", s=8, alpha=0.3, label="BraTS")
    axes[0].set_xlabel("SNR cerveau")
    axes[0].set_ylabel("Gradient cerveau")
    axes[0].set_title("(a) SNR vs Gradient")
    axes[0].legend()

    axes[1].scatter(df_outliers["snr_cerveau"], df_outliers["mahalanobis_d"],
                    c=df_outliers["mahalanobis_d"], cmap="viridis", s=8, alpha=0.6)
    axes[1].axhline(4.297, color="red", ls="--", label="seuil chi2 (p<0.001)")
    axes[1].set_xlabel("SNR cerveau (BraTS)")
    axes[1].set_ylabel("Distance de Mahalanobis")
    axes[1].set_yscale("log")
    axes[1].set_title("(b) SNR vs Mahalanobis (log)")
    axes[1].legend()
    plt.suptitle("Fig. 4 - Distance multivariee de Mahalanobis", fontsize=11, y=1.02)
    plt.tight_layout()
    plt.savefig(FIGS / "fig4_mahalanobis.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  fig4_mahalanobis.png OK")


# --- Fig 5 : Sensibilite des seuils ---
def fig5():
    p = RESULTS / "sensibilite_seuils_v2.csv"
    if not p.exists():
        print("  fig5 SKIP")
        return
    df_s = pd.read_csv(p)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(df_s["seuil_outliers_min"].astype(int), df_s["pct"],
           color=["#06A77D", "#06A77D", "#F4A261", "#F4A261", "#E63946"])
    for i, (k, pct) in enumerate(zip(df_s["seuil_outliers_min"], df_s["pct"])):
        ax.text(int(k), pct + 1, f"{pct:.1f}%", ha="center", fontsize=9)
    ax.set_xlabel("Seuil k (nb minimum d'outliers pour status SUSPECT)")
    ax.set_ylabel("% de cas BraTS classes SUSPECT")
    ax.set_title("Fig. 5 - Analyse de sensibilite du seuil de classification (n=1251)")
    ax.set_ylim(0, 110)
    plt.tight_layout()
    plt.savefig(FIGS / "fig5_sensibilite_seuils.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  fig5_sensibilite_seuils.png OK")


# --- Fig 6 : Distributions par region BraTS ---
def fig6():
    fig, axes = plt.subplots(1, 4, figsize=(14, 4))
    regions = ["cerveau", "sain", "tumeur"]
    palette = {"cerveau": "#264653", "sain": "#06A77D", "tumeur": "#E63946"}
    for ax, m_base in zip(axes, ["snr", "entropie", "gradient", "cv_bruit"]):
        rows = []
        for reg in regions:
            col = f"{m_base}_{reg}"
            if col in df_brats.columns:
                rows.append(pd.DataFrame({"Valeur": df_brats[col], "Region": reg}))
        data = pd.concat(rows, ignore_index=True)
        sns.boxplot(data=data, x="Region", y="Valeur", hue="Region",
                    palette=palette, order=regions, legend=False, ax=ax,
                    showfliers=False)
        ax.set_title(m_base.upper())
        ax.set_xlabel("")
    plt.suptitle("Fig. 6 - Distributions BraTS par region (cerveau/sain/tumeur, n=1251)",
                 fontsize=11, y=1.02)
    plt.tight_layout()
    plt.savefig(FIGS / "fig6_distributions_regions.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  fig6_distributions_regions.png OK")


if __name__ == "__main__":
    print("\nGeneration des figures v2...")
    fig1(); fig2(); fig3(); fig4(); fig5(); fig6()
    print(f"\nToutes les figures dans : {FIGS.absolute()}")
