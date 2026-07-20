"""Étape d'extraction : lecture du fichier source BRFSS 2015."""

import pandas as pd

import config


def extraire(echantillon: int | None = None) -> pd.DataFrame:
    """Lit le CSV source et renvoie le DataFrame brut, sans transformation.

    Args:
        echantillon: si fourni, ne lit que les N premières lignes (mode test).

    Raises:
        FileNotFoundError: si le fichier source est absent du dossier data/.
    """
    if not config.FICHIER_SOURCE.exists():
        raise FileNotFoundError(
            f"Fichier source introuvable : {config.FICHIER_SOURCE}\n"
            "Le jeu de données doit se trouver dans le dossier data/."
        )

    df = pd.read_csv(config.FICHIER_SOURCE, nrows=echantillon)

    print(f"  [extraction] {len(df):,} lignes x {df.shape[1]} colonnes lues")
    return df
