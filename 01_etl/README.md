# 01 — ETL et analyse exploratoire

Chaîne d'extraction, de nettoyage et de transformation des données BRFSS 2015,
de la source brute vers la table analytique chargée dans DuckDB.

## Fichiers

| Fichier | Rôle |
|---|---|
| `config.py` | Chemins, groupes de colonnes, libellés du codebook, définition de la cible |
| `extract.py` | Lecture du CSV source |
| `transform.py` | Nettoyage, typage, variables dérivées, drapeaux qualité |
| `checks.py` | Contrôles qualité bloquants avant chargement |
| `load.py` | Écriture de la table analytique dans `heart.duckdb` |
| `run_etl.py` | Orchestrateur du pipeline |
| `notebooks/01_eda.ipynb` | Analyse exploratoire (généré par `_build_eda.py`) |

## Exécution

```bash
python run_etl.py              # pipeline complet
python run_etl.py --sample 5000  # échantillon, pour tester rapidement
```

> Le notebook est **généré** : modifier `_build_eda.py`, puis régénérer et
> réexécuter. Ne pas éditer le `.ipynb` à la main.
