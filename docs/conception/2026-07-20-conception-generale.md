# Conception générale — BRFSS Heart Analytics

> Date : 20 juillet 2026 — Auteur : Ahmed Ben Arfa

## 1. Objectif

Construire une chaîne analytique complète sur les données **BRFSS 2015** (CDC), de
la donnée brute jusqu'à une application web déployée, afin d'estimer le risque de
maladie ou d'accident cardiaque à partir d'un profil de santé déclaré.

## 2. Données

| Propriété | Valeur |
|---|---|
| Volume | 253 680 lignes × 22 colonnes |
| Type | Entièrement numérique (`float64`), déjà encodé |
| Valeurs manquantes | **Aucune** |
| Doublons exacts | 23 899 (9,42 %) — **conservés**, voir §3 |
| Cible | `HeartDiseaseorAttack` — 9,42 % de positifs |

### Limite méthodologique assumée

Les 21 variables explicatives sont auto-déclarées **au même moment** que la cible.
Le modèle mesure donc une **association transversale** — estimer un risque à partir
d'un profil — et non une prédiction d'un événement futur. Cette limite doit être
énoncée explicitement dans le rapport, la présentation et l'application.

## 3. Décision : conserver les doublons exacts

Hypothèse initiale : des lignes identiques seraient des erreurs de saisie à
supprimer. Quatre tests la réfutent.

| Test | Résultat | Interprétation |
|---|---|---|
| Taux selon la taille de l'échantillon | 1,50 % (12 684 lignes) → 9,42 % (253 680) | Le taux **croît** avec n : signature d'une collision (paradoxe des anniversaires). Des erreurs donneraient un taux constant. |
| Profil des lignes dupliquées | 95,7 % ont `MentHlth=0` vs 65 % chez les uniques | Les doublons frappent les profils **les plus fréquents**, pas au hasard. |
| Taille du plus gros groupe | 59 lignes identiques | Aucun mécanisme d'erreur ne produit 59 copies. |
| Impact sur la prévalence | 9,419 % → 10,322 % après déduplication | Dédupliquer **introduit** un biais au lieu de le corriger. |

**Conclusion :** ce sont des collisions légitimes entre répondants distincts. On
les conserve et on documente la démonstration dans l'EDA.

**Point connexe à traiter en ML :** des profils identiques portent parfois des
cibles opposées. C'est de l'**erreur irréductible**, qui fixe un plafond de
performance atteignable — à quantifier pour ne pas viser un seuil impossible.

## 4. Architecture

```
data/*.csv
    │
    ├─ 01_etl/        extract → transform → checks → load
    │                 (nettoyage, variables dérivées, drapeaux qualité)
    ▼
heart.duckdb  (analytical_base)
    │
    ├─ 02_data_warehouse/   schéma en étoile
    ▼
fact_respondent + 7 dimensions
    │
    ├─ 03_power_bi/         connexion ODBC en lecture seule
    ├─ 04_machine_learning/ modèle → heart_model.joblib
    ├─ 08_data_mining/      ACP, clustering, t-SNE
    ▼
05_web_app/  application Streamlit déployée
```

## 5. Modèle dimensionnel

**Table de faits** `fact_respondent` — grain : un répondant à l'enquête.
Clé dégénérée `respondent_id` (numéro de ligne : la source n'a pas de clé primaire).

Porte les mesures (`bmi`, `ment_hlth_days`, `phys_hlth_days`), les 11 indicateurs
binaires de santé et de comportement, la cible `heart_disease`, et les drapeaux
qualité.

**Dimensions** — reconstruites depuis le codebook BRFSS, pour afficher des
libellés lisibles plutôt que des codes numériques :

| Dimension | Membres | Exemple |
|---|---|---|
| `dim_age` | 13 | `55-59 ans` |
| `dim_education` | 6 | `Diplômé du supérieur` |
| `dim_income` | 8 | `75 000 $ et plus` |
| `dim_genhlth` | 5 | `Excellente` … `Mauvaise` |
| `dim_sex` | 2 | `Femme`, `Homme` |
| `dim_diabetes` | 3 | `Non`, `Prédiabète`, `Diabète` |
| `dim_bmi_class` | 6 | classes OMS, `Insuffisance pondérale` → `Obésité III` |

## 6. Qualité des données

Aucune valeur n'est supprimée ni imputée dans l'entrepôt : les faits restent
fidèles à la source. Les anomalies sont **signalées** par des drapeaux.

| Drapeau | Condition | Volume |
|---|---|---|
| `flag_bmi_extreme` | `BMI > 60` ou `BMI < 14` | 805 lignes (BMI > 60) |
| `flag_profil_duplique` | ligne appartenant à un groupe de doublons | 35 086 lignes |

## 7. Machine learning

- **Tâche** : classification binaire, classes déséquilibrées (9,42 % de positifs)
- **Modèles comparés** : régression logistique, kNN, arbre de décision, SVM,
  forêt aléatoire, XGBoost
- **Sélection** : ROC-AUC, avec report systématique du **PR-AUC**, du rappel et du
  F1 — l'exactitude seule est trompeuse à 9 % de positifs (un modèle constant
  atteindrait 90,6 %)
- **Déséquilibre** : `class_weight` / `scale_pos_weight`, comparé à SMOTE
- **Interprétation** : SHAP
- **Découpage** : train/test stratifié, préprocessing ajusté sur le train seul

## 8. Conventions

- Les notebooks sont **générés** depuis `_build_*.py` — ne jamais éditer le `.ipynb`
- Les PDF sont **générés** par script, en lisant les sources vivantes du dépôt
- L'entrepôt et les modèles sont **gitignorés** et régénérables
- Le jeu de données source est versionné (données publiques, reproductibilité)
