"""Assistant : répond aux questions sur les variables, les valeurs et l'outil.

Assistant à base de connaissances (pas de modèle de langage) : réponses curatées,
exactes et déterministes — adapté à un contexte de santé et déployable sans clé
d'API. Voir utils/faq.py pour la base.
"""

import streamlit as st

from utils import faq

st.caption(
    "Posez une question sur les variables (cholestérol, IMC…), les valeurs à "
    "saisir, ou le fonctionnement de l'outil. Réponses issues d'une base "
    "documentaire vérifiée."
)

# --- Historique de conversation -------------------------------------------

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [{
        "role": "assistant",
        "content": (
            "Bonjour 👋 Je peux expliquer les variables du formulaire, ce que "
            "signifient les résultats, et comment utiliser l'application. "
            "Choisissez une suggestion ci-dessous ou posez votre question."
        ),
        "liees": faq.SUGGESTIONS_INITIALES,
    }]


def traiter(question: str) -> None:
    """Ajoute la question de l'utilisateur et la réponse de l'assistant."""
    st.session_state.chat_messages.append({"role": "user", "content": question})
    resultat = faq.repondre(question)
    st.session_state.chat_messages.append({
        "role": "assistant",
        "content": resultat["reponse"],
        "liees": resultat.get("liees", []),
    })


# Une suggestion cliquée est traitée avant le réaffichage.
if "chat_suggestion" in st.session_state:
    suggestion = st.session_state.pop("chat_suggestion")
    entree = faq.entree(suggestion)
    if entree:
        traiter(entree["question"])

# --- Affichage des messages -----------------------------------------------

for i, msg in enumerate(st.session_state.chat_messages):
    avatar = ":material/robot_2:" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

        # Suggestions liées, uniquement sous le dernier message de l'assistant.
        liees = msg.get("liees", [])
        dernier = i == len(st.session_state.chat_messages) - 1
        if liees and msg["role"] == "assistant" and dernier:
            st.caption("Questions suggérées :")
            cols = st.columns(min(len(liees), 3))
            for j, ident in enumerate(liees):
                entree = faq.entree(ident)
                if not entree:
                    continue
                if cols[j % len(cols)].button(
                    entree["question"], key=f"sugg_{i}_{ident}",
                    width="stretch",
                ):
                    st.session_state["chat_suggestion"] = ident
                    st.rerun()

# --- Saisie libre ---------------------------------------------------------

if question := st.chat_input("Posez votre question…"):
    traiter(question)
    st.rerun()

# --- Réinitialisation ------------------------------------------------------

if len(st.session_state.chat_messages) > 1:
    if st.button("Nouvelle conversation", icon=":material/refresh:"):
        del st.session_state.chat_messages
        st.rerun()

st.divider()
st.caption(
    "Cet assistant fournit des informations générales et éducatives. Il ne "
    "remplace pas l'avis d'un professionnel de santé."
)
