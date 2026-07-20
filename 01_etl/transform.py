"""Étape de transformation : nettoyage, typage, variables dérivées, drapeaux.

Principe directeur : **aucune donnée n'est supprimée ni corrigée**. Les anomalies
sont signalées par des drapeaux, de sorte que la table analytique reste fidèle à
la source. Les décisions de traitement (imputation, exclusion) appartiennent aux
étapes aval — modélisation ou analyse — et sont prises en connaissance de cause.
"""

import pandas as pd

import config


def _renommer(df: pd.DataFrame) -> pd.DataFrame:
    """Harmonise les noms de colonnes en snake_case."""
    return df.rename(columns=config.RENOMMAGE)


def _typer(df: pd.DataFrame) -> pd.DataFrame:
    """Convertit les float64 de la source vers des types adaptés.

    La source encode tout en float64, y compris des indicateurs 0/1 et des codes
    ordinaux. On rétablit des entiers : c'est plus compact, plus juste
    sémantiquement, et cela évite des libellés « 9.0 » dans les rapports.
    """
    colonnes_entieres = (
        config.COLONNES_BINAIRES
        + config.COLONNES_ORDINALES
        + config.COLONNES_CATEGORIELLES
        + [config.COLONNE_CIBLE, "ment_hlth_days", "phys_hlth_days"]
    )
    for col in colonnes_entieres:
        df[col] = df[col].astype("int8" if df[col].max() < 128 else "int16")

    df["bmi"] = df["bmi"].astype("float32")
    return df


def _ajouter_classe_imc(df: pd.DataFrame) -> pd.DataFrame:
    """Dérive la classe d'IMC selon les seuils de l'OMS."""
    bornes = [c[0] for c in config.CLASSES_IMC] + [float("inf")]
    codes = [c[2] for c in config.CLASSES_IMC]

    df["bmi_class"] = pd.cut(
        df["bmi"], bins=bornes, labels=codes, right=False, ordered=False
    ).astype("int8")
    return df


def _ajouter_variables_derivees(df: pd.DataFrame) -> pd.DataFrame:
    """Construit les variables métier absentes de la source.

    Ces agrégats résument des dimensions dispersées sur plusieurs colonnes et
    servent aussi bien à l'analyse exploratoire qu'aux visualisations Power BI.
    """
    # Nombre total de jours de mal-être déclarés sur les 30 derniers jours.
    # Plafonné à 30 : au-delà, le cumul n'a pas de sens calendaire.
    df["total_unhealthy_days"] = (
        (df["ment_hlth_days"] + df["phys_hlth_days"]).clip(upper=30).astype("int8")
    )

    # Score de risque cardiovasculaire : cumul des facteurs de risque connus.
    # Indicateur descriptif destiné à la segmentation, pas une variable du modèle.
    df["risk_factor_count"] = (
        df["high_bp"]
        + df["high_chol"]
        + df["smoker"]
        + df["stroke"]
        + df["diff_walk"]
        + (df["diabetes"] > 0).astype("int8")
        + (df["bmi"] >= 30).astype("int8")
    ).astype("int8")

    # Hygiène de vie : comportements protecteurs déclarés.
    df["healthy_habits_count"] = (
        df["phys_activity"] + df["fruits"] + df["veggies"]
    ).astype("int8")

    # Accès aux soins : couvert par une assurance ET sans renoncement pour raison
    # financière.
    df["has_care_access"] = (
        (df["any_healthcare"] == 1) & (df["no_doc_cost"] == 0)
    ).astype("int8")

    return df


def _ajouter_drapeaux_qualite(df: pd.DataFrame) -> pd.DataFrame:
    """Signale les anomalies sans les corriger."""
    # IMC physiologiquement improbable (la source monte jusqu'à 98).
    df["flag_bmi_extreme"] = (
        (df["bmi"] > config.IMC_MAX_PLAUSIBLE) | (df["bmi"] < config.IMC_MIN_PLAUSIBLE)
    ).astype("int8")

    # Profil strictement identique à au moins un autre répondant.
    #
    # Ces lignes sont CONSERVÉES : il s'agit de collisions légitimes entre
    # répondants distincts, pas d'erreurs de saisie. Démonstration : le taux de
    # doublons croît avec la taille de l'échantillon (1,5 % à 12 684 lignes contre
    # 9,4 % à 253 680) — signature d'une collision, là où des erreurs de saisie
    # donneraient un taux constant. Dédupliquer ferait passer la prévalence de la
    # cible de 9,42 % à 10,32 %, introduisant un biais au lieu de le corriger.
    colonnes_source = [c for c in config.RENOMMAGE.values() if c in df.columns]
    df["flag_profil_duplique"] = df.duplicated(
        subset=colonnes_source, keep=False
    ).astype("int8")

    # Déclare zéro jour de mal-être tout en se disant en mauvaise santé générale :
    # incohérence apparente, mais légitime (une maladie chronique stabilisée
    # n'occasionne pas forcément de « mauvais jour »). Signalée, non corrigée.
    df["flag_sante_incoherente"] = (
        (df["gen_hlth"] >= 4) & (df["total_unhealthy_days"] == 0)
    ).astype("int8")

    return df


def transformer(df: pd.DataFrame) -> pd.DataFrame:
    """Applique la chaîne de transformation complète."""
    df = _renommer(df.copy())
    df = _typer(df)
    df = _ajouter_classe_imc(df)
    df = _ajouter_variables_derivees(df)
    df = _ajouter_drapeaux_qualite(df)

    # Clé dégénérée : la source ne fournit aucun identifiant de répondant.
    df.insert(0, "respondent_id", range(1, len(df) + 1))

    print(f"  [transformation] {df.shape[1]} colonnes apres enrichissement")
    print(
        f"      IMC extremes : {df.flag_bmi_extreme.sum():,} | "
        f"profils dupliques : {df.flag_profil_duplique.sum():,} | "
        f"sante incoherente : {df.flag_sante_incoherente.sum():,}"
    )
    return df
