"""Générateur du notebook d'analyse exploratoire.

Le notebook `01_eda.ipynb` est PRODUIT par ce script : on ne l'édite jamais à la
main. Pour le modifier, modifier ce fichier puis relancer :

    python _build_eda.py
    python -m jupyter nbconvert --to notebook --execute --inplace 01_eda.ipynb
"""

from pathlib import Path

import nbformat as nbf

DESTINATION = Path(__file__).resolve().parent / "01_eda.ipynb"

cellules: list = []


def md(texte: str) -> None:
    """Ajoute une cellule Markdown."""
    cellules.append(nbf.v4.new_markdown_cell(texte.strip()))


def code(source: str) -> None:
    """Ajoute une cellule de code."""
    cellules.append(nbf.v4.new_code_cell(source.strip()))


# ===========================================================================
# Introduction
# ===========================================================================

md(
    """
# Analyse exploratoire — BRFSS Heart Analytics

**Jeu de données** : *Behavioral Risk Factor Surveillance System* (BRFSS 2015, CDC)
— 253 680 répondants, 22 variables initiales.

**Objectif** : comprendre la structure des données, évaluer leur qualité et
identifier les facteurs associés à la maladie cardiovasculaire, avant toute
modélisation.

> ⚠️ **Limite méthodologique** — les variables explicatives sont auto-déclarées
> **au même moment** que la variable cible. Ce qui suit décrit donc des
> **associations transversales**, et non des relations de cause à effet ni des
> prédictions d'événements futurs.

---
"""
)

code(
    """
import warnings
from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

warnings.filterwarnings("ignore")

RACINE = Path.cwd().parent.parent
FIGURES = RACINE / "06_rapport" / "figures" / "eda"
FIGURES.mkdir(parents=True, exist_ok=True)

pd.set_option("display.width", 120)
pd.set_option("display.max_columns", 40)

sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams["figure.dpi"] = 110
plt.rcParams["savefig.dpi"] = 150
plt.rcParams["savefig.bbox"] = "tight"
plt.rcParams["font.size"] = 10

# Palette du projet : bleu = sains, rouge = malades. Conservée dans tout le
# notebook pour que les figures se lisent sans relire la légende.
BLEU, ROUGE = "#2E5C8A", "#C1443F"


def enregistrer(nom):
    \"\"\"Sauvegarde la figure courante pour réutilisation dans le rapport.\"\"\"
    plt.savefig(FIGURES / f"{nom}.png")


print("Environnement pret.")
"""
)

# ===========================================================================
# Chargement
# ===========================================================================

md(
    """
## 1. Chargement des données

Les données proviennent de la table analytique produite par le pipeline ETL
(`python run_etl.py`), et non du CSV brut : l'analyse porte ainsi exactement sur
ce qui alimente l'entrepôt et les modèles.
"""
)

code(
    """
BASE = RACINE / "02_data_warehouse" / "heart.duckdb"

with duckdb.connect(str(BASE), read_only=True) as conn:
    df = conn.execute("SELECT * FROM analytical_base").df()

print(f"{len(df):,} lignes x {df.shape[1]} colonnes")
df.head()
"""
)

code(
    """
apercu = pd.DataFrame({
    "type": df.dtypes.astype(str),
    "valeurs_distinctes": df.nunique(),
    "manquantes": df.isna().sum(),
})
apercu
"""
)

md(
    """
**Premier constat** : aucune valeur manquante sur l'ensemble des colonnes. C'est
inhabituel et cela s'explique — le jeu Kaggle est une version déjà nettoyée du
BRFSS, dont les non-réponses ont été écartées en amont. Il n'y a donc pas de
stratégie d'imputation à concevoir, mais il faut garder en tête que **cette
sélection préalable a pu écarter des profils particuliers** (les personnes les
plus fragiles répondent moins).
"""
)

# ===========================================================================
# Qualité — doublons
# ===========================================================================

md(
    """
## 2. Qualité des données : le cas des doublons exacts

Le jeu contient **23 899 lignes strictement identiques à une autre** (9,42 %).
Le réflexe habituel serait de les supprimer. Avant cela, il faut trancher une
question : s'agit-il d'**erreurs de saisie** (le même répondant compté plusieurs
fois) ou de **collisions légitimes** (deux répondants différents partageant le
même profil) ?

Les deux hypothèses font des prédictions opposées et vérifiables.
"""
)

md(
    """
### Test 1 — le taux de doublons dépend-il de la taille de l'échantillon ?

- **Si erreurs de saisie** → le taux est une propriété du fichier : il reste
  **constant** quel que soit l'échantillon.
- **Si collisions** → le taux **croît avec la taille** : plus il y a de
  répondants, plus deux d'entre eux finissent par coïncider (paradoxe des
  anniversaires).
"""
)

code(
    """
colonnes_source = [
    "heart_disease", "high_bp", "high_chol", "chol_check", "bmi", "smoker",
    "stroke", "diabetes", "phys_activity", "fruits", "veggies", "hvy_alcohol",
    "any_healthcare", "no_doc_cost", "gen_hlth", "ment_hlth_days",
    "phys_hlth_days", "diff_walk", "sex", "age_group", "education", "income",
]

rng = np.random.default_rng(42)
resultats = []
for fraction in [0.05, 0.10, 0.25, 0.50, 1.00]:
    n = int(len(df) * fraction)
    taux = [
        df.sample(n, random_state=int(graine))[colonnes_source].duplicated().mean() * 100
        for graine in rng.integers(0, 10_000, 3)
    ]
    resultats.append({"taille": n, "taux_doublons_pct": round(np.mean(taux), 2)})

test1 = pd.DataFrame(resultats)
test1
"""
)

code(
    """
fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(test1.taille, test1.taux_doublons_pct, "o-", color=ROUGE, lw=2, label="observé")
ax.axhline(9.42, ls="--", c="grey", label="attendu si erreurs de saisie (constant)")
ax.set_xlabel("Taille de l'échantillon")
ax.set_ylabel("% de lignes dupliquées")
ax.set_title("Le taux de doublons croît avec la taille de l'échantillon")
ax.legend()
enregistrer("01_doublons_scaling")
plt.show()
"""
)

md(
    """
Le taux passe de **1,50 %** à 12 684 lignes à **9,42 %** à 253 680. Il n'est pas
constant : l'hypothèse « erreurs de saisie » est écartée.
"""
)

md(
    """
### Test 2 — quels profils sont dupliqués ?

Une erreur de saisie n'a aucune raison de viser préférentiellement certains
profils. Une collision, si : elle frappe d'abord les profils **les plus fréquents**.
"""
)

code(
    """
masque = df[colonnes_source].duplicated(keep=False)
dupliques, uniques = df[masque], df[~masque]

comparaison = pd.DataFrame({
    "lignes dupliquées (%)": [
        (dupliques.ment_hlth_days == 0).mean() * 100,
        (dupliques.phys_hlth_days == 0).mean() * 100,
        (dupliques.bmi <= 30).mean() * 100,
        dupliques.heart_disease.mean() * 100,
    ],
    "lignes uniques (%)": [
        (uniques.ment_hlth_days == 0).mean() * 100,
        (uniques.phys_hlth_days == 0).mean() * 100,
        (uniques.bmi <= 30).mean() * 100,
        uniques.heart_disease.mean() * 100,
    ],
}, index=[
    "aucun jour de mal-être mental",
    "aucun jour de mal-être physique",
    "IMC <= 30",
    "atteintes d'une maladie cardiaque",
]).round(1)

comparaison
"""
)

md(
    """
Les lignes dupliquées sont massivement des **profils banals** : 95,7 % déclarent
zéro jour de mal-être mental, contre 65 % chez les lignes uniques. Ce sont les
répondants « en bonne santé, IMC modéré, rien à signaler » — le profil le plus
courant de la population. Exactement ce qu'on attend de collisions.
"""
)

md(
    """
### Test 3 — taille des groupes de doublons
"""
)

code(
    """
tailles = df.groupby(colonnes_source).size().value_counts().sort_index()
print("Profils vus n fois :")
for taille, nombre in tailles.head(8).items():
    print(f"  {taille:>3}x : {nombre:>7,} profils distincts")
print(f"\\n  groupe le plus important : {tailles.index.max()} lignes identiques")
"""
)

md(
    """
Le plus gros groupe compte **59 lignes identiques**. Aucun mécanisme d'erreur de
saisie plausible ne produit 59 copies d'un même enregistrement. En revanche, que
59 répondants sur 253 680 partagent le profil le plus commun est parfaitement
attendu.
"""
)

md(
    """
### Test 4 — quel serait l'impact d'une déduplication ?
"""
)

code(
    """
avec = df.heart_disease.mean() * 100
sans = df.drop_duplicates(subset=colonnes_source).heart_disease.mean() * 100

print(f"Prévalence avec doublons : {avec:.3f} %")
print(f"Prévalence sans doublons : {sans:.3f} %")
print(f"Écart introduit          : {sans - avec:+.3f} point de pourcentage")
"""
)

md(
    """
### Conclusion

Les quatre tests convergent : ce sont des **collisions légitimes entre répondants
distincts**. Les supprimer reviendrait à **effacer de vrais répondants en bonne
santé**, faisant grimper artificiellement la prévalence de 9,42 % à 10,32 %.

**Décision : les doublons sont conservés.** La déduplication n'aurait pas nettoyé
les données, elle les aurait biaisées.

> **Point connexe, à traiter en modélisation** : des profils identiques portent
> parfois des cibles opposées (deux personnes au même profil, l'une malade,
> l'autre non). Ce n'est pas un défaut de qualité mais de l'**erreur
> irréductible** — elle fixe un plafond de performance qu'aucun modèle ne pourra
> dépasser. Quantifiée dans le module 04.
"""
)

# ===========================================================================
# Cible
# ===========================================================================

md(
    """
## 3. La variable cible : un déséquilibre marqué
"""
)

code(
    """
effectifs = df.heart_disease.value_counts().sort_index()
parts = df.heart_disease.value_counts(normalize=True).sort_index() * 100

fig, axes = plt.subplots(1, 2, figsize=(11, 4))

axes[0].bar(["Non atteints", "Atteints"], effectifs, color=[BLEU, ROUGE])
axes[0].set_title("Effectifs")
axes[0].set_ylabel("Nombre de répondants")
for i, v in enumerate(effectifs):
    axes[0].text(i, v, f"{v:,}", ha="center", va="bottom")

axes[1].pie(parts, labels=["Non atteints", "Atteints"], colors=[BLEU, ROUGE],
            autopct="%1.2f%%", startangle=90, explode=(0, 0.08))
axes[1].set_title("Répartition")

plt.suptitle("Maladie ou accident cardiaque déclaré", y=1.02, fontsize=12)
enregistrer("02_cible_desequilibre")
plt.show()

print(f"Prévalence : {parts[1]:.2f} %  —  ratio 1 malade pour {effectifs[0]/effectifs[1]:.1f} sains")
"""
)

md(
    """
**Conséquence directe pour la modélisation** : avec 9,42 % de positifs, un modèle
qui prédirait « aucun malade » pour tout le monde atteindrait **90,58 %
d'exactitude** tout en étant parfaitement inutile. L'*accuracy* est donc à
proscrire comme critère. On s'appuiera sur le **ROC-AUC**, le **PR-AUC**, le
**rappel** et le **F1**.
"""
)

# ===========================================================================
# Variables numériques
# ===========================================================================

md(
    """
## 4. Distribution des variables continues
"""
)

code(
    """
continues = ["bmi", "ment_hlth_days", "phys_hlth_days", "total_unhealthy_days"]

stats = df[continues].describe().T
stats["asymétrie"] = df[continues].skew()
stats["aplatissement"] = df[continues].kurtosis()
stats.round(2)
"""
)

code(
    """
fig, axes = plt.subplots(2, 2, figsize=(12, 7))
titres = {
    "bmi": "Indice de masse corporelle",
    "ment_hlth_days": "Jours de mal-être mental (sur 30)",
    "phys_hlth_days": "Jours de mal-être physique (sur 30)",
    "total_unhealthy_days": "Total jours de mal-être (plafonné à 30)",
}

for ax, colonne in zip(axes.ravel(), continues):
    ax.hist(df[colonne], bins=40, color=BLEU, edgecolor="white", linewidth=0.4)
    ax.set_title(titres[colonne], fontsize=10)
    ax.set_ylabel("Effectif")

plt.suptitle("Distribution des variables continues", y=1.00, fontsize=12)
plt.tight_layout()
enregistrer("03_distributions_continues")
plt.show()
"""
)

md(
    """
Les variables de mal-être sont **extrêmement asymétriques** : l'écrasante majorité
des répondants déclare zéro jour, avec un pic secondaire à 30 jours (les
personnes en souffrance permanente). Ce sont donc des variables presque
binaires en pratique, avec une longue queue — un modèle linéaire aura du mal à
en tirer parti tel quel.

L'IMC est plus régulier mais reste asymétrique à droite, avec des valeurs
extrêmes jusqu'à 98 — physiologiquement très improbables, signalées par
`flag_bmi_extreme` sans être supprimées.
"""
)

# ===========================================================================
# Valeurs aberrantes et standardisation
# ===========================================================================

md(
    """
## 5. Valeurs aberrantes et justification de la standardisation

Avant de modéliser, deux questions distinctes se posent — souvent confondues :

1. **Y a-t-il des valeurs aberrantes ?** C'est-à-dire des valeurs *fausses*,
   issues d'une erreur de saisie ou de mesure.
2. **Faut-il standardiser ?** C'est-à-dire ramener les variables à une échelle
   commune.

La seconde ne découle pas de la première. Une variable peut être parfaitement
propre et exiger malgré tout une standardisation, simplement parce que son
échelle écrase celle des autres.
"""
)

md(
    """
### 5.1 Boxplots par statut cardiaque
"""
)

code(
    """
continues_box = ["bmi", "ment_hlth_days", "phys_hlth_days", "risk_factor_count"]
titres_box = {
    "bmi": "Indice de masse corporelle",
    "ment_hlth_days": "Jours de mal-être mental",
    "phys_hlth_days": "Jours de mal-être physique",
    "risk_factor_count": "Nombre de facteurs de risque",
}

fig, axes = plt.subplots(1, 4, figsize=(15, 4.5))

for ax, colonne in zip(axes, continues_box):
    donnees = [
        df.loc[df.heart_disease == 0, colonne],
        df.loc[df.heart_disease == 1, colonne],
    ]
    boite = ax.boxplot(
        donnees, labels=["Non atteints", "Atteints"], patch_artist=True,
        widths=0.55, flierprops={"marker": ".", "markersize": 2, "alpha": 0.25},
        medianprops={"color": "black", "linewidth": 1.6},
    )
    for patch, couleur in zip(boite["boxes"], [BLEU, ROUGE]):
        patch.set_facecolor(couleur)
        patch.set_alpha(0.65)
    ax.set_title(titres_box[colonne], fontsize=10)
    ax.tick_params(axis="x", labelsize=9)

plt.suptitle("Distribution des variables continues selon le statut cardiaque",
             y=1.02, fontsize=12)
plt.tight_layout()
enregistrer("09_boxplots_par_statut")
plt.show()
"""
)

md(
    """
Lecture des boîtes :

- **IMC** — les deux distributions se recouvrent très largement (médianes 27 et
  28). Les points isolés montent jusqu'à 98. Pris seul, l'IMC sépare mal les deux
  groupes, ce qui confirme la faible corrélation observée au §8.
- **Jours de mal-être mental** — les deux groupes sont concentrés sur zéro
  (Q1 = médiane = 0 dans les deux cas, Q3 = 2 contre 4). L'écart existe mais reste
  ténu.
- **Jours de mal-être physique** — c'est le contraste le plus frappant du
  graphique. Chez les non atteints, la boîte est écrasée (Q1 = médiane = 0,
  Q3 = 2). Chez les atteints, elle s'étale de 0 à 20, avec une médiane à 2. Un
  quart des personnes atteintes déclarent au moins 20 jours de souffrance
  physique sur 30.
- **Facteurs de risque** — séparation nette et lisible : médiane 2 contre 3,
  boîtes largement décalées. La variable dérivée sépare mieux que n'importe
  laquelle des variables brutes.
"""
)

md(
    """
### 5.2 Combien de valeurs sortent des bornes statistiques ?

On applique deux règles classiques : la règle de l'**IQR** (hors de
[Q1 − 1,5·IQR ; Q3 + 1,5·IQR]) et celle du **z-score** (|z| > 3).
"""
)

code(
    """
def compter_aberrantes(serie):
    \"\"\"Compte les valeurs hors bornes selon l'IQR et le z-score.\"\"\"
    q1, q3 = serie.quantile([0.25, 0.75])
    iqr = q3 - q1
    hors_iqr = ((serie < q1 - 1.5 * iqr) | (serie > q3 + 1.5 * iqr)).sum()
    ecart_type = serie.std()
    hors_z = (((serie - serie.mean()).abs() / ecart_type) > 3).sum() if ecart_type else 0
    return {
        "Q1": q1, "médiane": serie.median(), "Q3": q3, "IQR": iqr,
        "n hors IQR": hors_iqr, "% hors IQR": hors_iqr / len(serie) * 100,
        "n |z|>3": hors_z, "% |z|>3": hors_z / len(serie) * 100,
    }


aberrantes = pd.DataFrame(
    {c: compter_aberrantes(df[c]) for c in
     ["bmi", "ment_hlth_days", "phys_hlth_days", "total_unhealthy_days"]}
).T
aberrantes.round(2)
"""
)

code(
    """
# Pourquoi les deux règles divergent : où tombe le seuil de chaque méthode ?
for colonne in ["bmi", "ment_hlth_days", "phys_hlth_days"]:
    serie = df[colonne]
    q1, q3 = serie.quantile([0.25, 0.75])
    seuil_iqr = q3 + 1.5 * (q3 - q1)
    seuil_z = serie.mean() + 3 * serie.std()
    print(f"{colonne:22s} max observé = {serie.max():5.1f} | "
          f"seuil IQR = {seuil_iqr:5.1f} | seuil z=3 : {seuil_z:5.1f}")
"""
)

md(
    """
**Les deux règles se contredisent, et de façon spectaculaire.**

Pour l'IMC, elles restent cohérentes : 3,88 % de valeurs hors IQR contre 1,17 %
au-delà de 3 écarts-types — même ordre de grandeur.

Pour `phys_hlth_days`, en revanche, la règle de l'IQR signale **16,14 %** de
l'échantillon là où celle du z-score n'en signale **aucune** (0,00 %). Ce n'est
pas une erreur de calcul : la variable est **bornée à 30 par le questionnaire**,
et son seuil à 3 écarts-types dépasse 30. Aucune valeur ne peut donc être
atteinte, tandis que le seuil de l'IQR tombe à 7,5 et coupe en pleine
distribution légitime.

**Conclusion : la notion même de « valeur aberrante » n'a pas de sens ici.** Ces
variables sont bornées et à forte inflation de zéros ; les deux règles classiques
supposent une distribution approximativement symétrique et non bornée. Appliquer
l'IQR mécaniquement reviendrait à écarter environ 40 000 réponses parfaitement
valides — précisément celles des personnes en souffrance, c'est-à-dire celles qui
portent le signal recherché.
"""
)

md(
    """
### 5.3 Valeurs extrêmes : erreurs ou réalité ?

Il faut examiner ce que sont réellement ces valeurs plutôt que de leur appliquer
un seuil aveugle.
"""
)

code(
    """
print("--- IMC : queue haute de la distribution ---")
print(df.bmi.quantile([0.95, 0.99, 0.999, 1.0]).round(1).to_string())
print(f"\\nIMC > 60  : {(df.bmi > 60).sum():>6,} lignes  "
      f"({(df.bmi > 60).mean()*100:.3f} %)  -> physiologiquement douteux")
print(f"IMC > 80  : {(df.bmi > 80).sum():>6,} lignes  "
      f"({(df.bmi > 80).mean()*100:.3f} %)  -> tres probablement errone")
print(f"\\nPrevalence si IMC > 60 : {df.loc[df.bmi > 60, 'heart_disease'].mean()*100:.2f} %")
print(f"Prevalence generale    : {df.heart_disease.mean()*100:.2f} %")

print("\\n--- Jours de mal-etre : les valeurs a 30 ---")
print(f"ment_hlth_days = 30 : {(df.ment_hlth_days == 30).sum():>6,} lignes "
      f"({(df.ment_hlth_days == 30).mean()*100:.2f} %)")
print(f"phys_hlth_days = 30 : {(df.phys_hlth_days == 30).sum():>6,} lignes "
      f"({(df.phys_hlth_days == 30).mean()*100:.2f} %)")
print(f"\\nPrevalence si phys_hlth_days = 30 : "
      f"{df.loc[df.phys_hlth_days == 30, 'heart_disease'].mean()*100:.2f} %")
"""
)

md(
    """
**Deux situations diamétralement opposées.**

Les **IMC supérieurs à 60** (805 lignes, 0,32 %) sont physiologiquement très
improbables — un IMC de 98 supposerait par exemple 285 kg pour 1,70 m. Fait
révélateur : leur prévalence de maladie cardiaque est de **8,94 %**, soit
*inférieure* à la moyenne générale de 9,42 %. S'il s'agissait de cas d'obésité
extrême réels, on attendrait l'inverse — l'obésité massive majore le risque
cardiaque. Cette absence de signal suggère du **bruit de saisie** plutôt que des
mesures authentiques. Ils restent néanmoins **conservés et signalés** par
`flag_bmi_extreme` : 0,32 % de l'échantillon ne pèsera pas sur l'apprentissage, et
les supprimer serait une décision arbitraire que rien n'impose.

Les **30 jours de mal-être** relèvent d'une tout autre logique : ce n'est pas une
anomalie mais la **borne du questionnaire** — on ne peut pas déclarer plus de
30 jours sur 30. Et le signal est massif : parmi les répondants déclarant 30 jours
de souffrance physique, **23,86 % sont atteints**, contre 9,42 % en moyenne, soit
2,5 fois plus. Ces observations sont **parmi les plus informatives du jeu de
données**. Les traiter comme des valeurs aberrantes détruirait précisément ce
qu'on cherche à modéliser.

**Décision : aucune valeur n'est supprimée ni winsorisée.** Les extrêmes sont
signalés, et les modèles robustes aux valeurs extrêmes (arbres, ensembles) seront
privilégiés.
"""
)

md(
    """
### 5.4 Comparaison des échelles : le vrai argument pour la standardisation
"""
)

code(
    """
a_comparer = [
    "bmi", "ment_hlth_days", "phys_hlth_days", "age_group", "gen_hlth",
    "income", "education", "risk_factor_count", "high_bp", "smoker",
]

echelles = pd.DataFrame({
    "min": df[a_comparer].min(),
    "max": df[a_comparer].max(),
    "étendue": df[a_comparer].max() - df[a_comparer].min(),
    "moyenne": df[a_comparer].mean(),
    "écart-type": df[a_comparer].std(),
}).sort_values("étendue", ascending=False)

echelles.round(2)
"""
)

code(
    """
fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))

axes[0].barh(echelles.index, echelles["étendue"], color=BLEU)
axes[0].set_xlabel("Étendue (max - min)")
axes[0].set_title("Avant standardisation : échelles très hétérogènes")
axes[0].invert_yaxis()

standardise = (df[a_comparer] - df[a_comparer].mean()) / df[a_comparer].std()
etendues_std = (standardise.max() - standardise.min()).loc[echelles.index]
axes[1].barh(etendues_std.index, etendues_std.values, color="#3D8B5F")
axes[1].set_xlabel("Étendue après centrage-réduction")
axes[1].set_title("Après standardisation : ordres de grandeur comparables")
axes[1].invert_yaxis()

plt.tight_layout()
enregistrer("10_echelles_standardisation")
plt.show()

print(f"Rapport des etendues avant : {echelles['étendue'].max() / echelles['étendue'].min():.0f} pour 1")
print(f"Rapport des etendues apres : {etendues_std.max() / etendues_std.min():.1f} pour 1")
"""
)

md(
    """
Voilà l'argument décisif — et il **ne repose pas sur les valeurs aberrantes**.

L'IMC s'étend sur 86 unités quand les indicateurs binaires n'en couvrent qu'une
seule. Pour tout algorithme fondé sur une **distance** ou sur une **régularisation
pénalisant l'amplitude des coefficients**, l'IMC écraserait mécaniquement les
autres variables — non parce qu'il est plus informatif, mais parce qu'il est
numériquement plus grand.

| Famille de modèle | Standardisation | Raison |
|---|---|---|
| kNN, SVM | **Indispensable** | Fondés sur des distances euclidiennes |
| Régression logistique (avec pénalisation) | **Nécessaire** | La pénalité L1/L2 dépend de l'échelle des coefficients |
| Arbre de décision, forêt aléatoire, XGBoost | **Inutile** | Les seuils de découpe sont invariants par changement d'échelle monotone |

**Décision retenue** : la standardisation est intégrée au `ColumnTransformer` du
pipeline (module 04), **ajusté sur le jeu d'entraînement uniquement** puis
appliqué au jeu de test — faute de quoi les statistiques du test fuiteraient dans
l'apprentissage. Elle est conservée même pour les modèles à base d'arbres, où elle
est neutre, afin que tous les modèles partagent exactement le même préprocessing
et restent comparables.
"""
)

# ===========================================================================
# Prévalence par segment
# ===========================================================================

md(
    """
## 6. Prévalence par segment

C'est le cœur de l'analyse : quels profils sont les plus touchés ?
"""
)

code(
    """
LIBELLES = {
    "age_group": {
        1: "18-24", 2: "25-29", 3: "30-34", 4: "35-39", 5: "40-44", 6: "45-49",
        7: "50-54", 8: "55-59", 9: "60-64", 10: "65-69", 11: "70-74",
        12: "75-79", 13: "80+",
    },
    "gen_hlth": {1: "Excellente", 2: "Très bonne", 3: "Bonne", 4: "Moyenne", 5: "Mauvaise"},
    "bmi_class": {
        1: "Insuff. pond.", 2: "Normale", 3: "Surpoids",
        4: "Obésité I", 5: "Obésité II", 6: "Obésité III",
    },
    "income": {
        1: "<10k", 2: "10-15k", 3: "15-20k", 4: "20-25k",
        5: "25-35k", 6: "35-50k", 7: "50-75k", 8: "75k+",
    },
    "education": {
        1: "Aucune", 2: "Primaire", 3: "Sec. non ach.",
        4: "Secondaire", 5: "Sup. non ach.", 6: "Diplômé sup.",
    },
    "diabetes": {0: "Non", 1: "Prédiabète", 2: "Diabète"},
    "sex": {0: "Femme", 1: "Homme"},
}


def prevalence_par(colonne):
    \"\"\"Prévalence de la maladie par modalité, avec effectifs.\"\"\"
    resultat = df.groupby(colonne).agg(
        effectif=("heart_disease", "size"),
        prevalence=("heart_disease", "mean"),
    )
    resultat["prevalence"] *= 100
    resultat.index = resultat.index.map(LIBELLES.get(colonne, {}))
    return resultat
"""
)

code(
    """
segments = ["age_group", "gen_hlth", "bmi_class", "income", "education", "diabetes"]
titres_seg = {
    "age_group": "Tranche d'âge",
    "gen_hlth": "État de santé perçu",
    "bmi_class": "Classe d'IMC (OMS)",
    "income": "Revenu du foyer",
    "education": "Niveau d'études",
    "diabetes": "Diabète",
}

fig, axes = plt.subplots(2, 3, figsize=(15, 8))

for ax, colonne in zip(axes.ravel(), segments):
    donnees = prevalence_par(colonne)
    couleurs = plt.cm.Reds(np.linspace(0.35, 0.85, len(donnees)))
    ax.bar(donnees.index.astype(str), donnees.prevalence, color=couleurs)
    ax.axhline(9.42, ls="--", c="grey", lw=1)
    ax.set_title(titres_seg[colonne], fontsize=10)
    ax.set_ylabel("% atteints")
    ax.tick_params(axis="x", rotation=45, labelsize=8)

plt.suptitle(
    "Prévalence de la maladie cardiaque par segment (trait = moyenne 9,42 %)",
    y=1.00, fontsize=12,
)
plt.tight_layout()
enregistrer("04_prevalence_segments")
plt.show()
"""
)

code(
    """
prevalence_par("age_group").round(2)
"""
)

md(
    """
**L'âge est le facteur le plus discriminant** : la prévalence passe de moins de
1 % chez les 18-24 ans à plus de 20 % chez les 80 ans et plus. La progression est
strictement monotone.

**L'état de santé perçu est presque aussi puissant** — les personnes se déclarant
en mauvaise santé sont environ dix fois plus touchées que celles se disant en
excellente santé. C'est une variable subjective, mais elle résume beaucoup
d'information clinique.

**Le gradient social est net** : la prévalence décroît régulièrement à mesure que
le revenu et le niveau d'études augmentent.
"""
)

md(
    """
### La courbe en J de l'IMC
"""
)

code(
    """
imc = prevalence_par("bmi_class")

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(imc.index.astype(str), imc.prevalence, "o-", color=ROUGE, lw=2, ms=8)
ax.axhline(9.42, ls="--", c="grey", lw=1, label="moyenne (9,42 %)")
ax.set_ylabel("% atteints")
ax.set_title("Prévalence selon la classe d'IMC : une courbe en J, non linéaire")
ax.legend()
enregistrer("05_imc_courbe_j")
plt.show()

imc.round(2)
"""
)

md(
    """
**Résultat important.** La relation entre IMC et maladie cardiaque **n'est pas
monotone** : les personnes en insuffisance pondérale (10,59 %) sont *plus*
touchées que celles de corpulence normale (6,84 %), à un niveau proche de
l'obésité modérée.

Ce phénomène est bien documenté en épidémiologie — il relève largement de la
**causalité inverse** : la maladie chronique fait maigrir, plutôt que la maigreur
ne cause la maladie. La cohabitation dans le temps des variables (§ limite
méthodologique) empêche de trancher ici.

**Conséquence pratique** : un modèle linéaire appliqué à l'IMC brut manquerait
complètement cette structure. Cela justifie de conserver la **classe d'IMC**
catégorielle en plus de la valeur continue, et privilégie les modèles à base
d'arbres, capables de capturer ce type de non-linéarité.
"""
)

# ===========================================================================
# Facteurs de risque
# ===========================================================================

md(
    """
## 7. Cumul des facteurs de risque

`risk_factor_count` compte les facteurs de risque cardiovasculaire reconnus
présents chez un répondant : hypertension, cholestérol élevé, tabagisme, AVC,
difficulté à marcher, diabète, obésité.
"""
)

code(
    """
cumul = df.groupby("risk_factor_count").agg(
    effectif=("heart_disease", "size"),
    prevalence=("heart_disease", "mean"),
)
cumul["prevalence"] *= 100

fig, ax1 = plt.subplots(figsize=(9, 4.5))
ax1.bar(cumul.index, cumul.effectif, color=BLEU, alpha=0.30, label="effectif")
ax1.set_xlabel("Nombre de facteurs de risque")
ax1.set_ylabel("Effectif", color=BLEU)
ax1.grid(False)

ax2 = ax1.twinx()
ax2.plot(cumul.index, cumul.prevalence, "o-", color=ROUGE, lw=2.5, ms=8,
         label="prévalence")
ax2.set_ylabel("% atteints", color=ROUGE)
ax2.grid(False)
for x, y in zip(cumul.index, cumul.prevalence):
    ax2.annotate(f"{y:.1f}%", (x, y), textcoords="offset points",
                 xytext=(0, 9), ha="center", fontsize=8, color=ROUGE)

plt.title("La prévalence croît de 1,2 % à 59 % avec le cumul des facteurs")
enregistrer("06_cumul_facteurs_risque")
plt.show()

cumul.round(2)
"""
)

md(
    """
Le gradient est **strictement monotone et très étendu** : de **1,19 %** chez les
répondants sans aucun facteur de risque à **59,18 %** chez ceux qui en cumulent
sept — un rapport de 1 à 50.

Cette variable dérivée, construite à partir de sept colonnes, résume à elle seule
une part importante du signal. Elle sera précieuse pour la segmentation et pour
l'application web, où elle offre une lecture immédiate du risque.
"""
)

# ===========================================================================
# Corrélations
# ===========================================================================

md(
    """
## 8. Structure des corrélations
"""
)

code(
    """
colonnes_corr = [
    "heart_disease", "high_bp", "high_chol", "bmi", "smoker", "stroke",
    "diabetes", "phys_activity", "gen_hlth", "ment_hlth_days",
    "phys_hlth_days", "diff_walk", "sex", "age_group", "education", "income",
]

correlations = df[colonnes_corr].corr()

fig, ax = plt.subplots(figsize=(11, 9))
masque = np.triu(np.ones_like(correlations, dtype=bool))
sns.heatmap(correlations, mask=masque, annot=True, fmt=".2f", cmap="RdBu_r",
            center=0, vmin=-0.6, vmax=0.6, square=True,
            cbar_kws={"shrink": 0.7}, annot_kws={"size": 7}, ax=ax)
ax.set_title("Matrice des corrélations de Pearson", pad=12)
enregistrer("07_correlations")
plt.show()
"""
)

code(
    """
liens = (
    correlations["heart_disease"]
    .drop("heart_disease")
    .sort_values(key=abs, ascending=False)
    .to_frame("corrélation avec la cible")
)
liens.round(3)
"""
)

md(
    """
Aucune corrélation linéaire n'est très forte — la plus élevée avoisine 0,3. C'est
attendu : la plupart des variables sont binaires, et le coefficient de Pearson
mesure mal les relations non linéaires comme la courbe en J de l'IMC.

**Conséquence** : il ne faut pas conclure que ces variables sont peu informatives.
Le cumul des facteurs (§7) montre au contraire un signal très net. Les modèles
non linéaires devraient nettement surpasser une régression logistique simple.

**Aucune paire de variables explicatives n'est fortement corrélée entre elles**
(pas de multicolinéarité problématique) : on peut toutes les conserver.
"""
)

# ===========================================================================
# Profils comparés
# ===========================================================================

md(
    """
## 9. Comparaison des profils : atteints contre non atteints
"""
)

code(
    """
indicateurs = [
    "high_bp", "high_chol", "smoker", "stroke", "diabetes", "phys_activity",
    "fruits", "veggies", "hvy_alcohol", "diff_walk", "has_care_access",
]
noms = [
    "Hypertension", "Cholestérol élevé", "Fumeur", "AVC", "Diabète",
    "Activité physique", "Fruits quotidiens", "Légumes quotidiens",
    "Alcool excessif", "Difficulté à marcher", "Accès aux soins",
]

profils = pd.DataFrame({
    "Non atteints (%)": [df.loc[df.heart_disease == 0, c].gt(0).mean() * 100 for c in indicateurs],
    "Atteints (%)": [df.loc[df.heart_disease == 1, c].gt(0).mean() * 100 for c in indicateurs],
}, index=noms)
profils["Écart"] = profils["Atteints (%)"] - profils["Non atteints (%)"]
profils = profils.sort_values("Écart")

fig, ax = plt.subplots(figsize=(9, 6))
y = np.arange(len(profils))
ax.barh(y - 0.2, profils["Non atteints (%)"], height=0.4, color=BLEU, label="Non atteints")
ax.barh(y + 0.2, profils["Atteints (%)"], height=0.4, color=ROUGE, label="Atteints")
ax.set_yticks(y)
ax.set_yticklabels(profils.index)
ax.set_xlabel("% de répondants concernés")
ax.set_title("Profils comparés selon le statut cardiaque")
ax.legend()
enregistrer("08_profils_compares")
plt.show()

profils.round(1)
"""
)

md(
    """
Les écarts les plus marqués concernent la **difficulté à marcher**, l'**AVC**,
l'**hypertension** et le **cholestérol élevé**. À l'inverse, l'**activité
physique** est plus fréquente chez les non atteints — le seul indicateur nettement
protecteur.

L'**alcool excessif** apparaît paradoxalement plus fréquent chez les non atteints.
Il faut y voir un effet de structure plutôt qu'un effet protecteur : les gros
consommateurs déclarés sont en moyenne plus jeunes, et l'âge domine largement le
risque.
"""
)

# ===========================================================================
# Synthèse
# ===========================================================================

md(
    """
## 10. Synthèse

### Qualité des données

| Point | Constat | Décision |
|---|---|---|
| Valeurs manquantes | Aucune | Pas d'imputation nécessaire |
| Doublons exacts | 23 899 (9,42 %) | **Conservés** — collisions légitimes, démontré par 4 tests |
| IMC extrêmes | 832 lignes hors [14, 60] | Signalés par `flag_bmi_extreme`, non supprimés |
| Incohérences santé | 7 213 lignes | Signalées, légitimes (maladie chronique stabilisée) |

### Facteurs associés, par ordre d'importance

1. **Âge** — de moins de 1 % à plus de 20 % de prévalence
2. **État de santé perçu** — rapport d'environ 1 à 10
3. **Cumul de facteurs de risque** — de 1,2 % à 59 %
4. **Antécédent d'AVC, difficulté à marcher, hypertension, cholestérol**
5. **Gradient socio-économique** — revenu et niveau d'études

### Ce que l'analyse impose à la modélisation

- **Ne pas utiliser l'exactitude** : à 9,42 % de positifs, prédire « aucun malade »
  donnerait 90,58 %. Critères retenus : ROC-AUC, PR-AUC, rappel, F1.
- **Traiter le déséquilibre** : pondération des classes, comparée à SMOTE.
- **Privilégier les modèles non linéaires** : la courbe en J de l'IMC et la
  faiblesse des corrélations de Pearson montrent que le signal n'est pas linéaire.
- **Quantifier l'erreur irréductible** : des profils identiques portent des cibles
  opposées, ce qui plafonne la performance atteignable.
- **Rester prudent sur l'interprétation** : associations transversales, pas de
  causalité — à rappeler dans tous les livrables.
"""
)

# ===========================================================================
# Écriture
# ===========================================================================

notebook = nbf.v4.new_notebook(cells=cellules)
notebook.metadata = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    },
    "language_info": {"name": "python", "version": "3.13"},
}

nbf.write(notebook, DESTINATION)
print(f"Notebook genere : {DESTINATION} ({len(cellules)} cellules)")
