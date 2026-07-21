"""Formatage des nombres à la française.

Streamlit n'applique aucune localisation : `f"{x:.1%}"` produit « 19.2% ».
Dans une application entièrement en français, on attend « 19,2 % » — virgule
décimale et espace insécable avant le signe pourcent.
"""

# Espace insécable étroit, recommandé avant % et comme séparateur de milliers.
INSECABLE = " "


def pourcent(valeur: float, decimales: int = 1) -> str:
    """0.192 -> « 19,2 % »."""
    texte = f"{valeur * 100:.{decimales}f}".replace(".", ",")
    return f"{texte}{INSECABLE}%"


def nombre(valeur: float, decimales: int = 1) -> str:
    """2.04 -> « 2,0 »."""
    return f"{valeur:.{decimales}f}".replace(".", ",")


def entier(valeur: int) -> str:
    """253680 -> « 253 680 »."""
    return f"{valeur:,}".replace(",", INSECABLE)


def points(valeur: float, decimales: int = 1) -> str:
    """Écart en points de pourcentage, signe compris : 0.098 -> « +9,8 pts »."""
    texte = f"{valeur * 100:+.{decimales}f}".replace(".", ",")
    return f"{texte} pts"
