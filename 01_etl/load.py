"""Étape de chargement : écriture de la table analytique dans DuckDB."""

import duckdb
import pandas as pd

import config


def charger(df: pd.DataFrame) -> None:
    """Écrit la table analytique dans heart.duckdb, en remplaçant l'existante.

    Raises:
        duckdb.IOException: si la base est verrouillée par un autre processus
            (Power BI ou un noyau Jupyter ouvert, typiquement).
    """
    config.BASE_DUCKDB.parent.mkdir(parents=True, exist_ok=True)

    try:
        connexion = duckdb.connect(str(config.BASE_DUCKDB))
    except duckdb.IOException as erreur:
        raise duckdb.IOException(
            f"Impossible d'ouvrir {config.BASE_DUCKDB} en ecriture.\n"
            "DuckDB n'autorise qu'un seul processus en ecriture : fermer Power BI "
            "et tout noyau Jupyter connecte a la base, puis reessayer."
        ) from erreur

    try:
        # DuckDB lit directement le DataFrame présent dans la portée locale.
        connexion.register("df_source", df)
        connexion.execute(
            f"CREATE OR REPLACE TABLE {config.TABLE_ANALYTIQUE} AS "
            "SELECT * FROM df_source"
        )
        connexion.unregister("df_source")

        nb = connexion.execute(
            f"SELECT COUNT(*) FROM {config.TABLE_ANALYTIQUE}"
        ).fetchone()[0]
    finally:
        connexion.close()

    print(
        f"  [chargement] {nb:,} lignes ecrites dans "
        f"{config.BASE_DUCKDB.name}::{config.TABLE_ANALYTIQUE}"
    )
