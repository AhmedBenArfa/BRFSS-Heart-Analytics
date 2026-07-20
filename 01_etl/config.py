"""Configuration centrale du pipeline ETL.

Regroupe les chemins, la définition de la cible, les groupes de colonnes et le
codebook BRFSS 2015. Aucun autre module ne code en dur un chemin ou un libellé.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------

RACINE = Path(__file__).resolve().parent.parent

FICHIER_SOURCE = RACINE / "data" / "heart_disease_health_indicators_BRFSS2015.csv"
BASE_DUCKDB = RACINE / "02_data_warehouse" / "heart.duckdb"

TABLE_ANALYTIQUE = "analytical_base"

# ---------------------------------------------------------------------------
# Cible
# ---------------------------------------------------------------------------

COLONNE_CIBLE_SOURCE = "HeartDiseaseorAttack"
COLONNE_CIBLE = "heart_disease"

# ---------------------------------------------------------------------------
# Renommage : CamelCase de la source -> snake_case
#
# La source est déjà propre et encodée ; on se contente d'harmoniser le nommage
# pour que les colonnes soient utilisables telles quelles en SQL.
# ---------------------------------------------------------------------------

RENOMMAGE = {
    "HeartDiseaseorAttack": "heart_disease",
    "HighBP": "high_bp",
    "HighChol": "high_chol",
    "CholCheck": "chol_check",
    "BMI": "bmi",
    "Smoker": "smoker",
    "Stroke": "stroke",
    "Diabetes": "diabetes",
    "PhysActivity": "phys_activity",
    "Fruits": "fruits",
    "Veggies": "veggies",
    "HvyAlcoholConsump": "hvy_alcohol",
    "AnyHealthcare": "any_healthcare",
    "NoDocbcCost": "no_doc_cost",
    "GenHlth": "gen_hlth",
    "MentHlth": "ment_hlth_days",
    "PhysHlth": "phys_hlth_days",
    "DiffWalk": "diff_walk",
    "Sex": "sex",
    "Age": "age_group",
    "Education": "education",
    "Income": "income",
}

# ---------------------------------------------------------------------------
# Groupes de colonnes
# ---------------------------------------------------------------------------

# Indicateurs binaires (0/1) — conditions médicales et comportements
COLONNES_BINAIRES = [
    "high_bp",
    "high_chol",
    "chol_check",
    "smoker",
    "stroke",
    "phys_activity",
    "fruits",
    "veggies",
    "hvy_alcohol",
    "any_healthcare",
    "no_doc_cost",
    "diff_walk",
]

# Variables ordinales issues du codebook (deviendront des dimensions)
COLONNES_ORDINALES = ["gen_hlth", "age_group", "education", "income"]

# Variables catégorielles nominales
COLONNES_CATEGORIELLES = ["sex", "diabetes"]

# Mesures continues / de comptage
COLONNES_NUMERIQUES = ["bmi", "ment_hlth_days", "phys_hlth_days"]

# ---------------------------------------------------------------------------
# Domaines attendus — utilisés par checks.py pour valider la source
# ---------------------------------------------------------------------------

DOMAINES = {
    **{col: {0, 1} for col in COLONNES_BINAIRES},
    "heart_disease": {0, 1},
    "sex": {0, 1},
    "diabetes": {0, 1, 2},
    "gen_hlth": set(range(1, 6)),
    "age_group": set(range(1, 14)),
    "education": set(range(1, 7)),
    "income": set(range(1, 9)),
}

BORNES = {
    "bmi": (12, 98),
    "ment_hlth_days": (0, 30),
    "phys_hlth_days": (0, 30),
}

# ---------------------------------------------------------------------------
# Codebook BRFSS 2015 — libellés lisibles
#
# Source : CDC, BRFSS 2015 Codebook. Ces libellés alimentent les dimensions de
# l'entrepôt afin que Power BI affiche « 55-59 ans » et non « 9.0 ».
# ---------------------------------------------------------------------------

LIBELLES_AGE = {
    1: "18-24 ans",
    2: "25-29 ans",
    3: "30-34 ans",
    4: "35-39 ans",
    5: "40-44 ans",
    6: "45-49 ans",
    7: "50-54 ans",
    8: "55-59 ans",
    9: "60-64 ans",
    10: "65-69 ans",
    11: "70-74 ans",
    12: "75-79 ans",
    13: "80 ans et plus",
}

LIBELLES_EDUCATION = {
    1: "Aucune scolarité",
    2: "Primaire",
    3: "Secondaire non achevé",
    4: "Secondaire achevé",
    5: "Supérieur non achevé",
    6: "Diplômé du supérieur",
}

LIBELLES_INCOME = {
    1: "Moins de 10 000 $",
    2: "10 000 à 15 000 $",
    3: "15 000 à 20 000 $",
    4: "20 000 à 25 000 $",
    5: "25 000 à 35 000 $",
    6: "35 000 à 50 000 $",
    7: "50 000 à 75 000 $",
    8: "75 000 $ et plus",
}

LIBELLES_GENHLTH = {
    1: "Excellente",
    2: "Très bonne",
    3: "Bonne",
    4: "Moyenne",
    5: "Mauvaise",
}

LIBELLES_SEX = {0: "Femme", 1: "Homme"}

LIBELLES_DIABETES = {0: "Non", 1: "Prédiabète", 2: "Diabète"}

# Classes d'IMC selon l'Organisation mondiale de la santé.
# Bornes sous la forme (minimum inclus, maximum exclu).
CLASSES_IMC = [
    (0.0, 18.5, 1, "Insuffisance pondérale"),
    (18.5, 25.0, 2, "Corpulence normale"),
    (25.0, 30.0, 3, "Surpoids"),
    (30.0, 35.0, 4, "Obésité modérée (I)"),
    (35.0, 40.0, 5, "Obésité sévère (II)"),
    (40.0, float("inf"), 6, "Obésité morbide (III)"),
]

# ---------------------------------------------------------------------------
# Seuils qualité
# ---------------------------------------------------------------------------

# Un IMC hors de cet intervalle est physiologiquement très improbable : on le
# signale sans le supprimer ni le corriger (le fait reste fidèle à la source).
IMC_MIN_PLAUSIBLE = 14.0
IMC_MAX_PLAUSIBLE = 60.0

# Volumétrie attendue de la source — un écart signale un fichier inattendu.
NB_LIGNES_ATTENDU = 253_680
NB_COLONNES_ATTENDU = 22
