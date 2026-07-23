"""Page d'évaluation individuelle du risque cardiovasculaire.

Le résultat est conservé dans st.session_state : il persiste ainsi lorsque
l'utilisateur télécharge le bilan PDF ou explore le simulateur, actions qui
provoquent un rerun sans nouvelle soumission du formulaire.
"""

import pandas as pd
import streamlit as st

from utils import codebook, conseils, format_fr, reference, simulateur
from utils import rapport_pdf
from utils.modele import (
    PREVALENCE_REFERENCE,
    charger_metadonnees,
    contributions,
    estimer,
    niveau_de_risque,
)

meta = charger_metadonnees()

st.caption(
    "Renseignez le profil ci-dessous. L'estimation repose sur les déclarations "
    "de 253 680 répondants à l'enquête de santé BRFSS 2015."
)

# --- Formulaire -----------------------------------------------------------

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

# --- Calcul à la soumission, stocké en session ----------------------------

if valide:
    profil = pd.DataFrame([{
        "bmi": imc, "ment_hlth_days": jours_mental,
        "phys_hlth_days": jours_physique, "gen_hlth": sante, "age_group": age,
        "education": education, "income": revenu, "diabetes": diabete,
        "high_bp": int(hypertension), "high_chol": int(cholesterol),
        "chol_check": int(depistage), "smoker": int(fumeur), "stroke": int(avc),
        "phys_activity": int(activite), "fruits": int(fruits),
        "veggies": int(legumes), "hvy_alcohol": int(alcool),
        "any_healthcare": int(assurance), "no_doc_cost": int(renoncement),
        "diff_walk": int(marche), "sex": sexe,
    }])
    probabilite = float(estimer(profil).iloc[0])

    st.session_state["eval_resultat"] = {
        "profil": profil,
        "probabilite": probabilite,
        "age": age, "sexe": sexe, "imc": imc, "sante": sante,
    }
    # Historique (fonctionnalité G) : on empile les estimations successives.
    historique = st.session_state.setdefault("eval_historique", [])
    historique.append({
        "Âge": codebook.AGE[age], "Sexe": codebook.SEXE[sexe],
        "IMC": imc, "Santé": codebook.SANTE_GENERALE[sante],
        "Risque": probabilite,
    })

if "eval_resultat" not in st.session_state:
    st.info(
        "Complétez le formulaire puis cliquez sur **Estimer le risque**.",
        icon=":material/info:",
    )
    st.stop()

# --- Restitution du dernier résultat --------------------------------------

res = st.session_state["eval_resultat"]
profil = res["profil"]
probabilite = res["probabilite"]
niveau, couleur = niveau_de_risque(probabilite)
ratio = probabilite / PREVALENCE_REFERENCE
position = reference.positionner(probabilite, res["age"], res["sexe"])

st.divider()
st.markdown("### Résultat de l'estimation")

with st.container(horizontal=True):
    st.metric("Risque estimé", format_fr.pourcent(probabilite), border=True)
    st.metric("Niveau", niveau, border=True)
    st.metric(
        "Comparaison", f"× {format_fr.nombre(ratio)}",
        delta=format_fr.points(probabilite - PREVALENCE_REFERENCE),
        border=True,
        help="Rapport au risque moyen de la population de référence (9,4 %)",
    )
    if position:
        st.metric(
            "Position", f"{position['percentile']:.0f}e centile", border=True,
            help="Parmi les personnes de même âge et sexe : part dont le risque "
                 "estimé est inférieur au vôtre",
        )

st.progress(min(probabilite, 1.0))
st.markdown(
    f"Ce profil présente un risque estimé de "
    f"**:{couleur}[{format_fr.pourcent(probabilite)}]**, soit "
    f"**{format_fr.nombre(ratio)} fois** le risque moyen de la population "
    f"({format_fr.pourcent(PREVALENCE_REFERENCE)})."
)

# --- D : positionnement dans la population --------------------------------

if position:
    moyenne_pairs = position["moyenne_pairs"]
    ecart = probabilite - moyenne_pairs
    comparatif = (
        "supérieur à" if ecart > 0.005
        else "inférieur à" if ecart < -0.005 else "comparable à"
    )
    st.markdown(
        f"Votre risque est **{comparatif}** la moyenne des personnes de même âge "
        f"et sexe ({format_fr.pourcent(moyenne_pairs)}). Vous vous situez au "
        f"**{position['percentile']:.0f}ᵉ centile** de ce groupe : "
        f"{position['percentile']:.0f} % d'entre elles ont un risque estimé "
        f"inférieur au vôtre."
    )

# --- Contributions (facteurs) ---------------------------------------------

shap_valeurs = contributions(profil)
if not shap_valeurs.empty:
    st.markdown("### Ce qui pèse dans cette estimation")
    st.caption(
        "Contribution de chaque variable à l'écart par rapport au risque moyen. "
        "En rouge, ce qui augmente le risque ; en bleu, ce qui le diminue."
    )
    top = shap_valeurs.reindex(
        shap_valeurs.abs().sort_values(ascending=False).index
    ).head(8).sort_values()
    tableau = pd.DataFrame({
        "Facteur": [codebook.libelle(v) for v in top.index],
        "Augmente le risque": [v if v > 0 else None for v in top.values],
        "Diminue le risque": [v if v <= 0 else None for v in top.values],
    }).set_index("Facteur")
    st.bar_chart(tableau, horizontal=True, color=["#C1443F", "#2E5C8A"],
                 height=300)

# --- B : simulateur « et si… » --------------------------------------------

scenarios = simulateur.scenarios(profil, probabilite)
if scenarios:
    st.markdown("### Simulateur : et si… ?")
    st.caption(
        "Impact estimé de changements sur lesquels il est possible d'agir. "
        "L'âge et le sexe, non modifiables, ne figurent pas ici."
    )

    combine = simulateur.scenario_combine(profil)
    if combine and (probabilite - combine["risque"]) > 0.005:
        gain = probabilite - combine["risque"]
        st.success(
            f"En cumulant l'ensemble de ces changements, le risque estimé "
            f"passerait de **{format_fr.pourcent(probabilite)}** à "
            f"**{format_fr.pourcent(combine['risque'])}** — une baisse de "
            f"**{format_fr.points(-gain).replace('-', '')}**.",
            icon=":material/trending_down:",
        )

    for s in scenarios:
        gain = -s["delta"]
        cols = st.columns([5, 2, 2])
        cols[0].markdown(f"{s['icone']} {s['libelle']}")
        cols[1].metric("Risque", format_fr.pourcent(s["risque"]),
                       label_visibility="collapsed")
        cols[2].markdown(
            f":green[**−{format_fr.points(gain).replace('+', '').replace('-', '')}**]"
            if gain > 0.0005 else "_effet négligeable_"
        )

# --- C : conseils ---------------------------------------------------------

liste_conseils = conseils.generer(profil)
st.markdown("### Conseils de prévention")
for icone, titre, message in liste_conseils:
    with st.container(border=True):
        st.markdown(f"**{icone} {titre}**")
        st.markdown(message)

# --- A : téléchargement du bilan PDF --------------------------------------

resume_profil = {
    "Tranche d'âge": codebook.AGE[res["age"]],
    "Sexe": codebook.SEXE[res["sexe"]],
    "Indice de masse corporelle": format_fr.nombre(res["imc"]),
    "Santé perçue": codebook.SANTE_GENERALE[res["sante"]],
}
pdf_octets = rapport_pdf.bilan_individuel(
    resume_profil, probabilite, niveau, ratio, position, shap_valeurs,
    liste_conseils, codebook.libelle,
)
st.download_button(
    "Télécharger le bilan (PDF)",
    pdf_octets,
    "bilan_risque_cardiaque.pdf",
    "application/pdf",
    type="primary",
    icon=":material/download:",
)

# --- G : historique de session --------------------------------------------

historique = st.session_state.get("eval_historique", [])
if len(historique) > 1:
    with st.expander(
        f":material/history: Comparer mes {len(historique)} estimations"
    ):
        hist = pd.DataFrame(historique)
        hist["Risque"] = hist["Risque"] * 100  # la barre formate la valeur brute
        st.dataframe(
            hist, hide_index=True,
            column_config={
                "Risque": st.column_config.ProgressColumn(
                    "Risque estimé", format="%.1f %%",
                    min_value=0.0, max_value=100.0,
                ),
            },
        )
        if st.button("Effacer l'historique", icon=":material/delete:"):
            st.session_state["eval_historique"] = []
            st.rerun()

st.divider()
st.warning(
    "**Ceci n'est pas un diagnostic médical.** Cette estimation statistique "
    "traduit une association observée dans une population, à un instant donné. "
    "Elle ne prédit pas la survenue d'un accident cardiaque et ne remplace en "
    "aucun cas l'avis d'un professionnel de santé.",
    icon=":material/warning:",
)
