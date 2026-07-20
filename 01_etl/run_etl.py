"""Orchestrateur du pipeline ETL.

Usage :
    python run_etl.py                # pipeline complet
    python run_etl.py --sample 5000  # échantillon, pour tester rapidement
"""

import argparse
import sys
import time

import checks
import extract
import load
import transform


def main() -> int:
    analyseur = argparse.ArgumentParser(
        description="Pipeline ETL — BRFSS Heart Analytics"
    )
    analyseur.add_argument(
        "--sample",
        type=int,
        default=None,
        metavar="N",
        help="ne traiter que les N premieres lignes (mode test)",
    )
    arguments = analyseur.parse_args()

    depart = time.perf_counter()
    print("=" * 62)
    print("  PIPELINE ETL — BRFSS Heart Analytics")
    if arguments.sample:
        print(f"  MODE ECHANTILLON : {arguments.sample:,} lignes")
    print("=" * 62)

    try:
        df = extract.extraire(echantillon=arguments.sample)
        df = transform.transformer(df)
        checks.controler(df, mode_echantillon=arguments.sample is not None)
        load.charger(df)
    except checks.EchecControleQualite as erreur:
        print(f"\n[ECHEC] Controle qualite :\n{erreur}", file=sys.stderr)
        return 1
    except (FileNotFoundError, OSError) as erreur:
        print(f"\n[ECHEC] {erreur}", file=sys.stderr)
        return 1

    duree = time.perf_counter() - depart
    print("=" * 62)
    print(f"  TERMINE en {duree:.1f}s")
    print("=" * 62)
    return 0


if __name__ == "__main__":
    sys.exit(main())
