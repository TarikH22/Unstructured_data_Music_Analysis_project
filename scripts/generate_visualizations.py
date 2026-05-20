"""CLI entry-point — regenerates all static and interactive charts.

Usage:
    python scripts/generate_visualizations.py
    python scripts/generate_visualizations.py --data path/to/custom.csv
"""

import argparse
import sys
from pathlib import Path

# Ensure src/ is on the path when called from the project root.
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from visualization.chart_generator import run_all_charts, DEFAULT_DATA


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate all music analytics visualizations."
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=DEFAULT_DATA,
        help="Path to the cleaned CSV dataset (default: data/processed/cleaned/clean.csv)",
    )
    args = parser.parse_args()

    print(f"Generating visualizations from: {args.data}")
    results = run_all_charts(args.data)
    print(
        f"\nOutput directories:\n"
        f"  Static (PNG+PDF): {ROOT_DIR / 'outputs' / 'visualizations' / 'static'}\n"
        f"  Interactive (HTML): {ROOT_DIR / 'outputs' / 'visualizations' / 'interactive'}"
    )
    sys.exit(0 if results["static"] > 0 else 1)


if __name__ == "__main__":
    main()
