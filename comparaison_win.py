#!/usr/bin/env python3
"""
Étape 7 — Comparaison des résultats BraTS aux seuils calibrés

Ce script confronte les métriques QC calculées sur les cas BraTS aux seuils
calibrés sur le dataset ds000030, et identifie les outliers.

Auteur : Manus AI
Date : Mai 2026
"""

import numpy as np
import pandas as pd
import json
from pathlib import Path

# === Configuration ===
RESULTS_DIR = Path('/home/ubuntu/project/results')


def charger_donnees():
    """Charge les métriques BraTS et les seuils calibrés."""
    
    df_brats = pd.read_csv(RESULTS_DIR / 'brats_metriques.csv')
    df_calib = pd.read_csv(RESULTS_DIR / 'calibration_metriques.csv')
    
    with open(RESULTS_DIR / 'seuils_calibres.json', 'r') as f:
        seuils = json.load(f)
    
    return df_brats, df_calib, seuils


def identifier_outliers(df_brats, seuils):
    """
    Identifie les outliers BraTS selon les deux méthodes de seuillage.
    
    Paramètres
    ----------
    df_brats : pandas.DataFrame
        Métriques BraTS
    seuils : dict
        Seuils calibrés
    
    Retourne
    --------
    pandas.DataFrame
        DataFrame avec colonnes d'outliers ajoutées
    """
    colonnes_metriques = [
        'snr_cerveau', 'entropie_cerveau', 'gradient_cerveau', 'cv_bruit_cerveau',
        'snr_sain', 'entropie_sain', 'gradient_sain', 'cv_bruit_sain',
        'snr_tumeur', 'entropie_tumeur', 'gradient_tumeur', 'cv_bruit_tumeur'
    ]
    
    df_outliers = df_brats.copy()
    
    for col in colonnes_metriques:
        if col not in seuils:
            # Pour les métriques tumorales, utiliser les seuils cerveau comme référence
            col_ref = col.replace('_tumeur', '_cerveau')
            if col_ref not in seuils:
                continue
            s = seuils[col_ref]
        else:
            s = seuils[col]
        
        valeurs = df_outliers[col]
        
        # Méthode Z-score
        df_outliers[f'{col}_outlier_zscore'] = (
            (valeurs < s['zscore_bas']) | (valeurs > s['zscore_haut'])
        ).astype(int)
        
        # Méthode Percentiles
        df_outliers[f'{col}_outlier_pct'] = (
            (valeurs < s['percentile_5']) | (valeurs > s['percentile_95'])
        ).astype(int)
        
        # Z-score calculé
        if s['ecart_type'] > 0:
            df_outliers[f'{col}_zscore'] = (valeurs - s['moyenne']) / s['ecart_type']
        else:
            df_outliers[f'{col}_zscore'] = 0
    
    return df_outliers


def generer_rapport_outliers(df_outliers):
    """
    Génère un rapport résumé des outliers détectés.
    
    Paramètres
    ----------
    df_outliers : pandas.DataFrame
        DataFrame avec colonnes d'outliers
    
    Retourne
    --------
    pandas.DataFrame
        Résumé par sujet
    """
    colonnes_zscore = [c for c in df_outliers.columns if c.endswith('_outlier_zscore')]
    colonnes_pct = [c for c in df_outliers.columns if c.endswith('_outlier_pct')]
    
    rapport = pd.DataFrame()
    rapport['sujet_id'] = df_outliers['sujet_id']
    rapport['n_outliers_zscore'] = df_outliers[colonnes_zscore].sum(axis=1)
    rapport['n_outliers_pct'] = df_outliers[colonnes_pct].sum(axis=1)
    rapport['n_metriques_total'] = len(colonnes_zscore)
    rapport['pct_outliers_zscore'] = (rapport['n_outliers_zscore'] / rapport['n_metriques_total'] * 100).round(1)
    rapport['pct_outliers_pct'] = (rapport['n_outliers_pct'] / rapport['n_metriques_total'] * 100).round(1)
    
    # Déterminer le statut global
    rapport['statut_zscore'] = rapport['n_outliers_zscore'].apply(
        lambda x: 'SUSPECT' if x >= 3 else ('ATTENTION' if x >= 1 else 'OK')
    )
    rapport['statut_pct'] = rapport['n_outliers_pct'].apply(
        lambda x: 'SUSPECT' if x >= 3 else ('ATTENTION' if x >= 1 else 'OK')
    )
    
    return rapport.sort_values('n_outliers_zscore', ascending=False)


def generer_comparaison_distributions(df_brats, df_calib, seuils):
    """
    Compare les distributions des métriques entre calibration et BraTS.
    
    Retourne
    --------
    pandas.DataFrame
        Tableau comparatif des distributions
    """
    colonnes_cerveau = ['snr_cerveau', 'entropie_cerveau', 'gradient_cerveau', 'cv_bruit_cerveau']
    
    comparaison = []
    for col in colonnes_cerveau:
        if col in df_calib.columns and col in df_brats.columns:
            calib_vals = df_calib[col].dropna()
            brats_vals = df_brats[col].dropna()
            
            comparaison.append({
                'metrique': col,
                'calib_moyenne': calib_vals.mean(),
                'calib_std': calib_vals.std(),
                'calib_mediane': calib_vals.median(),
                'brats_moyenne': brats_vals.mean(),
                'brats_std': brats_vals.std(),
                'brats_mediane': brats_vals.median(),
                'diff_moyenne_pct': ((brats_vals.mean() - calib_vals.mean()) / calib_vals.mean() * 100),
                'seuil_zscore_bas': seuils[col]['zscore_bas'],
                'seuil_zscore_haut': seuils[col]['zscore_haut'],
                'n_brats_hors_seuils': int(
                    ((brats_vals < seuils[col]['zscore_bas']) | 
                     (brats_vals > seuils[col]['zscore_haut'])).sum()
                )
            })
    
    return pd.DataFrame(comparaison)


def main():
    """Fonction principale de comparaison."""
    
    print("=" * 60)
    print("COMPARAISON BraTS vs SEUILS CALIBRÉS")
    print("=" * 60)
    
    # 1. Charger les données
    print("\n1. Chargement des données...")
    df_brats, df_calib, seuils = charger_donnees()
    print(f"   Cas BraTS : {len(df_brats)}")
    print(f"   Sujets calibration : {len(df_calib)}")
    print(f"   Métriques avec seuils : {len(seuils)}")
    
    # 2. Identifier les outliers
    print("\n2. Identification des outliers...")
    df_outliers = identifier_outliers(df_brats, seuils)
    
    # 3. Rapport des outliers
    print("\n3. Rapport des outliers :")
    rapport = generer_rapport_outliers(df_outliers)
    
    print(f"\n   === Résumé par statut (Z-score) ===")
    for statut in ['OK', 'ATTENTION', 'SUSPECT']:
        n = (rapport['statut_zscore'] == statut).sum()
        print(f"   {statut}: {n} cas")
    
    print(f"\n   === Top 10 cas les plus outliers ===")
    print(f"   {'Sujet':<25} {'N outliers Z':<15} {'N outliers P':<15} {'Statut':<10}")
    print(f"   {'-'*65}")
    for _, row in rapport.head(10).iterrows():
        print(f"   {row['sujet_id']:<25} {row['n_outliers_zscore']:<15} "
              f"{row['n_outliers_pct']:<15} {row['statut_zscore']:<10}")
    
    # 4. Comparaison des distributions
    print("\n4. Comparaison des distributions :")
    df_comp = generer_comparaison_distributions(df_brats, df_calib, seuils)
    
    print(f"\n   {'Métrique':<20} {'Calib moy':<12} {'BraTS moy':<12} {'Diff %':<10} {'Hors seuils':<12}")
    print(f"   {'-'*66}")
    for _, row in df_comp.iterrows():
        print(f"   {row['metrique']:<20} {row['calib_moyenne']:<12.3f} "
              f"{row['brats_moyenne']:<12.3f} {row['diff_moyenne_pct']:<10.1f} "
              f"{row['n_brats_hors_seuils']:<12}")
    
    # 5. Sauvegarder les résultats
    print("\n5. Sauvegarde des résultats...")
    
    df_outliers.to_csv(RESULTS_DIR / 'brats_outliers_detail.csv', index=False)
    rapport.to_csv(RESULTS_DIR / 'brats_rapport_outliers.csv', index=False)
    df_comp.to_csv(RESULTS_DIR / 'comparaison_distributions.csv', index=False)
    
    print(f"   - {RESULTS_DIR / 'brats_outliers_detail.csv'}")
    print(f"   - {RESULTS_DIR / 'brats_rapport_outliers.csv'}")
    print(f"   - {RESULTS_DIR / 'comparaison_distributions.csv'}")
    
    print("\n" + "=" * 60)
    print("COMPARAISON TERMINÉE")
    print("=" * 60)
    
    return df_outliers, rapport, df_comp


if __name__ == '__main__':
    df_outliers, rapport, df_comp = main()
