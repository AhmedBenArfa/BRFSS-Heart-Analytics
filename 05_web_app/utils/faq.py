"""Base de connaissances de l'assistant.

Assistant **à base de règles**, sans modèle de langage : les réponses sont
curatées, exactes et déterministes — un choix délibéré pour un outil de santé
(aucun risque de réponse inventée) et pour un déploiement sans clé d'API.

Chaque entrée : un identifiant, la question canonique, des mots-clés de
correspondance, une réponse (Markdown) et des identifiants de questions liées.
Le moteur `repondre()` associe une saisie libre à la meilleure entrée.
"""

from __future__ import annotations

import re
import unicodedata

# --- Base de connaissances -------------------------------------------------

FAQ: list[dict] = [
    # ===================== Variables de santé =====================
    {
        "id": "cholesterol",
        "categorie": "Variables",
        "question": "C'est quoi le cholestérol élevé ?",
        "cles": ["cholesterol", "cholestérol", "hdl", "ldl", "lipides", "gras"],
        "reponse": (
            "Le **cholestérol** est une graisse présente dans le sang. En excès, "
            "il se dépose sur les parois des artères et les rétrécit "
            "(athérosclérose), ce qui gêne la circulation vers le cœur.\n\n"
            "Dans le formulaire, cochez **« Cholestérol élevé »** si un médecin "
            "vous a dit que votre cholestérol était trop haut. C'est l'un des "
            "facteurs de risque cardiovasculaire les plus importants.\n\n"
            "_Il se contrôle par l'alimentation, l'activité physique et, si "
            "nécessaire, un traitement — parlez-en à votre médecin._"
        ),
        "liees": ["hypertension", "reduire_risque"],
    },
    {
        "id": "hypertension",
        "categorie": "Variables",
        "question": "Qu'est-ce que l'hypertension ?",
        "cles": ["hypertension", "tension", "pression", "arterielle", "hta",
                 "high bp"],
        "reponse": (
            "L'**hypertension artérielle** est une pression du sang trop élevée "
            "dans les artères, de façon durable. Le cœur doit fournir plus "
            "d'effort, ce qui augmente le risque d'infarctus et d'AVC.\n\n"
            "Cochez **« Hypertension »** si un professionnel de santé a "
            "diagnostiqué une tension trop haute. C'est, avec l'âge, l'un des "
            "facteurs les plus déterminants du modèle.\n\n"
            "_Elle est souvent silencieuse : seul un contrôle régulier permet de "
            "la détecter._"
        ),
        "liees": ["cholesterol", "reduire_risque"],
    },
    {
        "id": "imc",
        "categorie": "Variables",
        "question": "C'est quoi l'IMC et comment le calculer ?",
        "cles": ["imc", "indice", "masse", "corporelle", "poids", "bmi",
                 "obesite", "surpoids"],
        "reponse": (
            "L'**indice de masse corporelle (IMC)** rapporte le poids à la taille. "
            "On le calcule ainsi :\n\n"
            "**IMC = poids (kg) ÷ taille (m)²**\n\n"
            "Exemple : 70 kg pour 1,75 m → 70 ÷ (1,75 × 1,75) ≈ **22,9**.\n\n"
            "Repères de l'OMS : moins de 18,5 = insuffisance pondérale · "
            "18,5 à 25 = normal · 25 à 30 = surpoids · 30 et plus = obésité.\n\n"
            "_Fait intéressant du projet : le risque cardiaque suit une « courbe "
            "en J » — les personnes très maigres sont aussi un peu plus exposées "
            "que les personnes de corpulence normale._"
        ),
        "liees": ["reduire_risque", "courbe_j"],
    },
    {
        "id": "diabete",
        "categorie": "Variables",
        "question": "Pourquoi le diabète compte-t-il ?",
        "cles": ["diabete", "diabète", "glycemie", "sucre", "prediabete",
                 "insuline"],
        "reponse": (
            "Le **diabète** est un excès de sucre (glucose) dans le sang. À la "
            "longue, il abîme les vaisseaux sanguins et multiplie le risque "
            "cardiovasculaire.\n\n"
            "Trois choix dans le formulaire :\n"
            "- **Non** : pas de diabète\n"
            "- **Prédiabète** : glycémie élevée, avant le seuil du diabète\n"
            "- **Diabète** : diabète diagnostiqué\n\n"
            "_Un bon contrôle de la glycémie réduit nettement le risque._"
        ),
        "liees": ["reduire_risque", "hypertension"],
    },
    {
        "id": "tabac",
        "categorie": "Variables",
        "question": "Quels sont les risques du tabagisme ?",
        "cles": ["tabac", "tabagisme", "fumer", "fumeur", "cigarette",
                 "smoker", "nicotine"],
        "reponse": (
            "Le **tabac** endommage les artères, favorise les caillots et réduit "
            "l'oxygène apporté au cœur. C'est l'un des principaux facteurs de "
            "risque évitables.\n\n"
            "Cochez **« Fumeur (ou ancien) »** si vous avez fumé au moins 100 "
            "cigarettes dans votre vie.\n\n"
            "**Bonne nouvelle** : l'arrêt du tabac fait baisser le risque "
            "cardiovasculaire dès les premières semaines. Testez son effet dans le "
            "**simulateur « et si… »** de la page d'évaluation."
        ),
        "liees": ["simulateur", "reduire_risque"],
    },
    {
        "id": "sante_percue",
        "categorie": "Variables",
        "question": "Que signifie « santé perçue » ?",
        "cles": ["sante", "santé", "percue", "perçue", "generale", "genhlth",
                 "etat"],
        "reponse": (
            "La **santé perçue** est votre propre appréciation de votre état de "
            "santé général, de **Excellente** à **Mauvaise**.\n\n"
            "Bien que subjective, c'est une variable étonnamment puissante : elle "
            "résume beaucoup d'informations (fatigue, douleurs, moral, maladies…). "
            "Dans l'analyse, les personnes se déclarant en mauvaise santé sont "
            "environ dix fois plus touchées que celles se disant en excellente "
            "santé."
        ),
        "liees": ["facteurs", "score"],
    },
    {
        "id": "mal_etre",
        "categorie": "Variables",
        "question": "Que sont les « jours de mal-être » ?",
        "cles": ["mal-etre", "mal etre", "jours", "mental", "physique",
                 "menthlth", "physhlth", "moral"],
        "reponse": (
            "Deux curseurs mesurent, sur les **30 derniers jours**, le nombre de "
            "jours où votre santé **mentale** (stress, déprime…) ou **physique** "
            "(douleurs, maladie…) n'a pas été bonne.\n\n"
            "0 = aucun mauvais jour, 30 = tous les jours. Un nombre élevé de jours "
            "de mal-être physique est associé à un risque plus important."
        ),
        "liees": ["sante_percue"],
    },
    {
        "id": "acces_soins",
        "categorie": "Variables",
        "question": "Couverture santé et renoncement aux soins ?",
        "cles": ["couverture", "assurance", "soins", "medecin", "renoncement",
                 "cout", "acces", "assure"],
        "reponse": (
            "Deux cases décrivent votre accès aux soins :\n"
            "- **Couverture santé** : disposez-vous d'une assurance maladie ?\n"
            "- **Renoncement aux soins (coût)** : avez-vous déjà renoncé à voir un "
            "médecin pour des raisons financières ?\n\n"
            "Ces variables comptent : l'analyse du projet a même identifié un "
            "groupe de population **défini par l'absence de couverture santé** — "
            "l'accès aux soins influence la santé cardiaque."
        ),
        "liees": ["profils", "tableau_bord"],
    },
    # ===================== Fonctionnalités =====================
    {
        "id": "simulateur",
        "categorie": "Fonctionnalités",
        "question": "Comment utiliser le simulateur « et si… » ?",
        "cles": ["simulateur", "et si", "scenario", "changement", "ameliorer",
                 "what if"],
        "reponse": (
            "Le **simulateur « et si… »** montre l'effet de changements sur "
            "lesquels vous pouvez agir.\n\n"
            "**Comment l'utiliser** : remplissez le formulaire (en cochant vos "
            "facteurs de risque), cliquez sur **Estimer le risque**, puis faites "
            "défiler jusqu'à la section « Simulateur ».\n\n"
            "Pour chaque facteur modifiable présent (tabac, poids, tension…), il "
            "affiche votre risque **s'il était corrigé**, et l'encadré vert donne "
            "le risque atteignable en **cumulant tous** les changements.\n\n"
            "_L'âge et le sexe n'y figurent pas : on ne peut pas les modifier._"
        ),
        "liees": ["reduire_risque", "score"],
    },
    {
        "id": "score",
        "categorie": "Fonctionnalités",
        "question": "Que signifie le pourcentage de risque ?",
        "cles": ["score", "pourcentage", "risque estime", "probabilite",
                 "resultat", "chiffre", "signifie"],
        "reponse": (
            "Le **risque estimé** est la probabilité, pour une personne au profil "
            "que vous avez saisi, de présenter une maladie ou un accident "
            "cardiaque — d'après 253 680 répondants à l'enquête BRFSS 2015.\n\n"
            "Exemple : **12 %** signifie qu'environ 12 personnes sur 100 partageant "
            "ce profil sont concernées. La moyenne de la population est de "
            "**9,4 %** : le résultat vous situe par rapport à cette référence.\n\n"
            "⚠️ C'est une **association statistique**, pas un diagnostic ni une "
            "prédiction de ce qui vous arrivera personnellement."
        ),
        "liees": ["niveau", "positionnement", "diagnostic"],
    },
    {
        "id": "niveau",
        "categorie": "Fonctionnalités",
        "question": "Comment sont définis les niveaux de risque ?",
        "cles": ["niveau", "faible", "eleve", "élevé", "moyen", "couleur"],
        "reponse": (
            "Le **niveau** traduit le risque par rapport à la moyenne de la "
            "population (9,4 %) :\n\n"
            "- **Faible** : moins de la moitié du risque moyen\n"
            "- **Proche de la moyenne** : autour de 9,4 %\n"
            "- **Élevé** : environ 1,5 à 3 fois la moyenne\n"
            "- **Très élevé** : plus de 3 fois la moyenne\n\n"
            "C'est une lecture plus parlante que le pourcentage seul."
        ),
        "liees": ["score", "positionnement"],
    },
    {
        "id": "positionnement",
        "categorie": "Fonctionnalités",
        "question": "Qu'est-ce que le positionnement / le centile ?",
        "cles": ["positionnement", "centile", "percentile", "pairs", "position",
                 "comparaison", "moyenne"],
        "reponse": (
            "Le **positionnement** vous compare aux personnes de **même âge et "
            "même sexe**. Le **centile** indique la part d'entre elles dont le "
            "risque estimé est inférieur au vôtre.\n\n"
            "Exemple : au **80ᵉ centile**, votre risque est supérieur à celui de "
            "80 % des personnes de votre âge et sexe. C'est une façon de savoir si "
            "vous êtes plutôt bien ou mal placé **à âge égal** — ce que le "
            "pourcentage brut ne dit pas (le risque augmente naturellement avec "
            "l'âge)."
        ),
        "liees": ["score", "tableau_bord"],
    },
    {
        "id": "scoring_lot",
        "categorie": "Fonctionnalités",
        "question": "À quoi sert le scoring par lot ?",
        "cles": ["lot", "batch", "csv", "fichier", "masse", "plusieurs",
                 "importer"],
        "reponse": (
            "La page **Scoring par lot** estime le risque pour **plusieurs "
            "personnes à la fois**. Vous importez un fichier CSV (une ligne par "
            "personne, avec les 21 variables), et l'application calcule le risque "
            "de chacune.\n\n"
            "Vous obtenez la distribution des risques, les profils les plus "
            "exposés, et pouvez exporter les résultats en **CSV** ou une "
            "**synthèse PDF**. Un **gabarit vide** est téléchargeable sur la page."
        ),
        "liees": ["score", "pdf"],
    },
    {
        "id": "pdf",
        "categorie": "Fonctionnalités",
        "question": "Comment obtenir un bilan PDF ?",
        "cles": ["pdf", "telecharger", "bilan", "rapport", "imprimer",
                 "document"],
        "reponse": (
            "Après une estimation, un bouton **« Télécharger le bilan (PDF) »** "
            "apparaît en bas de la page d'évaluation. Le document reprend votre "
            "profil, le risque estimé, les facteurs influents, les conseils et "
            "l'avertissement — pratique pour le garder ou en discuter avec un "
            "professionnel de santé.\n\n"
            "La page **Scoring par lot** propose de son côté une **synthèse PDF** "
            "de l'ensemble analysé."
        ),
        "liees": ["score", "scoring_lot"],
    },
    {
        "id": "tableau_bord",
        "categorie": "Fonctionnalités",
        "question": "Que montre le tableau de bord ?",
        "cles": ["tableau", "bord", "dashboard", "population", "graphique",
                 "tendance"],
        "reponse": (
            "Le **Tableau de bord** présente la population de référence : risque "
            "moyen par tranche d'âge, distribution des risques, et les **quatre "
            "profils de population** identifiés par l'analyse.\n\n"
            "Il inclut aussi un graphique « le modèle est-il bien calibré ? » qui "
            "compare, pour chaque niveau de risque estimé, la fréquence réellement "
            "observée."
        ),
        "liees": ["profils", "positionnement"],
    },
    # ===================== Général =====================
    {
        "id": "diagnostic",
        "categorie": "Général",
        "question": "Est-ce un diagnostic médical ?",
        "cles": ["diagnostic", "medical", "confiance", "vrai", "certain",
                 "malade", "serieux"],
        "reponse": (
            "**Non, absolument pas.** Cet outil fournit une **estimation "
            "statistique à visée pédagogique**, fondée sur des associations "
            "observées dans une population.\n\n"
            "Il ne pose aucun diagnostic, ne prédit pas ce qui vous arrivera, et "
            "**ne remplace jamais l'avis d'un professionnel de santé**. Si vous "
            "avez des inquiétudes, consultez un médecin."
        ),
        "liees": ["score", "donnees"],
    },
    {
        "id": "donnees",
        "categorie": "Général",
        "question": "D'où viennent les données ?",
        "cles": ["donnees", "données", "source", "brfss", "cdc", "origine",
                 "provenance", "echantillon"],
        "reponse": (
            "Les données proviennent du **BRFSS 2015** (*Behavioral Risk Factor "
            "Surveillance System*), une grande enquête de santé menée par les "
            "**CDC** aux États-Unis. Elle regroupe **253 680 répondants** et 21 "
            "variables déclaratives.\n\n"
            "Ce sont des **données publiques**. Comme la population est américaine "
            "et l'enquête date de 2015, les résultats reflètent ce contexte "
            "particulier."
        ),
        "liees": ["diagnostic", "fiabilite"],
    },
    {
        "id": "fiabilite",
        "categorie": "Général",
        "question": "Le modèle est-il fiable ?",
        "cles": ["fiabilite", "fiable", "performance", "precision", "auc",
                 "qualite", "marche"],
        "reponse": (
            "Le modèle atteint un **ROC-AUC d'environ 0,85** : il classe "
            "correctement les personnes par niveau de risque dans une large "
            "majorité des cas. Ses probabilités sont **calibrées** (un « 10 % » "
            "correspond bien à une fréquence réelle de 10 %).\n\n"
            "Mais 21 variables ne suffisent pas à tout expliquer : la génétique, "
            "les antécédents familiaux ou l'environnement n'y figurent pas. Le "
            "résultat est une **tendance**, pas une certitude individuelle."
        ),
        "liees": ["diagnostic", "score"],
    },
    {
        "id": "reduire_risque",
        "categorie": "Général",
        "question": "Comment réduire mon risque ?",
        "cles": ["reduire", "réduire", "baisser", "ameliorer", "diminuer",
                 "prevention", "conseils", "faire"],
        "reponse": (
            "Plusieurs leviers **modifiables** sont associés à un risque plus "
            "faible :\n\n"
            "- Arrêter de fumer\n"
            "- Pratiquer une activité physique régulière\n"
            "- Maintenir un poids sain\n"
            "- Contrôler tension, cholestérol et glycémie\n"
            "- Manger fruits et légumes chaque jour\n\n"
            "Le **simulateur « et si… »** de la page d'évaluation chiffre l'effet "
            "de chacun de ces changements sur **votre** profil.\n\n"
            "_Ces informations sont générales : pour un plan adapté, consultez un "
            "professionnel de santé._"
        ),
        "liees": ["simulateur", "diagnostic"],
    },
    {
        "id": "profils",
        "categorie": "Général",
        "question": "Quels sont les quatre profils de population ?",
        "cles": ["profils", "profil", "groupes", "clustering", "types",
                 "categories", "population"],
        "reponse": (
            "Une analyse non supervisée (clustering) a dégagé **quatre profils** "
            "de population, du moins au plus exposé :\n\n"
            "1. **Jeunes actifs en bonne santé** (~2 %)\n"
            "2. **Adultes non assurés** (~7 %) — définis par l'absence de "
            "couverture santé\n"
            "3. **Seniors autonomes** (~13 %) — âgés mais en forme\n"
            "4. **Seniors multi-morbides fragiles** (~24 %)\n\n"
            "Détails et graphiques sur la page **Tableau de bord**."
        ),
        "liees": ["tableau_bord", "acces_soins"],
    },
]

# Questions mises en avant au démarrage de l'assistant.
SUGGESTIONS_INITIALES = [
    "cholesterol", "tabac", "simulateur", "score", "diagnostic", "reduire_risque",
]

_PAR_ID = {e["id"]: e for e in FAQ}


def _normaliser(texte: str) -> str:
    """Minuscules, sans accents, sans ponctuation — pour la correspondance."""
    texte = unicodedata.normalize("NFD", texte.lower())
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]", " ", texte)


def entree(identifiant: str) -> dict | None:
    return _PAR_ID.get(identifiant)


def repondre(question: str) -> dict:
    """Associe une saisie libre à la meilleure entrée de la base.

    Renvoie un dict {trouve, reponse, question, liees}. Si rien ne correspond
    avec assez de confiance, `trouve` est False et des suggestions sont fournies.
    """
    texte = _normaliser(question)
    mots = set(texte.split())

    meilleur, meilleur_score = None, 0
    for e in FAQ:
        score = 0
        # Déduplication : « sante » et « santé » normalisent vers la même clé et
        # ne doivent compter qu'une fois.
        cles_normalisees = {_normaliser(cle) for cle in e["cles"]}
        for cle_norm in cles_normalisees:
            if " " in cle_norm:  # expression : correspondance exacte, poids fort
                if cle_norm in texte:
                    score += 3
            elif cle_norm in mots:  # mot entier
                score += 2
            elif len(cle_norm) >= 5 and cle_norm in texte:  # sous-chaîne longue
                score += 1
        if score > meilleur_score:
            meilleur, meilleur_score = e, score

    if meilleur is None or meilleur_score < 2:
        return {
            "trouve": False,
            "reponse": (
                "Je n'ai pas de réponse précise à cette question. Voici quelques "
                "sujets que je maîtrise — cliquez ou reformulez avec un mot-clé "
                "(cholestérol, tabac, IMC, simulateur, risque…)."
            ),
            "liees": SUGGESTIONS_INITIALES[:4],
        }

    return {
        "trouve": True,
        "reponse": meilleur["reponse"],
        "question": meilleur["question"],
        "liees": meilleur.get("liees", []),
    }
