# BRFSS Heart Analytics — Analyse et Prédiction du Risque Cardiovasculaire

> **Auteur** : Ahmed Ben Arfa
> **Type** : Projet personnel de data analytics / machine learning
> **Année** : 2026

Chaîne analytique complète construite sur les données de santé publique
**BRFSS 2015** (Behavioral Risk Factor Surveillance System, CDC) :

**Données brutes → ETL → Entrepôt de données (schéma en étoile) → Power BI →
Machine Learning → Data Mining → Application web déployée → Rapport → Présentation.**

## Objectif

Estimer le **risque de maladie ou d'accident cardiaque** d'une personne à partir de
son profil de santé déclaré (tension, cholestérol, IMC, tabac, activité physique,
diabète, état de santé perçu, données socio-démographiques), et identifier les
facteurs les plus déterminants.

## Source des données

- **Jeu de données** : [Heart Disease Health Indicators Dataset](https://www.kaggle.com/datasets/alexteboul/heart-disease-health-indicators-dataset) (Kaggle)
- **Source primaire** : CDC — *Behavioral Risk Factor Surveillance System*, édition 2015
- **Volume** : 253 680 répondants × 22 variables
- **Variable cible** : `HeartDiseaseorAttack` — 9,42 % de cas positifs (classes déséquilibrées)
- **Licence** : données publiques

> ⚠️ **Note méthodologique** : les variables explicatives sont auto-déclarées **au
> même moment** que la variable cible. Le modèle mesure donc une **association
> transversale** (estimer un risque à partir d'un profil), et non une prédiction
> d'un événement futur. Cette limite est assumée et discutée dans le rapport.

## Structure du dépôt

| Dossier | Contenu |
|---|---|
| `00_documentation/` | Cadrage du projet, description des données, planning |
| `01_etl/` | Extraction, nettoyage, transformation + notebook d'analyse exploratoire |
| `02_data_warehouse/` | Schéma en étoile DuckDB, scripts de chargement, exports |
| `03_power_bi/` | Guide de construction, mesures DAX, captures du rapport |
| `04_machine_learning/` | Préparation, préprocessing, comparaison de modèles, modèle final |
| `05_web_app/` | Application Streamlit de prédiction du risque |
| `06_rapport/` | Documentations techniques et rapport final (PDF) |
| `07_presentation/` | Support de présentation HTML |
| `08_data_mining/` | ACP, clustering, réduction de dimension |
| `data/` | Jeu de données source (versionné — données publiques) |

## Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/AhmedBenArfa/BRFSS-Heart-Analytics.git
cd BRFSS-Heart-Analytics

# 2. Créer un environnement virtuel
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Linux / macOS

# 3. Installer les dépendances
pip install -r requirements.txt
```

Le jeu de données est inclus dans le dépôt : aucun téléchargement supplémentaire
n'est nécessaire.

## Exécution du pipeline

```bash
# 1. ETL : données brutes -> table analytique
cd 01_etl && python run_etl.py

# 2. Entrepôt : schéma en étoile + exports CSV/Parquet
cd ../02_data_warehouse && python build_star_schema.py

# 3. Inspection de l'entrepôt
python explore_warehouse.py                  # tables + volumétrie
python explore_warehouse.py fact_respondent  # aperçu
```

## Conventions du projet

- **Les notebooks sont générés** depuis un script `_build_*.py`. Pour modifier un
  notebook, on modifie le générateur puis on régénère — on n'édite jamais le
  `.ipynb` à la main.
- **Les PDF sont générés** par script, en lisant les fichiers sources vivants du
  dépôt : la documentation ne peut pas diverger du code.
- **Reproductibilité** : tout livrable doit pouvoir être reconstruit à partir du
  dépôt cloné et de `requirements.txt`.

## Avancement

| Module | État |
|---|---|
| 00 — Documentation | ✅ Terminé (projet, données, démarche — MD + PDF) |
| 01 — ETL + EDA | ✅ Terminé |
| 02 — Entrepôt de données | ✅ Terminé |
| 03 — Power BI | ✅ Terminé (rapport 6 pages, captures dans `03_power_bi/screenshots/`) |
| 04 — Machine Learning | ✅ Terminé (XGBoost, ROC-AUC 0,850 sur test) |
| 08 — Data Mining | ✅ Terminé (ACP, clustering k=4, CAH, t-SNE) |
| 05 — Application web | ✅ Terminé (3 pages, modèle calibré) |
| 06 — Rapport | 🚧 Docs techniques ETL/EDA et Entrepôt/Power BI générées |
| 07 — Présentation | 🔜 À faire |

## Livrables

1. Ce dépôt GitHub, public et documenté
2. Le rapport PDF (`06_rapport/`)
3. Le support de présentation (`07_presentation/`)
4. L'URL publique de l'application web _(à compléter après déploiement)_
