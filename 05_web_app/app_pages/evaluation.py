"""Page d'évaluation individuelle du risque cardiovasculaire."""

import pandas as pd
import streamlit as st

from utils import codebook, format_fr
from utils.modele import (
    PREVALENCE_REFERENCE,
    contributions,
    charger_metadonnees,
    estimer,
    niveau_de_risque,
)

meta = charger_metadonnees()

st.caption(
    "Renseignez le profil ci-dessous. L'estimation repose sur les déclarations "
    "de 253 680 répondants à l'enquête de santé BRFSS 2015."
)

# --- Formulaire -----------------------------------------------------------
# st.form regroupe les saisies : l'application ne se recalcule qu'à la
# validation, au lieu de réagir à chaque champ modifié.

with st.form("profil"):
    st.markdown("##### Profil socio-démographique")
    c1, c2, c3, c4 = st.columns(4)
    age = c1.selectbox("Tranche d'âge", list(codebook.AGE),
                       format_func=codebook.AGE.get, index=8)
    sexe = c2.selectbox("Sexe", list(codebook.SEXE),
                        format_func=codebook.SEXE.get)
    education = c3.selectbox("Niveau d'études", list(codebook.EDUCATION),
                             format_func=codebook.EDUCATION.get, index=3)
    revenu = c4.selectbox("Revenu du foyer", list(codebook.REVENU),
                          format_func=codebook.REVENU.get, index=4)

    st.markdown("##### État de santé")
    c1, c2, c3 = st.columns(3)
    sante = c1.selectbox("Santé perçue", list(codebook.SANTE_GENERALE),
                         format_func=codebook.SANTE_GENERALE.get, index=2)
    imc = c2.number_input("Indice de masse corporelle", 12.0, 98.0, 27.0, 0.5,
                          help="Poids (kg) divisé par la taille au carré (m²)")
    diabete = c3.selectbox("Diabète", list(codebook.DIABETE),
                           format_func=codebook.DIABETE.get)

    c1, c2 = st.columns(2)
    jours_mental = c1.slider("Jours de mal-être mental (sur 30)", 0, 30, 0)
    jours_physique = c2.slider("Jours de mal-être physique (sur 30)", 0, 30, 0)

    st.markdown("##### Antécédents médicaux")
    c1, c2, c3, c4 = st.columns(4)
    hypertension = c1.checkbox("Hypertension")
    cholesterol = c2.checkbox("Cholestérol élevé")
    avc = c3.checkbox("Antécédent d'AVC")
    marche = c4.checkbox("Difficulté à marcher")

    st.markdown("##### Habitudes de vie")
    c1, c2, c3, c4 = st.columns(4)
    fumeur = c1.checkbox("Fumeur (ou ancien)")
    activite = c2.checkbox("Activité physique", value=True)
    fruits = c3.checkbox("Fruits quotidiens", value=True)
    legumes = c4.checkbox("Légumes quotidiens", value=True)

    st.markdown("##### Accès aux soins")
    c1, c2, c3 = st.columns(3)
    assurance = c1.checkbox("Couverture santé", value=True)
    renoncement = c2.checkbox("Renoncement aux soins (coût)")
    depistage = c3.checkbox("Cholestérol dosé (5 ans)", value=True)
    alcool = st.checkbox("Consommation d'alcool excessive")

    valide = st.form_submit_button("Estimer le risque", type="primary")

# --- Résultat -------------------------------------------------------------

if not valide:
    st.info(
        "Complétez le formulaire puis cliquez sur **Estimer le risque**.",
        icon=":material/info:",
    )
    st.stop()

profil = pd.DataFrame([{
    "bmi": imc,
    "ment_hlth_days": jours_mental,
    "phys_hlth_days": jours_physique,
    "gen_hlth": sante,
    "age_group": age,
    "education": education,
    "income": revenu,
    "diabetes": diabete,
    "high_bp": int(hypertension),
    "high_chol": int(cholesterol),
    "chol_check": int(depistage),
    "smoker": int(fumeur),
    "stroke": int(avc),
    "phys_activity": int(activite),
    "fruits": int(fruits),
    "veggies": int(legumes),
    "hvy_alcohol": int(alcool),
    "any_healthcare": int(assurance),
    "no_doc_cost": int(renoncement),
    "diff_walk": int(marche),
    "sex": sexe,
}])

probabilite = float(estimer(profil).iloc[0])
niveau, couleur = niveau_de_risque(probabilite)
ratio = probabilite / PREVALENCE_REFERENCE

st.divider()
st.markdown("### Résultat de l'estimation")

with st.container(horizontal=True):
    st.metric("Risque estimé", format_fr.pourcent(probabilite), border=True)
    st.metric("Niveau", niveau, border=True)
    st.metric(
        "Comparaison",
        f"× {format_fr.nombre(ratio)}",
        delta=format_fr.points(probabilite - PREVALENCE_REFERENCE),
        border=True,
        help="Rapport au risque moyen de la population de référence (9,4 %)",
    )

st.progress(min(probabilite, 1.0))
st.markdown(
    f"Ce profil présente un risque estimé de "
    f"**:{couleur}[{format_fr.pourcent(probabilite)}]**, soit "
    f"**{format_fr.nombre(ratio)} fois** le risque moyen de la population "
    f"({format_fr.pourcent(PREVALENCE_REFERENCE)})."
)

# --- Facteurs contributifs ------------------------------------------------

shap_valeurs = contributions(profil)

if not shap_valeurs.empty:
    st.markdown("### Ce qui pèse dans cette estimation")
    st.caption(
        "Contribution de chaque variable à l'écart par rapport au risque moyen. "
        "En rouge, ce qui augmente le risque ; en bleu, ce qui le diminue."
    )

    top = shap_valeurs.reindex(shap_valeurs.abs().sort_values(ascending=False).index)
    top = top.head(8).sort_values()

    # Deux séries distinctes pour que la couleur porte du sens : le rouge
    # signale ce qui pousse le risque à la hausse, le bleu ce qui l'atténue.
    tableau = pd.DataFrame({
        "Facteur": [codebook.libelle(v) for v in top.index],
        "Augmente le risque": [v if v > 0 else None for v in top.values],
        "Diminue le risque": [v if v <= 0 else None for v in top.values],
    }).set_index("Facteur")

    st.bar_chart(
        tableau,
        horizontal=True,
        color=["#C1443F", "#2E5C8A"],
        height=300,
    )

st.divider()
st.warning(
    "**Ceci n'est pas un diagnostic médical.** Cette estimation statistique "
    "traduit une association observée dans une population, à un instant donné. "
    "Elle ne prédit pas la survenue d'un accident cardiaque et ne remplace en "
    "aucun cas l'avis d'un professionnel de santé.",
    icon=":material/warning:",
)
