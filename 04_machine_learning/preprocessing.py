"""Construction du préprocesseur.

Point méthodologique central : le préprocesseur est un objet **scikit-learn**
intégré à un `Pipeline`. Il est donc ajusté (`fit`) sur le seul jeu
d'entraînement, puis appliqué au jeu de test. Cela évite la **fuite de données**
— si l'on calculait moyennes et écarts-types sur l'ensemble du jeu, les
statistiques du test contamineraient l'apprentissage et l'évaluation serait
optimiste.

Le préprocesseur est sauvegardé avec le modèle : l'application web appliquera
exactement les mêmes transformations qu'à l'entraînement.
"""

from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler

import config


def construire_preprocesseur() -> ColumnTransformer:
    """Assemble les transformations par groupe de variables.

    - Continues et ordinales : centrage-réduction. Indispensable pour les modèles
      fondés sur des distances (kNN, SVM) ou sur une pénalisation (régression
      logistique). Sur les variables ordinales, la transformation est monotone :
      l'ordre des modalités est préservé.
    - Binaires : laissées telles quelles. Déjà codées 0/1, les mettre à l'échelle
      n'apporterait rien.

    Le même préprocesseur est utilisé pour TOUS les modèles, y compris ceux à base
    d'arbres (pour lesquels il est neutre), afin que la comparaison ne porte que
    sur les algorithmes et non sur des préparations différentes.
    """
    return ColumnTransformer(
        transformers=[
            ("continues", StandardScaler(), config.VARIABLES_CONTINUES),
            ("ordinales", StandardScaler(), config.VARIABLES_ORDINALES),
            ("binaires", "passthrough", config.VARIABLES_BINAIRES),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def noms_variables() -> list[str]:
    """Noms des colonnes en sortie du préprocesseur, dans l'ordre.

    Utile pour interpréter les coefficients et les valeurs SHAP.
    """
    return (
        config.VARIABLES_CONTINUES
        + config.VARIABLES_ORDINALES
        + config.VARIABLES_BINAIRES
    )
