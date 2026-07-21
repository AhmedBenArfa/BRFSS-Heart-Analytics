"""Génère les PDF des documents de cadrage (module 00_documentation).

Rend chaque fichier Markdown de 00_documentation/ en PDF de même nom. Le Markdown
reste la source de vérité (lisible sur GitHub) ; le PDF en est une projection.

Gère le sous-ensemble Markdown utilisé par ces documents : titres (#, ##, ###),
paragraphes, listes à puces, tableaux, blocs de code, citations, gras inline.

Usage :
    python _build_doc_pdf_cadrage.py

Sortie :
    00_documentation/1_description_projet.pdf
    00_documentation/2_description_donnees.pdf
    00_documentation/3_demarche.pdf
"""

from __future__ import annotations

import re
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from fpdf.fonts import FontFace

RACINE = Path(__file__).resolve().parents[1]
DOSSIER = RACINE / "00_documentation"

DOSSIER_POLICES = Path(
    r"C:\Users\Mega-pc\anaconda3\Lib\site-packages\matplotlib\mpl-data\fonts\ttf"
)

MARINE = (31, 59, 92)
GRIS = (90, 90, 90)
ACCENT = (193, 68, 63)
BLEU = (46, 92, 138)
GRIS_CLAIR = (245, 246, 248)

FICHIERS = [
    "1_description_projet",
    "2_description_donnees",
    "3_demarche",
]


class Doc(FPDF):
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

    # -- éléments -----------------------------------------------------------
    def titre_doc(self, texte):
        self.set_font("DJ", "B", 20)
        self.set_text_color(*MARINE)
        self.multi_cell(0, 11, texte)
        self.ln(1)
        y = self.get_y()
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.8)
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(5)
        self.set_text_color(0, 0, 0)

    def section(self, texte):
        self.ln(2)
        self.set_font("DJ", "B", 13)
        self.set_text_color(*MARINE)
        self.multi_cell(0, 7, texte)
        self.ln(1)
        self.set_text_color(0, 0, 0)

    def sous_section(self, texte):
        self.ln(1)
        self.set_font("DJ", "B", 11)
        self.set_text_color(*BLEU)
        self.multi_cell(0, 6, texte)
        self.set_text_color(0, 0, 0)

    def paragraphe(self, texte):
        self.set_font("DJ", "", 10.5)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 5.3, _md(texte), markdown=True)
        self.ln(1.5)

    def puce(self, texte):
        self.set_font("DJ", "", 10.5)
        x = self.get_x()
        self.set_x(x + 3)
        self.cell(4, 5.2, "•")
        self.multi_cell(0, 5.2, _md(texte), markdown=True)
        self.set_x(x)

    def citation(self, texte):
        self.ln(1)
        self.set_draw_color(*BLEU)
        self.set_line_width(0.9)
        self.set_font("DJ", "I", 10)
        self.set_text_color(60, 60, 60)
        y0 = self.get_y()
        self.set_x(self.l_margin + 4)
        self.multi_cell(self.w - self.l_margin - self.r_margin - 8, 5.3, _md(texte),
                        markdown=True)
        self.line(self.l_margin, y0, self.l_margin, self.get_y())
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def bloc_code(self, lignes):
        self.ln(1)
        self.set_font("MONO", "", 8.2)
        self.set_fill_color(*GRIS_CLAIR)
        for ligne in lignes:
            self.cell(0, 4.4, "  " + ligne, fill=True, new_x=XPos.LMARGIN,
                      new_y=YPos.NEXT)
        self.ln(2.5)

    def tableau(self, entetes, lignes):
        # Saut de page si le tableau ne tient manifestement pas.
        if self.get_y() + 8 + 6.5 * (len(lignes) + 1) > self.h - 20:
            self.add_page()
        self.set_font("DJ", "", 8.8)
        self.set_draw_color(210, 214, 220)
        with self.table(
            headings_style=FontFace(
                emphasis="BOLD", color=(255, 255, 255), fill_color=MARINE
            ),
            cell_fill_color=(248, 249, 251),
            cell_fill_mode="ROWS",
            line_height=5.4,
            markdown=True,
            text_align="LEFT",
        ) as table:
            entete = table.row()
            for e in entetes:
                entete.cell(e)
            for ligne in lignes:
                r = table.row()
                for c in ligne:
                    r.cell(c)
        self.ln(2)


def _md(texte: str) -> str:
    """Convertit les code spans `x` en gras (fpdf ne gère pas les backticks)."""
    return re.sub(r"`([^`]+)`", r"**\1**", texte)


def _cellules(ligne_tableau: str) -> list[str]:
    """Découpe une ligne « | a | b | c | » en cellules."""
    return [c.strip() for c in ligne_tableau.strip().strip("|").split("|")]


def rendre(pdf: Doc, lignes: list[str]) -> None:
    """Parcourt le Markdown ligne à ligne et appelle les rendus adéquats."""
    i = 0
    para: list[str] = []

    def vider_para():
        if para:
            pdf.paragraphe(" ".join(para))
            para.clear()

    while i < len(lignes):
        ligne = lignes[i].rstrip("\n")
        strip = ligne.strip()

        # Bloc de code délimité par ```
        if strip.startswith("```"):
            vider_para()
            i += 1
            code = []
            while i < len(lignes) and not lignes[i].strip().startswith("```"):
                code.append(lignes[i].rstrip("\n"))
                i += 1
            pdf.bloc_code(code)
            i += 1
            continue

        # Tableau : lignes commençant par |
        if strip.startswith("|"):
            vider_para()
            entetes = _cellules(strip)
            i += 1
            # ligne de séparation |---|---|
            if i < len(lignes) and set(lignes[i].strip()) <= set("|-: "):
                i += 1
            corps = []
            while i < len(lignes) and lignes[i].strip().startswith("|"):
                corps.append(_cellules(lignes[i].strip()))
                i += 1
            pdf.tableau(entetes, corps)
            continue

        if strip.startswith("### "):
            vider_para()
            pdf.sous_section(strip[4:])
        elif strip.startswith("## "):
            vider_para()
            pdf.section(strip[3:])
        elif strip.startswith("# "):
            vider_para()
            pdf.titre_doc(strip[2:])
        elif strip.startswith("> "):
            vider_para()
            pdf.citation(strip[2:])
        elif strip.startswith("- "):
            vider_para()
            pdf.puce(strip[2:])
        elif strip.startswith("---"):
            vider_para()
        elif strip == "":
            vider_para()
        else:
            para.append(strip)
        i += 1

    vider_para()


def construire_un(nom: str) -> None:
    source = DOSSIER / f"{nom}.md"
    sortie = DOSSIER / f"{nom}.pdf"
    if not source.exists():
        print(f"  [ignore] {source.name} absent")
        return

    lignes = source.read_text(encoding="utf-8").splitlines()

    # Titre du pied de page = premier titre # du document.
    titre = next((l[2:].strip() for l in lignes if l.startswith("# ")), nom)

    pdf = Doc(pied=titre)
    pdf.add_page()
    rendre(pdf, lignes)
    pdf.output(str(sortie))
    print(f"  {sortie.name} ({pdf.page_no()} pages)")


def main() -> None:
    print("Generation des PDF de cadrage...")
    for nom in FICHIERS:
        construire_un(nom)
    print("Termine.")


if __name__ == "__main__":
    main()
