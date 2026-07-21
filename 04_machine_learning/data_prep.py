"""Chargement des données et découpage entraînement / test.

Le découpage est **stratifié** : la proportion de cas positifs (9,42 %) est
préservée dans les deux jeux. Sans cela, un tirage malchanceux pourrait donner un
jeu de test à la prévalence très différente, faussant toute l'évaluation.
"""

from __future__ import annotations

import duckdb
import pandas as pd
from sklearn.model_selection import train_test_split

import config


def charger() -> pd.DataFrame:
    """Charge la table analytique depuis l'entrepôt DuckDB."""
    if not config.BASE_DUCKDB.exists():
        raise FileNotFoundError(
            f"Entrepôt introuvable : {config.BASE_DUCKDB}\n"
            "Exécuter d'abord : cd 01_etl && python run_etl.py"
        )

    colonnes = ", ".join(config.VARIABLES + [config.CIBLE])
    with duckdb.connect(str(config.BASE_DUCKDB), read_only=True) as conn:
        df = conn.execute(f"SELECT {colonnes} FROM {config.TABLE}").df()

    return df


def decouper(df: pd.DataFrame):
    """Sépare variables et cible, puis découpe en entraînement / test.

    Returns:
        X_train, X_test, y_train, y_test
    """
    X = df[config.VARIABLES]
    y = df[config.CIBLE]

    return train_test_split(
        X, y,
        test_size=config.TAILLE_TEST,
        random_state=config.GRAINE,
        stratify=y,  # préserve la prévalence dans les deux jeux
    )


def echantillon_comparaison(X_train: pd.DataFrame, y_train: pd.Series):
    """Sous-échantillon stratifié pour la phase de comparaison des modèles.

    Certains algorithmes (kNN, SVM) ont un coût prohibitif sur 200 000 lignes.
    Comparer tous les modèles sur un même sous-échantillon est plus équitable que
    d'en avantager certains ; le modèle retenu sera réentraîné sur l'intégralité
    du jeu d'entraînement.
    """
    if len(X_train) <= config.TAILLE_COMPARAISON:
        return X_train, y_train

    X_ech, _, y_ech, _ = train_test_split(
        X_train, y_train,
        train_size=config.TAILLE_COMPARAISON,
        random_state=config.GRAINE,
        stratify=y_train,
    )
    return X_ech, y_ech


def resume(y_train, y_test) -> pd.DataFrame:
    """Petit tableau de contrôle du découpage."""
    return pd.DataFrame({
        "effectif": [len(y_train), len(y_test)],
        "cas positifs": [int(y_train.sum()), int(y_test.sum())],
        "prévalence (%)": [
            round(y_train.mean() * 100, 3),
            round(y_test.mean() * 100, 3),
        ],
    }, index=["entraînement", "test"])
