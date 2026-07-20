"""Inspecteur en lecture seule de l'entrepôt DuckDB.

Ouvre l'entrepôt en mode read_only : il peut donc tourner pendant que Power BI
est connecté (plusieurs lecteurs coexistent ; un seul écrivain).

Usage :
    python explore_warehouse.py                    # liste des tables + volumétrie
    python explore_warehouse.py fact_respondent    # aperçu d'une table
    python explore_warehouse.py "SELECT ..."       # requête SQL libre
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

BASE = Path(__file__).resolve().parent / "heart.duckdb"


def lister(conn: duckdb.DuckDBPyConnection) -> None:
    """Affiche toutes les tables avec leur volumétrie."""
    tables = conn.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'main' ORDER BY table_name"
    ).fetchall()

    print(f"{'Table':<22} {'Lignes':>12} {'Colonnes':>10}")
    print("-" * 46)
    for (nom,) in tables:
        nb = conn.execute(f"SELECT COUNT(*) FROM {nom}").fetchone()[0]
        cols = conn.execute(
            "SELECT COUNT(*) FROM information_schema.columns "
            f"WHERE table_name = '{nom}'"
        ).fetchone()[0]
        print(f"{nom:<22} {nb:>12,} {cols:>10}".replace(",", " "))


def apercu(conn: duckdb.DuckDBPyConnection, table: str) -> None:
    """Affiche les premières lignes d'une table."""
    df = conn.execute(f"SELECT * FROM {table} LIMIT 10").df()
    print(df.to_string(index=False))


def requete(conn: duckdb.DuckDBPyConnection, sql: str) -> None:
    """Exécute une requête SQL arbitraire et affiche le résultat."""
    print(conn.execute(sql).df().to_string(index=False))


def main() -> int:
    if not BASE.exists():
        print(f"[ECHEC] Entrepot introuvable : {BASE}", file=sys.stderr)
        return 1

    conn = duckdb.connect(str(BASE), read_only=True)
    try:
        if len(sys.argv) == 1:
            lister(conn)
        else:
            argument = sys.argv[1]
            mots_sql = ("SELECT", "WITH", "PRAGMA", "DESCRIBE", "SUMMARIZE")
            if argument.strip().upper().startswith(mots_sql):
                requete(conn, argument)
            else:
                apercu(conn, argument)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
