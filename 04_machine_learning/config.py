"""Configuration centrale du module de machine learning.

Regroupe les chemins, les listes de variables, les paramètres de découpage et la
graine aléatoire. Aucun autre module ne code en dur un chemin ou une liste.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------

RACINE = Path(__file__).resolve().parent.parent
BASE_DUCKDB = RACINE / "02_data_warehouse" / "heart.duckdb"
TABLE = "analytical_base"

DOSSIER_MODELES = Path(__file__).resolve().parent / "models"
MODELE_FINAL = DOSSIER_MODELES / "heart_model.joblib"
METADONNEES = DOSSIER_MODELES / "metadata.json"

# ---------------------------------------------------------------------------
# Cible et découpage
# ---------------------------------------------------------------------------

CIBLE = "heart_disease"

GRAINE = 42
TAILLE_TEST = 0.20

# Le jeu complet compte 253 680 lignes. La phase de COMPARAISON des modèles
# s'effectue sur un échantillon stratifié : certains algorithmes (kNN, SVM) ont
# un coût prohibitif à cette volumétrie, et une comparaison n'est équitable que
# si tous les modèles voient exactement les mêmes données. Le modèle retenu est
# ensuite réentraîné sur l'intégralité du jeu d'entraînement.
TAILLE_COMPARAISON = 80_000

# ---------------------------------------------------------------------------
# Variables explicatives
#
# On retient les 21 variables d'origine, à l'exclusion :
#   - de la cible ;
#   - des variables dérivées de l'ETL (risk_factor_count, etc.), qui sont des
#     fonctions déterministes des colonnes ci-dessous et n'apporteraient que de
#     la redondance ;
#   - des drapeaux qualité, qui décrivent la donnée et non le répondant.
# ---------------------------------------------------------------------------

# Mesures continues : à centrer-réduire.
VARIABLES_CONTINUES = ["bmi", "ment_hlth_days", "phys_hlth_days"]

# Variables ordinales (l'ordre des codes a un sens) : conservées telles quelles
# puis centrées-réduites, ce qui préserve la monotonie.
VARIABLES_ORDINALES = ["gen_hlth", "age_group", "education", "income", "diabetes"]

# Indicateurs déjà codés 0/1 : aucune mise à l'échelle nécessaire.
VARIABLES_BINAIRES = [
    "high_bp", "high_chol", "chol_check", "smoker", "stroke", "phys_activity",
    "fruits", "veggies", "hvy_alcohol", "any_healthcare", "no_doc_cost",
    "diff_walk", "sex",
]

VARIABLES = VARIABLES_CONTINUES + VARIABLES_ORDINALES + VARIABLES_BINAIRES

# ---------------------------------------------------------------------------
# Évaluation
# ---------------------------------------------------------------------------

# Métrique de sélection : le ROC-AUC est indépendant du seuil et compare les
# modèles sur leur capacité à ORDONNER le risque — ce qui correspond à l'usage
# visé (estimer un risque, pas trancher un diagnostic).
# Le PR-AUC sert d'arbitre : centré sur la classe minoritaire, il départage deux
# modèles aux ROC-AUC proches.
METRIQUE_SELECTION = "roc_auc"

METRIQUES = {
    "roc_auc": "roc_auc",
    "pr_auc": "average_precision",
    "rappel": "recall",
    "f1": "f1",
    "precision": "precision",
}

NB_PLIS = 5

# Seuil de décision de l'application : choisi APRÈS la sélection du modèle, pour
# atteindre un rappel cible. En santé, un faux négatif (rater une personne à
# risque) coûte plus qu'un faux positif (recommander une visite inutile).
RAPPEL_CIBLE = 0.75
