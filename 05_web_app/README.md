# 05 — Application web

Application **Streamlit** d'estimation du risque cardiovasculaire, réutilisant le
pipeline entraîné dans `04_machine_learning/`.

## Fonctionnalités prévues

- Formulaire de profil individuel → probabilité de risque estimée
- Scoring par lot et liste des profils les plus à risque
- Tableau de bord des indicateurs clés
- Explication de la prédiction (contributions SHAP)

## Exécution locale

```bash
pip install -r requirements.txt
streamlit run app.py
```

> ⚠️ L'application fournit une **estimation statistique à visée pédagogique**.
> Elle ne constitue en aucun cas un diagnostic médical.
