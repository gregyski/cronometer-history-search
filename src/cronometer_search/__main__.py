import argparse
from pathlib import Path

from cronometer_search.loader import discover_csv, load_meals
from cronometer_search.app import CronometerApp


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search Cronometer food history",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--csv",
        type=Path,
        metavar="PATH",
        help="path to Cronometer CSV export (default: auto-discover in ./input/)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=3,
        metavar="N",
        help="number of meals to show",
    )
    args = parser.parse_args()

    csv_path = args.csv if args.csv else discover_csv(Path.cwd() / "input")
    meals = load_meals(csv_path)
    CronometerApp(meals=meals, count=args.count).run()


if __name__ == "__main__":
    main()
