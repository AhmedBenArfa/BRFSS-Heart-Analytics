# 04 — Machine Learning

Modélisation du risque de maladie cardiovasculaire (classification binaire,
classes déséquilibrées : 9,42 % de positifs).

## Fichiers

| Fichier | Rôle |
|---|---|
| `config.py` | Listes de variables, chemins, graine aléatoire |
| `data_prep.py` | Chargement depuis DuckDB, découpage entraînement/test |
| `preprocessing.py` | `ColumnTransformer` (mise à l'échelle + encodage), sauvegardé avec le modèle |
| `notebooks/01_ml.ipynb` | Livrable ML complet (généré par `_build_ml.py`) |
| `models/` | Modèle entraîné et ses métadonnées |

## Démarche

Comparaison de plusieurs familles de modèles (régression logistique, kNN, arbre
de décision, SVM, forêt aléatoire, XGBoost), sélection par **ROC-AUC** avec
report du **PR-AUC**, du rappel et du F1 — indispensables sur des classes
déséquilibrées. Interprétation par **SHAP**.
