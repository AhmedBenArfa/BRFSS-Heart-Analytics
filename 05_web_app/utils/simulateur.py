"""Simulateur « et si… » : impact des changements modifiables sur le risque.

À partir d'un profil, on recalcule le risque estimé après modification d'un
facteur **sur lequel une personne peut agir** (tabac, activité, poids, tension…).
Les facteurs non modifiables (âge, sexe) sont exclus par construction.

Chaque scénario n'est proposé que s'il est **pertinent** : inutile de suggérer
« arrêter de fumer » à un non-fumeur.
"""

from __future__ import annotations

import pandas as pd

from utils.modele import estimer

# Chaque scénario : (condition de pertinence, icône, libellé, modifications).
# Les modifications sont appliquées à une copie du profil.
SCENARIOS = [
    (
        lambda p: p["smoker"] == 1,
        ":material/smoke_free:",
        "Arrêter de fumer",
        {"smoker": 0},
    ),
    (
        lambda p: p["phys_activity"] == 0,
        ":material/directions_run:",
        "Reprendre une activité physique",
        {"phys_activity": 1},
    ),
    (
        lambda p: p["bmi"] >= 25,
        ":material/monitor_weight:",
        "Atteindre un IMC de 24 (corpulence normale)",
        {"bmi": 24.0},
    ),
    (
        lambda p: p["high_bp"] == 1,
        ":material/cardiology:",
        "Faire baisser la tension (traitement / hygiène de vie)",
        {"high_bp": 0},
    ),
    (
        lambda p: p["high_chol"] == 1,
        ":material/water_drop:",
        "Faire baisser le cholestérol",
        {"high_chol": 0},
    ),
    (
        lambda p: (p["fruits"] == 0) or (p["veggies"] == 0),
        ":material/nutrition:",
        "Fruits et légumes au quotidien",
        {"fruits": 1, "veggies": 1},
    ),
    (
        lambda p: p["hvy_alcohol"] == 1,
        ":material/no_drinks:",
        "Réduire la consommation d'alcool",
        {"hvy_alcohol": 0},
    ),
]


def _applique(profil: pd.DataFrame, modifs: dict) -> pd.DataFrame:
    copie = profil.copy()
    for variable, valeur in modifs.items():
        copie[variable] = valeur
    return copie


def scenarios(profil: pd.DataFrame, risque_actuel: float) -> list[dict]:
    """Liste des scénarios pertinents avec le risque et le gain associés.

    Chaque élément : {icone, libelle, risque, delta}. `delta` est négatif quand
    le changement réduit le risque (le cas attendu).
    """
    pertinents = [
        (icone, libelle, modifs)
        for condition, icone, libelle, modifs in SCENARIOS
        if condition(profil.iloc[0])
    ]
    if not pertinents:
        return []

    resultats = []
    for icone, libelle, modifs in pertinents:
        risque = float(estimer(_applique(profil, modifs)).iloc[0])
        resultats.append({
            "icone": icone,
            "libelle": libelle,
            "risque": risque,
            "delta": risque - risque_actuel,
        })

    return sorted(resultats, key=lambda s: s["delta"])


def scenario_combine(profil: pd.DataFrame) -> dict | None:
    """Risque atteignable en cumulant TOUS les changements modifiables pertinents."""
    modifs_totales: dict = {}
    for condition, _icone, _libelle, modifs in SCENARIOS:
        if condition(profil.iloc[0]):
            modifs_totales.update(modifs)

    if not modifs_totales:
        return None

    risque = float(estimer(_applique(profil, modifs_totales)).iloc[0])
    return {"risque": risque, "nb_changements": len(modifs_totales)}
