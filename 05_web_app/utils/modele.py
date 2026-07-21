"""Chargement du modèle et calcul des estimations.

Le pipeline sérialisé contient le préprocesseur ET le modèle : l'application
applique donc exactement les mêmes transformations qu'à l'entraînement, sans
avoir à les réimplémenter.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

DOSSIER = Path(__file__).resolve().parent.parent / "models"

# Modèle déployé : calibré. Ses probabilités correspondent à des fréquences
# réelles et peuvent donc être affichées telles quelles.
CHEMIN_MODELE = DOSSIER / "heart_model.joblib"

# Pipeline brut, uniquement pour l'explication SHAP : l'explicateur doit accéder
# au préprocesseur et au modèle d'arbres, que la calibration encapsule. La
# calibration étant monotone, la hiérarchie des contributions est identique.
CHEMIN_MODELE_BRUT = DOSSIER / "heart_model_base.joblib"

CHEMIN_META = DOSSIER / "metadata.json"

# Prévalence observée dans la population de référence (BRFSS 2015).
PREVALENCE_REFERENCE = 0.0942


@st.cache_resource
def charger_modele():
    """Charge le pipeline entraîné.

    `cache_resource` (et non `cache_data`) : un modèle est un objet non
    sérialisable qu'on veut partager entre toutes les sessions, pas une donnée à
    copier pour chaque utilisateur.
    """
    import joblib

    if not CHEMIN_MODELE.exists():
        st.error(
            f"Modèle introuvable : `{CHEMIN_MODELE.name}`. "
            "Exécuter le notebook `04_machine_learning/notebooks/01_ml.ipynb`, "
            "puis copier le fichier dans `05_web_app/models/`."
        )
        st.stop()
    return joblib.load(CHEMIN_MODELE)


@st.cache_data
def charger_metadonnees() -> dict:
    """Métadonnées du modèle : variables attendues, seuil, performances."""
    if not CHEMIN_META.exists():
        st.error(f"Métadonnées introuvables : `{CHEMIN_META.name}`.")
        st.stop()
    return json.loads(CHEMIN_META.read_text(encoding="utf-8"))


def estimer(profils: pd.DataFrame) -> pd.Series:
    """Probabilité estimée de maladie cardiaque pour chaque ligne."""
    modele = charger_modele()
    meta = charger_metadonnees()
    # On réordonne les colonnes : le pipeline attend un ordre précis.
    X = profils[meta["variables"]]
    return pd.Series(modele.predict_proba(X)[:, 1], index=profils.index)


def niveau_de_risque(probabilite: float) -> tuple[str, str]:
    """Traduit une probabilité en niveau qualitatif et en couleur.

    Les bornes sont exprimées par rapport à la prévalence de référence (9,42 %),
    ce qui est plus parlant qu'une échelle absolue arbitraire : « deux fois le
    risque moyen » se comprend mieux que « 19 % ».
    """
    ratio = probabilite / PREVALENCE_REFERENCE
    if ratio < 0.5:
        return "Faible", "green"
    if ratio < 1.5:
        return "Proche de la moyenne", "blue"
    if ratio < 3:
        return "Élevé", "orange"
    return "Très élevé", "red"


@st.cache_resource
def _modele_brut():
    """Pipeline non calibré, support de l'explication SHAP."""
    import joblib

    if not CHEMIN_MODELE_BRUT.exists():
        return None
    return joblib.load(CHEMIN_MODELE_BRUT)


@st.cache_resource
def _explainer():
    """Explicateur SHAP, construit une seule fois."""
    import shap

    brut = _modele_brut()
    if brut is None:
        return None
    return shap.TreeExplainer(brut.named_steps["model"])


def contributions(profil: pd.DataFrame) -> pd.Series:
    """Contribution de chaque variable à l'estimation, pour un profil unique.

    Renvoie les valeurs SHAP : positives = poussent le risque à la hausse,
    négatives = à la baisse. Renvoie une série vide si le calcul échoue — le
    résultat principal reste affiché quoi qu'il arrive.
    """
    try:
        brut = _modele_brut()
        explicateur = _explainer()
        if brut is None or explicateur is None:
            return pd.Series(dtype=float)

        meta = charger_metadonnees()
        X = profil[meta["variables"]]
        X_prep = brut.named_steps["prep"].transform(X)
        valeurs = explicateur.shap_values(X_prep)
        if isinstance(valeurs, list):
            valeurs = valeurs[1]
        return pd.Series(valeurs[0], index=meta["variables"])
    except Exception:
        return pd.Series(dtype=float)
