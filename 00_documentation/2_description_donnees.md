# Description des données

## Source

- **Jeu de données** : *Heart Disease Health Indicators Dataset* (Kaggle)
- **Origine primaire** : CDC — *Behavioral Risk Factor Surveillance System* (BRFSS),
  édition 2015
- **Nature** : enquête téléphonique de santé menée à l'échelle des États-Unis
- **Licence** : données publiques

Le fichier utilisé est une version déjà **nettoyée et encodée** du BRFSS 2015,
diffusée sur Kaggle. Les non-réponses ont été écartées en amont par l'auteur du jeu.

## Volumétrie

| Propriété | Valeur |
|---|---|
| Nombre de répondants | 253 680 |
| Nombre de variables | 22 |
| Type | Entièrement numérique |
| Valeurs manquantes | Aucune |
| Doublons exacts | 23 899 (conservés — voir plus bas) |

## La variable cible

`HeartDiseaseorAttack` — indique si le répondant a déclaré une maladie coronarienne
ou un infarctus (0 = non, 1 = oui).

- **Prévalence** : 9,42 % de cas positifs
- **Conséquence** : classes fortement déséquilibrées. Un modèle prédisant « aucun
  malade » atteindrait 90,58 % d'exactitude tout en étant inutile — l'exactitude
  est donc écartée comme critère au profit du ROC-AUC, du PR-AUC, du rappel et du
  F1.

## Les 22 variables

### Conditions médicales déclarées

| Variable | Description | Modalités |
|---|---|---|
| HighBP | Hypertension artérielle | 0 / 1 |
| HighChol | Cholestérol élevé | 0 / 1 |
| CholCheck | Dosage du cholestérol depuis 5 ans | 0 / 1 |
| Stroke | Antécédent d'AVC | 0 / 1 |
| Diabetes | Statut diabétique | 0 / 1 / 2 |
| DiffWalk | Difficulté sérieuse à marcher | 0 / 1 |

### Comportements et hygiène de vie

| Variable | Description | Modalités |
|---|---|---|
| Smoker | A fumé au moins 100 cigarettes dans sa vie | 0 / 1 |
| PhysActivity | Activité physique le mois écoulé | 0 / 1 |
| Fruits | Fruits au moins une fois par jour | 0 / 1 |
| Veggies | Légumes au moins une fois par jour | 0 / 1 |
| HvyAlcoholConsump | Consommation d'alcool excessive | 0 / 1 |

### État de santé perçu et mesures

| Variable | Description | Modalités |
|---|---|---|
| GenHlth | État de santé général perçu | 1 (excellent) à 5 (mauvais) |
| MentHlth | Jours de mal-être mental sur 30 | 0 à 30 |
| PhysHlth | Jours de mal-être physique sur 30 | 0 à 30 |
| BMI | Indice de masse corporelle | 12 à 98 |

### Accès aux soins et données socio-démographiques

| Variable | Description | Modalités |
|---|---|---|
| AnyHealthcare | Dispose d'une couverture santé | 0 / 1 |
| NoDocbcCost | A renoncé à un médecin pour raison financière | 0 / 1 |
| Sex | Sexe déclaré | 0 (femme) / 1 (homme) |
| Age | Tranche d'âge | 1 à 13 |
| Education | Niveau d'études | 1 à 6 |
| Income | Tranche de revenu du foyer | 1 à 8 |

## Codebook des variables ordinales

Les variables `Age`, `Education` et `Income` sont codées par des entiers dont voici
la signification (source : codebook BRFSS 2015). Ces libellés sont réintégrés dans
l'entrepôt pour afficher un texte lisible plutôt qu'un code.

### Tranches d'âge (Age)

| Code | Tranche | Code | Tranche |
|---|---|---|---|
| 1 | 18-24 ans | 8 | 55-59 ans |
| 2 | 25-29 ans | 9 | 60-64 ans |
| 3 | 30-34 ans | 10 | 65-69 ans |
| 4 | 35-39 ans | 11 | 70-74 ans |
| 5 | 40-44 ans | 12 | 75-79 ans |
| 6 | 45-49 ans | 13 | 80 ans et plus |
| 7 | 50-54 ans | | |

### Niveau d'études (Education)

| Code | Niveau |
|---|---|
| 1 | Aucune scolarité |
| 2 | Primaire |
| 3 | Secondaire non achevé |
| 4 | Secondaire achevé |
| 5 | Supérieur non achevé |
| 6 | Diplômé du supérieur |

### Tranche de revenu du foyer (Income)

| Code | Revenu annuel |
|---|---|
| 1 | Moins de 10 000 $ |
| 2 | 10 000 à 15 000 $ |
| 3 | 15 000 à 20 000 $ |
| 4 | 20 000 à 25 000 $ |
| 5 | 25 000 à 35 000 $ |
| 6 | 35 000 à 50 000 $ |
| 7 | 50 000 à 75 000 $ |
| 8 | 75 000 $ et plus |

## Qualité des données

### Aucune valeur manquante

Le fichier ne contient aucune valeur manquante — conséquence du nettoyage préalable
appliqué sur Kaggle. Aucune stratégie d'imputation n'est donc nécessaire, mais cette
sélection en amont a pu écarter des profils particuliers (les personnes les plus
fragiles répondant généralement moins).

### Doublons exacts : conservés

Le jeu contient 23 899 lignes strictement identiques à une autre (9,42 %). Une
analyse en quatre tests (détaillée dans la documentation ETL & EDA) montre qu'il
s'agit de **collisions légitimes** entre répondants distincts, et non d'erreurs de
saisie : avec 22 variables grossièrement codées, deux personnes différentes peuvent
présenter le même profil. Les supprimer ferait passer artificiellement la prévalence
de 9,42 % à 10,32 %. Ils sont donc **conservés**.

### Valeurs extrêmes : signalées, non supprimées

Aucune valeur n'est supprimée ni corrigée dans le pipeline. Les anomalies (IMC
physiologiquement improbable, incohérences) sont signalées par des drapeaux
booléens, laissant la table analytique fidèle à la source.
