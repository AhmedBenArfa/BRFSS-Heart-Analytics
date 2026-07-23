"""Page de scoring par lot : estimation du risque sur un fichier entier."""

import pandas as pd
import streamlit as st

from utils import codebook, format_fr, rapport_pdf
from utils.modele import (
    PREVALENCE_REFERENCE,
    charger_metadonnees,
    estimer,
)

meta = charger_metadonnees()
variables = meta["variables"]
seuil = meta["seuil_decision"]

st.caption(
    "Importez un fichier CSV contenant une ligne par personne et les "
    f"{len(variables)} variables attendues. Chaque ligne reçoit une estimation."
)

with st.expander("Format attendu du fichier", icon=":material/table_view:"):
    st.markdown(
        "Le fichier doit contenir les colonnes suivantes, avec les mêmes "
        "codages que l'enquête BRFSS :"
    )
    st.code(", ".join(variables), language=None)
    modele_vide = pd.DataFrame(columns=variables)
    st.download_button(
        "Télécharger un gabarit vide",
        modele_vide.to_csv(index=False).encode("utf-8"),
        "gabarit_profils.csv",
        "text/csv",
        icon=":material/download:",
    )

fichier = st.file_uploader("Fichier CSV", type="csv")

if fichier is None:
    st.info("Aucun fichier chargé.", icon=":material/info:")
    st.stop()

try:
    donnees = pd.read_csv(fichier)
except Exception as erreur:
    st.error(f"Lecture impossible : {erreur}")
    st.stop()

# --- Contrôle des colonnes ------------------------------------------------

manquantes = [v for v in variables if v not in donnees.columns]
if manquantes:
    st.error(
        f"{len(manquantes)} colonne(s) manquante(s) : "
        + ", ".join(f"`{c}`" for c in manquantes)
    )
    st.stop()

if donnees.empty:
    st.warning("Le fichier ne contient aucune ligne.")
    st.stop()

nb_nuls = int(donnees[variables].isna().sum().sum())
if nb_nuls:
    st.error(
        f"{nb_nuls} valeur(s) manquante(s) dans les colonnes attendues. "
        "Le modèle exige un profil complet : corrigez le fichier."
    )
    st.stop()

# --- Estimation -----------------------------------------------------------

with st.spinner(f"Estimation sur {format_fr.entier(len(donnees))} profils…"):
    resultats = donnees.copy()
    resultats["risque_estime"] = estimer(donnees)
    resultats["signale"] = (resultats["risque_estime"] >= seuil).astype(int)

nb_signales = int(resultats["signale"].sum())

st.success(
    f"{format_fr.entier(len(resultats))} profils analysés.",
    icon=":material/check_circle:",
)

with st.container(horizontal=True):
    st.metric("Profils analysés", format_fr.entier(len(resultats)), border=True)
    st.metric("Profils signalés", format_fr.entier(nb_signales), border=True,
              help=f"Risque estimé supérieur au seuil ({format_fr.nombre(seuil, 3)})")
    st.metric("Part signalée", format_fr.pourcent(nb_signales / len(resultats)),
              border=True)
    st.metric("Risque moyen", format_fr.pourcent(resultats["risque_estime"].mean()),
              border=True,
              help=f"Référence population : {format_fr.pourcent(PREVALENCE_REFERENCE)}")

# --- Distribution ---------------------------------------------------------

col_gauche, col_droite = st.columns([3, 2])

with col_gauche:
    with st.container(border=True):
        st.markdown("**Distribution des risques estimés**")
        tranches = pd.cut(
            resultats["risque_estime"],
            bins=[0, 0.05, 0.10, 0.20, 0.40, 1.0],
            labels=["< 5 %", "5-10 %", "10-20 %", "20-40 %", "> 40 %"],
        ).value_counts().sort_index()
        st.bar_chart(tranches, color="#C1443F", height=260)

with col_droite:
    with st.container(border=True):
        st.markdown("**Profils les plus exposés**")
        colonnes_apercu = ["risque_estime", "age_group", "gen_hlth", "high_bp"]
        top = resultats.nlargest(10, "risque_estime")[colonnes_apercu].copy()
        # La barre de progression formate la valeur brute : on passe donc en
        # points de pourcentage (0-100) plutôt qu'en proportion (0-1).
        top["risque_estime"] *= 100
        top["age_group"] = top["age_group"].map(codebook.AGE)
        top["gen_hlth"] = top["gen_hlth"].map(codebook.SANTE_GENERALE)
        top["high_bp"] = top["high_bp"].map({0: "Non", 1: "Oui"})
        top = top.rename(columns={
            "risque_estime": "Risque", "age_group": "Âge",
            "gen_hlth": "Santé perçue", "high_bp": "Hypertension",
        })

        st.dataframe(
            top,
            hide_index=True,
            column_config={
                "Risque": st.column_config.ProgressColumn(
                    "Risque", format="%.1f %%", min_value=0.0, max_value=100.0,
                ),
            },
            height=260,
        )

# --- Export : CSV détaillé + synthèse PDF ---------------------------------

# Synthèse PDF (fonctionnalité F) : agrégats du lot pour un rapport partageable.
apercu_pdf = resultats.nlargest(8, "risque_estime")[
    ["risque_estime", "age_group", "gen_hlth", "high_bp"]
].copy()
apercu_pdf["risque_estime"] = (apercu_pdf["risque_estime"] * 100).map(
    lambda v: f"{v:.1f} %".replace(".", ",")
)
apercu_pdf["age_group"] = apercu_pdf["age_group"].map(codebook.AGE)
apercu_pdf["gen_hlth"] = apercu_pdf["gen_hlth"].map(codebook.SANTE_GENERALE)
apercu_pdf["high_bp"] = apercu_pdf["high_bp"].map({0: "Non", 1: "Oui"})
apercu_pdf.columns = ["Risque", "Age", "Sante", "HTA"]

pdf_lot = rapport_pdf.synthese_lot(
    nb_total=len(resultats),
    nb_signales=nb_signales,
    risque_moyen=float(resultats["risque_estime"].mean()),
    seuil=seuil,
    distribution=tranches,
    top_profils=apercu_pdf,
)

col_csv, col_pdf = st.columns(2)
col_csv.download_button(
    "Télécharger les résultats (CSV)",
    resultats.to_csv(index=False).encode("utf-8"),
    "profils_scores.csv", "text/csv",
    type="primary", icon=":material/download:",
)
col_pdf.download_button(
    "Télécharger la synthèse (PDF)",
    pdf_lot, "synthese_scoring.pdf", "application/pdf",
    icon=":material/picture_as_pdf:",
)

with st.expander("Voir les résultats complets"):
    st.dataframe(resultats, height=340)

st.warning(
    "**Usage pédagogique uniquement.** Ces estimations traduisent des "
    "associations statistiques, non des diagnostics. Elles ne doivent pas "
    "fonder de décision individuelle de santé.",
    icon=":material/warning:",
)
