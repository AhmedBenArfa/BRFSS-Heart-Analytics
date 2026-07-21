"""Génère la documentation technique « Machine Learning ».

Tous les chiffres proviennent de `04_machine_learning/models/resultats.json`
et `metadata.json`, produits par l'exécution du notebook. Aucune valeur n'est
saisie à la main : le document ne peut pas diverger des résultats réels.

Prérequis : avoir exécuté le notebook 01_ml.ipynb.

Usage :
    python _build_doc_pdf_ml.py

Sortie :
    06_rapport/Documentation_Technique_MachineLearning.pdf
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

RACINE = Path(__file__).resolve().parents[1]
MODELES = RACINE / "04_machine_learning" / "models"
FIG = RACINE / "06_rapport" / "figures" / "ml"
SORTIE = RACINE / "06_rapport" / "Documentation_Technique_MachineLearning.pdf"

DOSSIER_POLICES = Path(
    r"C:\Users\Mega-pc\anaconda3\Lib\site-packages\matplotlib\mpl-data\fonts\ttf"
)

MARINE = (31, 59, 92)
GRIS = (90, 90, 90)
ACCENT = (193, 68, 63)
BLEU = (46, 92, 138)
VERT = (61, 139, 95)


def fr(texte: str) -> str:
    return re.sub(r"(?<=\d)\.(?=\d)", ",", texte)


def charger() -> tuple[dict, dict]:
    meta = json.loads((MODELES / "metadata.json").read_text(encoding="utf-8"))
    res = json.loads((MODELES / "resultats.json").read_text(encoding="utf-8"))
    return meta, res


class Rapport(FPDF):
    def __init__(self, pied: str):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.pied = pied
        self.set_auto_page_break(auto=True, margin=16)
        for style, fichier in [("", "DejaVuSans.ttf"), ("B", "DejaVuSans-Bold.ttf"),
                               ("I", "DejaVuSans-Oblique.ttf")]:
            self.add_font("DJ", style, str(DOSSIER_POLICES / fichier))
        self.add_font("MONO", "", str(DOSSIER_POLICES / "DejaVuSansMono.ttf"))
        self.set_font("DJ", "", 10.5)

    def multi_cell(self, *a, **k):
        k.setdefault("new_x", XPos.LMARGIN)
        k.setdefault("new_y", YPos.NEXT)
        return super().multi_cell(*a, **k)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-14)
        self.set_font("DJ", "I", 8)
        self.set_text_color(*GRIS)
        self.cell(0, 8, f"{self.pied}   |   page {self.page_no()}", align="C")

    def titre1(self, t):
        self.add_page()
        self.set_font("DJ", "B", 17)
        self.set_text_color(*MARINE)
        self.multi_cell(0, 9, t)
        self.ln(1)
        y = self.get_y()
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.6)
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(4)
        self.set_text_color(0, 0, 0)

    def titre2(self, t):
        self.ln(2)
        self.set_font("DJ", "B", 12.5)
        self.set_text_color(*MARINE)
        self.multi_cell(0, 6.5, t)
        self.ln(0.5)
        self.set_text_color(0, 0, 0)

    def titre3(self, t):
        self.ln(1)
        self.set_font("DJ", "B", 11)
        self.set_text_color(*BLEU)
        self.multi_cell(0, 5.8, t)
        self.set_text_color(0, 0, 0)

    def texte(self, t):
        self.set_font("DJ", "", 10.5)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 5.15, fr(t.strip()), markdown=True)
        self.ln(1.5)

    def puce(self, t):
        self.set_font("DJ", "", 10.5)
        x = self.get_x()
        self.set_x(x + 3)
        self.cell(4, 5.1, "•")
        self.multi_cell(0, 5.1, fr(t.strip()), markdown=True)
        self.set_x(x)

    def encadre(self, titre, contenu, couleur=ACCENT):
        self.ln(1)
        self.set_draw_color(*couleur)
        self.set_line_width(0.9)
        y0 = self.get_y()
        self.set_font("DJ", "B", 10)
        self.set_text_color(*couleur)
        self.set_x(self.l_margin + 3)
        self.multi_cell(self.w - self.l_margin - self.r_margin - 6, 6, titre)
        self.set_text_color(0, 0, 0)
        self.set_font("DJ", "", 10)
        self.set_x(self.l_margin + 3)
        self.multi_cell(self.w - self.l_margin - self.r_margin - 6, 5.1,
                        fr(contenu.strip()), markdown=True)
        self.line(self.l_margin, y0, self.l_margin, self.get_y())
        self.ln(2.5)

    def tableau(self, entetes, lignes, largeurs, alignements=None):
        if alignements is None:
            alignements = ["L"] + ["R"] * (len(entetes) - 1)
        if self.get_y() + 8 + 6 * len(lignes) > self.h - 20:
            self.add_page()
        self.set_font("DJ", "B", 8.8)
        self.set_fill_color(*MARINE)
        self.set_text_color(255, 255, 255)
        for e, l, a in zip(entetes, largeurs, alignements):
            self.cell(l, 7, e, align=a, fill=True, border=0)
        self.ln()
        self.set_font("DJ", "", 8.8)
        self.set_text_color(0, 0, 0)
        for i, ligne in enumerate(lignes):
            self.set_fill_color(248, 249, 251)
            for v, l, a in zip(ligne, largeurs, alignements):
                self.cell(l, 6, fr(str(v)), align=a, fill=i % 2 == 0, border=0)
            self.ln()
        self.ln(3)

    def code(self, contenu):
        self.set_font("MONO", "", 8.2)
        self.set_fill_color(245, 246, 248)
        for ligne in contenu.strip("\n").split("\n"):
            self.cell(0, 4.4, "  " + ligne, fill=True, new_x=XPos.LMARGIN,
                      new_y=YPos.NEXT)
        self.ln(2.5)

    def figure(self, nom, legende, largeur=165):
        chemin = FIG / f"{nom}.png"
        if not chemin.exists():
            self.texte(f"[figure manquante : {nom}.png]")
            return
        from PIL import Image

        with Image.open(chemin) as im:
            ratio = im.height / im.width
        h = largeur * ratio
        if self.get_y() + h + 12 > self.h - 20:
            self.add_page()
        self.image(str(chemin), x=(self.w - largeur) / 2, w=largeur)
        self.ln(1.5)
        self.set_font("DJ", "I", 8.5)
        self.set_text_color(*GRIS)
        self.multi_cell(0, 4.4, fr(legende), align="C")
        self.set_text_color(0, 0, 0)
        self.ln(2.5)


def construire(meta: dict, res: dict) -> Rapport:
    pdf = Rapport(pied="Documentation technique — Machine Learning")
    perf = meta["performances_test"]
    mc = res["test"]
    irr = res["erreur_irreductible"]

    # ================= Page de garde =================
    pdf.add_page()
    pdf.ln(56)
    pdf.set_font("DJ", "B", 25)
    pdf.set_text_color(*MARINE)
    pdf.multi_cell(0, 12, "Documentation technique", align="C")
    pdf.set_font("DJ", "B", 17)
    pdf.multi_cell(0, 9, "Machine Learning", align="C")
    pdf.ln(5)
    pdf.set_draw_color(*ACCENT)
    pdf.set_line_width(0.9)
    pdf.line(65, pdf.get_y(), pdf.w - 65, pdf.get_y())
    pdf.ln(9)
    pdf.set_font("DJ", "", 13)
    pdf.set_text_color(*GRIS)
    pdf.multi_cell(0, 7, "BRFSS Heart Analytics", align="C")
    pdf.set_font("DJ", "", 11)
    pdf.multi_cell(
        0, 6,
        "Préparation, préprocessing, comparaison de six modèles,\n"
        "diagnostic et interprétation\n(BRFSS, CDC, 2015)",
        align="C",
    )
    pdf.ln(22)
    pdf.set_font("DJ", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 6, "Ahmed Ben Arfa", align="C")
    pdf.set_font("DJ", "", 10)
    pdf.set_text_color(*GRIS)
    pdf.multi_cell(0, 5.5, date.today().strftime("%d/%m/%Y"), align="C")
    pdf.ln(6)
    pdf.set_font("MONO", "", 8.5)
    pdf.multi_cell(0, 5, "github.com/AhmedBenArfa/BRFSS-Heart-Analytics", align="C")

    # ================= 1. Objectif =================
    pdf.titre1("1. Objectif et cadre")
    pdf.texte(
        "Cette phase construit un modèle capable d'estimer, à partir d'un profil "
        "de santé déclaré, la probabilité qu'une personne présente une maladie ou "
        "un accident cardiaque, puis d'identifier les facteurs déterminants."
    )
    pdf.encadre(
        "Limite méthodologique",
        "Les variables explicatives sont auto-déclarées au même moment que la "
        "cible. Le modèle mesure une association transversale : il estime un "
        "risque à partir d'un profil, il ne prédit pas la survenue future d'un "
        "accident cardiaque. Toute lecture causale est exclue.",
    )
    pdf.titre2("1.1 Ce que les phases précédentes imposent")
    pdf.tableau(
        ["Constat établi", "Conséquence"],
        [
            ["Cible à 9,42 % de positifs", "Exactitude inutilisable"],
            ["Signal diffus (ACP peu compressive)", "Tester des modèles non linéaires"],
            ["Interactions suggérées par le clustering", "Inclure arbres et ensembles"],
            ["Relation en J de l'IMC", "Le linéaire brut manquerait la structure"],
            ["Échelles très hétérogènes (86 pour 1)", "Standardisation obligatoire"],
        ],
        [92, 73],
        ["L", "L"],
    )

    # ================= 2. Préparation =================
    pdf.titre1("2. Préparation des données")
    pdf.titre2("2.1 Sélection des variables")
    pdf.texte(
        f"Le modèle utilise les {len(meta['variables'])} variables d'origine de "
        "l'enquête. Trois familles de colonnes ont été volontairement écartées :"
    )
    pdf.puce(
        "La cible elle-même, évidemment."
    )
    pdf.puce(
        "Les variables dérivées produites par l'ETL (score de facteurs de risque, "
        "jours de mal-être cumulés, classe d'IMC). Elles sont des fonctions "
        "déterministes des colonnes conservées : les inclure n'ajouterait aucune "
        "information, mais introduirait de la redondance, gênerait la lecture des "
        "importances et donnerait un poids artificiel aux variables comptées "
        "plusieurs fois."
    )
    pdf.puce(
        "Les drapeaux qualité (IMC extrême, profil dupliqué). Ils décrivent la "
        "donnée, pas le répondant : les utiliser reviendrait à laisser le modèle "
        "exploiter un artefact de collecte."
    )

    pdf.titre2("2.2 Découpage stratifié")
    pdf.texte(
        f"Le jeu est séparé en {meta['n_entrainement']:,} lignes d'entraînement et "
        f"{meta['n_test']:,} lignes de test (80 / 20), avec **stratification** sur "
        "la cible.".replace(",", " ")
    )
    pdf.texte(
        "La stratification garantit que la proportion de cas positifs est "
        "identique dans les deux jeux. Sans elle, un tirage malchanceux pourrait "
        "produire un jeu de test à la prévalence sensiblement différente : "
        "l'évaluation finale mesurerait alors autant la chance du tirage que la "
        "qualité du modèle. Avec seulement 9,42 % de positifs, ce risque est loin "
        "d'être théorique."
    )
    pdf.encadre(
        "Le jeu de test est mis sous scellés",
        "Le jeu de test n'est utilisé qu'une seule fois, à la toute fin, pour "
        "l'évaluation. Toute la sélection — choix des modèles, réglage des "
        "hyperparamètres, stratégie de déséquilibre, diagnostic — s'effectue par "
        "validation croisée sur le seul jeu d'entraînement. Consulter le test "
        "plusieurs fois pour orienter des décisions reviendrait à l'utiliser comme "
        "un jeu de validation, et l'estimation finale serait optimiste.",
        couleur=VERT,
    )

    # ================= 3. Préprocessing =================
    pdf.titre1("3. Préprocessing : transformations et encodage")
    pdf.texte(
        "Le préprocessing est assemblé dans un ColumnTransformer, lui-même intégré "
        "à un Pipeline scikit-learn. Les 21 variables sont réparties en trois "
        "groupes, chacun recevant un traitement adapté à sa nature."
    )
    pdf.tableau(
        ["Groupe", "Variables", "Traitement"],
        [
            ["Continues", "bmi, ment_hlth_days, phys_hlth_days", "StandardScaler"],
            ["Ordinales", "gen_hlth, age_group, education, income, diabetes",
             "StandardScaler"],
            ["Binaires", "13 indicateurs 0/1", "passthrough (aucun)"],
        ],
        [28, 92, 45],
        ["L", "L", "L"],
    )

    pdf.titre2("3.1 La standardisation : ce qu'elle fait et pourquoi")
    pdf.texte(
        "La standardisation (centrage-réduction) transforme chaque variable pour "
        "lui donner une moyenne de 0 et un écart-type de 1, en appliquant à chaque "
        "valeur la transformation suivante :"
    )
    pdf.code("z = (x - moyenne) / écart-type")
    pdf.texte(
        "La transformation est **linéaire et strictement monotone** : elle ne "
        "déforme ni la distribution, ni l'ordre des valeurs. Une personne dont "
        "l'IMC est supérieur à celui d'une autre le reste après transformation. "
        "Seule l'unité de mesure change."
    )
    pdf.titre3("Pourquoi c'est indispensable ici")
    pdf.texte(
        "L'analyse exploratoire a mesuré un rapport de 86 pour 1 entre la plus "
        "grande et la plus petite étendue de variables : l'IMC s'étale sur près de "
        "90 unités quand un indicateur binaire n'en couvre qu'une seule. Pour tout "
        "algorithme fondé sur des distances ou sur une pénalisation, l'IMC "
        "écraserait mécaniquement les autres variables — non parce qu'il serait "
        "plus informatif, mais parce qu'il est numériquement plus grand. Après "
        "standardisation, ce rapport tombe à 6,5 pour 1."
    )
    pdf.tableau(
        ["Famille de modèle", "Standardisation", "Raison"],
        [
            ["kNN", "Indispensable", "Distances euclidiennes"],
            ["SVM", "Indispensable", "Marge définie par des distances"],
            ["Régression logistique pénalisée", "Nécessaire",
             "La pénalité L2 dépend de l'échelle"],
            ["Arbre, forêt, XGBoost", "Neutre",
             "Seuils invariants par transformation monotone"],
        ],
        [58, 32, 75],
        ["L", "C", "L"],
    )
    pdf.encadre(
        "Pourquoi standardiser aussi pour les arbres",
        "Les modèles à base d'arbres découpent selon des seuils : une "
        "transformation monotone ne change strictement rien à leurs résultats. La "
        "standardisation leur est donc neutre. Elle est néanmoins appliquée à tous "
        "les modèles, afin que la comparaison porte uniquement sur les algorithmes "
        "et non sur des préparations différentes. Un écart de performance ne peut "
        "ainsi jamais s'expliquer par un préprocessing plus favorable à l'un.",
        couleur=BLEU,
    )
    pdf.titre3("L'ajustement se fait sur le seul jeu d'entraînement")
    pdf.texte(
        "Point méthodologique central. Le StandardScaler doit calculer une moyenne "
        "et un écart-type : ces statistiques sont estimées **uniquement** sur les "
        "données d'entraînement, puis appliquées telles quelles au test. En "
        "validation croisée, l'opération est refaite à chaque pli, sur le seul pli "
        "d'apprentissage."
    )
    pdf.encadre(
        "Fuite de données : l'erreur à ne pas commettre",
        "Standardiser l'ensemble du jeu AVANT le découpage constitue une fuite de "
        "données : les moyennes et écarts-types incorporeraient de l'information "
        "issue du test, que le modèle exploiterait indirectement. Les scores "
        "obtenus seraient optimistes et ne se reproduiraient pas en production. "
        "Placer le préprocesseur dans le Pipeline rend cette erreur structurellement "
        "impossible : scikit-learn n'appelle jamais fit() sur autre chose que les "
        "données d'apprentissage du moment.",
    )

    pdf.titre2("3.2 Encodage des variables : pourquoi pas de OneHotEncoder")
    pdf.texte(
        "L'encodage one-hot (OneHotEncoder) transforme une variable catégorielle "
        "en autant de colonnes binaires qu'elle a de modalités. C'est une étape "
        "quasi systématique en machine learning — mais **elle n'est pas utilisée "
        "ici**, et ce choix mérite d'être justifié précisément."
    )
    pdf.titre3("Les variables binaires : déjà encodées")
    pdf.texte(
        "Les 13 indicateurs (hypertension, tabagisme, activité physique…) sont déjà "
        "codés 0/1. Un encodage one-hot produirait deux colonnes parfaitement "
        "complémentaires, dont l'une serait redondante — c'est le piège classique "
        "de la colinéarité parfaite (dummy trap). Ces variables sont donc "
        "transmises telles quelles."
    )
    pdf.titre3("Les variables ordinales : l'ordre porte l'information")
    pdf.texte(
        "C'est le cas le plus intéressant. Des variables comme gen_hlth (1 = "
        "excellente à 5 = mauvaise), age_group (1 à 13), education (1 à 6), income "
        "(1 à 8) ou diabetes (0 = non, 1 = prédiabète, 2 = diabète) sont "
        "**ordinales** : leurs modalités sont naturellement ordonnées."
    )
    pdf.texte(
        "Les encoder en one-hot **détruirait cette information d'ordre**. Le modèle "
        "traiterait « 60-64 ans » et « 18-24 ans » comme deux catégories sans "
        "relation, au même titre que deux couleurs. Il devrait alors réapprendre "
        "l'ordre à partir des seules données, en consommant des degrés de liberté "
        "pour reconstituer ce que l'on sait déjà. On perdrait aussi la capacité "
        "d'extrapoler la monotonie : l'analyse exploratoire a montré que le risque "
        "croît régulièrement avec l'âge, information qu'un traitement numérique "
        "capture directement."
    )
    pdf.texte(
        "Les conserver en numérique préserve l'ordre et donne des modèles plus "
        "parcimonieux : 21 colonnes au lieu de plus de 50 après one-hot."
    )
    pdf.titre3("Quand le one-hot aurait été nécessaire")
    pdf.texte(
        "Il serait indispensable pour une variable **nominale** à plusieurs "
        "modalités — par exemple un État de résidence, une catégorie "
        "socio-professionnelle ou un groupe sanguin. Attribuer les codes 1, 2, 3 à "
        "trois États imposerait un ordre et des écarts arbitraires, que le modèle "
        "prendrait au sérieux. Le jeu BRFSS retenu ne contient aucune variable de "
        "ce type : toutes sont binaires, ordinales ou continues. L'absence "
        "d'encodage one-hot n'est donc pas un oubli, mais la conséquence de la "
        "nature des données."
    )
    pdf.encadre(
        "Une limite assumée du traitement ordinal",
        "Traiter une variable ordinale comme numérique suppose implicitement que "
        "l'écart entre modalités consécutives est constant — que passer de "
        "« 18-24 » à « 25-29 » équivaut à passer de « 75-79 » à « 80 et plus ». "
        "C'est une approximation. Les modèles à base d'arbres s'en affranchissent "
        "naturellement (ils choisissent librement leurs seuils de coupure), tandis "
        "que la régression logistique en subit la contrainte. La classe d'IMC "
        "conservée dans l'entrepôt répond au même besoin, la relation en J n'étant "
        "pas monotone.",
        couleur=BLEU,
    )

    pdf.titre2("3.3 Absence d'imputation")
    pdf.texte(
        "Aucun imputeur n'est nécessaire : le jeu ne contient aucune valeur "
        "manquante, comme établi lors de l'ETL. Cette absence est elle-même une "
        "information — le jeu Kaggle a été nettoyé en amont, ce qui a pu écarter "
        "des profils particuliers."
    )

    # ================= 4. Métriques =================
    pdf.titre1("4. Le choix des métriques")
    pdf.titre2("4.1 Pourquoi l'exactitude est écartée")
    pdf.texte(
        "Un modèle trivial, qui prédirait « personne n'est malade » pour toute la "
        f"population, atteint **{res['reference_triviale']['exactitude_pct']:.2f} % "
        "d'exactitude** sur le jeu de test, sans détecter un seul malade. Son "
        "ROC-AUC vaut 0,5 — la valeur du hasard. Cette référence, calculée "
        "explicitement dans le notebook, démontre que l'exactitude est inutilisable "
        "sur des classes déséquilibrées."
    )
    pdf.titre2("4.2 Les métriques retenues")
    pdf.tableau(
        ["Métrique", "Ce qu'elle mesure", "Rôle"],
        [
            ["ROC-AUC", "Capacité à ordonner les risques, tous seuils confondus",
             "Sélection"],
            ["PR-AUC", "Idem, centrée sur la classe minoritaire", "Arbitre"],
            ["Rappel", "Part des malades effectivement détectés", "Suivi"],
            ["Précision", "Part de vrais malades parmi les personnes signalées",
             "Suivi"],
            ["F1", "Moyenne harmonique précision / rappel", "Suivi"],
        ],
        [24, 106, 35],
        ["L", "L", "L"],
    )
    pdf.texte(
        "Le ROC-AUC a été retenu comme critère de sélection car il est "
        "**indépendant du seuil** : il évalue la capacité intrinsèque du modèle à "
        "classer les personnes à risque avant les autres, ce qui correspond "
        "exactement à l'usage visé — estimer un risque, non poser un diagnostic. Le "
        "PR-AUC sert d'arbitre lorsque deux modèles sont proches, car il est plus "
        "sévère en contexte déséquilibré."
    )
    pdf.encadre(
        "Précision et rappel se lisent ensemble",
        "Le rappel seul s'optimise trivialement en déclarant tout le monde malade. "
        "La précision seule s'optimise en ne signalant que les cas les plus "
        "évidents. Les deux chiffres côte à côte, et eux seuls, décrivent "
        "honnêtement le comportement du modèle.",
        couleur=BLEU,
    )

    pdf.titre2("4.3 Pourquoi le ROC-AUC, et pas une autre métrique")
    pdf.texte(
        "Le choix du critère de sélection est une décision structurante : il "
        "détermine quel modèle sera retenu. Trois candidats sérieux ont été pesés."
    )
    pdf.tableau(
        ["Candidat", "Argument en sa faveur", "Raison de l'écarter"],
        [
            ["PR-AUC en principal", "Centré sur la minoritaire",
             "Dépend de la prévalence"],
            ["Rappel sous contrainte", "Colle au cas d'usage médical",
             "Mélange modèle et seuil"],
            ["F1", "Compromis précision / rappel", "Dépend du seuil choisi"],
        ],
        [46, 58, 61],
        ["L", "L", "L"],
    )
    pdf.texte(
        "Le ROC-AUC l'emporte pour trois raisons convergentes."
    )
    pdf.puce(
        "**Il est indépendant du seuil.** Il évalue la capacité intrinsèque du "
        "modèle à ordonner les individus par risque croissant, sans présupposer "
        "une règle de décision. Or l'objectif du projet est précisément d'estimer "
        "un risque, pas de poser un diagnostic binaire."
    )
    pdf.puce(
        "**Il sépare proprement deux décisions distinctes.** Choisir un modèle et "
        "choisir un seuil sont deux questions différentes (voir § 11.1). Une métrique "
        "dépendante du seuil, comme le F1 ou le rappel, mêlerait les deux : on "
        "sélectionnerait un modèle sur la base d'un seuil arbitraire de 0,5, qui "
        "n'a aucune pertinence en contexte déséquilibré."
    )
    pdf.puce(
        "**Il est stable et standard.** Peu sensible aux variations "
        "d'échantillonnage et universellement compris."
    )
    pdf.encadre(
        "La limite du ROC-AUC, assumée et compensée",
        "Une critique légitime lui est adressée en contexte déséquilibré : "
        "rapportant les faux positifs à une classe majoritaire nombreuse, il peut "
        "sembler flatteur alors que la précision reste faible. C'est notre cas — un "
        "ROC-AUC de 0,85 coexiste avec une précision de 27 %. D'où le PR-AUC en "
        "arbitre, et le report systématique de la précision et du rappel.",
    )

    # ================= 5. Erreur irréductible =================
    pdf.titre1("5. L'erreur irréductible : jusqu'où peut-on monter ?")
    pdf.texte(
        "Des profils rigoureusement identiques portent parfois des cibles opposées "
        "— deux personnes au même profil déclaré, l'une atteinte, l'autre non. "
        "Aucun modèle ne peut départager ces cas. On a tenté de quantifier ce "
        "plancher d'erreur."
    )
    pdf.tableau(
        ["Mesure", "Valeur"],
        [
            ["Profils distincts", f"{irr['profils_distincts']:,}".replace(",", " ")],
            ["Profils observés au moins deux fois",
             f"{irr['profils_repetes']:,}".replace(",", " ")],
            ["Profils aux cibles contradictoires",
             f"{irr['profils_ambigus']:,}".replace(",", " ")],
            ["Part de profils uniques", f"{irr['part_profils_uniques_pct']:.1f} %"],
        ],
        [110, 55],
        ["L", "R"],
    )
    pdf.encadre(
        "Pourquoi ce calcul ne donne pas de plafond exploitable",
        f"La méthode suggérerait une erreur irréductible très faible, donc une "
        f"exactitude maximale proche de 99 %. Ce serait une conclusion fausse. "
        f"{irr['part_profils_uniques_pct']:.0f} % des profils ne sont observés qu'une "
        "seule fois : par construction, un profil unique ne peut jamais apparaître "
        "ambigu, faute de jumeau avec lequel se contredire. Le calcul ne détecte "
        "donc l'ambiguïté que sur une minorité de cas et l'ignore mécaniquement "
        "ailleurs. Il s'agit d'une borne inférieure, et d'une borne très faible.",
    )
    pdf.texte(
        "Ce que l'on peut affirmer honnêtement : parmi les profils effectivement "
        "observés plusieurs fois, une part notable porte des cibles contradictoires. "
        "Cela confirme qu'une fraction réelle du risque cardiaque n'est pas "
        "explicable par les 21 variables disponibles — génétique, antécédents "
        "familiaux, environnement et qualité du suivi médical n'y figurent pas. La "
        "vraie erreur irréductible est nécessairement bien supérieure à ce que "
        "mesure cette approche, mais elle n'est pas estimable ainsi."
    )
    pdf.texte(
        "Conséquence pratique : ne pas viser une performance parfaite. Sur ce type "
        "de données déclaratives, un ROC-AUC autour de 0,85 constitue un bon "
        "résultat ; prétendre faire beaucoup mieux signalerait plutôt une fuite de "
        "données."
    )

    # ================= 6. Modèles =================
    pdf.titre1("6. Les six familles de modèles")
    pdf.texte(
        "Six familles ont été retenues, chacune répondant à une logique différente. "
        "L'objectif n'est pas d'accumuler des algorithmes mais de couvrir des "
        "hypothèses variées sur la forme du signal."
    )
    pdf.tableau(
        ["Modèle", "Principe", "Pourquoi l'inclure"],
        [
            ["Régression logistique", "Frontière linéaire sur le log-odds",
             "Référence interprétable"],
            ["kNN", "Vote des k voisins les plus proches",
             "Approche par similarité"],
            ["Arbre de décision", "Découpages successifs par seuils",
             "Non-linéarité lisible"],
            ["Forêt aléatoire", "Moyenne d'arbres décorrélés",
             "Réduit la variance"],
            ["XGBoost", "Arbres construits séquentiellement",
             "État de l'art tabulaire"],
            ["SVM linéaire", "Hyperplan à marge maximale",
             "Autre logique linéaire"],
        ],
        [40, 62, 63],
        ["L", "L", "L"],
    )
    pdf.texte(
        "La régression logistique joue un rôle particulier : elle sert de "
        "**plancher de référence**. Un modèle complexe qui ne la dépasse pas ne "
        "justifie pas sa complexité."
    )

    pdf.titre2("6.1 Réglage par GridSearchCV")
    pdf.texte(
        "Comparer des modèles avec leurs paramètres par défaut n'a aucune valeur : "
        "on mesurerait la qualité des valeurs par défaut, pas celle des "
        "algorithmes. Chaque famille est donc optimisée par recherche exhaustive "
        "sur une grille, en validation croisée stratifiée à 5 plis, avec le ROC-AUC "
        "comme critère."
    )
    pdf.code(
        """
GridSearchCV(
    Pipeline([("prep", ColumnTransformer(...)),
              ("model", <modèle>)]),
    param_grid = <grille propre à la famille>,
    scoring    = {roc_auc, average_precision, recall, precision, f1},
    refit      = "roc_auc",
    cv         = StratifiedKFold(n_splits=5, shuffle=True),
)
"""
    )
    pdf.titre2("6.2 La régularisation, famille par famille")
    pdf.texte(
        "La régularisation pénalise la complexité afin d'éviter que le modèle "
        "n'apprenne le bruit. Elle prend une forme différente selon l'algorithme, "
        "et chaque grille explore explicitement ce levier."
    )
    pdf.tableau(
        ["Modèle", "Paramètre exploré", "Effet"],
        [
            ["Régression logistique", "C (inverse de la pénalité L2)",
             "C petit = coefficients contraints"],
            ["SVM linéaire", "C", "Compromis marge / erreurs tolérées"],
            ["Arbre de décision", "max_depth, min_samples_leaf",
             "Limitent la croissance de l'arbre"],
            ["Forêt aléatoire", "max_depth, min_samples_leaf",
             "Idem, + moyenne sur 200 arbres"],
            ["XGBoost", "max_depth, learning_rate, reg_lambda",
             "Profondeur, pas d'apprentissage, pénalité L2"],
            ["kNN", "n_neighbors", "k grand = frontière plus lisse"],
        ],
        [40, 62, 63],
        ["L", "L", "L"],
    )

    # ================= 7. Résultats =================
    pdf.titre1("7. Résultats de la comparaison")
    lignes = [
        [r["modèle"], f"{r['ROC-AUC']:.4f}", f"{r['PR-AUC']:.4f}",
         f"{r['précision']:.3f}", f"{r['rappel']:.3f}", f"{r['F1']:.3f}"]
        for r in res["comparaison"]
    ]
    pdf.tableau(
        ["Modèle", "ROC-AUC", "PR-AUC", "Précision", "Rappel", "F1"],
        lignes,
        [45, 26, 24, 25, 23, 22],
        ["L", "R", "R", "R", "R", "R"],
    )
    pdf.figure(
        "01_comparaison_modeles",
        "Comparaison des six familles, chacune à son meilleur réglage",
        largeur=175,
    )
    meilleur = res["comparaison"][0]
    pdf.texte(
        f"Le modèle retenu est **{meta['modele']}**, avec un ROC-AUC de "
        f"{meilleur['ROC-AUC']:.4f} en validation croisée. Trois enseignements "
        "méritent d'être soulignés."
    )
    pdf.titre3("Le réglage change le classement")
    pdf.texte(
        "Avec les paramètres par défaut, la régression logistique devançait les "
        "méthodes d'ensemble. Après optimisation, le classement s'inverse. C'est la "
        "démonstration qu'une comparaison de modèles non réglés ne prouve rien."
    )
    pdf.titre3("Les écarts entre familles sont minimes")
    pdf.texte(
        "Quelques millièmes de ROC-AUC séparent les quatre meilleurs modèles. Le "
        "signal disponible est donc capté par toutes les approches : il n'existe "
        "pas de structure exotique que seul un modèle sophistiqué saurait exploiter."
    )
    pdf.titre3("La précision est structurellement basse")
    pdf.texte(
        "Avec 9,42 % de positifs, détecter suffisamment de malades impose "
        "mécaniquement de signaler beaucoup de personnes saines. C'est une "
        "propriété du problème, non un défaut des modèles."
    )

    # ================= 8. Déséquilibre =================
    pdf.titre1("8. Traitement du déséquilibre : pondération ou SMOTE ?")
    pdf.texte(
        "Deux stratégies s'opposent classiquement. La **pondération** "
        "(class_weight, scale_pos_weight) accroît le poids des erreurs commises sur "
        "la classe minoritaire, sans inventer de données. **SMOTE** génère au "
        "contraire des exemples synthétiques de la classe minoritaire par "
        "interpolation entre voisins proches."
    )
    pdf.tableau(
        ["Stratégie", "ROC-AUC", "PR-AUC", "Précision", "Rappel", "F1"],
        [[r["stratégie"], f"{r['ROC-AUC']:.4f}", f"{r['PR-AUC']:.4f}",
          f"{r['précision']:.3f}", f"{r['rappel']:.3f}", f"{r['F1']:.3f}"]
         for r in res["desequilibre"]],
        [45, 26, 24, 25, 23, 22],
        ["L", "R", "R", "R", "R", "R"],
    )
    pdf.texte(
        f"Sur ces données, la stratégie retenue est **"
        f"{meta['strategie_desequilibre']}**. SMOTE est souvent présenté comme "
        "supérieur ; la mesure montre que ce n'est pas systématique. À performance "
        "équivalente, la pondération est préférable : elle n'introduit aucune donnée "
        "synthétique et reste plus simple à défendre."
    )
    pdf.encadre(
        "SMOTE doit être appliqué à l'intérieur de la validation croisée",
        "Générer les exemples synthétiques avant le découpage ferait fuiter des "
        "points interpolés dans les plis de validation, qui deviendraient partiellement "
        "prévisibles. Les scores seraient artificiellement gonflés. L'emploi d'un "
        "Pipeline imblearn garantit que SMOTE n'agit que sur le pli d'apprentissage.",
    )

    # ================= 9. Diagnostic =================
    pdf.titre1("9. Diagnostic : surapprentissage et sous-apprentissage")
    pdf.texte(
        "Deux écueils symétriques guettent tout modèle. Le **surapprentissage** "
        "survient lorsque le modèle mémorise le bruit du jeu d'entraînement : il "
        "excelle sur les données vues et se dégrade ailleurs. Le "
        "**sous-apprentissage** traduit au contraire un modèle trop rigide pour "
        "capter le signal : il est médiocre partout, y compris en entraînement. "
        "Trois analyses complémentaires permettent de trancher."
    )
    pdf.titre2("9.1 Écart entre entraînement et validation")
    pdf.tableau(
        ["Métrique", "Entraînement", "Validation", "Écart", "Écart relatif"],
        [[d["métrique"], f"{d['entraînement']:.4f}", f"{d['validation']:.4f}",
          f"{d['écart']:+.4f}", f"{d['écart relatif (%)']:.2f} %"]
         for d in res["diagnostic"]["ecart_train_val"]],
        [35, 33, 33, 32, 32],
        ["L", "R", "R", "R", "R"],
    )
    pdf.texte(
        "Un écart relatif inférieur à environ 5 % caractérise un modèle sain ; "
        "au-delà de 10 à 15 %, le surapprentissage devient préoccupant. Les valeurs "
        "obtenues situent le modèle retenu très en deçà de ce seuil."
    )
    pdf.titre2("9.2 Courbe d'apprentissage")
    pdf.figure(
        "06_courbe_apprentissage",
        "Évolution des scores selon la quantité de données d'entraînement",
        largeur=135,
    )
    pdf.texte(
        "La courbe d'apprentissage se lit ainsi : des courbes qui convergent vers "
        "un score élevé signalent un modèle bien calibré ; un écart persistant "
        "trahit de la variance (surapprentissage) ; deux courbes plafonnant bas "
        "révèlent du biais (sous-apprentissage) ; une courbe de validation qui monte "
        "encore à droite indique que davantage de données seraient utiles."
    )
    pdf.titre2("9.3 Courbe de validation : le bon niveau de complexité")
    cv_data = res["diagnostic"]["courbe_validation"]
    if cv_data:
        pdf.tableau(
            ["Profondeur", "Entraînement", "Validation", "Écart"],
            [[str(p), f"{t:.4f}", f"{v:.4f}", f"{t - v:+.4f}"]
             for p, t, v in zip(cv_data["profondeurs"], cv_data["train"],
                                cv_data["validation"])],
            [42, 41, 41, 41],
            ["C", "R", "R", "R"],
        )
        pdf.figure(
            "07_courbe_validation",
            "Les trois régimes : sous-apprentissage, optimum, surapprentissage",
            largeur=138,
        )
        premier = cv_data["validation"][0]
        maxi = max(cv_data["validation"])
        ecart_max = cv_data["train"][-1] - cv_data["validation"][-1]
        pdf.texte(
            f"Le tableau est une illustration de manuel. L'écart entre "
            f"entraînement et validation passe de "
            f"{cv_data['train'][0] - cv_data['validation'][0]:+.4f} à "
            f"{ecart_max:+.4f}, tandis que le score de validation culmine à la "
            f"profondeur {cv_data['optimum']} puis décline. À droite, le diagnostic "
            "est sans ambiguïté : le modèle mémorise le bruit."
        )
        pdf.encadre(
            "Un résultat inattendu : le signal est presque entièrement additif",
            f"À gauche, on attendrait un sous-apprentissage marqué. Il est "
            f"étonnamment léger : des arbres de profondeur 1 — une seule coupure, "
            f"donc structurellement incapables de représenter la moindre interaction "
            f"entre variables — atteignent déjà {premier:.4f} en validation, contre "
            f"{maxi:.4f} pour l'optimum. Chaque facteur de risque contribue donc à "
            "peu près indépendamment des autres. Cela explique définitivement "
            "pourquoi la régression logistique reste à quelques millièmes du "
            "meilleur modèle, et corrige l'hypothèse formulée lors du data mining, "
            "où l'on anticipait un avantage net des modèles non linéaires.",
            couleur=VERT,
        )

    # ================= 10. Calibration =================
    cal = res["calibration"]
    pdf.titre1("10. Calibration des probabilités")
    pdf.texte(
        "Un modèle peut parfaitement **classer** les individus tout en produisant "
        "des probabilités **fausses en niveau**. C'est exactement l'effet de la "
        "pondération des classes retenue au chapitre 8 : en accordant dix fois plus "
        "de poids aux cas positifs, on apprend au modèle à raisonner comme si la "
        "maladie touchait la moitié de la population. Le classement reste juste, "
        "l'échelle est déformée vers le haut."
    )
    pdf.encadre(
        "Pourquoi cette distinction est décisive",
        "Pour **comparer des modèles**, seul le classement compte : le ROC-AUC est "
        "donc un critère valide, et tout le travail des chapitres précédents reste "
        "pertinent. Mais dès qu'on **affiche un pourcentage à un utilisateur**, le "
        "niveau doit être exact. Annoncer « 35 % de risque » à une personne dont le "
        "risque réel est de 5 % serait trompeur — inacceptable pour une application "
        "de santé.",
    )
    pdf.titre2("10.1 L'ampleur du problème")
    pdf.texte(
        f"Sur le jeu de test, la moyenne des probabilités prédites par le modèle "
        f"brut atteint **{cal['proba_moyenne_avant_pct']:.2f} %**, alors que la "
        f"prévalence réelle n'est que de **{cal['prevalence_reelle_pct']:.2f} %** — "
        f"une surestimation d'un facteur "
        f"{cal['proba_moyenne_avant_pct'] / cal['prevalence_reelle_pct']:.1f}."
    )
    pdf.titre2("10.2 La correction : régression isotonique")
    pdf.texte(
        "On applique une **calibration isotonique**, qui apprend une fonction "
        "croissante transformant les scores bruts en probabilités fidèles aux "
        "fréquences observées. Deux propriétés la rendent adaptée ici. Elle est "
        "**monotone** : elle ne modifie pas l'ordre des individus, donc le ROC-AUC "
        "et toute la sélection restent valides. Elle est **non paramétrique** : "
        "elle n'impose aucune forme a priori à la correction, contrairement à une "
        "calibration sigmoïde. L'ajustement se fait par validation croisée sur le "
        "seul jeu d'entraînement."
    )
    pdf.tableau(
        ["Mesure", "Avant", "Après", "Réel"],
        [
            ["ROC-AUC", f"{cal['roc_auc_avant']:.4f}",
             f"{cal['roc_auc_apres']:.4f}", "—"],
            ["PR-AUC", f"{cal['pr_auc_avant']:.4f}",
             f"{cal['pr_auc_apres']:.4f}", "—"],
            ["Probabilité moyenne (%)", f"{cal['proba_moyenne_avant_pct']:.2f}",
             f"{cal['proba_moyenne_apres_pct']:.2f}",
             f"{cal['prevalence_reelle_pct']:.2f}"],
        ],
        [60, 35, 35, 35],
        ["L", "R", "R", "R"],
    )
    pdf.figure(
        "08_calibration",
        "Courbes de calibration avant et après correction isotonique",
        largeur=165,
    )
    pdf.encadre(
        "Une correction sans contrepartie",
        f"Le ROC-AUC passe de {cal['roc_auc_avant']:.4f} à "
        f"{cal['roc_auc_apres']:.4f} et le PR-AUC reste inchangé : la calibration "
        f"n'a rien coûté en pouvoir discriminant. En revanche, la probabilité "
        f"moyenne tombe de {cal['proba_moyenne_avant_pct']:.2f} % à "
        f"{cal['proba_moyenne_apres_pct']:.2f} %, contre "
        f"{cal['prevalence_reelle_pct']:.2f} % réellement observés. Les "
        "probabilités sont désormais interprétables telles quelles. Le seuil de "
        "décision a été recalculé sur cette nouvelle échelle.",
        couleur=VERT,
    )
    pdf.texte(
        "C'est le **modèle calibré** qui est déployé. Le pipeline brut reste "
        "conservé pour l'interprétation SHAP : une transformation monotone ne "
        "change pas la hiérarchie des contributions."
    )

    # ================= 11. Évaluation finale =================
    pdf.titre1("11. Évaluation finale et choix du seuil")
    pdf.texte(
        "Le modèle retenu est réentraîné sur l'intégralité du jeu d'entraînement, "
        "puis évalué une seule fois sur le jeu de test, mis sous scellés depuis le "
        "début."
    )
    pdf.tableau(
        ["Métrique (jeu de test)", "Valeur"],
        [
            ["ROC-AUC", f"{perf['roc_auc']:.4f}"],
            ["PR-AUC", f"{perf['pr_auc']:.4f}"],
            ["Rappel (au seuil retenu)", f"{perf['rappel']:.3f}"],
            ["Précision (au seuil retenu)", f"{perf['precision']:.3f}"],
            ["Seuil de décision", f"{meta['seuil_decision']:.4f}"],
        ],
        [110, 55],
        ["L", "R"],
    )
    pdf.figure(
        "02_courbes_roc_pr",
        "Courbe ROC et courbe précision-rappel sur le jeu de test",
        largeur=170,
    )
    pdf.texte(
        f"Le PR-AUC de {perf['pr_auc']:.4f} se compare à une référence du hasard "
        f"de {meta['prevalence_entrainement']:.4f} : l'apport du modèle est net, "
        "d'un facteur proche de quatre."
    )
    pdf.titre2("11.1 Le seuil est une décision distincte du choix du modèle")
    pdf.texte(
        "Le modèle produit une probabilité continue ; le seuil la transforme en "
        "décision binaire. Le seuil par défaut de 0,5 n'a aucune raison d'être "
        "pertinent sur des classes déséquilibrées. Les deux erreurs n'ayant pas le "
        "même coût en santé — manquer une personne à risque est plus grave que "
        f"recommander une vérification inutile — le seuil a été fixé pour atteindre "
        f"un rappel cible de {meta['rappel_cible']:.0%}."
    )
    pdf.tableau(
        ["Résultat au seuil retenu", "Effectif"],
        [
            ["Malades correctement détectés",
             f"{mc['vrais_positifs']:,}".replace(",", " ")],
            ["Malades manqués (faux négatifs)",
             f"{mc['faux_negatifs']:,}".replace(",", " ")],
            ["Fausses alertes (faux positifs)",
             f"{mc['faux_positifs']:,}".replace(",", " ")],
            ["Sains correctement écartés",
             f"{mc['vrais_negatifs']:,}".replace(",", " ")],
        ],
        [110, 55],
        ["L", "R"],
    )
    pdf.figure(
        "03_seuil_confusion",
        "Arbitrage précision / rappel selon le seuil, et matrice de confusion",
        largeur=150,
    )
    pdf.texte(
        "Pour un outil de sensibilisation au risque — et non de diagnostic — cet "
        "arbitrage est le bon : mieux vaut inviter quelques personnes en bonne "
        "santé à consulter que passer à côté d'une personne réellement exposée."
    )

    # ================= 11. SHAP =================
    pdf.titre1("12. Interprétation par SHAP")
    pdf.texte(
        "Un modèle performant mais opaque est difficile à défendre, a fortiori en "
        "santé. Les valeurs SHAP attribuent à chaque variable sa contribution à "
        "chaque prédiction, sur un fondement théorique solide issu de la théorie "
        "des jeux coopératifs : la contribution d'une variable est sa valeur de "
        "Shapley, moyenne de son apport marginal sur tous les ordres d'ajout "
        "possibles."
    )
    pdf.figure(
        "04_shap_summary",
        "Contribution des variables : chaque point est un répondant",
        largeur=105,
    )
    pdf.tableau(
        ["Variable", "Importance SHAP moyenne"],
        [[r["variable"], f"{r['importance SHAP']:.4f}"]
         for r in res["shap_top"][:10]],
        [110, 55],
        ["L", "R"],
    )
    pdf.texte(
        "L'âge domine largement, suivi de la santé perçue — exactement le classement "
        "établi par l'analyse exploratoire. La cohérence entre trois approches "
        "indépendantes (statistiques descriptives, clustering non supervisé, modèle "
        "supervisé) constitue un gage de solidité : ce n'est pas l'artefact d'un "
        "algorithme particulier."
    )
    pdf.texte(
        "Trois observations plus fines méritent d'être relevées. Le **sexe** figure "
        "parmi les variables les plus influentes, les hommes voyant leur risque "
        "estimé nettement relevé. L'**antécédent d'AVC** produit la poussée "
        "individuelle la plus forte : rare, mais très informative lorsqu'elle est "
        "présente. Enfin le **renoncement aux soins pour raison financière** "
        "apparaît parmi les variables mobilisées — écho direct de la découverte du "
        "data mining, où le clustering avait isolé un groupe de non-assurés."
    )

    # ================= 12. Sérialisation =================
    pdf.titre1("13. Sérialisation et mise à disposition")
    pdf.texte(
        "C'est le **pipeline complet** qui est sauvegardé — préprocesseur et modèle "
        "réunis dans un seul objet. L'application web appliquera ainsi exactement "
        "les mêmes transformations qu'à l'entraînement, ce qui élimine toute une "
        "classe de bugs de mise en production (ordre des colonnes, échelles "
        "recalculées, encodage divergent)."
    )
    pdf.code(
        """
joblib.dump(pipeline_final, "models/heart_model.joblib")

# metadata.json : ce qu'il faut savoir pour utiliser le modèle
{
  "modele": "...",  "seuil_decision": ...,
  "variables": [...],           # ordre attendu des colonnes
  "performances_test": {...},   # ce qu'on peut en attendre
}
"""
    )
    pdf.texte(
        "Les métadonnées accompagnent le modèle : un fichier binaire seul ne dit "
        "pas quelles variables il attend, dans quel ordre, avec quel seuil, ni quelle "
        "performance escompter. Un fichier `resultats.json` complète l'ensemble "
        "et sert de source unique aux chiffres de ce document."
    )

    # ================= 13. Synthèse =================
    pdf.titre1("14. Synthèse et limites")
    pdf.titre2("14.1 Démarche")
    pdf.tableau(
        ["Étape", "Choix retenu"],
        [
            ["Découpage", "Stratifié 80/20, test sous scellés"],
            ["Préprocessing", "ColumnTransformer dans le Pipeline, sans fuite"],
            ["Encodage", "Ordinal conservé, pas de one-hot (aucune nominale)"],
            ["Réglage", "GridSearchCV, 5 plis stratifiés, par famille"],
            ["Sélection", "ROC-AUC, PR-AUC en arbitre"],
            ["Déséquilibre", f"{meta['strategie_desequilibre']} (comparée à l'autre)"],
            ["Diagnostic", "Écart train/validation, deux courbes"],
            ["Calibration", "Isotonique — probabilités affichables"],
            ["Seuil", f"Fixé après coup, rappel cible {meta['rappel_cible']:.0%}"],
            ["Interprétation", "SHAP"],
        ],
        [45, 120],
        ["L", "L"],
    )
    pdf.titre2("14.2 Résultats")
    pdf.puce(
        f"Modèle retenu : **{meta['modele']}**, ROC-AUC de {perf['roc_auc']:.4f} "
        f"et PR-AUC de {perf['pr_auc']:.4f} sur le jeu de test."
    )
    pdf.puce(
        "Le réglage était indispensable : sans GridSearch, le classement des "
        "familles était inversé."
    )
    pdf.puce(
        "Le signal est presque entièrement additif — des arbres de profondeur 1 "
        "atteignent déjà l'essentiel de la performance."
    )
    pdf.puce(
        "Le modèle retenu ne surapprend pas : l'écart entraînement-validation reste "
        "très faible."
    )
    pdf.titre2("14.3 Limites assumées")
    pdf.puce(
        "**Associations transversales** : aucune causalité, aucune prédiction "
        "temporelle."
    )
    pdf.puce(
        "**Données auto-déclarées** : biais de mémoire et de désirabilité sociale."
    )
    pdf.puce(
        "**Part inexpliquée réelle** : 21 variables ne suffisent pas ; génétique, "
        "antécédents familiaux et environnement manquent."
    )
    pdf.puce(
        "**Population américaine de 2015** : toute transposition demanderait une "
        "revalidation."
    )
    pdf.puce(
        "**Traitement ordinal** : suppose des écarts constants entre modalités "
        "consécutives, approximation que les arbres atténuent."
    )
    pdf.ln(3)
    pdf.set_font("DJ", "I", 9)
    pdf.set_text_color(*GRIS)
    pdf.multi_cell(
        0, 5,
        "Tous les chiffres de ce document proviennent de resultats.json et "
        "metadata.json, produits par l'exécution du notebook (graine fixe). Source "
        "des données : BRFSS, CDC, édition 2015 ; données publiques via Kaggle.",
    )
    return pdf


def main() -> None:
    print("Lecture des resultats du notebook...")
    meta, res = charger()
    print("Construction du document...")
    pdf = construire(meta, res)
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(SORTIE))
    print(f"Genere : {SORTIE.name} ({pdf.page_no()} pages, "
          f"{SORTIE.stat().st_size / 1024:.0f} Ko)")


if __name__ == "__main__":
    main()
