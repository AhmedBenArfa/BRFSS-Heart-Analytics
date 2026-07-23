# 05 — Application web

Application **Streamlit** d'estimation du risque cardiovasculaire, alimentée par
le pipeline entraîné dans `04_machine_learning/`.

## Pages

| Page | Contenu |
|---|---|
| **Évaluation du risque** | Formulaire → probabilité, niveau, **positionnement dans la population**, facteurs (SHAP), **simulateur « et si… »**, **conseils ciblés**, **bilan PDF téléchargeable**, historique de session |
| **Tableau de bord** | Vue population : risque par âge, distribution, les 4 profils du data mining, calibration |
| **Scoring par lot** | Import CSV → estimation de masse, distribution, export CSV et **synthèse PDF** |
| **Méthodologie** | Modèle, performances, seuil de décision, et limites |
| **Assistant** | FAQ conversationnelle : explique variables, valeurs et fonctionnalités, avec questions suggérées |

## Fonctionnalités clés

- **Simulateur « et si… »** — impact des changements modifiables (tabac, activité,
  poids, tension…) sur le risque, avec le total atteignable en les cumulant.
- **Positionnement** — comparaison au risque des personnes de même âge et sexe
  (percentile), à partir des données de référence embarquées.
- **Conseils** — recommandations éducatives générées selon les facteurs présents.
  Jamais des prescriptions : chaque conseil renvoie vers un professionnel.
- **Rapports PDF** — bilan individuel et synthèse de lot, générés à la volée avec
  les polices intégrées de fpdf2 (aucun fichier de police requis au déploiement).
- **Assistant** — FAQ à base de connaissances (`utils/faq.py`), **sans modèle de
  langage** : réponses curatées et déterministes, sans clé d'API ni risque de
  réponse inventée — adapté à un contexte de santé et à un déploiement gratuit.

## Structure

```
streamlit_app.py        point d'entrée et navigation
_build_reference.py     pré-calcule les données de référence (à relancer si le modèle change)
app_pages/              une page par vue (evaluation, population, lot, methodologie)
utils/
    modele.py           chargement (mis en cache) et estimation
    reference.py        données de référence (positionnement, dashboard)
    simulateur.py       scénarios « et si… »
    conseils.py         moteur de conseils
    rapport_pdf.py      génération des bilans PDF
    codebook.py         libellés BRFSS des champs
    format_fr.py        typographie française des nombres
models/                 modèles sérialisés + métadonnées
data_sample/            CSV d'exemple + données de référence (parquet, json)
lancer_app.bat          lanceur portable Windows (double-clic)
```

> Le dossier des pages s'appelle `app_pages/` et non `pages/` : ce dernier nom
> déclencherait l'ancienne découverte automatique de Streamlit et entrerait en
> conflit avec `st.navigation`.

## Les deux modèles

| Fichier | Rôle |
|---|---|
| `heart_model.joblib` | Modèle **calibré** — produit les probabilités affichées |
| `heart_model_base.joblib` | Pipeline **brut** — support de l'explication SHAP |

La calibration isotonique corrige l'échelle des probabilités, déformée par la
pondération des classes : sans elle, le modèle annonçait en moyenne 34,6 % de
risque là où la fréquence réelle est de 9,4 %. Étant monotone, elle ne change ni
le classement ni la hiérarchie des contributions — d'où le pipeline brut,
conservé pour SHAP.

## Exécution locale

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Déploiement

Prévu sur **Streamlit Community Cloud** : pointer sur ce dépôt, avec pour fichier
principal `05_web_app/streamlit_app.py`. Les modèles étant versionnés, aucune
étape supplémentaire n'est nécessaire.

> ⚠️ L'application fournit une **estimation statistique à visée pédagogique**.
> Elle ne constitue en aucun cas un diagnostic médical.
