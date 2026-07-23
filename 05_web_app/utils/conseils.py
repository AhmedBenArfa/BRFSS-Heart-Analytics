"""Moteur de conseils de santé.

Génère des recommandations **éducatives générales** à partir des facteurs de
risque réellement présents dans le profil saisi. Ce ne sont jamais des
prescriptions médicales individuelles : chaque conseil renvoie vers un
professionnel de santé.

Chaque règle est un triplet (condition, titre, message). Les conseils sont
ordonnés par priorité : d'abord les facteurs modifiables les plus déterminants.
"""

from __future__ import annotations

import pandas as pd

# Chaque entrée : (fonction condition sur le profil, icône Material, titre, message)
REGLES = [
    (
        lambda p: p["high_bp"] == 1,
        ":material/cardiology:",
        "Hypertension artérielle",
        "L'hypertension est l'un des principaux facteurs de risque "
        "cardiovasculaire. Un suivi régulier de la tension, une alimentation "
        "moins salée et l'activité physique y contribuent favorablement. "
        "Discutez de votre tension avec votre médecin.",
    ),
    (
        lambda p: p["smoker"] == 1,
        ":material/smoke_free:",
        "Tabagisme",
        "L'arrêt du tabac est l'action isolée la plus bénéfique pour le cœur : "
        "le risque cardiovasculaire commence à baisser dès les premières "
        "semaines. Des dispositifs d'aide au sevrage existent — un professionnel "
        "de santé peut vous accompagner.",
    ),
    (
        lambda p: p["high_chol"] == 1,
        ":material/water_drop:",
        "Cholestérol élevé",
        "Un cholestérol élevé favorise l'athérosclérose. Une alimentation riche "
        "en fibres, pauvre en graisses saturées, et l'activité physique aident à "
        "le réguler. Un bilan lipidique régulier est recommandé.",
    ),
    (
        lambda p: p["diabetes"] >= 1,
        ":material/glucose:",
        "Diabète ou prédiabète",
        "Le diabète multiplie le risque cardiovasculaire. Un bon contrôle de la "
        "glycémie, une alimentation équilibrée et une activité physique régulière "
        "sont essentiels. Un suivi médical adapté est indispensable.",
    ),
    (
        lambda p: p["phys_activity"] == 0,
        ":material/directions_run:",
        "Sédentarité",
        "L'activité physique régulière est associée à une réduction nette du "
        "risque cardiovasculaire. Les recommandations générales évoquent environ "
        "150 minutes d'activité modérée par semaine — même la marche compte. "
        "Commencez progressivement.",
    ),
    (
        lambda p: p["bmi"] >= 30,
        ":material/monitor_weight:",
        "Surpoids important (IMC ≥ 30)",
        "Un excès de poids sollicite le système cardiovasculaire. Une perte de "
        "poids même modérée, par une alimentation équilibrée et de l'activité, "
        "améliore plusieurs facteurs de risque à la fois. Un accompagnement "
        "diététique peut aider.",
    ),
    (
        lambda p: (p["fruits"] == 0) or (p["veggies"] == 0),
        ":material/nutrition:",
        "Alimentation",
        "Une consommation quotidienne de fruits et de légumes est associée à une "
        "meilleure santé cardiovasculaire. Viser au moins cinq portions par jour "
        "est un objectif simple et bénéfique.",
    ),
    (
        lambda p: p["hvy_alcohol"] == 1,
        ":material/no_drinks:",
        "Consommation d'alcool",
        "Une consommation excessive d'alcool pèse sur le cœur et la tension. "
        "Réduire sa consommation est bénéfique ; un professionnel de santé peut "
        "vous orienter si besoin.",
    ),
    (
        lambda p: (p["any_healthcare"] == 0) or (p["no_doc_cost"] == 1),
        ":material/local_hospital:",
        "Accès aux soins",
        "Un suivi médical régulier permet de détecter et traiter tôt les facteurs "
        "de risque. Si l'accès aux soins est difficile, des dispositifs d'aide "
        "existent selon votre situation — renseignez-vous auprès des structures "
        "de santé locales.",
    ),
]

# Message positif quand aucun facteur modifiable n'est présent.
CONSEIL_FAVORABLE = (
    ":material/check_circle:",
    "Profil favorable",
    "Aucun facteur de risque modifiable majeur n'a été signalé dans votre "
    "profil. Maintenir une activité physique régulière, une alimentation "
    "équilibrée et un suivi médical périodique reste la meilleure prévention.",
)


def generer(profil: pd.DataFrame) -> list[tuple[str, str, str]]:
    """Renvoie la liste des conseils (icône, titre, message) pour un profil.

    `profil` est un DataFrame d'une seule ligne, tel que construit par la page
    d'évaluation.
    """
    ligne = profil.iloc[0]
    conseils = [
        (icone, titre, message)
        for condition, icone, titre, message in REGLES
        if condition(ligne)
    ]
    return conseils if conseils else [CONSEIL_FAVORABLE]
