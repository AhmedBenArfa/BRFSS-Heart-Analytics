# 03 — Power BI

Rapport décisionnel branché sur l'entrepôt DuckDB. **6 pages** : 2 descriptives
(profil de la population, habitudes de vie) et 4 analytiques (vue d'ensemble,
facteurs de risque, profil socio-démographique, santé perçue et diabète).

## Fichiers

| Fichier | Rôle |
|---|---|
| `GUIDE_POWERBI.md` | Guide pas à pas : connexion ODBC, relations, les 6 pages |
| `mesures_dax.md` | Mesures et colonnes calculées créées dans le rapport |
| `screenshots/` | Captures des 6 pages + modèle relationnel (versionnées) |
| `HeartDiseasePowerBI.pbix` | Le rapport lui-même (**versionné** — données publiques, ~3,6 Mo, ouvrable après clone) |

## Source de données

Connexion **ODBC directe** vers `02_data_warehouse/heart.duckdb`
(`access_mode=read_only`), via la DSN utilisateur `heart_duckdb`. Les exports
CSV/Parquet de `02_data_warehouse/exports/` servent de repli si le pilote ODBC
n'est pas disponible.
