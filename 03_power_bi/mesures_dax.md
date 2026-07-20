# Mesures DAX

Ensemble des mesures à créer dans Power BI, à regrouper dans une table `_Mesures`.
La cible `heart_disease` est codée 0/1 : sa moyenne donne directement le taux de
maladie, et sa somme le nombre de cas.

---

## 1. Indicateurs de base

```dax
Nb Repondants = COUNTROWS ( fact_respondent )
```

```dax
Nb Cas Cardiaques = SUM ( fact_respondent[heart_disease] )
```

```dax
Taux Maladie Cardiaque =
DIVIDE (
    SUM ( fact_respondent[heart_disease] ),
    COUNTROWS ( fact_respondent )
)
```
> Mettre en forme en pourcentage. C'est la mesure centrale du rapport.

```dax
Nb Cas Sains = [Nb Repondants] - [Nb Cas Cardiaques]
```

---

## 2. Mesures de santé

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
Taux Activite Physique =
DIVIDE (
    SUM ( fact_respondent[phys_activity] ),
    COUNTROWS ( fact_respondent )
)
```

```dax
Taux Diabete =
DIVIDE (
    CALCULATE (
        COUNTROWS ( fact_respondent ),
        fact_respondent[diabetes_key] = 2
    ),
    COUNTROWS ( fact_respondent )
)
```

---

## 3. Mesures comparatives

```dax
Taux Maladie National = 
CALCULATE (
    [Taux Maladie Cardiaque],
    ALL ( fact_respondent )
)
```
> Constante (~9,42 %). Sert de ligne de référence : dans un visuel filtré par
> segment, comparer `[Taux Maladie Cardiaque]` (contextuel) à
> `[Taux Maladie National]` (global).

```dax
Ecart au National =
[Taux Maladie Cardiaque] - [Taux Maladie National]
```
> Positif = segment sur-exposé, négatif = sous-exposé. Idéal en mise en forme
> conditionnelle (rouge si positif).

```dax
Sur-risque =
DIVIDE ( [Taux Maladie Cardiaque], [Taux Maladie National] )
```
> Rapport au risque moyen. Une valeur de 2,5 signifie « 2,5 fois le risque
> national », lecture immédiate pour les segments extrêmes.

---

## 4. Mesures dynamiques de titre

```dax
Titre Segment Le Plus Touche =
VAR t =
    TOPN (
        1,
        ADDCOLUMNS (
            VALUES ( dim_age[tranche_age] ),
            "@taux", [Taux Maladie Cardiaque]
        ),
        [@taux], DESC
    )
RETURN
    "Tranche la plus touchée : "
        & MAXX ( t, dim_age[tranche_age] )
        & " (" & FORMAT ( MAXX ( t, [@taux] ), "0.0%" ) & ")"
```
> Titre dynamique pour la page « Vue d'ensemble ».

---

## Notes d'usage

- Toutes les mesures de taux sont à formater en **pourcentage** (1 décimale).
- `Taux Maladie Cardiaque` réagit automatiquement au contexte de filtre : posée
  sur un axe `dim_age`, elle donne le taux par tranche d'âge ; combinée à un
  segment, elle se recalcule.
- Rappel : ces taux décrivent des **associations transversales**. Ne pas les
  présenter comme des probabilités de survenue future.
