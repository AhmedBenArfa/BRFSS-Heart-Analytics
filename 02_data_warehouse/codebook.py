"""Codebook BRFSS 2015 — libellés d'affichage des dimensions.

Ce module est la source unique des libellés lisibles utilisés par l'entrepôt.
Il traduit les codes numériques de la source (« 9 ») en texte (« 60-64 ans »),
de sorte que Power BI et les exports affichent des modalités compréhensibles.

Ces libellés appartiennent à la couche entrepôt, et non à l'ETL : ils relèvent
de la restitution (comment présenter la donnée), pas de la transformation
(comment la nettoyer). La règle de dérivation des classes d'IMC, elle, reste
dans 01_etl/config.py car elle produit une colonne du modèle.

Source : CDC, BRFSS 2015 Codebook.
"""

# --- Dimensions socio-démographiques ---------------------------------------

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

LIBELLES_SEX = {0: "Femme", 1: "Homme"}

# --- Dimensions de santé ----------------------------------------------------

LIBELLES_GENHLTH = {
    1: "Excellente",
    2: "Très bonne",
    3: "Bonne",
    4: "Moyenne",
    5: "Mauvaise",
}

LIBELLES_DIABETES = {0: "Non", 1: "Prédiabète", 2: "Diabète"}

# Libellés des classes d'IMC. Les codes 1 à 6 sont produits par l'ETL
# (transform.py, via CLASSES_IMC) ; on ne conserve ici que leur traduction.
LIBELLES_BMI_CLASS = {
    1: "Insuffisance pondérale",
    2: "Corpulence normale",
    3: "Surpoids",
    4: "Obésité modérée (I)",
    5: "Obésité sévère (II)",
    6: "Obésité morbide (III)",
}


# --- Description des dimensions à construire --------------------------------
#
# Chaque entrée décrit une dimension du schéma en étoile :
#   - table       : nom de la table de dimension dans l'entrepôt
#   - cle          : nom de la clé primaire de la dimension
#   - colonne_fait : colonne de la table analytique portant le code source
#   - libelle      : nom de la colonne d'attribut lisible
#   - membres      : dictionnaire {code: libellé}
#
# build_star_schema.py itère sur cette liste : ajouter une dimension revient à
# ajouter une entrée ici, sans toucher à la logique de construction.

DIMENSIONS = [
    {
        "table": "dim_age",
        "cle": "age_key",
        "colonne_fait": "age_group",
        "libelle": "tranche_age",
        "membres": LIBELLES_AGE,
    },
    {
        "table": "dim_education",
        "cle": "education_key",
        "colonne_fait": "education",
        "libelle": "niveau_education",
        "membres": LIBELLES_EDUCATION,
    },
    {
        "table": "dim_income",
        "cle": "income_key",
        "colonne_fait": "income",
        "libelle": "tranche_revenu",
        "membres": LIBELLES_INCOME,
    },
    {
        "table": "dim_sex",
        "cle": "sex_key",
        "colonne_fait": "sex",
        "libelle": "sexe",
        "membres": LIBELLES_SEX,
    },
    {
        "table": "dim_genhlth",
        "cle": "genhlth_key",
        "colonne_fait": "gen_hlth",
        "libelle": "sante_generale",
        "membres": LIBELLES_GENHLTH,
    },
    {
        "table": "dim_diabetes",
        "cle": "diabetes_key",
        "colonne_fait": "diabetes",
        "libelle": "statut_diabete",
        "membres": LIBELLES_DIABETES,
    },
    {
        "table": "dim_bmi_class",
        "cle": "bmi_class_key",
        "colonne_fait": "bmi_class",
        "libelle": "classe_imc",
        "membres": LIBELLES_BMI_CLASS,
    },
]
