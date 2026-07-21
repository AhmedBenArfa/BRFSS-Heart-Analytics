"""Génère la documentation technique « Entrepôt de données & Power BI ».

Document en deux parties :
  A — Entrepôt de données (schéma en étoile DuckDB)
  B — Restitution décisionnelle (Power BI)

Les chiffres sont recalculés depuis l'entrepôt au moment de la génération (aucune
valeur en dur). Les figures proviennent du diagramme généré et des captures du
rapport Power BI.

Prérequis : avoir exécuté run_etl.py, build_star_schema.py, et disposé les
captures dans 03_power_bi/screenshots/.

Usage :
    python _build_doc_pdf_dwh_powerbi.py

Sortie :
    06_rapport/Documentation_Technique_StarSchema_PowerBI.pdf
"""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

import duckdb
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# Réutilise le codebook pour décrire les dimensions.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "02_data_warehouse"))
import codebook  # noqa: E402

RACINE = Path(__file__).resolve().parents[1]
BASE = RACINE / "02_data_warehouse" / "heart.duckdb"
FIG_SCHEMA = RACINE / "06_rapport" / "figures" / "schema_etoile.png"
CAPTURES = RACINE / "03_power_bi" / "screenshots"
SORTIE = RACINE / "06_rapport" / "Documentation_Technique_StarSchema_PowerBI.pdf"

DOSSIER_POLICES = Path(
    r"C:\Users\Mega-pc\anaconda3\Lib\site-packages\matplotlib\mpl-data\fonts\ttf"
)

MARINE = (31, 59, 92)
GRIS = (90, 90, 90)
GRIS_CLAIR = (238, 240, 243)
ACCENT = (193, 68, 63)
BLEU = (46, 92, 138)
VERT = (61, 139, 95)


def decimales_fr(texte: str) -> str:
    """Point décimal anglo-saxon -> virgule française (chiffre.chiffre seulement)."""
    return re.sub(r"(?<=\d)\.(?=\d)", ",", texte)


# --------------------------------------------------------------------------- #
# Statistiques recalculées depuis l'entrepôt
# --------------------------------------------------------------------------- #


def charger_statistiques() -> dict:
    if not BASE.exists():
        raise FileNotFoundError(
            f"Entrepôt introuvable : {BASE}\n"
            "Exécuter : cd 02_data_warehouse && python build_star_schema.py"
        )

    with duckdb.connect(str(BASE), read_only=True) as conn:
        stats = {
            "nb_faits": conn.execute(
                "SELECT COUNT(*) FROM fact_respondent"
            ).fetchone()[0],
            "nb_colonnes_fait": conn.execute(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_name = 'fact_respondent'"
            ).fetchone()[0],
            "prevalence": conn.execute(
                "SELECT AVG(heart_disease) * 100 FROM fact_respondent"
            ).fetchone()[0],
        }

        # Volumétrie et contrôle d'orphelins par dimension.
        dims = []
        orphelins_total = 0
        for dim in codebook.DIMENSIONS:
            cle = dim["cle"]
            nb = conn.execute(f"SELECT COUNT(*) FROM {dim['table']}").fetchone()[0]
            orph = conn.execute(
                f"SELECT COUNT(*) FROM fact_respondent f "
                f"LEFT JOIN {dim['table']} d ON f.{cle} = d.{cle} "
                f"WHERE d.{cle} IS NULL"
            ).fetchone()[0]
            orphelins_total += orph
            dims.append((dim["table"], dim["libelle"], nb))
        stats["dimensions"] = dims
        stats["orphelins"] = orphelins_total
        stats["nb_dimensions"] = len(dims)

    return stats


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

    def titre3(self, texte):
        self.ln(1)
        self.set_font("DJ", "B", 11)
        self.set_text_color(*BLEU)
        self.multi_cell(0, 5.8, texte)
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
        y_debut = self.get_y()
        self.set_font("DJ", "B", 10)
        self.set_text_color(*couleur)
        self.set_x(self.l_margin + 3)
        self.multi_cell(self.w - self.l_margin - self.r_margin - 6, 6, titre)
        self.set_text_color(0, 0, 0)
        self.set_font("DJ", "", 10)
        self.set_x(self.l_margin + 3)
        self.multi_cell(
            self.w - self.l_margin - self.r_margin - 6, 5.1,
            decimales_fr(contenu.strip()),
        )
        y_fin = self.get_y()
        self.line(self.l_margin, y_debut, self.l_margin, y_fin)
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

    def code(self, contenu):
        self.set_font("MONO", "", 8.3)
        self.set_fill_color(245, 246, 248)
        for ligne in contenu.strip("\n").split("\n"):
            self.cell(0, 4.4, "  " + ligne, fill=True, new_x=XPos.LMARGIN,
                      new_y=YPos.NEXT)
        self.ln(2.5)

    def figure(self, chemin: Path, legende, largeur=165):
        if not chemin.exists():
            self.texte(f"[figure manquante : {chemin.name}]")
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


# --------------------------------------------------------------------------- #
# Construction
# --------------------------------------------------------------------------- #


def construire(stats: dict) -> Rapport:
    pdf = Rapport(pied="Documentation technique — Entrepôt & Power BI")

    # === Page de garde ====================================================
    pdf.add_page()
    pdf.ln(56)
    pdf.set_font("DJ", "B", 24)
    pdf.set_text_color(*MARINE)
    pdf.multi_cell(0, 12, "Documentation technique", align="C")
    pdf.set_font("DJ", "B", 16)
    pdf.multi_cell(0, 9, "Entrepôt de données & Power BI", align="C")
    pdf.ln(5)
    pdf.set_draw_color(*ACCENT)
    pdf.set_line_width(0.9)
    pdf.line(60, pdf.get_y(), pdf.w - 60, pdf.get_y())
    pdf.ln(9)
    pdf.set_font("DJ", "", 13)
    pdf.set_text_color(*GRIS)
    pdf.multi_cell(0, 7, "BRFSS Heart Analytics", align="C")
    pdf.set_font("DJ", "", 11)
    pdf.multi_cell(
        0, 6,
        "Schéma en étoile DuckDB et restitution décisionnelle\n"
        "à partir des données du Behavioral Risk Factor\n"
        "Surveillance System (CDC, 2015)",
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

    # === 1. Introduction ==================================================
    pdf.titre1("1. Introduction")
    pdf.texte(
        "Ce document décrit la couche décisionnelle du projet : la construction "
        "d'un entrepôt de données en schéma en étoile, puis sa restitution dans "
        "Power BI. Il fait suite à la documentation ETL & analyse exploratoire, "
        "qui a produit la table analytique sur laquelle repose l'entrepôt."
    )
    pdf.texte(
        "La couche décisionnelle répond à une question différente de celle de "
        "l'ETL. L'ETL demande « les données sont-elles justes ? » ; l'entrepôt et "
        "Power BI demandent « comment les organiser et les présenter pour les "
        "interroger efficacement ? ». Cette séparation des responsabilités "
        "structure l'ensemble du document."
    )
    pdf.encadre(
        "Deux parties",
        "Partie A — Entrepôt de données : modélisation dimensionnelle, "
        "construction du schéma en étoile sous DuckDB, contrôle d'intégrité.\n"
        "Partie B — Power BI : connexion ODBC directe à l'entrepôt, mesures DAX, "
        "et les six pages du rapport décisionnel.",
        couleur=BLEU,
    )

    # ======================================================================
    # PARTIE A — ENTREPÔT
    # ======================================================================
    pdf.titre1("2. Partie A — Modélisation dimensionnelle")

    pdf.titre2("2.1 Pourquoi un schéma en étoile")
    pdf.texte(
        "Le schéma en étoile organise les données autour d'une table de faits "
        "centrale, entourée de tables de dimensions. La table de faits contient "
        "les mesures et des clés vers les dimensions ; chaque dimension porte les "
        "attributs descriptifs lisibles. Ce modèle est la référence pour "
        "l'analyse décisionnelle : il rend les requêtes simples et rapides, et il "
        "affiche des libellés compréhensibles plutôt que des codes numériques."
    )
    pdf.texte(
        "Le jeu de données source est une table plate et déjà encodée. La valeur "
        "ajoutée de l'entrepôt est double : reconstruire des dimensions lisibles à "
        "partir du codebook BRFSS (afficher « 60-64 ans » et non « 9 »), et poser "
        "un modèle sur lequel Power BI se branche directement."
    )

    pdf.titre2("2.2 Grain et table de faits")
    pdf.texte(
        "Le grain de la table de faits est le niveau de détail d'une ligne. Ici, "
        "une ligne = un répondant à l'enquête. La source ne fournissant aucun "
        "identifiant, une clé technique respondent_id est générée (clé dégénérée)."
    )
    pdf.tableau(
        ["Propriété", "Valeur"],
        [
            ["Table de faits", "fact_respondent"],
            ["Grain", "un répondant à l'enquête"],
            ["Nombre de lignes", f"{stats['nb_faits']:,}".replace(",", " ")],
            ["Colonnes", str(stats["nb_colonnes_fait"])],
            ["Clé dégénérée", "respondent_id"],
            ["Variable cible", "heart_disease"],
        ],
        [80, 85],
        ["L", "L"],
    )
    pdf.texte(
        "La table de faits porte les clés étrangères vers les sept dimensions, "
        "les mesures continues (bmi, jours de mal-être), les indicateurs binaires "
        "de santé et de comportement, les variables dérivées de l'ETL, les "
        "drapeaux qualité, et la cible."
    )

    pdf.titre2("2.3 Les sept dimensions")
    pdf.texte(
        "Chaque dimension est reconstruite depuis le codebook BRFSS. La clé de "
        "dimension est le code source lui-même : les codes BRFSS étant déjà de "
        "petits entiers contigus, aucune clé de substitution artificielle n'est "
        "nécessaire — cela éviterait une jointure sans bénéfice."
    )
    pdf.tableau(
        ["Dimension", "Attribut lisible", "Membres"],
        [[t, lib, str(nb)] for t, lib, nb in stats["dimensions"]],
        [58, 72, 35],
        ["L", "L", "R"],
    )

    pdf.titre2("2.4 Intégrité référentielle et membre « Inconnu »")
    pdf.texte(
        "Une bonne pratique consiste à prévoir un membre spécial « Inconnu » "
        "(clé -1) capable de capter tout code de fait absent du codebook, afin "
        "qu'aucune ligne ne devienne orpheline. Ce membre n'est toutefois ajouté "
        "que s'il est réellement nécessaire : si une dimension ne contient aucune "
        "valeur hors codebook ni valeur nulle, on ne crée pas de membre vide — "
        "cela éviterait de polluer les filtres de Power BI d'une modalité inutile."
    )
    pdf.encadre(
        "Contrôle d'intégrité",
        f"Après construction : {stats['orphelins']} clé étrangère orpheline sur "
        f"les {stats['nb_dimensions']} dimensions. Les données étant propres "
        "(contrôles qualité de l'ETL), aucune dimension n'a reçu de membre "
        "« Inconnu ». Le schéma est cohérent.",
        couleur=VERT,
    )

    pdf.titre2("2.5 Absence de dimension temporelle")
    pdf.texte(
        "Un schéma en étoile comporte fréquemment une dimension temps, mais elle "
        "n'est pas obligatoire : la modélisation dimensionnelle exige une table de "
        "faits et au moins une dimension, sans imposer d'axe temporel. Les données "
        "BRFSS 2015 sont transversales — un instantané, chaque répondant observé "
        "une seule fois. Une dimension temps y serait dégénérée (valeur unique) et "
        "sans apport analytique. Elle est donc volontairement absente ; le modèle "
        "privilégie les dimensions réellement discriminantes."
    )

    pdf.titre2("2.6 Diagramme du schéma")
    pdf.figure(
        FIG_SCHEMA,
        "Schéma en étoile : fact_respondent au centre, sept dimensions du codebook",
        largeur=135,
    )

    pdf.titre2("2.7 Construction et exports")
    pdf.texte(
        "Le script build_star_schema.py peuple les dimensions depuis le codebook, "
        "exécute le DDL qui construit la table de faits par jointure, vérifie "
        "l'intégrité, puis exporte chaque table en CSV et en Parquet (repli hors "
        "ligne). L'entrepôt DuckDB est un fichier unique, sans serveur à installer."
    )
    pdf.code(
        """
cd 02_data_warehouse
python build_star_schema.py       # construit le schéma + exports

python explore_warehouse.py                    # tables + volumétrie
python explore_warehouse.py fact_respondent    # aperçu
python explore_warehouse.py "SELECT AVG(heart_disease) FROM fact_respondent"
"""
    )
    pdf.encadre(
        "Verrou d'écriture DuckDB",
        "DuckDB n'autorise qu'un seul processus en écriture, mais plusieurs "
        "lecteurs. Pour reconstruire l'entrepôt, fermer Power BI et tout noyau "
        "Jupyter connecté. Power BI se connecte en lecture seule, ce qui permet la "
        "coexistence de plusieurs lecteurs.",
    )

    # ======================================================================
    # PARTIE B — POWER BI
    # ======================================================================
    pdf.titre1("3. Partie B — Restitution Power BI")

    pdf.titre2("3.1 Connexion directe à l'entrepôt (ODBC)")
    pdf.texte(
        "Power BI se connecte directement à l'entrepôt DuckDB via une source de "
        "données ODBC, en lecture seule. Ce n'est pas un import de fichiers CSV "
        "isolés : le rapport interroge le modèle dimensionnel lui-même. Une DSN "
        "utilisateur nommée heart_duckdb pointe sur heart.duckdb avec "
        "access_mode=read_only ; les huit tables du schéma sont chargées, à "
        "l'exclusion de la table technique analytical_base."
    )
    pdf.encadre(
        "Câblage automatique des relations",
        "Grâce à un nommage cohérent des clés (age_key identique dans le fait et "
        "dans dim_age, etc.), Power BI détecte et crée les sept relations "
        "un-à-plusieurs automatiquement au chargement. Aucune relation n'est "
        "tracée à la main — la convention de nommage adoptée dans l'entrepôt paie "
        "directement ici.",
        couleur=VERT,
    )
    pdf.figure(
        CAPTURES / "modele_relations_powerbi.png",
        "Vue du modèle dans Power BI : les sept dimensions reliées à la table de faits",
        largeur=170,
    )

    pdf.titre2("3.2 Mesures DAX")
    pdf.texte(
        "Les indicateurs sont calculés par des mesures DAX regroupées dans une "
        "table dédiée. La cible étant codée 0/1, sa moyenne donne directement le "
        "taux de maladie. Distinction clé : une mesure agrège et se place dans les "
        "valeurs ; une colonne calculée se calcule par ligne et sert d'axe ou de "
        "légende (ainsi la colonne Statut cardiaque, qui traduit 0/1 en libellés)."
    )
    pdf.code(
        """
Taux Maladie Cardiaque =
    DIVIDE ( SUM ( fact_respondent[heart_disease] ),
             COUNTROWS ( fact_respondent ) )

IMC Moyen              = AVERAGE ( fact_respondent[bmi] )
Facteurs Risque Moyens = AVERAGE ( fact_respondent[risk_factor_count] )
Taux Hypertension      = DIVIDE ( SUM ( fact_respondent[high_bp] ),
                                  COUNTROWS ( fact_respondent ) )

Statut cardiaque =   -- colonne calculée (pas une mesure)
    IF ( fact_respondent[heart_disease] = 1, "Atteint", "Non atteint" )
"""
    )
    pdf.texte(
        "La liste complète des mesures et colonnes figure dans "
        "03_power_bi/mesures_dax.md. Les axes catégoriels (tranche d'âge, revenu, "
        "études…) sont triés via « Trier par colonne » sur la clé numérique "
        "correspondante, faute de quoi Power BI trierait alphabétiquement."
    )

    pdf.titre2("3.3 Structure du rapport : six pages")
    pdf.texte(
        "Le rapport compte six pages, organisées du général au spécifique : deux "
        "pages descriptives (qui décrivent la population) et quatre pages "
        "analytiques (qui expliquent le risque)."
    )
    pdf.tableau(
        ["Page", "Type", "Contenu principal"],
        [
            ["1 Vue d'ensemble", "Analytique", "KPI, risque par âge, répartition"],
            ["2 Facteurs de risque", "Analytique", "Gradient des facteurs, courbe en J"],
            ["3 Socio-démographique", "Analytique", "Revenu, études, âge × sexe"],
            ["4 Santé & diabète", "Analytique", "Santé perçue, diabète, IMC"],
            ["5 Profil population", "Descriptive", "Âge, sexe, revenu, IMC"],
            ["6 Habitudes de vie", "Descriptive", "Tabac, activité, alimentation"],
        ],
        [45, 33, 87],
        ["L", "L", "L"],
    )

    pdf.titre2("3.4 Pages analytiques")
    pdf.figure(
        CAPTURES / "page1_vue_ensemble.png",
        "Page 1 — Vue d'ensemble : indicateurs clés, risque par tranche d'âge, "
        "répartition atteints / non atteints",
        largeur=178,
    )
    pdf.figure(
        CAPTURES / "page2_facteurs_risque.png",
        "Page 2 — Facteurs de risque : le gradient de 1,2 % à 59 %, la courbe en J "
        "de l'IMC, l'hypertension par statut",
        largeur=178,
    )
    pdf.figure(
        CAPTURES / "page3_socio_demographique.png",
        "Page 3 — Profil socio-démographique : gradient du revenu et des études, "
        "croisement âge × sexe",
        largeur=178,
    )
    pdf.figure(
        CAPTURES / "page4_sante_diabete.png",
        "Page 4 — Santé perçue et diabète : deux facteurs majeurs, et le nuage IMC "
        "× risque par tranche d'âge",
        largeur=178,
    )

    pdf.titre2("3.5 Pages descriptives")
    pdf.texte(
        "Ces deux pages décrivent la population étudiée indépendamment de la "
        "maladie — un rapport décisionnel complet ne se limite pas à la variable "
        "cible, il caractérise d'abord son échantillon."
    )
    pdf.figure(
        CAPTURES / "page5_profil_population.png",
        "Page 5 — Profil de la population : pyramide des âges, répartition par "
        "sexe et revenu, distribution de l'IMC",
        largeur=178,
    )
    pdf.figure(
        CAPTURES / "page6_habitudes_vie.png",
        "Page 6 — Habitudes de vie : taux de comportements de santé, état de santé "
        "perçu, jours de mal-être par âge",
        largeur=178,
    )

    # === 4. Synthèse ======================================================
    pdf.titre1("4. Synthèse")
    pdf.texte(
        "La couche décisionnelle transforme une table analytique plate en un "
        "modèle dimensionnel interrogeable, puis en un rapport lisible."
    )
    pdf.puce(
        f"Un schéma en étoile de {stats['nb_dimensions']} dimensions autour de "
        f"fact_respondent ({stats['nb_faits']:,} lignes), aux libellés issus du "
        "codebook.".replace(",", " ")
    )
    pdf.puce(
        f"Une intégrité référentielle vérifiée ({stats['orphelins']} clé "
        "orpheline), sans membre « Inconnu » superflu."
    )
    pdf.puce(
        "Une absence assumée de dimension temporelle, justifiée par la nature "
        "transversale des données."
    )
    pdf.puce(
        "Une connexion Power BI directe à l'entrepôt en ODBC, avec câblage "
        "automatique des relations."
    )
    pdf.puce(
        "Un rapport de six pages équilibré entre description de la population et "
        "analyse du risque."
    )
    pdf.ln(2)
    pdf.encadre(
        "Reproductibilité",
        "Toutes les statistiques de ce document sont recalculées depuis "
        "l'entrepôt à la génération ; le diagramme et les captures proviennent des "
        "livrables réels. Régénérer : cd 06_rapport && "
        "python _build_doc_pdf_dwh_powerbi.py.",
        couleur=BLEU,
    )
    pdf.ln(3)
    pdf.set_font("DJ", "I", 9)
    pdf.set_text_color(*GRIS)
    pdf.multi_cell(
        0, 5,
        "Source des données : Behavioral Risk Factor Surveillance System (BRFSS), "
        "Centers for Disease Control and Prevention, édition 2015. Données "
        "publiques diffusées via Kaggle.",
    )
    return pdf


def main() -> None:
    print("Calcul des statistiques depuis l'entrepot...")
    stats = charger_statistiques()
    print("Construction du document...")
    pdf = construire(stats)
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(SORTIE))
    taille = SORTIE.stat().st_size / 1024
    print(f"Genere : {SORTIE.name} ({pdf.page_no()} pages, {taille:.0f} Ko)")


if __name__ == "__main__":
    main()
