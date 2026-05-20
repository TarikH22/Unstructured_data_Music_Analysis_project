"""Orchestrator module — loads the cleaned dataset and runs all chart functions."""

from pathlib import Path
import pandas as pd

from .static_charts import (
    plot_top_artists_by_listeners,
    plot_playcount_by_source,
    plot_listeners_distribution,
    plot_playcount_distribution,
    plot_listeners_boxplot_by_source,
    plot_listeners_vs_playcount_scatter,
    plot_correlation_heatmap,
    plot_dashboard_subplots,
)
from .interactive_charts import (
    interactive_top_artists_bar,
    interactive_scatter_listeners_playcount,
    interactive_source_breakdown_pie,
    interactive_listeners_histogram,
    interactive_multi_layout,
)

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATA = ROOT_DIR / "data" / "processed" / "cleaned" / "clean.csv"
STATIC_OUT = ROOT_DIR / "outputs" / "visualizations" / "static"
INTERACTIVE_OUT = ROOT_DIR / "outputs" / "visualizations" / "interactive"

STATIC_CHARTS = [
    ("Top Artists by Listeners", plot_top_artists_by_listeners),
    ("Avg Play Count by Source", plot_playcount_by_source),
    ("Listeners Distribution", plot_listeners_distribution),
    ("Play Count Distribution", plot_playcount_distribution),
    ("Listeners Boxplot by Source", plot_listeners_boxplot_by_source),
    ("Listeners vs Play Count Scatter", plot_listeners_vs_playcount_scatter),
    ("Correlation Heatmap", plot_correlation_heatmap),
    ("Dashboard Subplots", plot_dashboard_subplots),
]

INTERACTIVE_CHARTS = [
    ("Interactive Top Artists Bar", interactive_top_artists_bar),
    ("Interactive Scatter", interactive_scatter_listeners_playcount),
    ("Source Breakdown Pie", interactive_source_breakdown_pie),
    ("Listeners Histogram", interactive_listeners_histogram),
    ("Multi-Layout Dashboard", interactive_multi_layout),
]


def run_all_charts(data_path: Path = DEFAULT_DATA) -> dict:
    """Load dataset and generate all static and interactive charts.

    Returns a dict with counts of generated files.
    """
    data_path = Path(data_path)
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found: {data_path}")

    df = pd.read_csv(data_path)
    print(f"Loaded dataset: {len(df)} rows, {list(df.columns)}")

    STATIC_OUT.mkdir(parents=True, exist_ok=True)
    INTERACTIVE_OUT.mkdir(parents=True, exist_ok=True)

    static_count = 0
    for label, fn in STATIC_CHARTS:
        try:
            fn(df, STATIC_OUT)
            print(f"  [static]  {label}")
            static_count += 1
        except Exception as exc:
            print(f"  [static]  {label} — FAILED: {exc}")

    interactive_count = 0
    for label, fn in INTERACTIVE_CHARTS:
        try:
            fn(df, INTERACTIVE_OUT)
            print(f"  [interactive]  {label}")
            interactive_count += 1
        except Exception as exc:
            print(f"  [interactive]  {label} — FAILED: {exc}")

    print(
        f"\nDone. Static: {static_count}/{len(STATIC_CHARTS)} charts "
        f"({static_count * 2} files). "
        f"Interactive: {interactive_count}/{len(INTERACTIVE_CHARTS)} charts."
    )
    return {"static": static_count, "interactive": interactive_count}


if __name__ == "__main__":
    run_all_charts()
