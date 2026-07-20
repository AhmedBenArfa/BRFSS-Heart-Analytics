"""Génère le diagramme du schéma en étoile.

Le diagramme est construit à partir de codebook.py et de la structure réelle de
fact_respondent : il ne peut donc pas diverger du modèle effectivement bâti.

Sortie :
    03_power_bi/screenshots/schema_etoile.png
    06_rapport/figures/schema_etoile.png
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

import codebook

RACINE = Path(__file__).resolve().parent
BASE = RACINE / "heart.duckdb"
SORTIES = [
    RACINE.parent / "03_power_bi" / "screenshots" / "schema_etoile.png",
    RACINE.parent / "06_rapport" / "figures" / "schema_etoile.png",
]

MARINE = "#1F3B5C"
ROUGE = "#C1443F"
BLEU_DIM = "#2E5C8A"
FOND_FAIT = "#FBE9E8"
FOND_DIM = "#E8EFF6"


def colonnes_fait() -> list[str]:
    """Récupère la liste réelle des colonnes de la table de faits."""
    with duckdb.connect(str(BASE), read_only=True) as conn:
        cols = conn.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'fact_respondent' ORDER BY ordinal_position"
        ).fetchall()
    return [c[0] for c in cols]


def boite(ax, x, y, largeur, hauteur, titre, lignes, couleur_fond, couleur_bord):
    """Dessine une table (dimension ou fait) façon entité relationnelle."""
    ax.add_patch(
        FancyBboxPatch(
            (x, y), largeur, hauteur,
            boxstyle="round,pad=0.02,rounding_size=0.08",
            facecolor=couleur_fond, edgecolor=couleur_bord, linewidth=1.8,
            mutation_aspect=1, zorder=2,
        )
    )
    # Bandeau de titre
    ax.text(
        x + largeur / 2, y + hauteur - 0.28, titre,
        ha="center", va="center", fontsize=9.5, fontweight="bold",
        color="white",
        bbox=dict(boxstyle="round,pad=0.25", facecolor=couleur_bord,
                  edgecolor="none"),
        zorder=3,
    )
    # Colonnes — pas de ligne adaptatif pour tenir dans la hauteur de la boîte
    haut_dispo = hauteur - 0.75
    pas = haut_dispo / max(len(lignes), 1)
    for i, ligne in enumerate(lignes):
        ax.text(
            x + 0.12, y + hauteur - 0.62 - i * pas, ligne,
            ha="left", va="center", fontsize=7, color="#222", zorder=3,
        )


def main() -> None:
    cols = colonnes_fait()
    cles = [c for c in cols if c.endswith("_key")]
    mesures = ["bmi", "ment_hlth_days", "phys_hlth_days", "total_unhealthy_days"]
    cible = ["heart_disease  (cible)"]

    fig, ax = plt.subplots(figsize=(13, 9.5))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 9.6)
    ax.axis("off")

    # --- Table de faits, au centre (contenu résumé pour rester compact) ---
    n_binaires = len([c for c in cols if c in (
        "high_bp", "high_chol", "chol_check", "smoker", "stroke",
        "phys_activity", "fruits", "veggies", "hvy_alcohol",
        "any_healthcare", "no_doc_cost", "diff_walk")])
    lignes_fait = (
        ["respondent_id  (PK)"]
        + [f"{len(cles)} clés étrangères (FK)"]
        + ["—"]
        + ["4 mesures : bmi, ment_hlth,"]
        + ["   phys_hlth, total_unhealthy"]
        + [f"{n_binaires} indicateurs binaires"]
        + ["3 variables dérivées"]
        + ["3 drapeaux qualité"]
        + ["—"]
        + cible
    )
    fx, fy, fw, fh = 4.75, 3.5, 3.5, 2.85
    boite(ax, fx, fy, fw, fh, "fact_respondent", lignes_fait, FOND_FAIT, ROUGE)

    # --- Dimensions, en couronne ---
    import math

    n = len(codebook.DIMENSIONS)
    cx, cy = fx + fw / 2, fy + fh / 2
    rayon_x, rayon_y = 5.3, 3.25
    dw, dh = 2.5, 1.15

    for i, dim in enumerate(codebook.DIMENSIONS):
        angle = math.pi / 2 + 2 * math.pi * i / n
        dx = cx + rayon_x * math.cos(angle) - dw / 2
        dy = cy + rayon_y * math.sin(angle) - dh / 2
        lignes_dim = [f"{dim['cle']}  (PK)", dim["libelle"]]
        boite(ax, dx, dy, dw, dh, dim["table"], lignes_dim, FOND_DIM, BLEU_DIM)

        # Trait de liaison fait -> dimension
        ax.annotate(
            "", xy=(dx + dw / 2, dy + dh / 2), xytext=(cx, cy),
            arrowprops=dict(arrowstyle="-", color="#9AA7B4", lw=1.3, zorder=1),
        )

    ax.text(
        6.5, 9.25, "Schéma en étoile — BRFSS Heart Analytics",
        ha="center", fontsize=14, fontweight="bold", color=MARINE,
    )
    ax.text(
        6.5, 8.9,
        f"1 table de faits ({len(cols)} colonnes) · {n} dimensions · "
        "grain : un répondant",
        ha="center", fontsize=9.5, color="#555", style="italic",
    )

    plt.tight_layout()
    for sortie in SORTIES:
        sortie.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(sortie, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Diagramme genere ({n} dimensions) -> {len(SORTIES)} emplacements")


if __name__ == "__main__":
    main()
