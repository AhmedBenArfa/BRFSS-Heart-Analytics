"""Accès aux données de référence de la population.

Ces données sont pré-calculées par `_build_reference.py` et embarquées avec
l'application (l'entrepôt DuckDB n'est pas déployé). Elles alimentent le
positionnement individuel et le tableau de bord population.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

DOSSIER = Path(__file__).resolve().parent.parent / "data_sample"
CHEMIN_PARQUET = DOSSIER / "population_reference.parquet"
CHEMIN_JSON = DOSSIER / "profils_reference.json"


@st.cache_data
def charger_echantillon() -> pd.DataFrame:
    """Échantillon de référence : un répondant par ligne, avec son risque estimé."""
    if not CHEMIN_PARQUET.exists():
        return pd.DataFrame()
    return pd.read_parquet(CHEMIN_PARQUET)


@st.cache_data
def charger_agregats() -> dict:
    """Agrégats globaux : prévalence, profils, moyennes par âge et sexe."""
    if not CHEMIN_JSON.exists():
        return {}
    return json.loads(CHEMIN_JSON.read_text(encoding="utf-8"))


def positionner(risque: float, age_group: int, sex: int) -> dict | None:
    """Situe un risque individuel parmi ses pairs (même âge et sexe).

    Returns:
        Dictionnaire avec le percentile, la moyenne des pairs et l'effectif,
        ou None si les données de référence sont absentes.
    """
    ech = charger_echantillon()
    if ech.empty:
        return None

    pairs = ech[(ech["age_group"] == age_group) & (ech["sex"] == sex)]
    if len(pairs) < 30:  # trop peu pour un percentile fiable
        pairs = ech[ech["age_group"] == age_group]
    if len(pairs) < 30:
        pairs = ech

    percentile = float((pairs["risque"] < risque).mean() * 100)
    return {
        "percentile": percentile,
        "moyenne_pairs": float(pairs["risque"].mean()),
        "mediane_pairs": float(pairs["risque"].median()),
        "effectif_pairs": int(len(pairs)),
    }
