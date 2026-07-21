# Description du projet

## Contexte

Les maladies cardiovasculaires sont la première cause de mortalité dans le monde.
Une large part des facteurs de risque est **connue et mesurable** : hypertension,
cholestérol, diabète, tabagisme, sédentarité, surpoids. Identifier les profils les
plus exposés à partir de données déclaratives est un enjeu majeur de santé
publique, notamment pour cibler les actions de prévention.

Ce projet exploite les données du **Behavioral Risk Factor Surveillance System**
(BRFSS), la grande enquête de santé annuelle des *Centers for Disease Control and
Prevention* (CDC) aux États-Unis, dans son édition 2015.

## Objectif

Construire une **chaîne analytique complète**, de la donnée brute jusqu'à une
application web déployée, autour d'une question centrale :

> À partir du profil de santé déclaré d'une personne, peut-on estimer son risque
> de maladie ou d'accident cardiaque, et identifier les facteurs les plus
> déterminants ?

Le projet ne se limite pas à un modèle prédictif : il couvre toute la chaîne de
valeur de la donnée — extraction, entreposage, restitution décisionnelle,
exploration, modélisation et mise en production.

## Nature du projet

Il s'agit d'un **projet personnel de data analytics et de machine learning**, conçu
comme une pièce de portfolio. Les données étant **publiques** (CDC / Kaggle), leur
source est citée ouvertement et le jeu de données est versionné dans le dépôt pour
garantir la reproductibilité.

## Périmètre : une chaîne en huit modules

| Module | Rôle |
|---|---|
| ETL & EDA | Extraction, nettoyage, contrôles qualité, analyse exploratoire |
| Entrepôt de données | Schéma en étoile sous DuckDB |
| Power BI | Rapport décisionnel branché sur l'entrepôt |
| Machine Learning | Comparaison de modèles, sélection, interprétation |
| Data Mining | Exploration non supervisée (ACP, clustering, t-SNE) |
| Application web | Interface de prédiction déployée |
| Rapport | Documentations techniques et rapport final |
| Présentation | Support de restitution |

## Stack technique

- **Langage** : Python (pandas, scikit-learn, XGBoost)
- **Entrepôt** : DuckDB (sans serveur, un fichier = une base)
- **Décisionnel** : Power BI Desktop, connecté en ODBC direct
- **Interprétabilité** : SHAP
- **Application** : Streamlit
- **Rapports** : génération PDF par script (fpdf2)

## Livrables attendus

1. Un dépôt GitHub public, documenté et reproductible.
2. Un rapport décisionnel Power BI.
3. Des modèles de machine learning comparés et un modèle retenu.
4. Une application web de prédiction déployée (URL publique).
5. Un rapport final PDF et un support de présentation.

## Limite méthodologique fondamentale

Les variables explicatives sont **auto-déclarées au même moment** que la variable
cible, lors d'un unique entretien. Les relations mises en évidence sont donc des
**associations transversales** : elles ne permettent d'établir ni causalité, ni
prédiction d'un événement futur. Le modèle estime un risque à partir d'un profil,
il ne prédit pas la survenue d'un accident cardiaque. Cette limite est rappelée
dans tous les livrables du projet.
