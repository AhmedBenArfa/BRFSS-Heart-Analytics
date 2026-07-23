"""BRFSS Heart Analytics — application d'estimation du risque cardiovasculaire.

Point d'entrée : configure la page et assemble la navigation.

Lancement :
    streamlit run streamlit_app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Risque cardiovasculaire — BRFSS",
    page_icon=":material/cardiology:",
    layout="wide",
)

pages = [
    st.Page(
        "app_pages/evaluation.py",
        title="Évaluation du risque",
        icon=":material/monitor_heart:",
        default=True,
    ),
    st.Page(
        "app_pages/population.py",
        title="Tableau de bord",
        icon=":material/bar_chart:",
    ),
    st.Page(
        "app_pages/lot.py",
        title="Scoring par lot",
        icon=":material/table_view:",
    ),
    st.Page(
        "app_pages/methodologie.py",
        title="Méthodologie",
        icon=":material/science:",
    ),
    st.Page(
        "app_pages/assistant.py",
        title="Assistant",
        icon=":material/robot_2:",
    ),
]

page = st.navigation(pages, position="top")

# Titre commun à toutes les pages : elles n'appellent donc pas st.title.
st.title(f"{page.icon} {page.title}")

page.run()
