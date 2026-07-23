"""Génération des rapports PDF téléchargeables.

Deux rapports :
  - bilan individuel (page Évaluation),
  - synthèse d'un scoring par lot (page Scoring par lot).

Contrainte de déploiement : sur Streamlit Community Cloud, aucun fichier de
police externe n'est garanti. On utilise donc les **polices intégrées** de fpdf2
(Helvetica), encodées en Latin-1. Le texte est assaini au préalable pour
remplacer les caractères hors Latin-1 (tirets longs, guillemets courbes, flèches).
"""

from __future__ import annotations

from datetime import date

import pandas as pd
from fpdf import FPDF
from fpdf.enums import XPos, YPos

MARINE = (31, 59, 92)
ROUGE = (193, 68, 63)
VERT = (61, 139, 95)
GRIS = (90, 90, 90)
GRIS_CLAIR = (244, 246, 249)

# Remplacements des caractères hors Latin-1 les plus courants.
_REMPLACEMENTS = {
    "—": "-", "–": "-", "’": "'", "‘": "'",
    "“": '"', "”": '"', "…": "...", "→": "->",
    "≤": "<=", "≥": ">=", "×": "x", "•": "-",
    "œ": "oe", "Œ": "OE", "æ": "ae", "Æ": "AE",
}


def _l1(texte: str) -> str:
    """Rend une chaîne compatible avec l'encodage Latin-1 des polices intégrées."""
    for source, cible in _REMPLACEMENTS.items():
        texte = texte.replace(source, cible)
    return texte.encode("latin-1", "replace").decode("latin-1")


class _Rapport(FPDF):
    def __init__(self, pied: str):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.pied = pied
        self.set_auto_page_break(auto=True, margin=16)
        self.set_font("Helvetica", "", 10.5)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(*GRIS)
        self.cell(0, 8, _l1(f"{self.pied}  -  page {self.page_no()}"),
                  align="C")

    def titre(self, texte, taille=13):
        self.ln(2)
        self.set_font("Helvetica", "B", taille)
        self.set_text_color(*MARINE)
        self.cell(0, 7, _l1(texte), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)
        self.set_text_color(0, 0, 0)

    def para(self, texte, taille=10):
        self.set_font("Helvetica", "", taille)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 5, _l1(texte), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def ligne_cle_valeur(self, cle, valeur):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*GRIS)
        self.cell(70, 6, _l1(cle))
        self.set_text_color(0, 0, 0)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 6, _l1(str(valeur)), new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _entete(pdf, sous_titre):
    pdf.set_fill_color(*MARINE)
    pdf.rect(0, 0, pdf.w, 26, "F")
    pdf.set_y(7)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, _l1("BRFSS Heart Analytics"),
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, _l1(sous_titre), align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(32)


def _avertissement(pdf):
    pdf.ln(2)
    pdf.set_fill_color(255, 249, 219)
    pdf.set_draw_color(230, 200, 90)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(120, 90, 0)
    x0, y0 = pdf.get_x(), pdf.get_y()
    pdf.multi_cell(
        0, 4.5,
        _l1("Avertissement : ce document n'est pas un diagnostic medical. "
            "L'estimation traduit une association statistique observee dans une "
            "population, a un instant donne. Elle ne predit pas la survenue d'un "
            "accident cardiaque et ne remplace pas l'avis d'un professionnel de "
            "sante."),
        fill=True, border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.set_text_color(0, 0, 0)


# --------------------------------------------------------------------------- #
# Rapport individuel
# --------------------------------------------------------------------------- #


def bilan_individuel(
    resume_profil: dict,
    probabilite: float,
    niveau: str,
    ratio: float,
    positionnement: dict | None,
    contributions: pd.Series,
    conseils: list,
    libelle_variable,
) -> bytes:
    """Construit le bilan individuel et renvoie le PDF en octets."""
    pdf = _Rapport(pied="Bilan individuel d'estimation du risque")
    pdf.add_page()
    _entete(pdf, "Bilan individuel d'estimation du risque cardiovasculaire")

    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*GRIS)
    pdf.cell(0, 5, _l1(f"Genere le {date.today().strftime('%d/%m/%Y')}"),
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)

    # --- Résultat ---
    pdf.titre("Resultat de l'estimation")
    couleur = ROUGE if probabilite >= 0.15 else (VERT if probabilite < 0.05 else MARINE)
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(*couleur)
    pdf.cell(0, 12, _l1(f"{probabilite * 100:.1f} %".replace(".", ",")),
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ligne_cle_valeur("Niveau de risque", niveau)
    pdf.ligne_cle_valeur(
        "Comparaison a la population",
        f"x {ratio:.1f} le risque moyen (9,4 %)".replace(".", ","),
    )
    if positionnement:
        pdf.ligne_cle_valeur(
            "Position parmi vos pairs",
            f"{positionnement['percentile']:.0f}e centile "
            f"(personnes de meme age et sexe)",
        )

    # --- Profil ---
    pdf.titre("Profil renseigne")
    for cle, valeur in resume_profil.items():
        pdf.ligne_cle_valeur(cle, valeur)

    # --- Facteurs contributifs ---
    if contributions is not None and not contributions.empty:
        pdf.titre("Facteurs les plus influents")
        pdf.para(
            "Contribution de chaque facteur a l'ecart par rapport au risque "
            "moyen. Un signe + augmente le risque estime, un signe - le diminue.",
            taille=9,
        )
        top = contributions.reindex(
            contributions.abs().sort_values(ascending=False).index
        ).head(6)
        for variable, valeur in top.items():
            signe = "+" if valeur > 0 else "-"
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*(ROUGE if valeur > 0 else VERT))
            pdf.cell(8, 5.5, signe)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 5.5, _l1(libelle_variable(variable)),
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # --- Conseils ---
    pdf.titre("Conseils de prevention")
    for _icone, titre, message in conseils:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*MARINE)
        pdf.multi_cell(0, 5, _l1(titre), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 9.5)
        pdf.multi_cell(0, 4.6, _l1(message), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1.5)

    _avertissement(pdf)

    sortie = pdf.output()
    return bytes(sortie)


# --------------------------------------------------------------------------- #
# Rapport de synthèse d'un lot
# --------------------------------------------------------------------------- #


def synthese_lot(
    nb_total: int,
    nb_signales: int,
    risque_moyen: float,
    seuil: float,
    distribution: pd.Series,
    top_profils: pd.DataFrame,
) -> bytes:
    """Construit la synthèse d'un scoring par lot et renvoie le PDF en octets."""
    pdf = _Rapport(pied="Synthese d'un scoring par lot")
    pdf.add_page()
    _entete(pdf, "Synthese d'un scoring par lot")

    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*GRIS)
    pdf.cell(0, 5, _l1(f"Genere le {date.today().strftime('%d/%m/%Y')}"),
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)

    # --- Indicateurs clés ---
    pdf.titre("Indicateurs cles")
    pdf.ligne_cle_valeur("Profils analyses", f"{nb_total:,}".replace(",", " "))
    pdf.ligne_cle_valeur(
        "Profils signales",
        f"{nb_signales:,}".replace(",", " ")
        + f"  ({nb_signales / nb_total * 100:.1f} %)".replace(".", ","),
    )
    pdf.ligne_cle_valeur("Seuil de decision",
                         f"{seuil:.3f}".replace(".", ","))
    pdf.ligne_cle_valeur("Risque moyen estime",
                         f"{risque_moyen * 100:.1f} %".replace(".", ","))

    # --- Distribution ---
    pdf.titre("Distribution des risques estimes")
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(*MARINE)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(60, 6, _l1("Tranche de risque"), fill=True)
    pdf.cell(40, 6, _l1("Nombre de profils"), fill=True,
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    for i, (tranche, nb) in enumerate(distribution.items()):
        pdf.set_fill_color(*(GRIS_CLAIR if i % 2 == 0 else (255, 255, 255)))
        pdf.cell(60, 5.5, _l1(str(tranche)), fill=True)
        pdf.cell(40, 5.5, _l1(f"{int(nb):,}".replace(",", " ")), fill=True,
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")

    # --- Profils les plus exposés ---
    pdf.titre("Profils les plus exposes")
    colonnes = list(top_profils.columns)
    largeurs = [30] + [ (160 / (len(colonnes) - 1)) ] * (len(colonnes) - 1)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_fill_color(*MARINE)
    pdf.set_text_color(255, 255, 255)
    for col, w in zip(colonnes, largeurs):
        pdf.cell(w, 6, _l1(str(col)), fill=True, align="C")
    pdf.ln()
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 8.5)
    for i, (_, ligne) in enumerate(top_profils.iterrows()):
        pdf.set_fill_color(*(GRIS_CLAIR if i % 2 == 0 else (255, 255, 255)))
        for valeur, w in zip(ligne, largeurs):
            pdf.cell(w, 5.5, _l1(str(valeur)), fill=True, align="C")
        pdf.ln()

    _avertissement(pdf)

    sortie = pdf.output()
    return bytes(sortie)
