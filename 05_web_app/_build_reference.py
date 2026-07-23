"""Pré-calcule les données de référence de la population, embarquées avec l'app.

L'application déployée n'a pas accès à l'entrepôt DuckDB. Ce script produit donc,
à partir de l'entrepôt, deux fichiers légers versionnés avec l'application :

  data_sample/population_reference.parquet
      Un échantillon stratifié de répondants, avec leur risque estimé par le
      modèle calibré. Sert au positionnement individuel (percentile par âge et
      sexe) et au tableau de bord population.

  data_sample/profils_reference.json
      Les quatre profils de population du data mining (k-means, k=4) et quelques
      agrégats globaux.

Prérequis : entrepôt construit et modèle calibré présent dans models/.

Usage :
    python _build_reference.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import duckdb
import joblib
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

RACINE = Path(__file__).resolve().parent
BASE = RACINE.parent / "02_data_warehouse" / "heart.duckdb"
MODELE = RACINE / "models" / "heart_model.joblib"
META = RACINE / "models" / "metadata.json"
SORTIE = RACINE / "data_sample"

TAILLE_ECHANTILLON = 25_000
GRAINE = 42


def main() -> int:
    if not BASE.exists():
        print(f"[ECHEC] Entrepot introuvable : {BASE}", file=sys.stderr)
        return 1
    if not MODELE.exists():
        print(f"[ECHEC] Modele introuvable : {MODELE}", file=sys.stderr)
        return 1

    meta = json.loads(META.read_text(encoding="utf-8"))
    variables = meta["variables"]

    print("Chargement des donnees...")
    with duckdb.connect(str(BASE), read_only=True) as conn:
        df = conn.execute(
            f"SELECT {', '.join(variables)}, heart_disease FROM analytical_base"
        ).df()

    # --- Profils du data mining (k-means, k=4) ----------------------------
    print("Clustering (k-means, k=4)...")
    X = StandardScaler().fit_transform(df[variables])
    km = KMeans(n_clusters=4, random_state=GRAINE, n_init=10).fit(X)
    df["cluster"] = km.labels_

    taux = df.groupby("cluster")["heart_disease"].mean().sort_values()
    ordre = {anc: nouv for nouv, anc in enumerate(taux.index)}
    df["profil"] = df["cluster"].map(ordre)

    noms_profils = [
        "Jeunes actifs en bonne santé",
        "Adultes non assurés",
        "Seniors autonomes",
        "Seniors multi-morbides fragiles",
    ]
    profils = []
    for p in range(4):
        sous = df[df["profil"] == p]
        profils.append({
            "id": p,
            "nom": noms_profils[p],
            "effectif": int(len(sous)),
            "part_pct": round(len(sous) / len(df) * 100, 1),
            "taux_maladie_pct": round(float(sous["heart_disease"].mean()) * 100, 1),
            "age_moyen_code": round(float(sous["age_group"].mean()), 1),
            "imc_moyen": round(float(sous["bmi"].mean()), 1),
            "sans_couverture_pct": round(float(1 - sous["any_healthcare"].mean()) * 100, 1),
        })

    # --- Risque estimé par le modèle calibré ------------------------------
    print("Estimation du risque sur la population...")
    modele = joblib.load(MODELE)
    df["risque"] = modele.predict_proba(df[variables])[:, 1]

    # --- Échantillon de référence (léger, versionné) ----------------------
    echantillon = df.sample(
        min(TAILLE_ECHANTILLON, len(df)), random_state=GRAINE
    )[["age_group", "sex", "bmi", "gen_hlth", "heart_disease", "risque", "profil"]]

    SORTIE.mkdir(parents=True, exist_ok=True)
    chemin_parquet = SORTIE / "population_reference.parquet"
    echantillon.to_parquet(chemin_parquet, index=False)

    # --- Agrégats globaux -------------------------------------------------
    reference = {
        "n_population_totale": int(len(df)),
        "prevalence_reelle_pct": round(float(df["heart_disease"].mean()) * 100, 2),
        "risque_moyen_estime_pct": round(float(df["risque"].mean()) * 100, 2),
        "seuil_decision": meta["seuil_decision"],
        "profils": profils,
        "risque_moyen_par_age": {
            int(a): round(float(g["risque"].mean()) * 100, 2)
            for a, g in df.groupby("age_group")
        },
        "risque_moyen_par_sexe": {
            int(s): round(float(g["risque"].mean()) * 100, 2)
            for s, g in df.groupby("sex")
        },
    }
    chemin_json = SORTIE / "profils_reference.json"
    chemin_json.write_text(
        json.dumps(reference, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    taille = chemin_parquet.stat().st_size / 1024
    print(f"\nGenere :")
    print(f"  {chemin_parquet.name} ({len(echantillon):,} lignes, {taille:.0f} Ko)"
          .replace(",", " "))
    print(f"  {chemin_json.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
