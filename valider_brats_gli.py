from pathlib import Path

def valider_brats_gli(n_cases=130):
    # CHEMIN CORRIGE : on pointe directement vers TrainingData
    base = Path(r"C:\Users\yaman\data\brats\data\BraTS-GLI\ASNR-MICCAI-BraTS2023-GLI-Challenge-TrainingData")
    
    print(f"=== VALIDATION BraTS-GLI TrainingData ({n_cases} premiers cas) ===\n")
    
    if not base.exists():
        print("ERREUR : Dossier TrainingData introuvable")
        return
    
    cas_dirs = sorted([d for d in base.iterdir() if d.is_dir() and d.name.startswith("BraTS-GLI-")])
    print(f"Total cas disponibles : {len(cas_dirs)}")
    
    if len(cas_dirs) < n_cases:
        print(f"ATTENTION : seulement {len(cas_dirs)} cas, demande {n_cases}")
        n_cases = len(cas_dirs)
    
    cas_a_tester = cas_dirs[:n_cases]
    print(f"Cas a valider : {n_cases}\n")
    
    suffixes = ["-t1n.nii.gz", "-t1c.nii.gz", "-t2w.nii.gz", "-t2f.nii.gz", "-seg.nii.gz"]
    
    cas_complets = []
    cas_incomplets = []
    
    for cas in cas_a_tester:
        manquants = []
        for suf in suffixes:
            f = cas / (cas.name + suf)
            if not f.exists():
                manquants.append(suf)
        
        if not manquants:
            cas_complets.append(cas.name)
        else:
            cas_incomplets.append((cas.name, manquants))
    
    print(f"Cas COMPLETS (5/5 fichiers)  : {len(cas_complets)}")
    print(f"Cas INCOMPLETS               : {len(cas_incomplets)}")
    
    if cas_incomplets:
        print("\nDetail des cas incomplets :")
        for nom, miss in cas_incomplets[:10]:
            print(f"  - {nom} : manque {miss}")
        if len(cas_incomplets) > 10:
            print(f"  ... et {len(cas_incomplets)-10} autres")
    
    if cas_complets:
        print(f"\nVerification taille fichiers (cas {cas_complets[0]}):")
        cas_ref = base / cas_complets[0]
        for suf in suffixes:
            f = cas_ref / (cas_complets[0] + suf)
            size_mb = f.stat().st_size / (1024**2)
            print(f"  {suf:20s} : {size_mb:6.2f} MB")
    
    print(f"\n=> {len(cas_complets)} cas utilisables sur {n_cases} demandes")
    
    if cas_complets:
        # Sauvegarder le chemin de base ET la liste des cas
        liste_path = Path("cas_brats_selectionnes.txt")
        with open(liste_path, "w", encoding="utf-8") as f:
            f.write(f"# Base : {base}\n")
            for nom in cas_complets:
                f.write(nom + "\n")
        print(f"=> Liste sauvegardee : {liste_path.absolute()}")

valider_brats_gli(n_cases=130)
