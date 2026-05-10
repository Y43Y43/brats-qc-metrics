#!/usr/bin/env python3
"""
Pipeline de Contrôle Qualité IRM - Calcul de Métriques

Ce module implémente le calcul de 4 métriques complémentaires de qualité d'image
sur 3 régions d'intérêt pour les images IRM structurelles (T1).

Métriques calculées :
    1. SNR (Signal-to-Noise Ratio) : rapport signal/bruit
    2. Entropie : mesure de la complexité/information de l'image
    3. Magnitude du gradient : mesure de la netteté des contours
    4. CV du bruit (Coefficient de Variation) : homogénéité du bruit de fond

Régions d'intérêt :
    1. Cerveau entier (masque Otsu)
    2. Tissu sain (cerveau sans tumeur, si segmentation disponible)
    3. Zone tumorale (segmentation BraTS, si disponible)

Auteur : Manus AI
Date : Mai 2026
"""

import numpy as np
import nibabel as nib
import pandas as pd
from scipy import ndimage
from scipy.stats import entropy as scipy_entropy
from skimage.filters import threshold_otsu
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')


def charger_nifti(chemin):
    """
    Charge un fichier NIfTI et retourne les données sous forme de tableau NumPy.
    
    Paramètres
    ----------
    chemin : str ou Path
        Chemin vers le fichier NIfTI (.nii ou .nii.gz)
    
    Retourne
    --------
    numpy.ndarray
        Données volumétriques de l'image
    """
    img = nib.load(str(chemin))
    data = img.get_fdata().astype(np.float64)
    return data


def creer_masque_cerveau(data):
    """
    Crée un masque binaire du cerveau par seuillage d'Otsu.
    
    Le seuillage d'Otsu sépare automatiquement le fond (air/bruit) du signal
    cérébral en minimisant la variance intra-classe.
    
    Paramètres
    ----------
    data : numpy.ndarray
        Données volumétriques de l'image IRM
    
    Retourne
    --------
    numpy.ndarray (bool)
        Masque binaire du cerveau
    """
    # Exclure les voxels à zéro pour le calcul du seuil
    voxels_non_nuls = data[data > 0]
    if len(voxels_non_nuls) == 0:
        return np.zeros_like(data, dtype=bool)
    
    seuil = threshold_otsu(voxels_non_nuls)
    masque = data > seuil
    
    # Nettoyage morphologique : garder le plus grand composant connexe
    masque_label, num_features = ndimage.label(masque)
    if num_features > 0:
        tailles = ndimage.sum(masque, masque_label, range(1, num_features + 1))
        plus_grand = np.argmax(tailles) + 1
        masque = masque_label == plus_grand
    
    # Remplir les trous internes
    masque = ndimage.binary_fill_holes(masque)
    
    return masque


def creer_masque_fond(data, masque_cerveau):
    """
    Crée un masque du fond (bruit) pour le calcul du SNR.
    
    Paramètres
    ----------
    data : numpy.ndarray
        Données volumétriques
    masque_cerveau : numpy.ndarray (bool)
        Masque du cerveau
    
    Retourne
    --------
    numpy.ndarray (bool)
        Masque du fond (hors cerveau, hors zéros)
    """
    masque_fond = (~masque_cerveau) & (data > 0)
    # Éroder pour éviter les voxels de transition
    masque_fond = ndimage.binary_erosion(masque_fond, iterations=3)
    return masque_fond


def calculer_snr(data, masque_region, masque_fond):
    """
    Calcule le rapport signal-sur-bruit (SNR).
    
    SNR = moyenne(signal dans la région) / écart-type(bruit de fond)
    
    Paramètres
    ----------
    data : numpy.ndarray
        Données volumétriques
    masque_region : numpy.ndarray (bool)
        Masque de la région d'intérêt
    masque_fond : numpy.ndarray (bool)
        Masque du bruit de fond
    
    Retourne
    --------
    float
        Valeur du SNR
    """
    signal = data[masque_region]
    bruit = data[masque_fond]
    
    if len(signal) == 0 or len(bruit) == 0:
        return np.nan
    
    std_bruit = np.std(bruit)
    if std_bruit == 0:
        return np.nan
    
    snr = np.mean(signal) / std_bruit
    return snr


def calculer_entropie(data, masque_region, n_bins=256):
    """
    Calcule l'entropie de Shannon de la distribution d'intensité dans la région.
    
    Une entropie élevée indique une distribution complexe (potentiellement artéfacts),
    une entropie faible indique une distribution homogène.
    
    Paramètres
    ----------
    data : numpy.ndarray
        Données volumétriques
    masque_region : numpy.ndarray (bool)
        Masque de la région d'intérêt
    n_bins : int
        Nombre de bins pour l'histogramme
    
    Retourne
    --------
    float
        Entropie de Shannon (en bits)
    """
    voxels = data[masque_region]
    
    if len(voxels) == 0:
        return np.nan
    
    # Normaliser entre 0 et 1
    vmin, vmax = np.min(voxels), np.max(voxels)
    if vmax == vmin:
        return 0.0
    
    voxels_norm = (voxels - vmin) / (vmax - vmin)
    
    # Calculer l'histogramme normalisé (probabilités)
    hist, _ = np.histogram(voxels_norm, bins=n_bins, density=True)
    hist = hist[hist > 0]  # Exclure les bins vides
    
    # Entropie de Shannon
    hist_prob = hist / hist.sum()
    ent = scipy_entropy(hist_prob, base=2)
    
    return ent


def calculer_gradient(data, masque_region):
    """
    Calcule la magnitude moyenne du gradient dans la région.
    
    Un gradient élevé indique des contours nets (bonne qualité),
    un gradient faible peut indiquer du flou (mouvement, mauvaise résolution).
    
    Paramètres
    ----------
    data : numpy.ndarray
        Données volumétriques
    masque_region : numpy.ndarray (bool)
        Masque de la région d'intérêt
    
    Retourne
    --------
    float
        Magnitude moyenne du gradient
    """
    if not np.any(masque_region):
        return np.nan
    
    # Calcul du gradient 3D (Sobel)
    gx = ndimage.sobel(data, axis=0)
    gy = ndimage.sobel(data, axis=1)
    gz = ndimage.sobel(data, axis=2)
    
    # Magnitude du gradient
    magnitude = np.sqrt(gx**2 + gy**2 + gz**2)
    
    # Moyenne dans la région
    gradient_moyen = np.mean(magnitude[masque_region])
    
    return gradient_moyen


def calculer_cv_bruit(data, masque_fond):
    """
    Calcule le coefficient de variation (CV) du bruit de fond.
    
    CV = écart-type(bruit) / moyenne(bruit)
    
    Un CV élevé indique un bruit non-uniforme (artéfacts potentiels).
    Un CV faible indique un bruit homogène (bonne qualité).
    
    Paramètres
    ----------
    data : numpy.ndarray
        Données volumétriques
    masque_fond : numpy.ndarray (bool)
        Masque du bruit de fond
    
    Retourne
    --------
    float
        Coefficient de variation du bruit
    """
    bruit = data[masque_fond]
    
    if len(bruit) == 0:
        return np.nan
    
    moyenne_bruit = np.mean(bruit)
    if moyenne_bruit == 0:
        return np.nan
    
    cv = np.std(bruit) / moyenne_bruit
    return cv


def calculer_metriques_sujet(chemin_t1, chemin_seg=None, sujet_id=None):
    """
    Calcule toutes les métriques QC pour un sujet donné.
    
    Paramètres
    ----------
    chemin_t1 : str ou Path
        Chemin vers l'image T1 NIfTI
    chemin_seg : str ou Path, optionnel
        Chemin vers la segmentation tumorale (format BraTS)
    sujet_id : str, optionnel
        Identifiant du sujet
    
    Retourne
    --------
    dict
        Dictionnaire contenant toutes les métriques calculées
    """
    resultats = {'sujet_id': sujet_id or Path(chemin_t1).stem}
    
    # Charger les données
    data = charger_nifti(chemin_t1)
    
    # Créer les masques
    masque_cerveau = creer_masque_cerveau(data)
    masque_fond = creer_masque_fond(data, masque_cerveau)
    
    # Masque tumoral (si segmentation disponible)
    masque_tumeur = None
    masque_sain = masque_cerveau.copy()
    
    if chemin_seg is not None and Path(chemin_seg).exists():
        seg_data = charger_nifti(chemin_seg)
        # BraTS 2023 : labels 1 (NCR), 2 (ED), 3 (ET)
        masque_tumeur = seg_data > 0
        masque_sain = masque_cerveau & (~masque_tumeur)
        resultats['a_segmentation'] = True
    else:
        resultats['a_segmentation'] = False
    
    # === Région 1 : Cerveau entier ===
    resultats['snr_cerveau'] = calculer_snr(data, masque_cerveau, masque_fond)
    resultats['entropie_cerveau'] = calculer_entropie(data, masque_cerveau)
    resultats['gradient_cerveau'] = calculer_gradient(data, masque_cerveau)
    resultats['cv_bruit_cerveau'] = calculer_cv_bruit(data, masque_fond)
    
    # === Région 2 : Tissu sain ===
    if np.any(masque_sain):
        resultats['snr_sain'] = calculer_snr(data, masque_sain, masque_fond)
        resultats['entropie_sain'] = calculer_entropie(data, masque_sain)
        resultats['gradient_sain'] = calculer_gradient(data, masque_sain)
        resultats['cv_bruit_sain'] = calculer_cv_bruit(data, masque_fond)
    else:
        resultats['snr_sain'] = np.nan
        resultats['entropie_sain'] = np.nan
        resultats['gradient_sain'] = np.nan
        resultats['cv_bruit_sain'] = np.nan
    
    # === Région 3 : Zone tumorale ===
    if masque_tumeur is not None and np.any(masque_tumeur):
        resultats['snr_tumeur'] = calculer_snr(data, masque_tumeur, masque_fond)
        resultats['entropie_tumeur'] = calculer_entropie(data, masque_tumeur)
        resultats['gradient_tumeur'] = calculer_gradient(data, masque_tumeur)
        resultats['cv_bruit_tumeur'] = calculer_cv_bruit(data, masque_fond)
        resultats['volume_tumeur_voxels'] = int(np.sum(masque_tumeur))
    else:
        resultats['snr_tumeur'] = np.nan
        resultats['entropie_tumeur'] = np.nan
        resultats['gradient_tumeur'] = np.nan
        resultats['cv_bruit_tumeur'] = np.nan
        resultats['volume_tumeur_voxels'] = 0
    
    # Métriques supplémentaires
    resultats['volume_cerveau_voxels'] = int(np.sum(masque_cerveau))
    resultats['volume_fond_voxels'] = int(np.sum(masque_fond))
    
    return resultats


def executer_pipeline(liste_sujets, description=""):
    """
    Exécute le pipeline QC sur une liste de sujets.
    
    Paramètres
    ----------
    liste_sujets : list of dict
        Liste de dictionnaires avec les clés :
        - 'sujet_id' : identifiant du sujet
        - 'chemin_t1' : chemin vers l'image T1
        - 'chemin_seg' : chemin vers la segmentation (optionnel)
    description : str
        Description du dataset pour l'affichage
    
    Retourne
    --------
    pandas.DataFrame
        DataFrame contenant toutes les métriques pour tous les sujets
    """
    print(f"\n{'='*60}")
    print(f"Pipeline QC - {description}")
    print(f"{'='*60}")
    print(f"Nombre de sujets : {len(liste_sujets)}")
    
    resultats = []
    for i, sujet in enumerate(liste_sujets):
        print(f"  [{i+1}/{len(liste_sujets)}] Traitement de {sujet['sujet_id']}...", end='')
        try:
            metriques = calculer_metriques_sujet(
                chemin_t1=sujet['chemin_t1'],
                chemin_seg=sujet.get('chemin_seg'),
                sujet_id=sujet['sujet_id']
            )
            resultats.append(metriques)
            print(" OK")
        except Exception as e:
            print(f" ERREUR: {e}")
            resultats.append({'sujet_id': sujet['sujet_id'], 'erreur': str(e)})
    
    df = pd.DataFrame(resultats)
    print(f"\nTerminé : {len(df)} sujets traités")
    return df


if __name__ == '__main__':
    # Test rapide sur un sujet de calibration
    import sys
    
    chemin_test = '/home/ubuntu/data/calibration/nifti/sub-10159/anat/sub-10159_T1w.nii.gz'
    if Path(chemin_test).exists():
        print("Test du pipeline sur un sujet de calibration...")
        result = calculer_metriques_sujet(chemin_test, sujet_id='sub-10159')
        for k, v in result.items():
            print(f"  {k}: {v}")
    else:
        print(f"Fichier de test non trouvé : {chemin_test}")
