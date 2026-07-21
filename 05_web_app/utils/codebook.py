"""Libellés lisibles pour les champs du formulaire.

Reprend le codebook BRFSS 2015 utilisé par l'entrepôt, afin que l'application
présente les mêmes intitulés que le rapport décisionnel.
"""

# --- Variables ordinales : {code: libellé} ---------------------------------

AGE = {
    1: "18-24 ans", 2: "25-29 ans", 3: "30-34 ans", 4: "35-39 ans",
    5: "40-44 ans", 6: "45-49 ans", 7: "50-54 ans", 8: "55-59 ans",
    9: "60-64 ans", 10: "65-69 ans", 11: "70-74 ans", 12: "75-79 ans",
    13: "80 ans et plus",
}

EDUCATION = {
    1: "Aucune scolarité", 2: "Primaire", 3: "Secondaire non achevé",
    4: "Secondaire achevé", 5: "Supérieur non achevé", 6: "Diplômé du supérieur",
}

REVENU = {
    1: "Moins de 10 000 $", 2: "10 000 à 15 000 $", 3: "15 000 à 20 000 $",
    4: "20 000 à 25 000 $", 5: "25 000 à 35 000 $", 6: "35 000 à 50 000 $",
    7: "50 000 à 75 000 $", 8: "75 000 $ et plus",
}

SANTE_GENERALE = {
    1: "Excellente", 2: "Très bonne", 3: "Bonne", 4: "Moyenne", 5: "Mauvaise",
}

DIABETE = {0: "Non", 1: "Prédiabète", 2: "Diabète"}

SEXE = {0: "Femme", 1: "Homme"}

# --- Noms lisibles des variables, pour l'explication des contributions -----

NOMS_VARIABLES = {
    "bmi": "Indice de masse corporelle",
    "ment_hlth_days": "Jours de mal-être mental",
    "phys_hlth_days": "Jours de mal-être physique",
    "gen_hlth": "État de santé perçu",
    "age_group": "Tranche d'âge",
    "education": "Niveau d'études",
    "income": "Revenu du foyer",
    "diabetes": "Diabète",
    "high_bp": "Hypertension",
    "high_chol": "Cholestérol élevé",
    "chol_check": "Dosage du cholestérol",
    "smoker": "Tabagisme",
    "stroke": "Antécédent d'AVC",
    "phys_activity": "Activité physique",
    "fruits": "Consommation de fruits",
    "veggies": "Consommation de légumes",
    "hvy_alcohol": "Consommation d'alcool excessive",
    "any_healthcare": "Couverture santé",
    "no_doc_cost": "Renoncement aux soins (coût)",
    "diff_walk": "Difficulté à marcher",
    "sex": "Sexe",
}


def libelle(variable: str) -> str:
    """Nom lisible d'une variable, ou la variable elle-même si inconnue."""
    return NOMS_VARIABLES.get(variable, variable)
