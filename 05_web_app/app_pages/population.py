"""Tableau de bord population : où se situe un individu dans le paysage BRFSS.

Reprend les découvertes de l'analyse exploratoire et du data mining, à partir des
données de référence embarquées.
"""

import pandas as pd
import streamlit as st

from utils import codebook, format_fr, reference

agregats = reference.charger_agregats()
echantillon = reference.charger_echantillon()

if not agregats or echantillon.empty:
    st.warning(
        "Données de référence indisponibles. Exécutez `python _build_reference.py` "
        "dans le dossier de l'application.",
        icon=":material/warning:",
    )
    st.stop()

st.caption(
    "Vue d'ensemble de la population de référence (BRFSS 2015) et des grands "
    "profils identifiés par l'analyse."
)

# --- Indicateurs globaux --------------------------------------------------

with st.container(horizontal=True):
    st.metric("Population étudiée",
              format_fr.entier(agregats["n_population_totale"]), border=True)
    st.metric("Prévalence réelle",
              format_fr.pourcent(agregats["prevalence_reelle_pct"] / 100),
              border=True, help="Part réellement atteinte dans la population")
    st.metric("Profils de population", "4", border=True,
              help="Groupes identifiés par clustering non supervisé")

# --- Risque par âge et par sexe -------------------------------------------

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("**Risque moyen estimé par tranche d'âge**")
        # Series indexée par le libellé d'âge, dans l'ordre du codebook.
        par_age = pd.Series(
            {codebook.AGE[int(a)]: v
             for a, v in agregats["risque_moyen_par_age"].items()},
            name="Risque moyen (%)",
        )
        st.bar_chart(par_age, color="#C1443F", height=280)

with col2:
    with st.container(border=True):
        st.markdown("**Distribution des risques dans la population**")
        tranches = pd.cut(
            echantillon["risque"],
            bins=[0, 0.05, 0.10, 0.20, 0.40, 1.0],
            labels=["< 5 %", "5-10 %", "10-20 %", "20-40 %", "> 40 %"],
        ).value_counts().sort_index()
        st.bar_chart(tranches, color="#2E5C8A", height=280)

# --- Les quatre profils ---------------------------------------------------

st.markdown("### Les quatre profils de population")
st.caption(
    "Groupes obtenus par clustering (k-means) sur les seules variables de santé, "
    "sans utiliser la maladie. Leur taux de maladie n'est mesuré qu'ensuite."
)

profils = sorted(agregats["profils"], key=lambda p: p["taux_maladie_pct"])
colonnes = st.columns(len(profils))
couleurs_niveau = ["green", "blue", "orange", "red"]

for col, profil, couleur in zip(colonnes, profils, couleurs_niveau):
    with col:
        with st.container(border=True):
            st.markdown(f"**{profil['nom']}**")
            st.markdown(
                f":{couleur}[**{format_fr.pourcent(profil['taux_maladie_pct'] / 100, 0)}** "
                "atteints]"
            )
            st.caption(
                f"{profil['part_pct']:.0f} % de la population · "
                f"IMC moyen {format_fr.nombre(profil['imc_moyen'])}"
            )
            if profil["sans_couverture_pct"] > 50:
                st.caption(
                    f":orange[{profil['sans_couverture_pct']:.0f} % sans "
                    "couverture santé]"
                )

st.info(
    "**À retenir** : le clustering distingue deux populations âgées que l'âge "
    "seul confondrait — les seniors autonomes et les seniors fragiles. Ce qui "
    "les sépare tient à la mobilité et au cumul de pathologies, pas à l'âge. Il "
    "isole aussi un groupe défini par l'accès aux soins (les non-assurés).",
    icon=":material/lightbulb:",
)

# --- Risque estimé vs réalité ---------------------------------------------

with st.container(border=True):
    st.markdown("**Le modèle est-il bien calibré ?**")
    st.caption(
        "Pour chaque tranche de risque estimé, part réellement atteinte dans la "
        "population de référence. Une bonne calibration aligne les deux."
    )
    ech = echantillon.copy()
    ech["tranche"] = pd.cut(
        ech["risque"], bins=[0, 0.05, 0.10, 0.20, 0.40, 1.0],
        labels=["< 5 %", "5-10 %", "10-20 %", "20-40 %", "> 40 %"],
    )
    calib = ech.groupby("tranche", observed=True).agg(
        risque_estime=("risque", "mean"),
        atteints_reels=("heart_disease", "mean"),
    ) * 100
    calib.columns = ["Risque estimé moyen (%)", "Atteints réels (%)"]
    # Barres côte à côte (non empilées) : les deux séries doivent coïncider si
    # le modèle est bien calibré.
    st.bar_chart(calib, height=280, color=["#C1443F", "#2E5C8A"], stack=False)

st.divider()
st.caption(
    "Source : BRFSS 2015, CDC — données publiques. Estimations produites par le "
    "modèle calibré du projet."
)
