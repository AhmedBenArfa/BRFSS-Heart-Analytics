"""Contrôles qualité exécutés avant le chargement.

Deux niveaux de sévérité :
  - ERREUR  : le pipeline s'arrête (donnée inexploitable en aval)
  - ALERTE  : affichée puis consignée, le pipeline continue

Le but n'est pas de « nettoyer » mais de garantir qu'aucune surprise silencieuse
ne se propage jusqu'à l'entrepôt.
"""

import pandas as pd

import config


class EchecControleQualite(Exception):
    """Levée lorsqu'un contrôle bloquant échoue."""


def _controler_domaines(df: pd.DataFrame) -> list[str]:
    """Vérifie que chaque variable codée respecte son domaine du codebook."""
    erreurs = []
    for colonne, domaine_attendu in config.DOMAINES.items():
        if colonne not in df.columns:
            continue
        valeurs = set(df[colonne].unique())
        hors_domaine = valeurs - domaine_attendu
        if hors_domaine:
            erreurs.append(
                f"{colonne} : valeurs hors codebook {sorted(hors_domaine)} "
                f"(attendu {sorted(domaine_attendu)})"
            )
    return erreurs


def _controler_bornes(df: pd.DataFrame) -> list[str]:
    """Vérifie que les variables continues restent dans leurs bornes connues."""
    erreurs = []
    for colonne, (mini, maxi) in config.BORNES.items():
        if colonne not in df.columns:
            continue
        if df[colonne].min() < mini or df[colonne].max() > maxi:
            erreurs.append(
                f"{colonne} : intervalle [{df[colonne].min()}, {df[colonne].max()}] "
                f"hors des bornes attendues [{mini}, {maxi}]"
            )
    return erreurs


def controler(df: pd.DataFrame, mode_echantillon: bool = False) -> None:
    """Exécute tous les contrôles. Lève EchecControleQualite si l'un est bloquant.

    Args:
        df: table transformée, prête à charger.
        mode_echantillon: assouplit les contrôles de volumétrie et de prévalence,
            qui n'ont pas de sens sur un échantillon partiel.
    """
    erreurs: list[str] = []
    alertes: list[str] = []

    # --- Contrôles bloquants ---------------------------------------------
    if df.empty:
        erreurs.append("la table est vide")

    if df["respondent_id"].duplicated().any():
        erreurs.append("respondent_id n'est pas unique")

    nb_nuls = int(df.isna().sum().sum())
    if nb_nuls:
        colonnes_nulles = df.columns[df.isna().any()].tolist()
        erreurs.append(f"{nb_nuls} valeurs manquantes dans {colonnes_nulles}")

    erreurs += _controler_domaines(df)
    erreurs += _controler_bornes(df)

    if config.COLONNE_CIBLE not in df.columns:
        erreurs.append(f"colonne cible '{config.COLONNE_CIBLE}' absente")

    # --- Contrôles non bloquants -----------------------------------------
    if not mode_echantillon:
        if len(df) != config.NB_LIGNES_ATTENDU:
            alertes.append(
                f"volumetrie inattendue : {len(df):,} lignes "
                f"(attendu {config.NB_LIGNES_ATTENDU:,})"
            )

        prevalence = df[config.COLONNE_CIBLE].mean() * 100
        if not 8.5 <= prevalence <= 10.5:
            alertes.append(
                f"prevalence de la cible inhabituelle : {prevalence:.2f}% "
                "(attendu ~9,42%)"
            )

    taux_imc_extreme = df["flag_bmi_extreme"].mean() * 100
    if taux_imc_extreme > 1.0:
        alertes.append(f"IMC extremes : {taux_imc_extreme:.2f}% des lignes")

    # --- Restitution ------------------------------------------------------
    for alerte in alertes:
        print(f"  [ALERTE] {alerte}")

    if erreurs:
        detail = "\n".join(f"    - {e}" for e in erreurs)
        raise EchecControleQualite(
            f"{len(erreurs)} controle(s) qualite en echec :\n{detail}"
        )

    print(f"  [controles] {len(df):,} lignes validees, {len(alertes)} alerte(s)")
