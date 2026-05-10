#!/usr/bin/env python3
"""
Étape 8 — Visualisations des résultats QC

Ce script génère les visualisations suivantes :
    1. Boxplots : distributions des métriques par dataset et par label de qualité
    2. Heatmap : matrice des z-scores par sujet et métrique (BraTS)
    3. Scatter plots : comparaison des métriques calibration vs BraTS
    4. Résumé visuel des outliers détectés

Auteur : Manus AI
Date : Mai 2026
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import json
from pathlib import Path

# === Configuration ===
RESULTS_DIR = Path('/home/ubuntu/project/results')
FIGURES_DIR = Path('/home/ubuntu/project/figures')
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Style global
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.dpi'] = 150
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 10


def charger_donnees():
    """Charge toutes les données nécessaires aux visualisations."""
    df_calib = pd.read_csv(RESULTS_DIR / 'calibration_metriques.csv')
    df_brats = pd.read_csv(RESULTS_DIR / 'brats_metriques.csv')
    df_outliers = pd.read_csv(RESULTS_DIR / 'brats_outliers_detail.csv')
    df_rapport = pd.read_csv(RESULTS_DIR / 'brats_rapport_outliers.csv')
    
    with open(RESULTS_DIR / 'seuils_calibres.json', 'r') as f:
        seuils = json.load(f)
    
    return df_calib, df_brats, df_outliers, df_rapport, seuils


def fig1_boxplots_comparaison(df_calib, df_brats, seuils):
    """
    Figure 1 : Boxplots comparant les distributions calibration vs BraTS
    pour les 4 métriques sur la région cerveau entier.
    """
    metriques = ['snr_cerveau', 'entropie_cerveau', 'gradient_cerveau', 'cv_bruit_cerveau']
    titres = ['SNR (Cerveau)', 'Entropie (Cerveau)', 'Gradient (Cerveau)', 'CV Bruit (Cerveau)']
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Comparaison des distributions : Calibration (ds000030) vs BraTS 2023', 
                 fontsize=14, fontweight='bold')
    
    for idx, (met, titre) in enumerate(zip(metriques, titres)):
        ax = axes[idx // 2, idx % 2]
        
        # Préparer les données
        calib_vals = df_calib[met].dropna()
        brats_vals = df_brats[met].dropna()
        
        data_plot = pd.DataFrame({
            'Valeur': pd.concat([calib_vals, brats_vals], ignore_index=True),
            'Dataset': ['Calibration (ds000030)'] * len(calib_vals) + ['BraTS 2023'] * len(brats_vals)
        })
        
        # Boxplot
        sns.boxplot(data=data_plot, x='Dataset', y='Valeur', ax=ax, 
                    palette=['#3498db', '#e74c3c'], width=0.5)
        
        # Ajouter les seuils calibrés
        if met in seuils:
            ax.axhline(y=seuils[met]['zscore_bas'], color='orange', linestyle='--', 
                      alpha=0.7, label=f"Seuil Z±2")
            ax.axhline(y=seuils[met]['zscore_haut'], color='orange', linestyle='--', alpha=0.7)
            ax.axhline(y=seuils[met]['percentile_5'], color='green', linestyle=':', 
                      alpha=0.7, label=f"P5/P95")
            ax.axhline(y=seuils[met]['percentile_95'], color='green', linestyle=':', alpha=0.7)
        
        ax.set_title(titre, fontweight='bold')
        ax.set_xlabel('')
        ax.set_ylabel('Valeur')
        ax.legend(loc='upper right', fontsize=8)
    
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'fig1_boxplots_comparaison.png', bbox_inches='tight')
    plt.close()
    print("  Figure 1 sauvegardée : fig1_boxplots_comparaison.png")


def fig2_boxplots_par_qualite(df_calib):
    """
    Figure 2 : Boxplots des métriques par label de qualité (calibration).
    """
    metriques = ['snr_cerveau', 'entropie_cerveau', 'gradient_cerveau', 'cv_bruit_cerveau']
    titres = ['SNR (Cerveau)', 'Entropie (Cerveau)', 'Gradient (Cerveau)', 'CV Bruit (Cerveau)']
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Distribution des métriques par label de qualité (Calibration ds000030)', 
                 fontsize=14, fontweight='bold')
    
    palette = {'include': '#2ecc71', 'uncertain': '#f39c12', 'exclude': '#e74c3c'}
    ordre = ['include', 'uncertain', 'exclude']
    
    for idx, (met, titre) in enumerate(zip(metriques, titres)):
        ax = axes[idx // 2, idx % 2]
        
        sns.boxplot(data=df_calib, x='quality_label', y=met, ax=ax,
                    palette=palette, order=ordre, width=0.5)
        sns.stripplot(data=df_calib, x='quality_label', y=met, ax=ax,
                     color='black', alpha=0.4, size=4, order=ordre)
        
        ax.set_title(titre, fontweight='bold')
        ax.set_xlabel('Label de qualité')
        ax.set_ylabel('Valeur')
    
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'fig2_boxplots_par_qualite.png', bbox_inches='tight')
    plt.close()
    print("  Figure 2 sauvegardée : fig2_boxplots_par_qualite.png")


def fig3_heatmap_zscores(df_outliers, seuils):
    """
    Figure 3 : Heatmap des z-scores des cas BraTS par métrique.
    """
    colonnes_zscore = [c for c in df_outliers.columns if c.endswith('_zscore') and 'outlier' not in c]
    
    if not colonnes_zscore:
        print("  Figure 3 : Pas de colonnes z-score trouvées, skip")
        return
    
    # Préparer la matrice
    df_heat = df_outliers[['sujet_id'] + colonnes_zscore].set_index('sujet_id')
    df_heat.columns = [c.replace('_zscore', '').replace('_', '\n') for c in df_heat.columns]
    
    # Limiter les z-scores extrêmes pour la visualisation
    df_heat = df_heat.clip(-5, 5)
    
    fig, ax = plt.subplots(figsize=(16, 12))
    
    sns.heatmap(df_heat, cmap='RdYlGn_r', center=0, vmin=-4, vmax=4,
                annot=True, fmt='.1f', linewidths=0.5, ax=ax,
                cbar_kws={'label': 'Z-score (vs calibration)'})
    
    ax.set_title('Heatmap des Z-scores : Cas BraTS vs Seuils Calibrés\n'
                 '(Rouge = outlier haut, Vert = dans la norme)', 
                 fontsize=14, fontweight='bold')
    ax.set_xlabel('Métrique')
    ax.set_ylabel('Cas BraTS')
    
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'fig3_heatmap_zscores.png', bbox_inches='tight')
    plt.close()
    print("  Figure 3 sauvegardée : fig3_heatmap_zscores.png")


def fig4_scatter_snr_gradient(df_calib, df_brats, seuils):
    """
    Figure 4 : Scatter plot SNR vs Gradient avec zones de seuils.
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    
    # Panel 1 : SNR vs Gradient (cerveau)
    ax = axes[0]
    
    # Calibration par label
    palette = {'include': '#2ecc71', 'uncertain': '#f39c12', 'exclude': '#e74c3c'}
    for label, color in palette.items():
        mask = df_calib['quality_label'] == label
        ax.scatter(df_calib.loc[mask, 'snr_cerveau'], 
                  df_calib.loc[mask, 'gradient_cerveau'],
                  c=color, alpha=0.7, s=60, label=f'Calib: {label}',
                  edgecolors='white', linewidth=0.5)
    
    # BraTS
    ax.scatter(df_brats['snr_cerveau'], df_brats['gradient_cerveau'],
              c='#9b59b6', marker='D', s=60, alpha=0.7, label='BraTS 2023',
              edgecolors='white', linewidth=0.5)
    
    # Seuils
    if 'snr_cerveau' in seuils:
        ax.axvline(x=seuils['snr_cerveau']['zscore_bas'], color='orange', 
                  linestyle='--', alpha=0.5)
        ax.axvline(x=seuils['snr_cerveau']['zscore_haut'], color='orange', 
                  linestyle='--', alpha=0.5)
    if 'gradient_cerveau' in seuils:
        ax.axhline(y=seuils['gradient_cerveau']['zscore_bas'], color='orange', 
                  linestyle='--', alpha=0.5)
        ax.axhline(y=seuils['gradient_cerveau']['zscore_haut'], color='orange', 
                  linestyle='--', alpha=0.5)
    
    ax.set_xlabel('SNR (Cerveau)')
    ax.set_ylabel('Gradient (Cerveau)')
    ax.set_title('SNR vs Gradient — Calibration et BraTS', fontweight='bold')
    ax.legend(loc='upper right', fontsize=8)
    
    # Panel 2 : SNR vs CV Bruit
    ax = axes[1]
    
    for label, color in palette.items():
        mask = df_calib['quality_label'] == label
        ax.scatter(df_calib.loc[mask, 'snr_cerveau'], 
                  df_calib.loc[mask, 'cv_bruit_cerveau'],
                  c=color, alpha=0.7, s=60, label=f'Calib: {label}',
                  edgecolors='white', linewidth=0.5)
    
    ax.scatter(df_brats['snr_cerveau'], df_brats['cv_bruit_cerveau'],
              c='#9b59b6', marker='D', s=60, alpha=0.7, label='BraTS 2023',
              edgecolors='white', linewidth=0.5)
    
    if 'snr_cerveau' in seuils:
        ax.axvline(x=seuils['snr_cerveau']['zscore_bas'], color='orange', 
                  linestyle='--', alpha=0.5)
        ax.axvline(x=seuils['snr_cerveau']['zscore_haut'], color='orange', 
                  linestyle='--', alpha=0.5)
    if 'cv_bruit_cerveau' in seuils:
        ax.axhline(y=seuils['cv_bruit_cerveau']['zscore_bas'], color='orange', 
                  linestyle='--', alpha=0.5)
        ax.axhline(y=seuils['cv_bruit_cerveau']['zscore_haut'], color='orange', 
                  linestyle='--', alpha=0.5)
    
    ax.set_xlabel('SNR (Cerveau)')
    ax.set_ylabel('CV Bruit (Cerveau)')
    ax.set_title('SNR vs CV Bruit — Calibration et BraTS', fontweight='bold')
    ax.legend(loc='upper right', fontsize=8)
    
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'fig4_scatter_snr_gradient.png', bbox_inches='tight')
    plt.close()
    print("  Figure 4 sauvegardée : fig4_scatter_snr_gradient.png")


def fig5_resume_outliers(df_rapport):
    """
    Figure 5 : Résumé visuel du nombre d'outliers par cas BraTS.
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))
    
    # Panel 1 : Barplot du nombre d'outliers par cas
    ax = axes[0]
    df_sorted = df_rapport.sort_values('n_outliers_zscore', ascending=True)
    
    colors = df_sorted['statut_zscore'].map({
        'OK': '#2ecc71', 'ATTENTION': '#f39c12', 'SUSPECT': '#e74c3c'
    })
    
    ax.barh(range(len(df_sorted)), df_sorted['n_outliers_zscore'], 
            color=colors, edgecolor='white', linewidth=0.5)
    ax.set_yticks(range(len(df_sorted)))
    ax.set_yticklabels(df_sorted['sujet_id'], fontsize=7)
    ax.set_xlabel('Nombre de métriques outliers (Z-score)')
    ax.set_title('Outliers par cas BraTS (méthode Z-score)', fontweight='bold')
    ax.axvline(x=3, color='red', linestyle='--', alpha=0.5, label='Seuil SUSPECT')
    ax.axvline(x=1, color='orange', linestyle='--', alpha=0.5, label='Seuil ATTENTION')
    ax.legend(loc='lower right')
    
    # Panel 2 : Pie chart des statuts
    ax = axes[1]
    statuts = df_rapport['statut_zscore'].value_counts()
    colors_pie = {'OK': '#2ecc71', 'ATTENTION': '#f39c12', 'SUSPECT': '#e74c3c'}
    
    wedges, texts, autotexts = ax.pie(
        statuts.values, labels=statuts.index, 
        colors=[colors_pie.get(s, '#95a5a6') for s in statuts.index],
        autopct='%1.0f%%', startangle=90, textprops={'fontsize': 12}
    )
    ax.set_title('Répartition des statuts QC (BraTS 2023)', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'fig5_resume_outliers.png', bbox_inches='tight')
    plt.close()
    print("  Figure 5 sauvegardée : fig5_resume_outliers.png")


def fig6_distributions_regions(df_brats):
    """
    Figure 6 : Comparaison des métriques entre les 3 régions (BraTS).
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Distribution des métriques par région (BraTS 2023)', 
                 fontsize=14, fontweight='bold')
    
    metriques_base = ['snr', 'entropie', 'gradient', 'cv_bruit']
    titres = ['SNR', 'Entropie', 'Gradient', 'CV Bruit']
    regions = ['cerveau', 'sain', 'tumeur']
    couleurs = {'cerveau': '#3498db', 'sain': '#2ecc71', 'tumeur': '#e74c3c'}
    
    for idx, (met, titre) in enumerate(zip(metriques_base, titres)):
        ax = axes[idx // 2, idx % 2]
        
        data_regions = []
        for region in regions:
            col = f'{met}_{region}'
            if col in df_brats.columns:
                vals = df_brats[col].dropna()
                for v in vals:
                    data_regions.append({'Valeur': v, 'Région': region.capitalize()})
        
        if data_regions:
            df_plot = pd.DataFrame(data_regions)
            sns.boxplot(data=df_plot, x='Région', y='Valeur', ax=ax,
                       palette=[couleurs[r] for r in regions if f'{met}_{r}' in df_brats.columns],
                       width=0.5)
            sns.stripplot(data=df_plot, x='Région', y='Valeur', ax=ax,
                         color='black', alpha=0.3, size=4)
        
        ax.set_title(titre, fontweight='bold')
        ax.set_xlabel('')
        ax.set_ylabel('Valeur')
    
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'fig6_distributions_regions.png', bbox_inches='tight')
    plt.close()
    print("  Figure 6 sauvegardée : fig6_distributions_regions.png")


def main():
    """Fonction principale de génération des visualisations."""
    
    print("=" * 60)
    print("GÉNÉRATION DES VISUALISATIONS")
    print("=" * 60)
    
    # Charger les données
    print("\nChargement des données...")
    df_calib, df_brats, df_outliers, df_rapport, seuils = charger_donnees()
    print(f"  Calibration : {len(df_calib)} sujets")
    print(f"  BraTS : {len(df_brats)} cas")
    
    # Générer les figures
    print("\nGénération des figures...")
    
    fig1_boxplots_comparaison(df_calib, df_brats, seuils)
    fig2_boxplots_par_qualite(df_calib)
    fig3_heatmap_zscores(df_outliers, seuils)
    fig4_scatter_snr_gradient(df_calib, df_brats, seuils)
    fig5_resume_outliers(df_rapport)
    fig6_distributions_regions(df_brats)
    
    print(f"\n  Toutes les figures sauvegardées dans : {FIGURES_DIR}")
    
    # Liste des fichiers générés
    print("\n  Fichiers générés :")
    for f in sorted(FIGURES_DIR.glob('*.png')):
        print(f"    - {f.name}")
    
    print("\n" + "=" * 60)
    print("VISUALISATIONS TERMINÉES")
    print("=" * 60)


if __name__ == '__main__':
    main()
