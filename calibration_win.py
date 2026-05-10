#!/usr/bin/env python3
"""
Étape 5 — Calibration des seuils QC

Ce script applique le pipeline de métriques QC sur le dataset de calibration
(ds000030, 50 sujets avec labels de qualité connus) et définit les seuils
de détection d'outliers.

Méthodes de seuillage :
    - Z-score > 2 : détection basée sur la distribution normale
    - Percentiles 5e/95e : seuils robustes non-paramétriques

Les seuils sont calibrés en comparant les métriques avec les labels de qualité
(include/exclude/uncertain) du fichier quality_annotations.tsv.

Auteur : Manus AI
Date : Mai 2026
"""

import sys
sys.path.insert(0, '/home/ubuntu/project/code')

import numpy as np
import pandas as pd
from pathlib import Path
from qc_metrics import executer_pipeline, calculer_metriques_sujet
import json

# === Configuration ===
CALIBRATION_DIR = Path('/home/ubuntu/data/calibration')
NIFTI_DIR = CALIBRATION_DIR / 'nifti'
ANNOTATIONS_FILE = CALIBRATION_DIR / 'quality_annotations.tsv'
RESULTS_DIR = Path('/home/ubuntu/project/results')
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def preparer_liste_sujets_calibration():
    """
    Prépare la liste des sujets de calibration avec leurs chemins.
    
    Retourne
    --------
    list of dict
        Liste des sujets avec chemins T1
    """
    annotations = pd.read_csv(ANNOTATIONS_FILE, sep='\t')
    
    liste_sujets = []
    for _, row in annotations.iterrows():
        sujet_id = row['participant_id']
        chemin_t1 = CALIBRATION_DIR / row['nifti_path']
        
        if chemin_t1.exists():
            liste_sujets.append({
                'sujet_id': sujet_id,
                'chemin_t1': str(chemin_t1),
                'quality_label': row['quality_label'],
                'quality_rating': row['quality_rating']
            })
    
    return liste_sujets


def calculer_seuils(df_metriques, colonnes_metriques):
    """
    Calcule les seuils de détection d'outliers par deux méthodes.
    
    Paramètres
    ----------
    df_metriques : pandas.DataFrame
        DataFrame avec les métriques calculées
    colonnes_metriques : list of str
        Noms des colonnes de métriques à analyser
    
    Retourne
    --------
    dict
        Dictionnaire des seuils par métrique et par méthode
    """
    seuils = {}
    
    for col in colonnes_metriques:
        valeurs = df_metriques[col].dropna()
        if len(valeurs) < 5:
            continue
        
        moyenne = valeurs.mean()
        ecart_type = valeurs.std()
        
        seuils[col] = {
            'moyenne': float(moyenne),
            'ecart_type': float(ecart_type),
            # Méthode 1 : Z-score > 2
            'zscore_bas': float(moyenne - 2 * ecart_type),
            'zscore_haut': float(moyenne + 2 * ecart_type),
            # Méthode 2 : Percentiles 5e/95e
            'percentile_5': float(np.percentile(valeurs, 5)),
            'percentile_95': float(np.percentile(valeurs, 95)),
            # Statistiques supplémentaires
            'mediane': float(np.median(valeurs)),
            'q1': float(np.percentile(valeurs, 25)),
            'q3': float(np.percentile(valeurs, 75)),
            'iqr': float(np.percentile(valeurs, 75) - np.percentile(valeurs, 25)),
            'n_valides': int(len(valeurs))
        }
    
    return seuils


def evaluer_seuils_vs_labels(df_metriques, seuils, colonnes_metriques):
    """
    Évalue la performance des seuils en les comparant aux labels de qualité connus.
    
    Paramètres
    ----------
    df_metriques : pandas.DataFrame
        DataFrame avec métriques et labels
    seuils : dict
        Seuils calculés
    colonnes_metriques : list of str
        Colonnes à évaluer
    
    Retourne
    --------
    pandas.DataFrame
        Résumé de la performance par métrique
    """
    resultats_eval = []
    
    for col in colonnes_metriques:
        if col not in seuils:
            continue
        
        s = seuils[col]
        valeurs = df_metriques[[col, 'quality_label']].dropna(subset=[col])
        
        if len(valeurs) == 0:
            continue
        
        # Détection par z-score
        outliers_zscore = (valeurs[col] < s['zscore_bas']) | (valeurs[col] > s['zscore_haut'])
        
        # Détection par percentiles
        outliers_pct = (valeurs[col] < s['percentile_5']) | (valeurs[col] > s['percentile_95'])
        
        # Comparer avec les labels
        vrais_mauvais = valeurs['quality_label'] == 'exclude'
        vrais_bons = valeurs['quality_label'] == 'include'
        
        # Sensibilité (détection des vrais mauvais)
        if vrais_mauvais.sum() > 0:
            sensibilite_zscore = (outliers_zscore & vrais_mauvais).sum() / vrais_mauvais.sum()
            sensibilite_pct = (outliers_pct & vrais_mauvais).sum() / vrais_mauvais.sum()
        else:
            sensibilite_zscore = np.nan
            sensibilite_pct = np.nan
        
        # Spécificité (non-détection des vrais bons)
        if vrais_bons.sum() > 0:
            specificite_zscore = (~outliers_zscore & vrais_bons).sum() / vrais_bons.sum()
            specificite_pct = (~outliers_pct & vrais_bons).sum() / vrais_bons.sum()
        else:
            specificite_zscore = np.nan
            specificite_pct = np.nan
        
        resultats_eval.append({
            'metrique': col,
            'n_sujets': len(valeurs),
            'n_outliers_zscore': int(outliers_zscore.sum()),
            'n_outliers_percentile': int(outliers_pct.sum()),
            'sensibilite_zscore': sensibilite_zscore,
            'specificite_zscore': specificite_zscore,
            'sensibilite_percentile': sensibilite_pct,
            'specificite_percentile': specificite_pct,
            'moyenne_include': float(valeurs.loc[vrais_bons, col].mean()) if vrais_bons.sum() > 0 else np.nan,
            'moyenne_exclude': float(valeurs.loc[vrais_mauvais, col].mean()) if vrais_mauvais.sum() > 0 else np.nan
        })
    
    return pd.DataFrame(resultats_eval)


def main():
    """Fonction principale de calibration."""
    
    print("=" * 60)
    print("CALIBRATION DES SEUILS QC")
    print("Dataset : ds000030 (OpenNeuro)")
    print("=" * 60)
    
    # 1. Préparer la liste des sujets
    print("\n1. Préparation de la liste des sujets...")
    liste_sujets = preparer_liste_sujets_calibration()
    print(f"   Sujets trouvés : {len(liste_sujets)}")
    
    # Compter par label
    labels = [s['quality_label'] for s in liste_sujets]
    for label in set(labels):
        print(f"   - {label} : {labels.count(label)}")
    
    # 2. Exécuter le pipeline
    print("\n2. Exécution du pipeline de métriques...")
    df_metriques = executer_pipeline(liste_sujets, description="Calibration ds000030")
    
    # Ajouter les labels de qualité
    labels_dict = {s['sujet_id']: s['quality_label'] for s in liste_sujets}
    ratings_dict = {s['sujet_id']: s['quality_rating'] for s in liste_sujets}
    df_metriques['quality_label'] = df_metriques['sujet_id'].map(labels_dict)
    df_metriques['quality_rating'] = df_metriques['sujet_id'].map(ratings_dict)
    
    # 3. Calculer les seuils
    print("\n3. Calcul des seuils...")
    colonnes_metriques = [
        'snr_cerveau', 'entropie_cerveau', 'gradient_cerveau', 'cv_bruit_cerveau',
        'snr_sain', 'entropie_sain', 'gradient_sain', 'cv_bruit_sain'
    ]
    
    seuils = calculer_seuils(df_metriques, colonnes_metriques)
    
    print("\n   Seuils calculés :")
    print(f"   {'Métrique':<25} {'Z-score bas':<12} {'Z-score haut':<12} {'P5':<12} {'P95':<12}")
    print(f"   {'-'*73}")
    for col, s in seuils.items():
        print(f"   {col:<25} {s['zscore_bas']:<12.3f} {s['zscore_haut']:<12.3f} "
              f"{s['percentile_5']:<12.3f} {s['percentile_95']:<12.3f}")
    
    # 4. Évaluer les seuils
    print("\n4. Évaluation des seuils vs labels de qualité...")
    df_eval = evaluer_seuils_vs_labels(df_metriques, seuils, colonnes_metriques)
    
    print("\n   Performance des seuils :")
    print(f"   {'Métrique':<25} {'Sens. Z':<10} {'Spéc. Z':<10} {'Sens. P':<10} {'Spéc. P':<10}")
    print(f"   {'-'*65}")
    for _, row in df_eval.iterrows():
        print(f"   {row['metrique']:<25} {row['sensibilite_zscore']:<10.3f} "
              f"{row['specificite_zscore']:<10.3f} {row['sensibilite_percentile']:<10.3f} "
              f"{row['specificite_percentile']:<10.3f}")
    
    # 5. Sauvegarder les résultats
    print("\n5. Sauvegarde des résultats...")
    
    # Métriques brutes
    df_metriques.to_csv(RESULTS_DIR / 'calibration_metriques.csv', index=False)
    print(f"   Métriques : {RESULTS_DIR / 'calibration_metriques.csv'}")
    
    # Seuils
    with open(RESULTS_DIR / 'seuils_calibres.json', 'w') as f:
        json.dump(seuils, f, indent=2)
    print(f"   Seuils : {RESULTS_DIR / 'seuils_calibres.json'}")
    
    # Évaluation
    df_eval.to_csv(RESULTS_DIR / 'evaluation_seuils.csv', index=False)
    print(f"   Évaluation : {RESULTS_DIR / 'evaluation_seuils.csv'}")
    
    print("\n" + "=" * 60)
    print("CALIBRATION TERMINÉE")
    print("=" * 60)
    
    return df_metriques, seuils, df_eval


if __name__ == '__main__':
    df_metriques, seuils, df_eval = main()
