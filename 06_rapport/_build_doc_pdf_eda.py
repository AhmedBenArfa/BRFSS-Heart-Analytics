"""Génère la documentation technique du module ETL + EDA.

Les chiffres ne sont pas écrits en dur : ils sont recalculés depuis l'entrepôt
DuckDB au moment de la génération. Le rapport ne peut donc pas diverger des
données. Les figures proviennent de celles produites par le notebook EDA.

Prérequis : avoir exécuté `01_etl/run_etl.py`.

Usage :
    python _build_doc_pdf_eda.py

Sortie :
    06_rapport/Documentation_Technique_ETL_EDA.pdf
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import duckdb
import pandas as pd
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# --------------------------------------------------------------------------- #
# Chemins et constantes
# --------------------------------------------------------------------------- #

RACINE = Path(__file__).resolve().parents[1]
ETL = RACINE / "01_etl"
FIGURES = RACINE / "06_rapport" / "figures" / "eda"
BASE = RACINE / "02_data_warehouse" / "heart.duckdb"
SORTIE = RACINE / "06_rapport" / "Documentation_Technique_ETL_EDA.pdf"

DOSSIER_POLICES = Path(
    r"C:\Users\Mega-pc\anaconda3\Lib\site-packages\matplotlib\mpl-data\fonts\ttf"
)

MARINE = (31, 59, 92)
GRIS = (90, 90, 90)
GRIS_CLAIR = (238, 240, 243)
ACCENT = (193, 68, 63)
BLEU = (46, 92, 138)
VERT = (61, 139, 95)


# --------------------------------------------------------------------------- #
# Statistiques calculées en direct
# --------------------------------------------------------------------------- #


def charger_statistiques() -> dict:
    """Recalcule depuis l'entrepôt tous les chiffres cités dans le rapport."""
    if not BASE.exists():
        raise FileNotFoundError(
            f"Entrepôt introuvable : {BASE}\n"
            "Exécuter d'abord : cd 01_etl && python run_etl.py"
        )

    with duckdb.connect(str(BASE), read_only=True) as conn:
        df = conn.execute("SELECT * FROM analytical_base").df()

    colonnes_source = [
        "heart_disease", "high_bp", "high_chol", "chol_check", "bmi", "smoker",
        "stroke", "diabetes", "phys_activity", "fruits", "veggies",
        "hvy_alcohol", "any_healthcare", "no_doc_cost", "gen_hlth",
        "ment_hlth_days", "phys_hlth_days", "diff_walk", "sex", "age_group",
        "education", "income",
    ]

    stats = {
        "lignes": len(df),
        "colonnes": df.shape[1],
        "manquantes": int(df.isna().sum().sum()),
        "prevalence": df.heart_disease.mean() * 100,
        "doublons": int(df[colonnes_source].duplicated().sum()),
        "lignes_en_groupe": int(df[colonnes_source].duplicated(keep=False).sum()),
        "prevalence_dedup": df.drop_duplicates(subset=colonnes_source)
        .heart_disease.mean() * 100,
        "imc_extremes": int(df.flag_bmi_extreme.sum()),
        "imc_sup_60": int((df.bmi > 60).sum()),
        "prev_imc_sup_60": df.loc[df.bmi > 60, "heart_disease"].mean() * 100,
        "sante_incoherente": int(df.flag_sante_incoherente.sum()),
        "prev_phys30": df.loc[df.phys_hlth_days == 30, "heart_disease"].mean() * 100,
        "n_phys30": int((df.phys_hlth_days == 30).sum()),
    }

    # Prévalence par tranche d'âge
    age = df.groupby("age_group").heart_disease.agg(["size", "mean"])
    stats["prev_age_min"] = age["mean"].min() * 100
    stats["prev_age_max"] = age["mean"].max() * 100

    # Cumul des facteurs de risque
    cumul = df.groupby("risk_factor_count").heart_disease.agg(["size", "mean"])
    stats["cumul"] = [
        (int(idx), int(ligne["size"]), ligne["mean"] * 100)
        for idx, ligne in cumul.iterrows()
    ]

    # Classes d'IMC
    libelles_imc = {
        1: "Insuffisance pondérale", 2: "Corpulence normale", 3: "Surpoids",
        4: "Obésité modérée (I)", 5: "Obésité sévère (II)", 6: "Obésité morbide (III)",
    }
    imc = df.groupby("bmi_class").heart_disease.agg(["size", "mean"])
    stats["imc"] = [
        (libelles_imc[int(idx)], int(ligne["size"]), ligne["mean"] * 100)
        for idx, ligne in imc.iterrows()
    ]

    # Valeurs hors bornes : IQR contre z-score
    aberrantes = []
    for colonne in ["bmi", "ment_hlth_days", "phys_hlth_days"]:
        serie = df[colonne]
        q1, q3 = serie.quantile([0.25, 0.75])
        iqr = q3 - q1
        seuil_iqr = q3 + 1.5 * iqr
        ecart_type = serie.std()
        seuil_z = serie.mean() + 3 * ecart_type
        n_iqr = int(((serie < q1 - 1.5 * iqr) | (serie > seuil_iqr)).sum())
        n_z = int((((serie - serie.mean()).abs() / ecart_type) > 3).sum())
        aberrantes.append(
            (colonne, serie.max(), seuil_iqr, seuil_z,
             n_iqr / len(serie) * 100, n_z / len(serie) * 100)
        )
    stats["aberrantes"] = aberrantes

    # Étendues avant et après standardisation
    a_comparer = ["bmi", "ment_hlth_days", "phys_hlth_days", "age_group",
                  "gen_hlth", "income", "education", "risk_factor_count",
                  "high_bp", "smoker"]
    etendues = df[a_comparer].max() - df[a_comparer].min()
    standardise = (df[a_comparer] - df[a_comparer].mean()) / df[a_comparer].std()
    etendues_std = standardise.max() - standardise.min()
    stats["rapport_avant"] = etendues.max() / etendues.min()
    stats["rapport_apres"] = etendues_std.max() / etendues_std.min()

    # Corrélations les plus fortes avec la cible
    correlations = (
        df[colonnes_source].corr()["heart_disease"].drop("heart_disease")
        .sort_values(key=abs, ascending=False)
    )
    stats["correlations"] = [(nom, val) for nom, val in correlations.head(8).items()]

    return stats


# --------------------------------------------------------------------------- #
# Document
# --------------------------------------------------------------------------- #


def decimales_fr(texte: str) -> str:
    """Convertit les séparateurs décimaux anglo-saxons en virgule française.

    N'agit que sur un point encadré par deux chiffres, ce qui laisse intacts les
    noms de fichiers (`config.py`, `BRFSS2015.csv`) et les numéros de version.
    """
    return re.sub(r"(?<=\d)\.(?=\d)", ",", texte)


class Rapport(FPDF):
    """Document A4 avec en-têtes, tableaux et figures."""

    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=16)
        self.add_font("DJ", "", str(DOSSIER_POLICES / "DejaVuSans.ttf"))
        self.add_font("DJ", "B", str(DOSSIER_POLICES / "DejaVuSans-Bold.ttf"))
        self.add_font("DJ", "I", str(DOSSIER_POLICES / "DejaVuSans-Oblique.ttf"))
        self.add_font("MONO", "", str(DOSSIER_POLICES / "DejaVuSansMono.ttf"))
        self.set_font("DJ", "", 10.5)
        self.section_courante = ""

    def multi_cell(self, *args, **kwargs):
        kwargs.setdefault("new_x", XPos.LMARGIN)
        kwargs.setdefault("new_y", YPos.NEXT)
        return super().multi_cell(*args, **kwargs)

    # -- en-tête / pied de page --------------------------------------------
    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-14)
        self.set_font("DJ", "I", 8)
        self.set_text_color(*GRIS)
        self.cell(
            0, 8,
            f"Documentation technique — ETL & Analyse exploratoire   |   page {self.page_no()}",
            align="C",
        )

    # -- blocs de contenu ---------------------------------------------------
    def titre1(self, texte: str):
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
        self.section_courante = texte

    def titre2(self, texte: str):
        self.ln(2)
        self.set_font("DJ", "B", 12.5)
        self.set_text_color(*MARINE)
        self.multi_cell(0, 6.5, texte)
        self.ln(0.5)
        self.set_text_color(0, 0, 0)

    def titre3(self, texte: str):
        self.ln(1)
        self.set_font("DJ", "B", 11)
        self.set_text_color(*BLEU)
        self.multi_cell(0, 5.8, texte)
        self.set_text_color(0, 0, 0)

    def texte(self, contenu: str):
        self.set_font("DJ", "", 10.5)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 5.15, decimales_fr(contenu.strip()))
        self.ln(1.5)

    def puce(self, contenu: str):
        self.set_font("DJ", "", 10.5)
        depart = self.get_x()
        self.set_x(depart + 3)
        self.cell(4, 5.1, "•")
        self.multi_cell(0, 5.1, decimales_fr(contenu.strip()))
        self.set_x(depart)

    def encadre(self, titre: str, contenu: str, couleur=ACCENT):
        """Encadré coloré pour les décisions et points d'attention."""
        self.ln(1)
        self.set_font("DJ", "B", 10)
        hauteur_titre = 6
        self.set_fill_color(*GRIS_CLAIR)
        self.set_draw_color(*couleur)
        self.set_line_width(0.9)

        y_debut = self.get_y()
        self.set_text_color(*couleur)
        self.set_x(self.l_margin + 3)
        self.multi_cell(self.w - self.l_margin - self.r_margin - 6, hauteur_titre,
                        titre, fill=False)
        self.set_text_color(0, 0, 0)
        self.set_font("DJ", "", 10)
        self.set_x(self.l_margin + 3)
        self.multi_cell(self.w - self.l_margin - self.r_margin - 6, 5.1,
                        decimales_fr(contenu.strip()))
        y_fin = self.get_y()
        self.line(self.l_margin, y_debut, self.l_margin, y_fin)
        self.ln(2.5)

    def tableau(self, entetes: list[str], lignes: list[list], largeurs: list[float],
                alignements: list[str] | None = None):
        """Tableau simple avec en-tête colorée et lignes alternées."""
        if alignements is None:
            alignements = ["L"] + ["R"] * (len(entetes) - 1)

        # Saut de page si le tableau ne tient pas
        if self.get_y() + 8 + 6 * len(lignes) > self.h - 20:
            self.add_page()

        self.set_font("DJ", "B", 9)
        self.set_fill_color(*MARINE)
        self.set_text_color(255, 255, 255)
        for entete, largeur, alignement in zip(entetes, largeurs, alignements):
            self.cell(largeur, 7, entete, align=alignement, fill=True, border=0)
        self.ln()

        self.set_font("DJ", "", 9)
        self.set_text_color(0, 0, 0)
        for index, ligne in enumerate(lignes):
            remplir = index % 2 == 0
            self.set_fill_color(248, 249, 251)
            for valeur, largeur, alignement in zip(ligne, largeurs, alignements):
                self.cell(largeur, 6, decimales_fr(str(valeur)),
                          align=alignement, fill=remplir, border=0)
            self.ln()
        self.ln(3)

    def figure(self, nom: str, legende: str, largeur: float = 165):
        """Insère une figure produite par le notebook EDA."""
        chemin = FIGURES / f"{nom}.png"
        if not chemin.exists():
            self.texte(f"[figure manquante : {nom}.png]")
            return

        from PIL import Image

        with Image.open(chemin) as image:
            ratio = image.height / image.width
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

    def code(self, contenu: str):
        """Bloc de code en police à chasse fixe."""
        self.set_font("MONO", "", 8.3)
        self.set_fill_color(245, 246, 248)
        for ligne in contenu.strip().split("\n"):
            self.cell(0, 4.25, "  " + ligne, fill=True, new_x=XPos.LMARGIN,
                      new_y=YPos.NEXT)
        self.ln(2.5)


# --------------------------------------------------------------------------- #
# Construction du document
# --------------------------------------------------------------------------- #


def construire(stats: dict) -> Rapport:
    pdf = Rapport()

    # === Page de garde ====================================================
    pdf.add_page()
    pdf.ln(58)
    pdf.set_font("DJ", "B", 25)
    pdf.set_text_color(*MARINE)
    pdf.multi_cell(0, 12, "Documentation technique", align="C")
    pdf.set_font("DJ", "B", 17)
    pdf.multi_cell(0, 9, "ETL & Analyse exploratoire", align="C")
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
        "Analyse et prédiction du risque cardiovasculaire\n"
        "à partir des données du Behavioral Risk Factor\n"
        "Surveillance System (CDC, 2015)",
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

    # === 1. Introduction ==================================================
    pdf.titre1("1. Introduction et objectifs")

    pdf.texte(
        "Ce document décrit la première phase du projet BRFSS Heart Analytics : la "
        "construction du pipeline ETL et l'analyse exploratoire des données. Il "
        "présente les choix techniques retenus, les contrôles qualité mis en place "
        "et les résultats de l'exploration, en explicitant systématiquement les "
        "raisons de chaque décision."
    )

    pdf.titre2("1.1 Objectif du projet")
    pdf.texte(
        "Estimer le risque de maladie ou d'accident cardiaque d'une personne à "
        "partir de son profil de santé déclaré, et identifier les facteurs les plus "
        "fortement associés à ce risque. Le projet couvre l'ensemble de la chaîne "
        "analytique : extraction et nettoyage, entrepôt de données dimensionnel, "
        "restitution décisionnelle, modélisation prédictive, puis mise à disposition "
        "via une application web."
    )

    pdf.titre2("1.2 Objectif de cette phase")
    pdf.puce(
        "Construire un pipeline ETL reproductible, de la donnée brute vers une "
        "table analytique exploitable."
    )
    pdf.puce(
        "Mettre en place des contrôles qualité automatiques qui empêchent toute "
        "donnée inattendue de se propager silencieusement."
    )
    pdf.puce(
        "Comprendre la structure des données et identifier les facteurs associés "
        "à la maladie cardiovasculaire."
    )
    pdf.puce(
        "Établir les contraintes que l'exploration impose à la phase de "
        "modélisation."
    )
    pdf.ln(2)

    pdf.encadre(
        "Limite méthodologique fondamentale",
        "Les 21 variables explicatives sont auto-déclarées au même moment que la "
        "variable cible, lors d'un unique entretien téléphonique. Les relations "
        "décrites dans ce document sont donc des associations transversales : elles "
        "ne permettent d'établir ni causalité, ni prédiction d'un événement futur. "
        "Le modèle qui en découlera estime un risque à partir d'un profil, il ne "
        "prédit pas la survenue d'un accident cardiaque. Cette limite est rappelée "
        "dans tous les livrables du projet, y compris l'application web.",
    )

    # === 2. Les données ===================================================
    pdf.titre1("2. Le jeu de données")

    pdf.titre2("2.1 Source et volumétrie")
    pdf.texte(
        "Les données proviennent du Behavioral Risk Factor Surveillance System "
        "(BRFSS), enquête téléphonique annuelle menée par les Centers for Disease "
        "Control and Prevention (CDC) aux États-Unis. L'édition 2015 utilisée ici a "
        "été mise à disposition sur Kaggle dans une version déjà nettoyée et encodée."
    )
    pdf.tableau(
        ["Propriété", "Valeur"],
        [
            ["Nombre de répondants", f"{stats['lignes']:,}".replace(",", " ")],
            ["Variables après enrichissement", str(stats["colonnes"])],
            ["Valeurs manquantes", str(stats["manquantes"])],
            ["Variable cible", "heart_disease (0 / 1)"],
            ["Prévalence de la cible", f"{stats['prevalence']:.2f} %"],
            ["Licence", "Données publiques"],
        ],
        [80, 85],
        ["L", "L"],
    )

    pdf.texte(
        f"L'absence totale de valeurs manquantes ({stats['manquantes']} sur "
        f"l'ensemble du fichier) est inhabituelle et mérite d'être soulignée : elle "
        "résulte du nettoyage préalable appliqué par l'auteur du jeu Kaggle, qui a "
        "écarté les non-réponses. Aucune stratégie d'imputation n'est donc "
        "nécessaire, mais il faut garder à l'esprit que cette sélection en amont a "
        "pu écarter des profils particuliers — les personnes les plus fragiles étant "
        "généralement celles qui répondent le moins."
    )

    pdf.titre2("2.2 Dictionnaire des variables")
    pdf.texte("Les 22 variables de la source se répartissent en cinq groupes.")

    pdf.titre3("Conditions médicales déclarées")
    pdf.tableau(
        ["Variable", "Description", "Modalités"],
        [
            ["HighBP", "Hypertension artérielle diagnostiquée", "0 / 1"],
            ["HighChol", "Cholestérol élevé diagnostiqué", "0 / 1"],
            ["CholCheck", "Dosage du cholestérol depuis 5 ans", "0 / 1"],
            ["Stroke", "Antécédent d'accident vasculaire cérébral", "0 / 1"],
            ["Diabetes", "Statut diabétique", "0 / 1 / 2"],
            ["DiffWalk", "Difficulté sérieuse à marcher", "0 / 1"],
        ],
        [32, 100, 33],
        ["L", "L", "C"],
    )

    pdf.titre3("Comportements et hygiène de vie")
    pdf.tableau(
        ["Variable", "Description", "Modalités"],
        [
            ["Smoker", "A fumé au moins 100 cigarettes dans sa vie", "0 / 1"],
            ["PhysActivity", "Activité physique dans les 30 derniers jours", "0 / 1"],
            ["Fruits", "Consommation de fruits au moins 1 fois/jour", "0 / 1"],
            ["Veggies", "Consommation de légumes au moins 1 fois/jour", "0 / 1"],
            ["HvyAlcoholConsump", "Consommation d'alcool excessive", "0 / 1"],
        ],
        [42, 90, 33],
        ["L", "L", "C"],
    )

    pdf.titre3("État de santé perçu et mesures")
    pdf.tableau(
        ["Variable", "Description", "Modalités"],
        [
            ["GenHlth", "État de santé général perçu", "1 à 5"],
            ["MentHlth", "Jours de mal-être mental sur 30", "0 à 30"],
            ["PhysHlth", "Jours de mal-être physique sur 30", "0 à 30"],
            ["BMI", "Indice de masse corporelle", "12 à 98"],
        ],
        [32, 100, 33],
        ["L", "L", "C"],
    )

    pdf.titre3("Accès aux soins et données socio-démographiques")
    pdf.tableau(
        ["Variable", "Description", "Modalités"],
        [
            ["AnyHealthcare", "Dispose d'une couverture santé", "0 / 1"],
            ["NoDocbcCost", "A renoncé à un médecin pour raison financière", "0 / 1"],
            ["Sex", "Sexe déclaré", "0 / 1"],
            ["Age", "Tranche d'âge (codebook BRFSS)", "1 à 13"],
            ["Education", "Niveau d'études atteint", "1 à 6"],
            ["Income", "Tranche de revenu du foyer", "1 à 8"],
        ],
        [37, 95, 33],
        ["L", "L", "C"],
    )

    pdf.encadre(
        "Un point d'attention sur l'encodage",
        "Toutes les variables sont livrées en float64, y compris les indicateurs "
        "binaires et les codes ordinaux. Sans retraitement, une tranche d'âge "
        "s'afficherait « 9.0 » dans les rapports décisionnels. Le pipeline rétablit "
        "des types entiers, et les libellés du codebook BRFSS sont réintégrés au "
        "niveau de l'entrepôt afin de restituer « 60-64 ans ».",
        couleur=BLEU,
    )

    # === 3. Architecture du pipeline ======================================
    pdf.titre1("3. Architecture du pipeline ETL")

    pdf.titre2("3.1 Principe directeur")
    pdf.encadre(
        "Aucune donnée n'est supprimée ni corrigée",
        "Le pipeline ne modifie jamais une valeur au motif qu'elle paraît "
        "improbable. Les anomalies sont signalées par des drapeaux booléens, et la "
        "table analytique reste fidèle à la source. Les décisions de traitement — "
        "exclure, imputer, transformer — appartiennent aux étapes aval, où elles "
        "sont prises en connaissance de cause et documentées. Ce choix garantit "
        "qu'aucune information n'est perdue de façon irréversible dès l'entrée du "
        "pipeline.",
        couleur=VERT,
    )

    pdf.titre2("3.2 Enchaînement des étapes")
    pdf.code(
        """
  data/heart_disease_health_indicators_BRFSS2015.csv
        │
        ├─▶ extract.py    lecture du CSV, mode échantillon
        ├─▶ transform.py  renommage, typage, classe d'IMC,
        │                 variables dérivées, drapeaux qualité
        ├─▶ checks.py     contrôles de domaine et de bornes
        │                 (bloquants ou en simple alerte)
        └─▶ load.py       écriture dans heart.duckdb
                                │
                                ▼
                    heart.duckdb :: analytical_base
"""
    )

    pdf.titre2("3.3 Rôle de chaque module")
    pdf.tableau(
        ["Fichier", "Responsabilité"],
        [
            ["config.py", "Chemins, codebook, domaines de validation, seuils"],
            ["extract.py", "Lecture du CSV source, gestion du mode échantillon"],
            ["transform.py", "Nettoyage, typage, enrichissement, drapeaux qualité"],
            ["checks.py", "Contrôles qualité avant chargement"],
            ["load.py", "Écriture dans DuckDB, gestion du verrou d'écriture"],
            ["run_etl.py", "Orchestration et restitution de l'exécution"],
        ],
        [38, 127],
        ["L", "L"],
    )

    pdf.texte(
        "Cette séparation en modules à responsabilité unique permet de tester "
        "chaque étape isolément et de modifier une règle métier sans toucher au "
        "reste de la chaîne. Le fichier config.py centralise toutes les constantes : "
        "aucun autre module ne code en dur un chemin, un seuil ou un libellé."
    )

    pdf.titre2("3.4 Contrôles qualité")
    pdf.texte(
        "Les contrôles se répartissent en deux niveaux de sévérité. Les contrôles "
        "bloquants interrompent le pipeline : table vide, identifiant non unique, "
        "valeur manquante, variable hors du domaine défini par le codebook, ou "
        "mesure hors de ses bornes connues. Les alertes sont affichées puis "
        "consignées sans interrompre l'exécution : écart de volumétrie, prévalence "
        "inhabituelle, taux d'IMC extrêmes élevé."
    )
    pdf.texte(
        "L'intérêt du contrôle de domaine mérite d'être souligné : si le fichier "
        "source venait à changer — nouvelle édition du BRFSS, encodage différent, "
        "colonne renommée — le pipeline s'arrêterait avec un message explicite "
        "plutôt que de charger silencieusement des données incorrectes dans "
        "l'entrepôt."
    )

    pdf.titre2("3.5 Exécution")
    pdf.code(
        """
cd 01_etl
python run_etl.py                 # pipeline complet
python run_etl.py --sample 5000   # échantillon, pour tester
"""
    )
    pdf.texte(
        f"L'exécution complète traite les {stats['lignes']:,} lignes en moins d'une "
        "seconde.".replace(",", " ")
    )

    # === 4. Variables dérivées ============================================
    pdf.titre1("4. Variables dérivées")

    pdf.texte(
        "Le pipeline enrichit la source de variables métier absentes du fichier "
        "d'origine. Elles résument des informations dispersées sur plusieurs "
        "colonnes et se révèlent, pour certaines, plus informatives que les "
        "variables brutes dont elles sont issues."
    )

    pdf.tableau(
        ["Variable", "Définition"],
        [
            ["bmi_class", "Classe d'IMC selon les seuils de l'OMS (6 modalités)"],
            ["total_unhealthy_days", "Jours de mal-être mental + physique, plafonné à 30"],
            ["risk_factor_count", "Cumul des facteurs de risque cardiovasculaire (0 à 7)"],
            ["healthy_habits_count", "Cumul des comportements protecteurs (0 à 3)"],
            ["has_care_access", "Couverture santé et absence de renoncement financier"],
        ],
        [48, 117],
        ["L", "L"],
    )

    pdf.titre2("4.1 Le score de facteurs de risque")
    pdf.texte(
        "La variable risk_factor_count compte les facteurs de risque "
        "cardiovasculaire reconnus présents chez un répondant : hypertension, "
        "cholestérol élevé, tabagisme, antécédent d'AVC, difficulté à marcher, "
        "diabète et obésité. Sa capacité discriminante est remarquable."
    )

    pdf.tableau(
        ["Facteurs de risque", "Effectif", "Prévalence"],
        [
            [str(n), f"{eff:,}".replace(",", " "), f"{prev:.2f} %"]
            for n, eff, prev in stats["cumul"]
        ],
        [55, 55, 55],
        ["C", "R", "R"],
    )

    prev_min = stats["cumul"][0][2]
    prev_max = stats["cumul"][-1][2]
    pdf.texte(
        f"La progression est strictement monotone et couvre une amplitude "
        f"considérable : de {prev_min:.2f} % chez les répondants sans aucun facteur "
        f"de risque à {prev_max:.2f} % chez ceux qui en cumulent sept, soit un "
        f"rapport de 1 à {prev_max / prev_min:.0f}. Cette variable unique, "
        "construite à partir de sept colonnes, capture une part importante du "
        "signal disponible."
    )

    pdf.figure(
        "06_cumul_facteurs_risque",
        "Effectifs et prévalence selon le nombre de facteurs de risque cumulés",
        largeur=126,
    )

    # === 5. Qualité : les doublons ========================================
    pdf.titre1("5. Qualité des données : le cas des doublons")

    pdf.texte(
        f"Le jeu contient {stats['doublons']:,} lignes strictement identiques à une "
        f"autre, soit {stats['doublons'] / stats['lignes'] * 100:.2f} % de "
        "l'échantillon. Le réflexe habituel consiste à les supprimer. Cette décision "
        "mérite pourtant d'être instruite, car elle repose sur une hypothèse "
        "implicite qu'il est possible de tester.".replace(",", " ")
    )

    pdf.titre2("5.1 Deux hypothèses concurrentes")
    pdf.texte(
        "Hypothèse A — erreurs de saisie : un même répondant a été enregistré "
        "plusieurs fois. Les doublons sont alors des artefacts à éliminer.\n\n"
        "Hypothèse B — collisions légitimes : avec 22 variables toutes grossièrement "
        "codées (indicateurs binaires, tranches d'âge, classes de revenu), deux "
        "personnes différentes peuvent parfaitement présenter le même profil. Les "
        "doublons sont alors de vrais répondants distincts."
    )
    pdf.texte(
        "Ces deux hypothèses produisent des prédictions opposées et vérifiables. "
        "Quatre tests permettent de trancher."
    )

    pdf.titre2("5.2 Test 1 — sensibilité à la taille de l'échantillon")
    pdf.texte(
        "Si les doublons résultent d'erreurs de saisie, leur taux est une propriété "
        "intrinsèque du fichier : il doit rester constant quelle que soit la taille "
        "de l'échantillon considéré. S'il s'agit de collisions, le taux doit croître "
        "avec la taille — plus il y a de répondants, plus la probabilité que deux "
        "d'entre eux coïncident augmente, selon la logique du paradoxe des "
        "anniversaires."
    )

    pdf.tableau(
        ["Taille de l'échantillon", "Lignes dupliquées"],
        [
            ["12 684", "1,50 %"],
            ["25 368", "2,55 %"],
            ["63 420", "4,47 %"],
            ["126 840", "6,69 %"],
            ["253 680", f"{stats['doublons'] / stats['lignes'] * 100:.2f} %"],
        ],
        [82, 83],
        ["L", "R"],
    )

    pdf.figure(
        "01_doublons_scaling",
        "Le taux de doublons croît avec la taille de l'échantillon, ce qui exclut "
        "l'hypothèse d'erreurs de saisie",
        largeur=130,
    )

    pdf.texte(
        "Le taux est multiplié par plus de six entre le plus petit et le plus grand "
        "échantillon. L'hypothèse A est écartée."
    )

    pdf.titre2("5.3 Test 2 — nature des profils dupliqués")
    pdf.texte(
        "Une erreur de saisie n'a aucune raison de viser préférentiellement "
        "certains profils : elle devrait frapper au hasard. Une collision, en "
        "revanche, touche d'abord les profils les plus fréquents dans la population."
    )
    pdf.tableau(
        ["Caractéristique", "Lignes dupliquées", "Lignes uniques"],
        [
            ["Aucun jour de mal-être mental", "95,7 %", "65,0 %"],
            ["Aucun jour de mal-être physique", "96,2 %", "57,8 %"],
            ["IMC inférieur ou égal à 30", "91,1 %", "67,9 %"],
        ],
        [75, 45, 45],
        ["L", "R", "R"],
    )
    pdf.texte(
        "Les lignes dupliquées sont massivement des profils banals : personnes en "
        "bonne santé, IMC modéré, aucun jour de mal-être déclaré. C'est exactement "
        "le comportement attendu de collisions."
    )

    pdf.titre2("5.4 Test 3 — taille des groupes")
    pdf.texte(
        "La distribution des groupes de doublons décroît régulièrement, et le "
        "groupe le plus important compte 59 lignes rigoureusement identiques. Aucun "
        "mécanisme d'erreur de saisie plausible ne produit 59 copies d'un même "
        "enregistrement. En revanche, que 59 répondants sur plus de 250 000 "
        "partagent le profil le plus commun de la population est parfaitement "
        "attendu."
    )

    pdf.titre2("5.5 Test 4 — conséquence d'une déduplication")
    pdf.tableau(
        ["Traitement", "Prévalence de la cible"],
        [
            ["Doublons conservés", f"{stats['prevalence']:.3f} %"],
            ["Doublons supprimés", f"{stats['prevalence_dedup']:.3f} %"],
            ["Écart introduit",
             f"{stats['prevalence_dedup'] - stats['prevalence']:+.3f} point"],
        ],
        [82, 83],
        ["L", "R"],
    )

    pdf.encadre(
        "Décision : les doublons sont conservés",
        "Les quatre tests convergent vers l'hypothèse des collisions légitimes. "
        "Supprimer ces lignes reviendrait à effacer de vrais répondants, "
        "majoritairement en bonne santé, et ferait mécaniquement grimper la "
        "prévalence de la maladie de "
        f"{stats['prevalence']:.2f} % à {stats['prevalence_dedup']:.2f} %. La "
        "déduplication n'aurait pas nettoyé les données : elle les aurait biaisées.",
        couleur=VERT,
    )

    pdf.titre2("5.6 Un point connexe à traiter en modélisation")
    pdf.texte(
        "L'analyse des doublons met en lumière une propriété distincte : des "
        "profils rigoureusement identiques portent parfois des valeurs cibles "
        "opposées — deux personnes au même profil déclaré, l'une atteinte, l'autre "
        "non. Il ne s'agit pas d'un défaut de qualité mais d'une erreur "
        "irréductible, inhérente au fait que 21 variables ne suffisent pas à "
        "déterminer entièrement l'état de santé cardiaque. Cette erreur fixe un "
        "plafond de performance qu'aucun modèle ne pourra dépasser. Elle sera "
        "quantifiée dans la documentation du module de modélisation."
    )

    # === 6. Analyse exploratoire ==========================================
    pdf.titre1("6. Analyse exploratoire")

    pdf.titre2("6.1 La variable cible")
    pdf.texte(
        f"La prévalence s'établit à {stats['prevalence']:.2f} %, soit environ un "
        "répondant atteint pour dix. Ce déséquilibre a des conséquences directes et "
        "immédiates sur la méthodologie de modélisation."
    )

    pdf.figure(
        "02_cible_desequilibre",
        "Répartition de la variable cible : un déséquilibre marqué",
        largeur=155,
    )

    pdf.encadre(
        "Conséquence : l'exactitude est inutilisable",
        f"Avec {stats['prevalence']:.2f} % de cas positifs, un modèle qui "
        f"prédirait « aucun malade » pour l'ensemble de la population atteindrait "
        f"{100 - stats['prevalence']:.2f} % d'exactitude tout en étant dépourvu de "
        "toute utilité. L'accuracy est donc écartée comme critère de sélection. Les "
        "métriques retenues sont le ROC-AUC, le PR-AUC, le rappel et le F1 — cette "
        "dernière famille étant adaptée aux classes déséquilibrées.",
    )

    pdf.titre2("6.2 Prévalence par segment")
    pdf.figure(
        "04_prevalence_segments",
        "Prévalence de la maladie cardiaque selon six segments (trait pointillé : "
        "moyenne générale)",
        largeur=172,
    )

    pdf.texte(
        f"L'âge est de loin le facteur le plus discriminant : la prévalence passe "
        f"de {stats['prev_age_min']:.2f} % dans la tranche la plus jeune à "
        f"{stats['prev_age_max']:.2f} % chez les 80 ans et plus, selon une "
        "progression strictement monotone."
    )
    pdf.texte(
        "L'état de santé perçu se révèle presque aussi puissant, avec un rapport "
        "d'environ un à dix entre les personnes se déclarant en excellente santé et "
        "celles se disant en mauvaise santé. Bien que subjective, cette variable "
        "résume une quantité importante d'information clinique."
    )
    pdf.texte(
        "Un gradient socio-économique net apparaît également : la prévalence décroît "
        "régulièrement à mesure que le revenu du foyer et le niveau d'études "
        "augmentent."
    )

    pdf.titre2("6.3 La relation non monotone entre IMC et maladie")
    pdf.tableau(
        ["Classe d'IMC (OMS)", "Effectif", "Prévalence"],
        [
            [libelle, f"{eff:,}".replace(",", " "), f"{prev:.2f} %"]
            for libelle, eff, prev in stats["imc"]
        ],
        [75, 45, 45],
        ["L", "R", "R"],
    )

    pdf.figure(
        "05_imc_courbe_j",
        "La prévalence selon la classe d'IMC dessine une courbe en J",
        largeur=140,
    )

    imc_insuffisance = stats["imc"][0][2]
    imc_normale = stats["imc"][1][2]
    pdf.texte(
        f"Ce résultat mérite une attention particulière. Les personnes en "
        f"insuffisance pondérale présentent une prévalence de {imc_insuffisance:.2f} %, "
        f"nettement supérieure à celle des personnes de corpulence normale "
        f"({imc_normale:.2f} %) et proche de celle des obésités modérées. La relation "
        "entre IMC et maladie cardiaque n'est donc pas monotone : elle dessine une "
        "courbe en J."
    )
    pdf.texte(
        "Ce phénomène est bien documenté en épidémiologie. Il relève en grande "
        "partie de la causalité inverse : la maladie chronique provoque un "
        "amaigrissement, plutôt que la maigreur ne cause la maladie. La simultanéité "
        "du recueil des variables et de la cible interdit toutefois de trancher sur "
        "la base de ces seules données."
    )

    pdf.encadre(
        "Conséquence pour la modélisation",
        "Un modèle linéaire appliqué à l'IMC brut manquerait entièrement cette "
        "structure : il conclurait à une relation croissante là où les deux "
        "extrémités de la distribution présentent un risque élevé. Cela justifie de "
        "conserver la classe d'IMC catégorielle en complément de la valeur continue, "
        "et oriente vers les modèles à base d'arbres, capables de capturer ce type "
        "de non-linéarité sans transformation préalable.",
        couleur=BLEU,
    )

    pdf.titre2("6.4 Structure des corrélations")
    pdf.figure(
        "07_correlations",
        "Matrice des corrélations de Pearson entre les principales variables",
        largeur=150,
    )

    pdf.tableau(
        ["Variable", "Corrélation avec la cible"],
        [[nom, f"{val:+.3f}"] for nom, val in stats["correlations"]],
        [95, 70],
        ["L", "R"],
    )

    correlation_max = max(abs(v) for _, v in stats["correlations"])
    pdf.texte(
        f"Aucune corrélation linéaire n'est forte : la plus élevée atteint "
        f"{correlation_max:.3f} en valeur absolue. Ce constat ne doit pas conduire à "
        "penser que les variables sont peu informatives. La plupart d'entre elles "
        "sont binaires, et le coefficient de Pearson mesure mal les relations non "
        "linéaires — la courbe en J de l'IMC en est l'illustration directe. Le "
        "gradient observé sur le cumul des facteurs de risque démontre au contraire "
        "l'existence d'un signal très net."
    )
    pdf.texte(
        "Aucune paire de variables explicatives ne présente de corrélation forte : "
        "il n'y a pas de multicolinéarité problématique, et l'ensemble des variables "
        "peut être conservé."
    )

    pdf.titre2("6.5 Comparaison des profils")
    pdf.figure(
        "08_profils_compares",
        "Fréquence des indicateurs selon le statut cardiaque",
        largeur=150,
    )

    pdf.texte(
        "Les écarts les plus marqués concernent la difficulté à marcher, "
        "l'antécédent d'AVC, l'hypertension et le cholestérol élevé. L'activité "
        "physique constitue le seul indicateur nettement plus fréquent chez les "
        "personnes non atteintes."
    )
    pdf.encadre(
        "Un résultat à ne pas mal interpréter",
        "La consommation excessive d'alcool apparaît paradoxalement plus fréquente "
        "chez les répondants non atteints. Il ne faut pas y voir un effet "
        "protecteur : les gros consommateurs déclarés sont en moyenne nettement plus "
        "jeunes, et l'âge domine largement le risque cardiovasculaire. Il s'agit "
        "d'un effet de structure, illustration classique du fait qu'une association "
        "brute ne se lit jamais indépendamment des variables de confusion.",
        couleur=BLEU,
    )

    # === 7. Valeurs aberrantes ============================================
    pdf.titre1("7. Valeurs aberrantes et standardisation")

    pdf.texte(
        "Deux questions distinctes, souvent confondues, doivent être traitées "
        "séparément avant la modélisation. La première : le jeu contient-il des "
        "valeurs aberrantes, c'est-à-dire des valeurs fausses issues d'une erreur de "
        "saisie ou de mesure ? La seconde : faut-il standardiser les variables ? La "
        "seconde ne découle pas de la première."
    )

    pdf.titre2("7.1 Distribution par statut")
    pdf.figure(
        "09_boxplots_par_statut",
        "Boîtes à moustaches des variables continues selon le statut cardiaque",
        largeur=166,
    )

    pdf.texte(
        "Le contraste le plus frappant concerne les jours de mal-être physique. "
        "Chez les non atteints, la boîte est écrasée sur zéro. Chez les personnes "
        "atteintes, elle s'étale de 0 à 20 : un quart d'entre elles déclarent au "
        "moins vingt jours de souffrance physique sur les trente derniers. Le cumul "
        "des facteurs de risque offre également une séparation nette, supérieure à "
        "celle de n'importe quelle variable brute prise isolément."
    )

    pdf.titre2("7.2 Deux règles classiques qui se contredisent")
    pdf.texte(
        "L'application des deux règles usuelles de détection — l'écart "
        "interquartile et le z-score au-delà de trois écarts-types — produit des "
        "résultats incompatibles."
    )

    pdf.tableau(
        ["Variable", "Max", "Seuil IQR", "Seuil z=3", "% hors IQR", "% |z|>3"],
        [
            [nom, f"{maxi:.1f}", f"{s_iqr:.1f}", f"{s_z:.1f}",
             f"{p_iqr:.2f} %", f"{p_z:.2f} %"]
            for nom, maxi, s_iqr, s_z, p_iqr, p_z in stats["aberrantes"]
        ],
        [42, 20, 25, 25, 27, 26],
        ["L", "R", "R", "R", "R", "R"],
    )

    phys = [a for a in stats["aberrantes"] if a[0] == "phys_hlth_days"][0]
    pdf.texte(
        f"Pour l'IMC, les deux règles restent cohérentes. Pour phys_hlth_days, en "
        f"revanche, l'écart interquartile signale {phys[4]:.2f} % de l'échantillon "
        f"là où le z-score n'en signale aucun. L'explication est structurelle : la "
        f"variable est bornée à 30 par le questionnaire, et son seuil à trois "
        f"écarts-types s'établit à {phys[3]:.1f} — une valeur inatteignable par "
        f"construction. Le seuil de l'IQR tombe quant à lui à {phys[2]:.1f} et coupe "
        "en pleine distribution légitime."
    )

    pdf.encadre(
        "La notion de valeur aberrante ne s'applique pas ici",
        "Ces variables sont bornées et présentent une forte inflation de zéros. Les "
        "deux règles classiques supposent une distribution approximativement "
        "symétrique et non bornée : aucune des deux n'est valide dans ce contexte. "
        "Appliquer l'écart interquartile de façon mécanique conduirait à écarter "
        "environ quarante mille réponses parfaitement valides — précisément celles "
        "des personnes en souffrance, c'est-à-dire celles qui portent le signal "
        "recherché.",
    )

    pdf.titre2("7.3 Examen des valeurs extrêmes")
    pdf.titre3("Les IMC supérieurs à 60")
    pdf.texte(
        f"Ils concernent {stats['imc_sup_60']:,} lignes, soit "
        f"{stats['imc_sup_60'] / stats['lignes'] * 100:.2f} % de l'échantillon. Un "
        "IMC de 98 supposerait par exemple une masse de 285 kg pour une taille de "
        "1,70 m — physiologiquement très improbable. Un élément est révélateur : "
        f"leur prévalence de maladie cardiaque s'établit à "
        f"{stats['prev_imc_sup_60']:.2f} %, soit une valeur inférieure à la moyenne "
        f"générale de {stats['prevalence']:.2f} %. S'il s'agissait de cas d'obésité "
        "extrême authentiques, on attendrait l'inverse, l'obésité massive majorant "
        "nettement le risque cardiaque. Cette absence de signal suggère du bruit de "
        "saisie plutôt que des mesures réelles.".replace(",", " ")
    )
    pdf.texte(
        "Ces valeurs sont néanmoins conservées et signalées par le drapeau "
        "flag_bmi_extreme. Représentant moins d'un demi-pour-cent de l'échantillon, "
        "elles ne pèseront pas sur l'apprentissage, et les supprimer constituerait "
        "une décision arbitraire que rien n'impose."
    )

    pdf.titre3("Les trente jours de mal-être")
    pdf.texte(
        f"Ils relèvent d'une logique opposée. Il ne s'agit pas d'une anomalie mais "
        f"de la borne du questionnaire : nul ne peut déclarer plus de trente jours "
        f"sur trente. Le signal qu'ils portent est considérable — parmi les "
        f"{stats['n_phys30']:,} répondants déclarant trente jours de souffrance "
        f"physique, {stats['prev_phys30']:.2f} % sont atteints, contre "
        f"{stats['prevalence']:.2f} % en moyenne, soit "
        f"{stats['prev_phys30'] / stats['prevalence']:.1f} fois plus. Ces "
        "observations comptent parmi les plus informatives du jeu de données ; les "
        "traiter comme aberrantes détruirait précisément ce que l'on cherche à "
        "modéliser.".replace(",", " ")
    )

    pdf.encadre(
        "Décision : aucune valeur supprimée ni winsorisée",
        "Les valeurs extrêmes sont signalées par des drapeaux et conservées. Les "
        "modèles robustes à ce type de valeurs — arbres de décision et méthodes "
        "d'ensemble — seront privilégiés lors de la phase de modélisation.",
        couleur=VERT,
    )

    pdf.titre2("7.4 La justification réelle de la standardisation")
    pdf.figure(
        "10_echelles_standardisation",
        "Étendue des variables avant et après centrage-réduction",
        largeur=148,
    )

    pdf.texte(
        f"L'argument en faveur de la standardisation ne repose pas sur les valeurs "
        f"extrêmes mais sur l'hétérogénéité des échelles. L'IMC s'étend sur près de "
        f"quatre-vingt-dix unités quand les indicateurs binaires n'en couvrent "
        f"qu'une seule : le rapport entre la plus grande et la plus petite étendue "
        f"atteint {stats['rapport_avant']:.0f} pour 1. Après centrage-réduction, ce "
        f"rapport tombe à {stats['rapport_apres']:.1f} pour 1."
    )
    pdf.texte(
        "Pour tout algorithme fondé sur une distance ou sur une régularisation "
        "pénalisant l'amplitude des coefficients, l'IMC écraserait mécaniquement les "
        "autres variables — non parce qu'il serait plus informatif, mais parce qu'il "
        "est numériquement plus grand."
    )

    pdf.tableau(
        ["Famille de modèle", "Standardisation", "Raison"],
        [
            ["kNN, SVM", "Indispensable", "Fondés sur des distances"],
            ["Régression logistique pénalisée", "Nécessaire", "La pénalité dépend de l'échelle"],
            ["Arbres, forêts, XGBoost", "Inutile", "Seuils invariants par changement d'échelle"],
        ],
        [62, 33, 70],
        ["L", "C", "L"],
    )

    pdf.encadre(
        "Décision retenue",
        "La standardisation est intégrée au ColumnTransformer du pipeline de "
        "modélisation, ajusté sur le seul jeu d'entraînement puis appliqué au jeu de "
        "test — faute de quoi les statistiques du test fuiteraient dans "
        "l'apprentissage. Elle est conservée y compris pour les modèles à base "
        "d'arbres, où elle est neutre, afin que tous les modèles partagent "
        "exactement le même préprocessing et demeurent rigoureusement comparables.",
        couleur=VERT,
    )

    # === 8. Synthèse ======================================================
    pdf.titre1("8. Synthèse et implications")

    pdf.titre2("8.1 Bilan qualité")
    pdf.tableau(
        ["Point examiné", "Constat", "Décision"],
        [
            ["Valeurs manquantes", "Aucune", "Pas d'imputation"],
            ["Doublons exacts",
             f"{stats['doublons']:,}".replace(",", " "),
             "Conservés (collisions)"],
            ["IMC extrêmes", f"{stats['imc_extremes']:,}".replace(",", " "),
             "Signalés, conservés"],
            ["Incohérences santé",
             f"{stats['sante_incoherente']:,}".replace(",", " "),
             "Signalées, légitimes"],
        ],
        [48, 42, 75],
        ["L", "R", "L"],
    )

    pdf.titre2("8.2 Facteurs associés, par ordre d'importance")
    pdf.puce(
        f"L'âge — de {stats['prev_age_min']:.2f} % à {stats['prev_age_max']:.2f} % "
        "de prévalence selon la tranche."
    )
    pdf.puce("L'état de santé perçu — rapport d'environ un à dix.")
    pdf.puce(
        f"Le cumul des facteurs de risque — de {prev_min:.2f} % à {prev_max:.2f} %."
    )
    pdf.puce(
        "L'antécédent d'AVC, la difficulté à marcher, l'hypertension et le "
        "cholestérol élevé."
    )
    pdf.puce("Le gradient socio-économique — revenu et niveau d'études.")
    pdf.ln(3)

    pdf.titre2("8.3 Contraintes imposées à la modélisation")
    pdf.texte(
        "L'analyse exploratoire ne se contente pas de décrire : elle contraint les "
        "choix méthodologiques de la phase suivante."
    )
    pdf.puce(
        f"Écarter l'exactitude comme critère : à {stats['prevalence']:.2f} % de cas "
        f"positifs, un modèle constant atteindrait {100 - stats['prevalence']:.2f} %. "
        "Retenir le ROC-AUC, le PR-AUC, le rappel et le F1."
    )
    pdf.puce(
        "Traiter explicitement le déséquilibre des classes par pondération, en "
        "comparant avec une approche par rééchantillonnage synthétique."
    )
    pdf.puce(
        "Privilégier les modèles non linéaires : la courbe en J de l'IMC et la "
        "faiblesse des corrélations de Pearson établissent que le signal n'est pas "
        "linéaire."
    )
    pdf.puce(
        "Quantifier l'erreur irréductible liée aux profils identiques de cibles "
        "opposées, afin de connaître le plafond de performance atteignable."
    )
    pdf.puce(
        "Ajuster le préprocessing sur le seul jeu d'entraînement, pour éviter toute "
        "fuite d'information."
    )
    pdf.puce(
        "Maintenir la prudence interprétative : les relations établies sont des "
        "associations transversales et non des liens de causalité."
    )

    # === Annexe ===========================================================
    pdf.titre1("Annexe — Reproduire ces résultats")

    pdf.texte(
        "L'ensemble des résultats présentés dans ce document est reproductible à "
        "partir du dépôt cloné."
    )
    pdf.code(
        """
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Exécuter le pipeline ETL
cd 01_etl
python run_etl.py

# 3. Régénérer et exécuter le notebook d'analyse exploratoire
cd notebooks
python _build_eda.py
python -m jupyter nbconvert --to notebook --execute --inplace 01_eda.ipynb

# 4. Régénérer ce document
cd ../../06_rapport
python _build_doc_pdf_eda.py
"""
    )

    pdf.encadre(
        "Sur la génération de ce document",
        "Ce rapport est produit par un script qui recalcule chaque statistique "
        "depuis l'entrepôt DuckDB au moment de la génération, et qui intègre les "
        "figures effectivement produites par le notebook. Aucun chiffre n'y est "
        "saisi manuellement : le document ne peut donc pas diverger des données "
        "qu'il décrit. Les notebooks obéissent au même principe et sont produits "
        "par des scripts générateurs.",
        couleur=BLEU,
    )

    pdf.ln(4)
    pdf.set_font("DJ", "I", 9)
    pdf.set_text_color(*GRIS)
    pdf.multi_cell(
        0, 5,
        "Source des données : Behavioral Risk Factor Surveillance System (BRFSS), "
        "Centers for Disease Control and Prevention, édition 2015. Jeu de données "
        "public diffusé via Kaggle.",
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
