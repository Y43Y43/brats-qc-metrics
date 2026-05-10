"""Pipeline QC v2 pour IRM cerebrales tumorales (BraTS).

Ameliorations vs v1 :
  - Masque de fond corrige (bande peri-cerebrale "rim") adapte aux
    images skull-strippees, conforme a la litterature MRIQC.
  - Conservation de cv_bruit_sain en parallele pour comparaison.
  - Suppression de la redondance des colonnes CV bruit.
  - Type hints modernes (Python 3.10+).
  - Auto-calibration tumorale possible via les distributions du tissu sain.

Auteur : Y43, doctorant en informatique cognitive (DIC), UQAM.
Cours  : DIC938R - Neuroinformatique, TP final.

"That which has a name has power." -- Rimuru Tempest
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import nibabel as nib
import pandas as pd
from scipy import ndimage
from skimage.filters import threshold_otsu


# ---------------------------------------------------------------------------
# Chargement et masques
# ---------------------------------------------------------------------------

def charger_nifti(chemin: Path) -> tuple[np.ndarray, Any]:
    """Charge un volume NIfTI et retourne (donnees, header)."""
    img = nib.load(str(chemin))
    return np.asarray(img.dataobj, dtype=np.float32), img.header


def creer_masque_cerveau(data: np.ndarray) -> np.ndarray:
    """Masque cerveau via Otsu sur voxels non nuls + plus grand composant + remplissage."""
    voxels_non_nuls = data[data > 0]
    if voxels_non_nuls.size == 0:
        return np.zeros_like(data, dtype=bool)
    seuil = threshold_otsu(voxels_non_nuls)
    masque = data > seuil

    # Plus grand composant connecte 3D
    labels, n = ndimage.label(masque)
    if n > 1:
        tailles = ndimage.sum(masque, labels, index=range(1, n + 1))
        masque = labels == (np.argmax(tailles) + 1)

    # Remplissage des trous slice par slice
    for z in range(masque.shape[2]):
        masque[:, :, z] = ndimage.binary_fill_holes(masque[:, :, z])
    return masque.astype(bool)


def creer_masque_rim(masque_cerveau: np.ndarray, epaisseur: int = 3) -> np.ndarray:
    """Bande peri-cerebrale (dilation - cerveau) : proxy du bruit ambiant.

    Sur images skull-strippees, le fond pur (=0) ne reflete plus le bruit
    d'acquisition. Cette bande capture les voxels juste autour du cerveau
    apres dilatation morphologique.
    """
    structure = ndimage.generate_binary_structure(3, 1)
    dilate = ndimage.binary_dilation(masque_cerveau, structure=structure, iterations=epaisseur)
    return dilate & (~masque_cerveau)


def creer_masques_tumeur_sain(
    masque_cerveau: np.ndarray, seg_data: np.ndarray | None
) -> tuple[np.ndarray, np.ndarray]:
    """Sépare cerveau en (tissu_sain, tumeur) a partir de la segmentation BraTS."""
    if seg_data is None:
        return masque_cerveau.copy(), np.zeros_like(masque_cerveau, dtype=bool)
    masque_tumeur = (seg_data > 0) & masque_cerveau
    masque_sain = masque_cerveau & (~masque_tumeur)
    return masque_sain, masque_tumeur


# ---------------------------------------------------------------------------
# Metriques
# ---------------------------------------------------------------------------

def snr(data: np.ndarray, masque_signal: np.ndarray, masque_bruit: np.ndarray) -> float:
    """SNR = mean(signal) / std(bruit). Renvoie NaN si masques vides."""
    if masque_signal.sum() == 0 or masque_bruit.sum() < 10:
        return float("nan")
    sig = float(data[masque_signal].mean())
    bruit = float(data[masque_bruit].std())
    return sig / bruit if bruit > 0 else float("nan")


def entropie_shannon(data: np.ndarray, masque: np.ndarray, n_bins: int = 256) -> float:
    """Entropie de Shannon (log2) sur l'histogramme normalise."""
    if masque.sum() == 0:
        return float("nan")
    valeurs = data[masque]
    hist, _ = np.histogram(valeurs, bins=n_bins)
    p = hist[hist > 0] / hist.sum()
    return float(-np.sum(p * np.log2(p)))


def gradient_moyen(data: np.ndarray, masque: np.ndarray) -> float:
    """Magnitude moyenne du gradient 3D Sobel sur la region masquee."""
    if masque.sum() == 0:
        return float("nan")
    gx = ndimage.sobel(data, axis=0)
    gy = ndimage.sobel(data, axis=1)
    gz = ndimage.sobel(data, axis=2)
    mag = np.sqrt(gx ** 2 + gy ** 2 + gz ** 2)
    return float(mag[masque].mean())


def cv_intensite(data: np.ndarray, masque: np.ndarray) -> float:
    """Coefficient de variation = std/mean dans le masque."""
    if masque.sum() == 0:
        return float("nan")
    valeurs = data[masque]
    m = float(valeurs.mean())
    return float(valeurs.std() / m) if m > 0 else float("nan")


# ---------------------------------------------------------------------------
# Pipeline par sujet
# ---------------------------------------------------------------------------

def calculer_metriques_sujet_v2(
    chemin_t1: Path,
    chemin_seg: Path | None = None,
    sujet_id: str = "",
) -> dict[str, Any]:
    """Calcule les 4 metriques sur 3 regions + bruit rim. Retourne un dict plat."""
    data, _ = charger_nifti(chemin_t1)
    seg_data = None
    if chemin_seg is not None and Path(chemin_seg).exists():
        seg_data, _ = charger_nifti(chemin_seg)

    masque_cerveau = creer_masque_cerveau(data)
    masque_rim = creer_masque_rim(masque_cerveau, epaisseur=3)
    masque_sain, masque_tumeur = creer_masques_tumeur_sain(masque_cerveau, seg_data)

    res: dict[str, Any] = {
        "sujet_id": sujet_id or Path(chemin_t1).stem,
        "a_segmentation": seg_data is not None,
    }

    # Cerveau entier
    res["snr_cerveau"] = snr(data, masque_cerveau, masque_rim)
    res["entropie_cerveau"] = entropie_shannon(data, masque_cerveau)
    res["gradient_cerveau"] = gradient_moyen(data, masque_cerveau)
    res["cv_bruit_cerveau"] = cv_intensite(data, masque_cerveau)

    # Tissu sain
    res["snr_sain"] = snr(data, masque_sain, masque_rim)
    res["entropie_sain"] = entropie_shannon(data, masque_sain)
    res["gradient_sain"] = gradient_moyen(data, masque_sain)
    res["cv_bruit_sain"] = cv_intensite(data, masque_sain)

    # Tumeur
    res["snr_tumeur"] = snr(data, masque_tumeur, masque_rim)
    res["entropie_tumeur"] = entropie_shannon(data, masque_tumeur)
    res["gradient_tumeur"] = gradient_moyen(data, masque_tumeur)
    res["cv_bruit_tumeur"] = cv_intensite(data, masque_tumeur)

    # Bruit rim (nouveau, scientifiquement plus correct)
    res["bruit_rim_std"] = float(data[masque_rim].std()) if masque_rim.sum() > 0 else float("nan")
    res["bruit_rim_voxels"] = int(masque_rim.sum())

    # Volumes
    res["volume_cerveau_voxels"] = int(masque_cerveau.sum())
    res["volume_sain_voxels"] = int(masque_sain.sum())
    res["volume_tumeur_voxels"] = int(masque_tumeur.sum())

    return res


def executer_pipeline_v2(sujets: list[dict[str, Any]]) -> pd.DataFrame:
    """Execute le pipeline sur une liste de sujets. Format: [{'sujet_id', 'chemin_t1', 'chemin_seg'}]."""
    resultats = []
    for s in sujets:
        try:
            r = calculer_metriques_sujet_v2(
                chemin_t1=Path(s["chemin_t1"]),
                chemin_seg=Path(s["chemin_seg"]) if s.get("chemin_seg") else None,
                sujet_id=s.get("sujet_id", ""),
            )
            resultats.append(r)
        except Exception as e:
            resultats.append({"sujet_id": s.get("sujet_id", ""), "erreur": str(e)})
    return pd.DataFrame(resultats)


if __name__ == "__main__":
    print("qc_metrics_v2.py - module charge correctement.")
    print("Auteur : Y43, doctorant en informatique cognitive (UQAM, DIC938R).")
