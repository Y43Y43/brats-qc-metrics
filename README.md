\# Métriques automatiques de contrôle qualité pour les IRM cérébrales



Application au sous-ensemble BraTS-GLI 2023 (1251 cas) avec calibration sur OpenNeuro ds000030.



\*\*Auteur\*\* : Jean-Vincent Bogui — Doctorat en informatique cognitive (DIC), UQAM

\*\*Cours\*\* : DIC938R — Neuroinformatique

\*\*Date\*\* : Mai 2026



\---



\## Résumé



Ce dépôt présente un pipeline automatisé de contrôle qualité (QC) pour les IRM cérébrales tumorales. Quatre métriques complémentaires — rapport signal/bruit (SNR), entropie de Shannon, magnitude du gradient 3-D et coefficient de variation du bruit (CV) — sont calculées sur trois régions d'intérêt : le cerveau entier, le tissu sain et la zone tumorale. Le pipeline est appliqué aux 1251 cas du jeu de données BraTS-GLI 2023 et calibré statistiquement sur 50 sujets sains du jeu OpenNeuro ds000030. La méthodologie introduit un masque péricérébral (« rim ») qui corrige une surestimation systématique du SNR liée au skull-stripping de BraTS, et propose une auto-calibration tumorale (z-scores tumeur vs tissu sain) afin de pallier le biais de domaine entre cohortes saines et pathologiques.



\---



\## Principales découvertes



\- \*\*Correction du SNR\*\* : le masque péricérébral corrige une surestimation de +217 % du SNR causée par le skull-stripping de BraTS (SNR moyen 11,52 → 5,31 ; CV bruit 1,26 → 0,47).

\- \*\*Métrique transférable\*\* : le gradient est la seule métrique robuste au transfert inter-cohortes (Mann-Whitney p = 0,011 ; r = 0,07), tandis que SNR (p < 10⁻²⁸, r = 0,31), entropie (p < 10⁻¹⁷, r = 0,24) et CV (p < 10⁻³², r = 0,33) montrent un décalage significatif.

\- \*\*Auto-calibration tumorale\*\* : identifie 0,3 %–18 % de cas atypiques selon la métrique, là où la calibration externe (z > 2) saturait à 100 %.

\- \*\*Décalage de domaine\*\* : la distance de Mahalanobis multivariée (médiane = 22,6 ; max = 827,6) dépasse largement le seuil χ²(4 ; 0,999) ≈ 4,30, confirmant un domain shift systématique entre BraTS-GLI et ds000030.



\---

\## Structure du dépôt



```text

brats-qc-metrics/

├── qc\_metrics\_v2.py                 # Cœur du pipeline : 4 métriques × 3 régions, masque rim

├── run\_qc\_v2\_full.py                # Exécution complète sur les 1251 cas BraTS-GLI

├── run\_calibration\_v2.py            # Calibration sur 50 sujets ds000030

├── comparaison\_v2.py                # Mann-Whitney, Mahalanobis, auto-calibration tumorale

├── visualisations\_v2.py             # Génération des 6 figures (PNG)

├── inspecter\_seuils\_v2.py           # Comparaison des seuils v1 vs v2

├── test\_qc\_v2\_un\_cas.py             # Test rapide (\~2 s) sur un cas

├── telecharger\_ds000030.py          # Téléchargement automatisé OpenNeuro

├── valider\_brats\_gli.py             # Vérification de l'intégrité du jeu BraTS

├── quality\_annotations.tsv          # Étiquettes qualité ds000030

├── cas\_brats\_full.txt               # Manifeste des 1251 cas BraTS-GLI

├── results\_calibration/

│   ├── seuils\_calibres\_v2.json

│   ├── calibration\_metriques\_v2.csv

│   ├── mann\_whitney\_v2.csv

│   ├── brats\_outliers\_v2.csv

│   └── sensibilite\_seuils\_v2.csv

├── figures\_v2/                      # 6 figures PNG

└── README.md

```



\---

\## Installation



Prérequis : Python 3.10+, Anaconda (recommandé), \~2 Go d'espace disque pour les résultats intermédiaires, \~600 Mo supplémentaires pour ds000030.



```bash

conda install -c conda-forge nibabel numpy pandas scipy scikit-image matplotlib seaborn

pip install openneuro-py

```



\---



\## Données



\*\*BraTS-GLI 2023\*\* (1251 cas, 4 modalités, 240×240×155) — à placer dans :



```text

C:\\Users\\<user>\\data\\brats\\data\\BraTS-GLI\\ASNR-MICCAI-BraTS2023-GLI-Challenge-TrainingData\\

```



Inscription requise sur Synapse BraTS 2023 : https://www.synapse.org/Synapse:syn51156910



\*\*OpenNeuro ds000030\*\* (50 sujets sains, T1w) — téléchargement automatique :



```bash

python telecharger\_ds000030.py

```



\---



\## Utilisation



```bash

\# 1. Validation de l'intégrité du jeu BraTS

python valider\_brats\_gli.py



\# 2. Test rapide sur un seul cas (\~2 s)

python test\_qc\_v2\_un\_cas.py



\# 3. Calibration sur ds000030 (\~3 min)

python run\_calibration\_v2.py



\# 4. Exécution complète sur les 1251 cas BraTS-GLI (\~45 min)

python run\_qc\_v2\_full.py



\# 5. Analyses statistiques (\~10 s)

python comparaison\_v2.py



\# 6. Génération des figures (\~30 s)

python visualisations\_v2.py



\# 7. Inspection comparative des seuils v1 vs v2

python inspecter\_seuils\_v2.py

```



\---



\## Résultats principaux



Métriques médianes par région (n = 1251 cas BraTS-GLI) :



| Métrique     | Cerveau entier | Tissu sain | Tumeur |

|--------------|:--------------:|:----------:|:------:|

| SNR          | 3,79           | 3,80       | 3,42   |

| Entropie     | 6,15           | 6,09       | 6,78   |

| Gradient     | 1009           | 1029       | 1559   |

| CV bruit     | 0,15           | 0,15       | 0,09   |



Seuils calibrés sur ds000030 (n = 20 sujets « include ») :



| Métrique       | μ      | σ     | Plage \[μ ± 2σ]   |

|----------------|:------:|:-----:|:----------------:|

| SNR cerveau    | 5,31   | 0,19  | \[4,94 ; 5,69]    |

| Entropie       | 6,75   | 0,21  | \[6,32 ; 7,18]    |

| Gradient       | 1261   | 158   | \[944 ; 1578]     |

| CV bruit       | 0,47   | 0,02  | \[0,42 ; 0,51]    |

| Bruit rim std  | 39,4   | 4,6   | \[30,2 ; 48,6]    |



Tests de Mann-Whitney U (BraTS vs ds000030) :



| Métrique        | Médiane BraTS | Médiane ds000030 | p           | r     | Significatif |

|-----------------|:-------------:|:----------------:|:-----------:|:-----:|:------------:|

| SNR cerveau     | 3,79          | 5,32             | 8,6 × 10⁻²⁹ | 0,31  | Oui          |

| Entropie        | 6,15          | 6,77             | 3,2 × 10⁻¹⁸ | 0,24  | Oui          |

| Gradient        | 1009          | 1253             | 1,1 × 10⁻²  | 0,07  | Non          |

| CV bruit        | 0,15          | 0,46             | 3,4 × 10⁻³³ | 0,33  | Oui          |



\---



\## Limitations connues



1\. Le masque Otsu sous-segmente les tumeurs très volumineuses (œdème + nécrose), ce qui peut sous-estimer le volume cérébral effectif.

2\. Calibration mono-site (ds000030, n = 50) à faible variance, ce qui rend les seuils z-score très stricts ; un recalibrage sur ABIDE (n ≈ 1100, multi-sites) est recommandé.

3\. Absence d'étiquettes qualité pour BraTS, empêchant une validation supervisée des classifications SUSPECT.

4\. Cohorte de calibration saine : le décalage de domaine inhérent justifie le recours à l'auto-calibration tumorale plutôt qu'aux seuils externes seuls.



\---



\## Références



\- Esteban, O. et al. (2017). MRIQC: Advancing the automatic prediction of image quality in MRI from unseen sites. PLOS ONE, 12(9), e0184661.

\- LaBella, D. et al. (2023). The ASNR-MICCAI Brain Tumor Segmentation (BraTS) Challenge 2023. arXiv:2305.17033.

\- Mortamet, B. et al. (2009). Automatic quality assessment in structural brain MRI. Magnetic Resonance in Medicine, 62(2), 365-372.

\- Otsu, N. (1979). A threshold selection method from gray-level histograms. IEEE Transactions on Systems, Man, and Cybernetics, 9(1), 62-66.

\- Di Martino, A. et al. (2014). The Autism Brain Imaging Data Exchange (ABIDE). Molecular Psychiatry, 19(6), 659-667.

\- Poldrack, R. A. et al. (2016). A phenome-wide examination of neural and cognitive function. Scientific Data, 3, 160110.

\- Mahalanobis, P. C. (1936). On the generalized distance in statistics. Proceedings of the National Institute of Sciences of India, 2, 49-55.



\---



\## Licence et citation



Travail académique, DIC938R — Neuroinformatique (UQAM, doctorat en informatique cognitive). Réutilisation à des fins de recherche et d'enseignement autorisée avec citation :



> Bogui, J.-V. (2026). Métriques automatiques de contrôle qualité pour les IRM cérébrales : adaptation et validation sur 1251 cas tumoraux BraTS-GLI 2023. Cours DIC938R, Doctorat en informatique cognitive, UQAM.



\---



\## Contact



Courriel : bogui.jean-vincent@courrier.uqam.ca

Dépôt : https://github.com/Y43Y43/brats-qc-metrics











