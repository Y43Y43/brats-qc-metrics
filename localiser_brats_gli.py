from pathlib import Path

def localiser():
    # Plusieurs chemins candidats
    candidats = [
        Path(r"C:\Users\yaman\data\brats\data\BraTS-GLI"),
        Path(r"C:\Users\yaman\data\brats\Data\BraTS-GLI"),
        Path(r"C:\Users\yaman\data\brats\BraTS-GLI"),
        Path(r"C:\Users\yaman\data\BraTS-GLI"),
    ]
    
    print("=== RECHERCHE BraTS-GLI ===\n")
    
    trouve = None
    for c in candidats:
        existe = c.exists()
        print(f"  {'OUI' if existe else 'NON'} : {c}")
        if existe and trouve is None:
            trouve = c
    
    if trouve:
        print(f"\n=> Dossier trouve : {trouve}")
        cas = sorted([d for d in trouve.iterdir() if d.is_dir() and d.name.startswith("BraTS-GLI-")])
        print(f"=> Nombre de cas patients : {len(cas)}")
        if cas:
            print(f"=> Premier cas : {cas[0].name}")
            print(f"=> Dernier cas : {cas[-1].name}")
    else:
        print("\n=> AUCUN candidat trouve. Recherche large...")
        # Recherche recursive depuis C:\Users\yaman\data
        racine = Path(r"C:\Users\yaman\data")
        if racine.exists():
            print(f"\nExploration de {racine} :")
            for item in racine.rglob("BraTS-GLI"):
                if item.is_dir():
                    print(f"  TROUVE : {item}")

localiser()
