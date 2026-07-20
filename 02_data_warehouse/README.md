# 02 — Entrepôt de données

Schéma en étoile construit sous **DuckDB** (choisi pour son absence totale de
configuration : une base = un fichier).

## Modèle dimensionnel

- **Table de faits** : `fact_respondent` — grain = un répondant à l'enquête
- **Dimensions** : `dim_age`, `dim_education`, `dim_income`, `dim_genhlth`,
  `dim_sex`, `dim_diabetes`, `dim_bmi_class`

Les dimensions sont reconstruites à partir du **codebook BRFSS**, ce qui permet
d'afficher des libellés lisibles (« 55-59 ans ») plutôt que les codes numériques
bruts (« 9.0 ») dans Power BI.

## Fichiers

| Fichier | Rôle |
|---|---|
| `create_star_schema.sql` | DDL du schéma — source de vérité du modèle |
| `build_star_schema.py` | Exécute le DDL et produit les exports CSV/Parquet |
| `explore_warehouse.py` | Inspecteur en lecture seule |
| `exports/` | Exports CSV et Parquet (repli hors ligne pour Power BI) |

## Exécution

```bash
python build_star_schema.py
python explore_warehouse.py                   # tables + volumétrie
python explore_warehouse.py fact_respondent   # aperçu d'une table
python explore_warehouse.py "SELECT AVG(heart_disease) FROM fact_respondent"
```

> ⚠️ **Verrou DuckDB** : un seul processus peut écrire à la fois. Fermer Power BI
> et tout noyau Jupyter avant de reconstruire l'entrepôt.
