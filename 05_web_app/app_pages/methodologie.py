"""Page de méthodologie : d'où vient le modèle, ce qu'il vaut, ses limites."""

import streamlit as st

from utils import format_fr
from utils.modele import PREVALENCE_REFERENCE, charger_metadonnees

meta = charger_metadonnees()
perf = meta["performances_test"]

st.caption("Comment cette estimation est produite, et ce qu'elle ne dit pas.")

# --- Le modèle ------------------------------------------------------------

st.markdown("### Le modèle")

with st.container(horizontal=True):
    st.metric("Algorithme", meta["modele"], border=True)
    st.metric("ROC-AUC", format_fr.nombre(perf["roc_auc"], 3), border=True,
              help="Capacité à ordonner les risques (0,5 = hasard, 1 = parfait)")
    st.metric("PR-AUC", format_fr.nombre(perf["pr_auc"], 3), border=True,
              help=f"Référence du hasard : {format_fr.nombre(PREVALENCE_REFERENCE, 3)}")
    st.metric("Rappel", format_fr.pourcent(perf["rappel"], 0), border=True,
              help="Part des personnes atteintes effectivement détectées")
    st.metric("Précision", format_fr.pourcent(perf["precision"], 0), border=True,
              help="Part de personnes réellement atteintes parmi celles signalées")

st.markdown(
    f"""
Le modèle a été sélectionné parmi **six familles d'algorithmes** (régression
logistique, k plus proches voisins, arbre de décision, forêt aléatoire, XGBoost,
SVM linéaire), chacune optimisée par recherche sur grille en validation croisée.
Il a été entraîné sur **{format_fr.entier(meta['n_entrainement'])} profils** et
évalué une seule fois sur **{format_fr.entier(meta['n_test'])} profils** jamais
utilisés pendant la sélection.
"""
)

# --- Le seuil -------------------------------------------------------------

st.markdown("### Le seuil de décision")

st.markdown(
    f"""
Le modèle produit une **probabilité continue**. Pour signaler un profil, il faut
un seuil — et celui par défaut (50 %) n'a aucune pertinence lorsque seulement
{format_fr.pourcent(PREVALENCE_REFERENCE)} de la population est concernée.

Le seuil retenu est **{format_fr.nombre(meta['seuil_decision'], 3)}**, choisi pour
atteindre un rappel d'environ **{format_fr.pourcent(meta['rappel_cible'], 0)}**. Ce choix assume un arbitrage :
en santé, ne pas repérer une personne à risque coûte plus cher que recommander
une vérification inutile. La contrepartie est une précision de
**{format_fr.pourcent(perf['precision'], 0)}** : parmi les profils signalés, une minorité seulement
sera effectivement concernée.
"""
)

st.info(
    "Choisir le modèle et choisir le seuil sont **deux décisions distinctes**. "
    "Le modèle a été sélectionné sur sa capacité à ordonner les risques "
    "(indépendamment de tout seuil) ; le seuil a été fixé ensuite, selon le coût "
    "relatif des erreurs.",
    icon=":material/lightbulb:",
)

# --- Les données ----------------------------------------------------------

st.markdown("### Les données")

st.markdown(
    """
**Source** : *Behavioral Risk Factor Surveillance System* (BRFSS 2015), enquête
téléphonique annuelle des *Centers for Disease Control and Prevention* (CDC)
aux États-Unis. 253 680 répondants, 21 variables déclaratives.

Le jeu de données est **public**, et versionné avec le projet pour garantir la
reproductibilité complète de la chaîne d'analyse.
"""
)

# --- Limites --------------------------------------------------------------

st.markdown("### Limites — à lire avant toute interprétation")

st.error(
    "**Ceci n'est pas un outil de diagnostic.** L'estimation produite est une "
    "association statistique observée dans une population, jamais un avis "
    "médical individuel.",
    icon=":material/warning:",
)

with st.container(border=True):
    st.markdown("**Association, et non causalité ni prédiction**")
    st.markdown(
        "Les variables explicatives ont été déclarées **au même moment** que la "
        "maladie, lors d'un unique entretien. Le modèle ne peut donc établir ni "
        "un lien de cause à effet, ni une prédiction dans le temps : il décrit "
        "un profil, il n'annonce pas un événement futur."
    )

with st.container(border=True):
    st.markdown("**Données auto-déclarées**")
    st.markdown(
        "Tout repose sur les déclarations des répondants, avec les biais que "
        "cela suppose : mémoire imparfaite, désirabilité sociale, pathologies "
        "non diagnostiquées donc non déclarées."
    )

with st.container(border=True):
    st.markdown("**Une part du risque reste inexplicable**")
    st.markdown(
        "Vingt et une variables ne suffisent pas à décrire un état de santé. "
        "Génétique, antécédents familiaux, environnement et qualité du suivi "
        "médical n'y figurent pas. Des personnes au profil déclaré identique "
        "présentent parfois des états de santé opposés."
    )

with st.container(border=True):
    st.markdown("**Population américaine de 2015**")
    st.markdown(
        "Le modèle reflète une population et une époque précises. Sa "
        "transposition à un autre contexte demanderait une revalidation."
    )

st.divider()
st.caption(
    "Projet BRFSS Heart Analytics — Ahmed Ben Arfa · "
    "Code et documentation : github.com/AhmedBenArfa/BRFSS-Heart-Analytics"
)
