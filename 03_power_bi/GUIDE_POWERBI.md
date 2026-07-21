# Guide de construction du rapport Power BI

Ce guide décrit, étape par étape, la construction du rapport décisionnel à partir
de l'entrepôt DuckDB. Il est destiné à être suivi dans **Power BI Desktop** (le
fichier `.pbix` se construit côté utilisateur — il est ignoré par Git).

---

## 1. Prérequis

- **Power BI Desktop** installé (Windows).
- L'entrepôt construit : avoir exécuté `01_etl/run_etl.py` puis
  `02_data_warehouse/build_star_schema.py`.
- **Le pilote ODBC de DuckDB** installé, et une **source de données ODBC** nommée
  `heart_duckdb` pointant vers `02_data_warehouse/heart.duckdb`, en mode
  `access_mode=read_only`.

> **Pourquoi le mode lecture seule ?** DuckDB n'autorise qu'un seul processus en
> écriture, mais plusieurs lecteurs simultanés. En connectant Power BI en lecture
> seule, on peut continuer à interroger l'entrepôt (et même le reconstruire depuis
> un autre processus) sans conflit de verrou.

### Configurer la source ODBC

Une **DSN utilisateur** suffit (elle ne demande pas de droits administrateur,
contrairement à une DSN système) et fonctionne parfaitement avec Power BI :

1. Ouvrir **Sources de données ODBC (64 bits)** (menu Démarrer).
2. Onglet **DSN utilisateur → Ajouter → DuckDB Driver**.
3. Nom de la source : `heart_duckdb`.
4. `database` : chemin absolu vers `heart.duckdb`.
5. `access_mode` : `read_only`.

> La DSN de ce projet a été créée par script (PowerShell `Add-OdbcDsn`) en DSN
> utilisateur, avec `database` pointant sur `heart.duckdb` et
> `access_mode=read_only`. Connexion vérifiée : les 9 tables sont lisibles.

---

## 2. Connexion des données

1. **Accueil → Obtenir les données → ODBC → `heart_duckdb`**.
2. Sélectionner les **8 tables** du schéma en étoile :
   - `fact_respondent`
   - `dim_age`, `dim_education`, `dim_income`, `dim_sex`, `dim_genhlth`,
     `dim_diabetes`, `dim_bmi_class`
3. **Ne pas** importer `analytical_base` : c'est la table technique de l'ETL, hors
   du modèle dimensionnel.
4. Charger.

> **Alternative hors ligne** : si le pilote ODBC n'est pas disponible, utiliser les
> exports du dossier `02_data_warehouse/exports/parquet/` (Obtenir les données →
> Parquet). Le modèle et les mesures restent identiques.

---

## 3. Relations du modèle

Power BI détecte souvent les relations automatiquement. Vérifier dans la vue
**Modèle** que chaque dimension est reliée au fait par sa clé, en relation
**un-à-plusieurs** (la dimension étant du côté « un ») :

| Dimension | Clé | Table de faits |
|---|---|---|
| `dim_age` | `age_key` | `fact_respondent.age_key` |
| `dim_education` | `education_key` | `fact_respondent.education_key` |
| `dim_income` | `income_key` | `fact_respondent.income_key` |
| `dim_sex` | `sex_key` | `fact_respondent.sex_key` |
| `dim_genhlth` | `genhlth_key` | `fact_respondent.genhlth_key` |
| `dim_diabetes` | `diabetes_key` | `fact_respondent.diabetes_key` |
| `dim_bmi_class` | `bmi_class_key` | `fact_respondent.bmi_class_key` |

Le sens de filtrage doit être **simple** (de la dimension vers le fait).

> Grâce au **nommage cohérent des clés** (`<dim>_key` identique dans le fait et la
> dimension), Power BI détecte et câble les 7 relations automatiquement au
> chargement. Aucune relation n'est à tracer à la main.

Schéma conceptuel : `screenshots/schema_etoile.png`. Vue du modèle réel dans Power
BI : `screenshots/modele_relations_powerbi.png`.

---

## 4. Mesures

Créer les mesures DAX listées dans **`mesures_dax.md`**. Les regrouper dans une
table de mesures dédiée (Accueil → Entrer des données → table vide `_Mesures`)
pour garder le modèle propre.

---

## 5. Pages du rapport

Le rapport compte **6 pages** : 2 descriptives (qui décrivent la population) et 4
analytiques (qui expliquent le risque). Ordre du général au spécifique.

### Page 1 — Vue d'ensemble
- **4 cartes KPI** : `Nb Repondants`, `Taux Maladie Cardiaque`, `IMC Moyen`,
  `Facteurs Risque Moyens`.
- **Histogramme** : `Taux Maladie Cardiaque` par `tranche_age` (montée 0,5 % → 24 %).
- **Anneau** : répartition `Statut cardiaque` (Atteint / Non atteint).

### Page 2 — Facteurs de risque
- **Histogramme** : `Taux Maladie Cardiaque` par `risk_factor_count` — le gradient
  de 1,2 % à 59 %.
- **Courbe** : `Taux Maladie Cardiaque` par `classe_imc` — la courbe en J.
- **Histogramme** : `Taux Hypertension` par `Statut cardiaque`.

### Page 3 — Profil socio-démographique
- **Histogramme** : `Taux Maladie Cardiaque` par `tranche_revenu`.
- **Histogramme** : `Taux Maladie Cardiaque` par `niveau_education`.
- **Histogramme** : `Taux Maladie Cardiaque` par `tranche_age`, légende `sexe`.
- **Segment** : `sexe`.

### Page 4 — Santé perçue et diabète
- **Histogramme** : `Taux Maladie Cardiaque` par `sante_generale`.
- **Histogramme** : `Taux Maladie Cardiaque` par `statut_diabete`.
- **Nuage de points** : `IMC Moyen` × `Taux Maladie Cardiaque`, détail `tranche_age`.

### Page 5 — Profil de la population (descriptive)
- **Histogramme** : `Nb Repondants` par `tranche_age` (pyramide des âges).
- **Anneau** : `Nb Repondants` par `sexe`.
- **Histogramme** : `Nb Repondants` par `tranche_revenu`.
- **Histogramme** : `Nb Repondants` par `bmi (compartiments)` (distribution de l'IMC).

### Page 6 — Habitudes de vie et santé (descriptive)
- **5 cartes KPI** : `Taux Fumeurs`, `Taux Activite Physique`,
  `Taux Consommation Fruits`, `Taux Consommation Legumes`, `Taux Acces Soins`.
- **Histogramme** : `Nb Repondants` par `sante_generale`.
- **Courbe** : `Jours Malaise Moyens` par `tranche_age`.

> **Tri des axes catégoriels** : les libellés texte (`tranche_age`,
> `tranche_revenu`, `niveau_education`, `sante_generale`, `statut_diabete`,
> `classe_imc`) sont ordonnés via **Outils de colonnes → Trier par colonne**, en
> pointant vers la clé numérique correspondante (`age_key`, `income_key`, etc.).
> Sans cela, Power BI trie alphabétiquement.

---

## 6. Mise en forme

- Palette cohérente avec le reste du projet : bleu marine (`#1F3B5C`) pour les
  éléments descriptifs, rouge (`#C1443F`) pour ce qui touche à la maladie.
- Un titre par page (Insérer → Zone de texte).
- Note de source rappelant l'origine (BRFSS 2015, CDC) et la limite
  d'interprétation (associations transversales).

---

## 7. Captures

Les captures des 6 pages sont dans `03_power_bi/screenshots/`
(`page1_vue_ensemble.png` … `page6_habitudes_vie.png`), avec la vue du modèle
relationnel (`modele_relations_powerbi.png`). Elles sont versionnées et réutilisées
dans le rapport et la présentation ; le `.pbix`, lui, reste hors du dépôt.
