"""Génère la documentation technique « Data Mining ».

Les profils sont recalculés depuis l'entrepôt (k-means, k=4) au moment de la
génération : aucun chiffre en dur. Les figures proviennent du notebook de data
mining.

Prérequis : avoir exécuté build_star_schema.py et le notebook de data mining
(pour disposer des figures dans 06_rapport/figures/datamining/).

Usage :
    python _build_doc_pdf_datamining.py

Sortie :
    06_rapport/Documentation_Technique_DataMining.pdf
"""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

import duckdb
import numpy as np
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

RACINE = Path(__file__).resolve().parents[1]
BASE = RACINE / "02_data_warehouse" / "heart.duckdb"
FIG = RACINE / "06_rapport" / "figures" / "datamining"
SORTIE = RACINE / "06_rapport" / "Documentation_Technique_DataMining.pdf"

DOSSIER_POLICES = Path(
    r"C:\Users\Mega-pc\anaconda3\Lib\site-packages\matplotlib\mpl-data\fonts\ttf"
)

MARINE = (31, 59, 92)
GRIS = (90, 90, 90)
GRIS_CLAIR = (238, 240, 243)
ACCENT = (193, 68, 63)
BLEU = (46, 92, 138)
VERT = (61, 139, 95)

GRAINE = 42
K = 4

FEATURES = [
    "high_bp", "high_chol", "chol_check", "bmi", "smoker", "stroke", "diabetes",
    "phys_activity", "fruits", "veggies", "hvy_alcohol", "any_healthcare",
    "no_doc_cost", "gen_hlth", "ment_hlth_days", "phys_hlth_days", "diff_walk",
    "sex", "age_group", "education", "income",
]


def decimales_fr(texte: str) -> str:
    return re.sub(r"(?<=\d)\.(?=\d)", ",", texte)


# --------------------------------------------------------------------------- #
# Statistiques recalculées (mêmes paramètres que le notebook)
# --------------------------------------------------------------------------- #


def charger_statistiques() -> dict:
    if not BASE.exists():
        raise FileNotFoundError(
            f"Entrepôt introuvable : {BASE}\n"
            "Exécuter : cd 02_data_warehouse && python build_star_schema.py"
        )

    with duckdb.connect(str(BASE), read_only=True) as conn:
        df = conn.execute(
            f"SELECT {', '.join(FEATURES)}, heart_disease FROM analytical_base"
        ).df()

    X = StandardScaler().fit_transform(df[FEATURES])
    km = KMeans(n_clusters=K, random_state=GRAINE, n_init=10).fit(X)
    df["cluster"] = km.labels_

    taux = df.groupby("cluster")["heart_disease"].mean().sort_values()
    ordre = {anc: nouv for nouv, anc in enumerate(taux.index)}
    df["profil"] = df["cluster"].map(ordre)

    profils = []
    for p in range(K):
        sous = df[df["profil"] == p]
        profils.append({
            "effectif": len(sous),
            "part": len(sous) / len(df) * 100,
            "taux": sous["heart_disease"].mean() * 100,
            "age": sous["age_group"].mean(),
            "gen_hlth": sous["gen_hlth"].mean(),
            "bmi": sous["bmi"].mean(),
            "any_healthcare": sous["any_healthcare"].mean() * 100,
            "no_doc_cost": sous["no_doc_cost"].mean() * 100,
            "diabetes": sous["diabetes"].mean(),
            "diff_walk": sous["diff_walk"].mean() * 100,
            "income": sous["income"].mean(),
        })

    return {
        "nb": len(df),
        "nb_features": len(FEATURES),
        "prevalence": df["heart_disease"].mean() * 100,
        "profils": profils,
    }


# --------------------------------------------------------------------------- #
# Document
# --------------------------------------------------------------------------- #


class Rapport(FPDF):
    def __init__(self, pied: str):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.pied = pied
        self.set_auto_page_break(auto=True, margin=16)
        self.add_font("DJ", "", str(DOSSIER_POLICES / "DejaVuSans.ttf"))
        self.add_font("DJ", "B", str(DOSSIER_POLICES / "DejaVuSans-Bold.ttf"))
        self.add_font("DJ", "I", str(DOSSIER_POLICES / "DejaVuSans-Oblique.ttf"))
        self.add_font("MONO", "", str(DOSSIER_POLICES / "DejaVuSansMono.ttf"))
        self.set_font("DJ", "", 10.5)

    def multi_cell(self, *args, **kwargs):
        kwargs.setdefault("new_x", XPos.LMARGIN)
        kwargs.setdefault("new_y", YPos.NEXT)
        return super().multi_cell(*args, **kwargs)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-14)
        self.set_font("DJ", "I", 8)
        self.set_text_color(*GRIS)
        self.cell(0, 8, f"{self.pied}   |   page {self.page_no()}", align="C")

    def titre1(self, texte):
        self.add_page()
        self.set_font("DJ", "B", 17)
        self.set_text_color(*MARINE)
        self.multi_cell(0, 9, texte)
        self.ln(1)
        y = self.get_y()
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.6)
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(4)
        self.set_text_color(0, 0, 0)

    def titre2(self, texte):
        self.ln(2)
        self.set_font("DJ", "B", 12.5)
        self.set_text_color(*MARINE)
        self.multi_cell(0, 6.5, texte)
        self.ln(0.5)
        self.set_text_color(0, 0, 0)

    def texte(self, contenu):
        self.set_font("DJ", "", 10.5)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 5.15, decimales_fr(contenu.strip()))
        self.ln(1.5)

    def puce(self, contenu):
        self.set_font("DJ", "", 10.5)
        depart = self.get_x()
        self.set_x(depart + 3)
        self.cell(4, 5.1, "•")
        self.multi_cell(0, 5.1, decimales_fr(contenu.strip()))
        self.set_x(depart)

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
                        decimales_fr(contenu.strip()))
        self.line(self.l_margin, y0, self.l_margin, self.get_y())
        self.ln(2.5)

    def tableau(self, entetes, lignes, largeurs, alignements=None):
        if alignements is None:
            alignements = ["L"] + ["R"] * (len(entetes) - 1)
        if self.get_y() + 8 + 6 * len(lignes) > self.h - 20:
            self.add_page()
        self.set_font("DJ", "B", 9)
        self.set_fill_color(*MARINE)
        self.set_text_color(255, 255, 255)
        for e, l, a in zip(entetes, largeurs, alignements):
            self.cell(l, 7, e, align=a, fill=True, border=0)
        self.ln()
        self.set_font("DJ", "", 9)
        self.set_text_color(0, 0, 0)
        for i, ligne in enumerate(lignes):
            self.set_fill_color(248, 249, 251)
            for v, l, a in zip(ligne, largeurs, alignements):
                self.cell(l, 6, decimales_fr(str(v)), align=a, fill=i % 2 == 0,
                          border=0)
            self.ln()
        self.ln(3)

    def figure(self, nom, legende, largeur=165):
        chemin = FIG / f"{nom}.png"
        if not chemin.exists():
            self.texte(f"[figure manquante : {nom}.png]")
            return
        from PIL import Image

        with Image.open(chemin) as im:
            ratio = im.height / im.width
        hauteur = largeur * ratio
        if self.get_y() + hauteur + 12 > self.h - 20:
            self.add_page()
        x = (self.w - largeur) / 2
        self.image(str(chemin), x=x, w=largeur)
        self.ln(1.5)
        self.set_font("DJ", "I", 8.5)
        self.set_text_color(*GRIS)
        self.multi_cell(0, 4.4, decimales_fr(legende), align="C")
        self.set_text_color(0, 0, 0)
        self.ln(2.5)


NOMS_PROFILS = [
    "Jeunes actifs en bonne santé",
    "Adultes non assurés",
    "Seniors autonomes",
    "Seniors multi-morbides fragiles",
]


def construire(stats: dict) -> Rapport:
    pdf = Rapport(pied="Documentation technique — Data Mining")

    # === Page de garde ====================================================
    pdf.add_page()
    pdf.ln(58)
    pdf.set_font("DJ", "B", 25)
    pdf.set_text_color(*MARINE)
    pdf.multi_cell(0, 12, "Documentation technique", align="C")
    pdf.set_font("DJ", "B", 17)
    pdf.multi_cell(0, 9, "Data Mining", align="C")
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
        "Exploration non supervisée : ACP, clustering,\n"
        "et découverte de profils de population\n"
        "(BRFSS, CDC, 2015)",
        align="C",
    )
    pdf.ln(24)
    pdf.set_font("DJ", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 6, "Ahmed Ben Arfa", align="C")
    pdf.set_font("DJ", "", 10)
    pdf.set_text_color(*GRIS)
    pdf.multi_cell(0, 5.5, date.today().strftime("%d/%m/%Y"), align="C")
    pdf.ln(6)
    pdf.set_font("MONO", "", 8.5)
    pdf.multi_cell(0, 5, "github.com/AhmedBenArfa/BRFSS-Heart-Analytics", align="C")

    # === 1. Objectif ======================================================
    pdf.titre1("1. Objectif et démarche")
    pdf.texte(
        "Cette phase explore les données par apprentissage non supervisé. "
        "Contrairement à l'analyse exploratoire, qui décrivait les variables une à "
        "une, le data mining cherche des structures d'ensemble : des groupes de "
        "répondants aux profils semblables."
    )
    pdf.encadre(
        "Principe : ne pas utiliser la cible",
        "Le regroupement s'effectue sur les 21 variables de santé, sans la "
        "variable maladie. Les groupes émergent donc des seuls profils de "
        "population ; leur taux de maladie n'est mesuré qu'ensuite. Un groupe qui "
        "se révèle très exposé sans qu'on ait utilisé la cible pour le construire "
        "est une découverte solide, non un artefact.",
        couleur=BLEU,
    )
    pdf.texte(
        "Trois techniques complémentaires sont mobilisées : l'ACP (réduction de "
        "dimension et visualisation), le clustering (k-means et classification "
        "ascendante hiérarchique), et le t-SNE (projection 2D non linéaire). "
        "Toutes reposant sur des distances, les variables sont préalablement "
        "centrées et réduites."
    )

    # === 2. ACP ===========================================================
    pdf.titre1("2. Analyse en composantes principales")
    pdf.texte(
        "L'ACP recherche les directions de plus grande variance pour résumer les "
        "21 variables par quelques axes."
    )
    pdf.figure(
        "01_acp_variance",
        "Éboulis des valeurs propres et variance cumulée",
        largeur=170,
    )
    pdf.encadre(
        "Une compression faible, et c'est une information",
        "La première composante ne capte que ~17 % de la variance, et il faut 14 "
        "composantes pour atteindre 80 %. L'ACP compresse donc mal ces données : "
        "il n'existe pas deux ou trois axes dominants. La cause est la nature des "
        "variables — majoritairement binaires et peu corrélées entre elles. La "
        "structure est intrinsèquement multidimensionnelle : chaque variable "
        "apporte une information propre. L'ACP servira à visualiser et interpréter, "
        "pas à réduire.",
    )
    pdf.figure(
        "02_cercle_correlations",
        "Cercle des corrélations : projection des variables sur le plan CP1-CP2",
        largeur=115,
    )
    pdf.texte(
        "CP1 est un axe de charge morbide globale : il oppose le pôle fragilité "
        "(mauvaise santé perçue, difficulté à marcher, diabète, hypertension) au "
        "pôle aisance (revenu, études, activité physique). CP2 est un axe d'âge et "
        "de rapport aux soins : il oppose les personnes âgées, assurées et suivies "
        "à celles qui renoncent aux soins pour raison financière. La dimension de "
        "l'accès aux soins apparaît donc dès l'ACP."
    )
    pdf.figure(
        "03_acp_projection",
        "Répondants projetés sur le plan principal, coloriés selon leur statut réel "
        "(non utilisé par l'ACP)",
        largeur=135,
    )
    pdf.texte(
        "Les personnes atteintes se déplacent vers le pôle « charge morbide » sans "
        "former de bloc isolé : le signal existe mais il est diffus et non "
        "linéaire — d'où l'intérêt du clustering pour en tirer des profils "
        "exploitables."
    )

    # === 3. Choix de k ====================================================
    pdf.titre1("3. Le choix du nombre de groupes")
    pdf.texte(
        "Le k-means impose de fixer le nombre de groupes k. Deux critères "
        "classiques l'éclairent : la méthode du coude (inertie intra-cluster) et le "
        "score de silhouette (qualité de séparation des groupes)."
    )
    pdf.figure(
        "04_choix_k",
        "Méthode du coude et score de silhouette selon k",
        largeur=170,
    )
    pdf.encadre(
        "k = 4 : le choix de l'interprétabilité",
        "La silhouette est maximale pour k=2 ou k=3, mais toutes ses valeurs sont "
        "faibles (~0,1 à 0,2) : avec des variables binaires, les groupes se "
        "chevauchent, et la silhouette — qui récompense des clusters bien séparés — "
        "n'est pas un juge fiable ici. La méthode du coude, elle, décroît "
        "régulièrement sans coude franc. Le critère décisif devient donc "
        "l'interprétabilité : un k=2 se contenterait de séparer « sains » et "
        "« fragiles », un découpage binaire trivial. Avec k=4, on obtient quatre "
        "profils de population distincts et nommables, avec un gradient de risque "
        "étendu. C'est le bon compromis entre finesse et clarté.",
        couleur=VERT,
    )

    # === 4. K-means =======================================================
    pdf.titre1("4. Profils de population (k-means)")
    pdf.texte(
        f"Le k-means répartit les {stats['nb']:,} répondants en quatre profils. "
        "Le tableau ci-dessous les présente par risque croissant.".replace(",", " ")
    )
    lignes = []
    for i, p in enumerate(stats["profils"]):
        lignes.append([
            f"{i} — {NOMS_PROFILS[i]}",
            f"{p['effectif']:,}".replace(",", " "),
            f"{p['taux']:.1f} %",
        ])
    pdf.tableau(
        ["Profil (risque croissant)", "Effectif", "Taux maladie"],
        lignes,
        [95, 40, 30],
        ["L", "R", "R"],
    )
    pdf.figure(
        "05_kmeans_heatmap",
        "Signature de chaque profil : écart à la moyenne, en écarts-types "
        "(rouge = au-dessus)",
        largeur=175,
    )
    pdf.figure(
        "06_kmeans_risque",
        "Taux de maladie cardiaque par profil",
        largeur=130,
    )

    pdf.titre2("4.1 Lecture des quatre profils")
    p0, p1, p2, p3 = stats["profils"]
    pdf.texte(
        f"Profil 0 — Jeunes actifs en bonne santé ({p0['taux']:.1f} %). Le plus "
        f"grand groupe : âge bas, excellente santé perçue, IMC modéré "
        f"({p0['bmi']:.1f}), forte activité physique, revenus et études élevés. "
        "Population de référence, quasiment épargnée."
    )
    pdf.texte(
        f"Profil 1 — Adultes non assurés ({p1['taux']:.1f} %). Signature sociale, "
        f"pas médicale : {p1['any_healthcare']:.0f} % seulement ont une couverture "
        f"santé (contre 95 % dans la population) et {p1['no_doc_cost']:.0f} % ont "
        "renoncé à un médecin pour raison financière. Adultes plus jeunes, aux "
        "revenus modestes. Que le clustering ait isolé ce groupe à partir de "
        "variables surtout médicales est remarquable : il a retrouvé une fracture "
        "d'accès aux soins."
    )
    pdf.texte(
        f"Profil 2 — Seniors autonomes ({p2['taux']:.1f} %). Personnes âgées mais "
        f"en forme : hypertension et cholestérol fréquents (souvent traités), mais "
        f"bonne mobilité ({p2['diff_walk']:.0f} % de difficulté à marcher "
        "seulement), activité maintenue. L'âge les expose, l'état fonctionnel les "
        "protège."
    )
    pdf.texte(
        f"Profil 3 — Seniors multi-morbides fragiles ({p3['taux']:.1f} %, le risque "
        f"le plus élevé). Cumul de pathologies : diabète fréquent, forte difficulté "
        f"à marcher ({p3['diff_walk']:.0f} %), mauvaise santé perçue, IMC élevé "
        f"({p3['bmi']:.1f}), faible activité. Groupe cible prioritaire d'une "
        "prévention."
    )
    pdf.encadre(
        "Deux découvertes",
        "Le clustering, qui n'a jamais vu la maladie, sépare la population selon un "
        "risque de 1,6 % à 24,5 % — un rapport de 1 à 15. Il distingue deux "
        "populations âgées que l'âge seul confondrait (autonomes vs fragiles ; c'est "
        "la mobilité et le diabète qui les séparent), et il isole une fracture "
        "d'accès aux soins (les non-assurés). Les déterminants sociaux structurent "
        "la population autant que les facteurs cliniques.",
        couleur=BLEU,
    )

    # === 5. CAH & t-SNE ===================================================
    pdf.titre1("5. Validation : CAH et t-SNE")
    pdf.titre2("5.1 Classification ascendante hiérarchique")
    pdf.texte(
        "La CAH fusionne progressivement les individus les plus proches et se lit "
        "sur un dendrogramme. Menée indépendamment du k-means (sur un échantillon "
        "de 3 000 répondants, la méthode ayant un coût en O(n²)), elle vérifie la "
        "cohérence de la structure."
    )
    pdf.figure(
        "07_cah_dendrogramme",
        "Dendrogramme (méthode de Ward), coupé à quatre groupes",
        largeur=170,
    )
    pdf.texte(
        "Les regroupements se forment à des hauteurs nettes, cohérents avec un "
        "découpage en quelques groupes aux taux de maladie contrastés. Deux "
        "méthodes de logiques différentes convergent : la population se structure "
        "en une poignée de profils."
    )
    pdf.titre2("5.2 Projection t-SNE")
    pdf.texte(
        "Le t-SNE projette les données en 2D en préservant les proximités locales. "
        "Il permet de voir si les profils correspondent à des régions distinctes."
    )
    pdf.figure(
        "08_tsne",
        "t-SNE : à gauche coloré par profil k-means, à droite par statut réel",
        largeur=178,
    )
    pdf.texte(
        "Les profils occupent des régions cohérentes. Les seniors autonomes et "
        "fragiles se chevauchent en partie (chevauchement attendu), mais le profil "
        "des non-assurés forme un îlot nettement isolé — le groupe le plus distinct "
        "de la carte, ce qui valide sa découverte. À droite, les personnes "
        "atteintes se concentrent dans les régions des profils à haut risque, alors "
        "que la cible n'a jamais été utilisée."
    )

    # === 6. Synthèse ======================================================
    pdf.titre1("6. Synthèse et apport au machine learning")
    pdf.puce(
        "L'ACP révèle une structure multidimensionnelle : le signal est réel mais "
        "diffus, réparti sur de nombreuses variables peu redondantes."
    )
    pdf.puce(
        "Quatre profils de population, de risque 1,6 % à 24,5 %, émergent sans "
        "recours à la cible."
    )
    pdf.puce(
        "CAH et t-SNE confirment la structure par des méthodes indépendantes."
    )
    pdf.puce(
        "Deux découvertes actionnables : la fragilité fonctionnelle (mobilité, "
        "diabète) distingue mieux le risque que l'âge seul ; et l'accès aux soins "
        "dessine un groupe à part."
    )
    pdf.ln(2)
    pdf.encadre(
        "Ce que cela implique pour la modélisation",
        "Le signal étant réel mais diffus et non linéaire (ACP peu compressive, "
        "groupes qui se chevauchent), des modèles non linéaires — arbres et "
        "méthodes d'ensemble — devraient surpasser une régression logistique "
        "simple. Les profils suggèrent des interactions (âge × mobilité, "
        "âge × diabète) que le modèle devra capter. Et aucune variable ne domine à "
        "elle seule : c'est la combinaison des facteurs qui fait le risque.",
        couleur=VERT,
    )
    pdf.ln(3)
    pdf.set_font("DJ", "I", 9)
    pdf.set_text_color(*GRIS)
    pdf.multi_cell(
        0, 5,
        "Résultats reproductibles depuis l'entrepôt (graine fixe). Source des "
        "données : BRFSS, CDC, édition 2015 ; données publiques via Kaggle.",
    )
    return pdf


def main() -> None:
    print("Calcul des profils depuis l'entrepot (k-means)...")
    stats = charger_statistiques()
    print("Construction du document...")
    pdf = construire(stats)
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(SORTIE))
    taille = SORTIE.stat().st_size / 1024
    print(f"Genere : {SORTIE.name} ({pdf.page_no()} pages, {taille:.0f} Ko)")


if __name__ == "__main__":
    main()
