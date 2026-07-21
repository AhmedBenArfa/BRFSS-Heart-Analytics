# Mesures et colonnes DAX

Éléments de calcul créés dans le rapport Power BI. Les mesures sont regroupées
dans une table dédiée `_Mesures` ; les colonnes calculées vivent dans
`fact_respondent`.

La cible `heart_disease` est codée 0/1 : sa moyenne donne directement le taux de
maladie, et sa somme le nombre de cas.

---

## 1. Colonnes calculées (table `fact_respondent`)

Créées via **Nouvelle colonne** (calcul ligne à ligne), et non « Nouvelle mesure ».

```dax
Statut cardiaque = IF ( fact_respondent[heart_disease] = 1, "Atteint", "Non atteint" )
```
> Libellé lisible pour les légendes et axes (anneau, barres par statut).

Colonne de regroupement **`bmi (compartiments)`** : créée par l'interface
(clic droit sur `bmi` → **Nouveau groupe** → type **Compartiment**, taille **2**).
Sert d'axe pour l'histogramme de distribution de l'IMC.

---

## 2. Indicateurs de base

```dax
Nb Repondants = COUNTROWS ( fact_respondent )
```

```dax
Taux Maladie Cardiaque =
DIVIDE (
    SUM ( fact_respondent[heart_disease] ),
    COUNTROWS ( fact_respondent )
)
```
> Format **pourcentage**, 1 décimale. C'est la mesure centrale du rapport.

---

## 3. Mesures de santé

```dax
IMC Moyen = AVERAGE ( fact_respondent[bmi] )
```

```dax
Facteurs Risque Moyens = AVERAGE ( fact_respondent[risk_factor_count] )
```

```dax
Jours Malaise Moyens = AVERAGE ( fact_respondent[total_unhealthy_days] )
```

```dax
Taux Hypertension =
DIVIDE ( SUM ( fact_respondent[high_bp] ), COUNTROWS ( fact_respondent ) )
```

---

## 4. Mesures de comportement et d'accès aux soins

Toutes à formater en **pourcentage**. Décrivent la population (page « Habitudes de
vie »), indépendamment de la maladie.

```dax
Taux Fumeurs =
DIVIDE ( SUM ( fact_respondent[smoker] ), COUNTROWS ( fact_respondent ) )
```

```dax
Taux Activite Physique =
DIVIDE ( SUM ( fact_respondent[phys_activity] ), COUNTROWS ( fact_respondent ) )
```

```dax
Taux Consommation Fruits =
DIVIDE ( SUM ( fact_respondent[fruits] ), COUNTROWS ( fact_respondent ) )
```

```dax
Taux Consommation Legumes =
DIVIDE ( SUM ( fact_respondent[veggies] ), COUNTROWS ( fact_respondent ) )
```

```dax
Taux Acces Soins =
DIVIDE ( SUM ( fact_respondent[has_care_access] ), COUNTROWS ( fact_respondent ) )
```

---

## 5. Mesures comparatives (optionnelles)

Non indispensables au rapport actuel, mais utiles pour enrichir l'analyse.

```dax
Taux Maladie National =
CALCULATE ( [Taux Maladie Cardiaque], ALL ( fact_respondent ) )
```
> Constante (~9,42 %). Ligne de référence : comparer le taux d'un segment filtré
> à ce taux global.

```dax
Ecart au National = [Taux Maladie Cardiaque] - [Taux Maladie National]
```
> Positif = segment sur-exposé. Idéal en mise en forme conditionnelle.

```dax
Sur-risque = DIVIDE ( [Taux Maladie Cardiaque], [Taux Maladie National] )
```
> Rapport au risque moyen. « 2,5 » = 2,5 fois le risque national.

---

## Notes d'usage

- Distinction fondamentale : une **mesure** agrège (SUM, AVERAGE, DIVIDE) et va
  dans **Valeurs** ; une **colonne** se calcule par ligne et va dans **Axe /
  Légende**. Créer `Statut cardiaque` en mesure déclenche l'erreur « impossible de
  déterminer une valeur unique ».
- Toutes les mesures de taux se formatent en **pourcentage** (onglet *Outils de
  mesure* → *Format*).
- `Taux Maladie Cardiaque` réagit au contexte de filtre : posée sur un axe
  `dim_age`, elle donne le taux par tranche d'âge ; combinée à un segment, elle se
  recalcule automatiquement.
- Rappel : ces taux décrivent des **associations transversales**, pas des
  probabilités de survenue future.
