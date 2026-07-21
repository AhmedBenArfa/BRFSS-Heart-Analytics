# 05 — Application web

Application **Streamlit** d'estimation du risque cardiovasculaire, alimentée par
le pipeline entraîné dans `04_machine_learning/`.

## Pages

| Page | Contenu |
|---|---|
| **Évaluation du risque** | Formulaire de profil → probabilité estimée, niveau, facteurs contributifs (SHAP) |
| **Scoring par lot** | Import CSV → estimation de masse, distribution, export des résultats |
| **Méthodologie** | Modèle, performances, seuil de décision, et limites |

## Structure

```
streamlit_app.py        point d'entrée et navigation
app_pages/              une page par vue
utils/
    modele.py           chargement (mis en cache) et estimation
    codebook.py         libellés BRFSS des champs
    format_fr.py        typographie française des nombres
models/                 modèles sérialisés + métadonnées
data_sample/            fichier CSV d'exemple pour le scoring par lot
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
