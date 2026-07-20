# Guide de construction du rapport Power BI

Ce guide décrit, étape par étape, la construction du rapport décisionnel à partir
de l'entrepôt DuckDB. Il est destiné à être suivi dans **Power BI Desktop** (le
fichier `.pbix` se construit côté utilisateur — il est ignoré par Git).

---

## 1. Prérequis

- **Power BI Desktop** installé (Windows).
- L'entrepôt construit : avoir exécuté `01_etl/run_etl.py` puis
  `02_data_warehouse/build_star_schema.py`.
- **Le pilote ODBC de DuckDB** installé, et une **source de données ODBC système**
  nommée `heart_duckdb` pointant vers `02_data_warehouse/heart.duckdb`, en mode
  `access_mode=read_only`.

> **Pourquoi le mode lecture seule ?** DuckDB n'autorise qu'un seul processus en
> écriture, mais plusieurs lecteurs simultanés. En connectant Power BI en lecture
> seule, on peut continuer à interroger l'entrepôt (et même le reconstruire depuis
> un autre processus) sans conflit de verrou.

### Configurer la source ODBC

1. Ouvrir **Outils d'administration Windows → Sources de données ODBC (64 bits)**.
2. Onglet **DSN système → Ajouter → DuckDB Driver**.
3. Nom de la source : `heart_duckdb`.
4. Base de données : chemin absolu vers `heart.duckdb`.
5. Dans les options avancées, ajouter `access_mode=read_only`.

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

Voir le schéma dans `screenshots/schema_etoile.png`.

---

## 4. Mesures

Créer les mesures DAX listées dans **`mesures_dax.md`**. Les regrouper dans une
table de mesures dédiée (Accueil → Entrer des données → table vide `_Mesures`)
pour garder le modèle propre.

---

## 5. Pages du rapport

Construire quatre pages, dans cet ordre.

### Page 1 — Vue d'ensemble
- **Cartes KPI** : Nb de répondants, Taux de maladie cardiaque, IMC moyen,
  Nb moyen de facteurs de risque.
- **Graphique en aires ou en barres** : Taux de maladie par tranche d'âge
  (`dim_age`).
- **Graphique en anneau** : répartition atteints / non atteints.

### Page 2 — Facteurs de risque
- **Barres** : Taux de maladie par nombre de facteurs de risque
  (`risk_factor_count`) — met en évidence le gradient de 1 % à 59 %.
- **Barres groupées** : présence des principaux facteurs (hypertension,
  cholestérol, AVC, difficulté à marcher) selon le statut cardiaque.
- **Courbe** : Taux de maladie par classe d'IMC (`dim_bmi_class`) — montre la
  courbe en J.

### Page 3 — Profil socio-démographique
- **Barres** : Taux de maladie par tranche de revenu (`dim_income`) et par niveau
  d'études (`dim_education`).
- **Matrice** : Taux de maladie croisant sexe (`dim_sex`) et tranche d'âge.
- **Segments (slicers)** : sexe, diabète, tranche d'âge.

### Page 4 — Santé perçue et diabète
- **Barres** : Taux de maladie par état de santé perçu (`dim_genhlth`).
- **Barres** : Taux de maladie par statut diabétique (`dim_diabetes`).
- **Nuage de points** : IMC moyen vs taux de maladie, par tranche d'âge.

---

## 6. Mise en forme

- Palette cohérente avec le reste du projet : bleu marine (`#1F3B5C`) pour les
  éléments neutres, rouge (`#C1443F`) pour la maladie.
- Titre de chaque page, filtres visibles, info-bulles activées.
- Ajouter une note de bas de page rappelant la source (BRFSS 2015, CDC) et la
  limite d'interprétation (associations transversales).

---

## 7. Captures

Une fois le rapport construit, exporter une capture de chaque page vers
`03_power_bi/screenshots/` (`page1_vue_ensemble.png`, etc.). Ces captures sont
versionnées et réutilisées dans le rapport et la présentation ; le `.pbix`, lui,
reste hors du dépôt.
