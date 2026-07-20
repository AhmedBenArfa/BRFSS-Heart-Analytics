# 03 — Power BI

Rapport décisionnel branché sur l'entrepôt DuckDB.

## Fichiers

| Fichier | Rôle |
|---|---|
| `GUIDE_POWERBI.md` | Guide pas à pas : connexion, relations, construction des pages |
| `mesures_dax.md` | Ensemble des mesures DAX et des KPI |
| `screenshots/` | Captures des pages du rapport (versionnées) |
| `Rapport.pbix` | Le rapport lui-même (**ignoré par Git** — trop volumineux) |

## Source de données

Connexion **ODBC directe** vers `02_data_warehouse/heart.duckdb`
(`access_mode=read_only`). Les exports CSV/Parquet servent de repli si le pilote
ODBC n'est pas disponible.
