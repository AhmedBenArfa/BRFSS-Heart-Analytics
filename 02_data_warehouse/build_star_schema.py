"""Construit le schéma en étoile dans l'entrepôt DuckDB.

Étapes :
  1. Peupler les tables de dimension depuis codebook.py (+ membre « Inconnu »).
  2. Exécuter le DDL (create_star_schema.sql) qui construit fact_respondent.
  3. Vérifier l'intégrité référentielle (aucune clé orpheline).
  4. Exporter chaque table en CSV et en Parquet.

Prérequis : avoir exécuté 01_etl/run_etl.py (table analytical_base présente).

Usage :
    python build_star_schema.py

⚠️ DuckDB n'autorise qu'un seul processus en écriture : fermer Power BI et tout
noyau Jupyter connecté à l'entrepôt avant de lancer ce script.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import duckdb

import codebook

RACINE = Path(__file__).resolve().parent
BASE = RACINE.parent / "02_data_warehouse" / "heart.duckdb"
DDL = RACINE / "create_star_schema.sql"
EXPORTS = RACINE / "exports"

# Clé et libellé du membre spécial capturant les codes hors codebook.
CLE_INCONNU = -1
LIBELLE_INCONNU = "Inconnu"


def peupler_dimensions(conn: duckdb.DuckDBPyConnection) -> None:
    """Crée et remplit chaque table de dimension à partir du codebook.

    Le DDL (étape suivante) recrée la structure des dimensions, mais il a besoin
    qu'elles existent DÉJÀ peuplées pour construire la table de faits. On insère
    donc ici, puis le DDL ne fait que la jointure — on sépare les CREATE de
    dimension du CREATE de fait pour cette raison.
    """
    for dim in codebook.DIMENSIONS:
        table, cle, libelle = dim["table"], dim["cle"], dim["libelle"]

        conn.execute(f"DROP TABLE IF EXISTS {table}")
        conn.execute(
            f"CREATE TABLE {table} ({cle} INTEGER PRIMARY KEY, {libelle} VARCHAR NOT NULL)"
        )

        # Membre « Inconnu » + tous les membres du codebook.
        lignes = [(CLE_INCONNU, LIBELLE_INCONNU)]
        lignes += [(code, texte) for code, texte in dim["membres"].items()]

        conn.executemany(
            f"INSERT INTO {table} ({cle}, {libelle}) VALUES (?, ?)", lignes
        )
        print(f"  [dimension] {table:16s} {len(lignes):>3} membres")


def construire_faits(conn: duckdb.DuckDBPyConnection) -> None:
    """Exécute le DDL du schéma, qui (re)crée les dimensions vides et le fait.

    Note : le fichier SQL recrée les dimensions en structure seule. Comme on
    vient de les peupler, on n'exécute du DDL que la partie fact_respondent, en
    laissant les dimensions déjà remplies intactes.
    """
    sql = DDL.read_text(encoding="utf-8")

    # On ne rejoue pas les CREATE des dimensions (elles sont déjà peuplées).
    # On isole la construction de la table de faits, marquée par son CREATE.
    marqueur = "CREATE OR REPLACE TABLE fact_respondent"
    if marqueur not in sql:
        raise RuntimeError("Marqueur fact_respondent introuvable dans le DDL.")
    sql_faits = sql[sql.index(marqueur):]

    conn.execute(sql_faits)
    nb = conn.execute("SELECT COUNT(*) FROM fact_respondent").fetchone()[0]
    print(f"  [fait]      fact_respondent  {nb:,} lignes".replace(",", " "))


def verifier_integrite(conn: duckdb.DuckDBPyConnection) -> list[str]:
    """Contrôle qu'aucune clé étrangère du fait n'est orpheline.

    Renvoie la liste des anomalies (vide si tout est cohérent).
    """
    anomalies = []
    for dim in codebook.DIMENSIONS:
        cle = dim["cle"]
        orphelins = conn.execute(
            f"SELECT COUNT(*) FROM fact_respondent f "
            f"LEFT JOIN {dim['table']} d ON f.{cle} = d.{cle} "
            f"WHERE d.{cle} IS NULL"
        ).fetchone()[0]
        if orphelins:
            anomalies.append(f"{dim['table']} : {orphelins} clés orphelines")

        # Combien de lignes ont été rattachées au membre « Inconnu » ?
        inconnus = conn.execute(
            f"SELECT COUNT(*) FROM fact_respondent WHERE {cle} = {CLE_INCONNU}"
        ).fetchone()[0]
        if inconnus:
            print(f"  [info] {dim['table']:16s} {inconnus} ligne(s) -> « Inconnu »")

    return anomalies


def exporter(conn: duckdb.DuckDBPyConnection) -> None:
    """Exporte chaque table en CSV et en Parquet (repli hors ligne)."""
    (EXPORTS / "csv").mkdir(parents=True, exist_ok=True)
    (EXPORTS / "parquet").mkdir(parents=True, exist_ok=True)

    tables = [d["table"] for d in codebook.DIMENSIONS] + ["fact_respondent"]
    for table in tables:
        chemin_csv = EXPORTS / "csv" / f"{table}.csv"
        chemin_parquet = EXPORTS / "parquet" / f"{table}.parquet"
        conn.execute(
            f"COPY {table} TO '{chemin_csv.as_posix()}' (HEADER, DELIMITER ',')"
        )
        conn.execute(
            f"COPY {table} TO '{chemin_parquet.as_posix()}' (FORMAT PARQUET)"
        )
    print(f"  [export]    {len(tables)} tables -> CSV + Parquet")


def main() -> int:
    if not BASE.exists():
        print(
            f"[ECHEC] Entrepot introuvable : {BASE}\n"
            "Executer d'abord : cd 01_etl && python run_etl.py",
            file=sys.stderr,
        )
        return 1

    depart = time.perf_counter()
    print("=" * 62)
    print("  CONSTRUCTION DU SCHEMA EN ETOILE — BRFSS Heart Analytics")
    print("=" * 62)

    try:
        conn = duckdb.connect(str(BASE))
    except duckdb.IOException:
        print(
            "[ECHEC] Entrepot verrouille. Fermer Power BI et tout noyau Jupyter "
            "connecte, puis reessayer.",
            file=sys.stderr,
        )
        return 1

    try:
        # Vérifier que la table analytique existe.
        existe = conn.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_name = 'analytical_base'"
        ).fetchone()[0]
        if not existe:
            print(
                "[ECHEC] Table analytical_base absente. Executer run_etl.py.",
                file=sys.stderr,
            )
            return 1

        peupler_dimensions(conn)
        construire_faits(conn)

        anomalies = verifier_integrite(conn)
        if anomalies:
            detail = "\n".join(f"    - {a}" for a in anomalies)
            print(f"\n[ECHEC] Integrite referentielle :\n{detail}", file=sys.stderr)
            return 1
        print("  [integrite] 0 cle orpheline — schema coherent")

        exporter(conn)
    finally:
        conn.close()

    duree = time.perf_counter() - depart
    print("=" * 62)
    print(f"  TERMINE en {duree:.1f}s")
    print("=" * 62)
    return 0


if __name__ == "__main__":
    sys.exit(main())
