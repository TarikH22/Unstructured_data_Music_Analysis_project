"""Static chart functions using matplotlib and seaborn (object-oriented API)."""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path


sns.set_theme(style="whitegrid", palette="muted")


def _save(fig: plt.Figure, out_dir: Path, name: str) -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f"{name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(out_dir / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_top_artists_by_listeners(df: pd.DataFrame, out_dir: Path) -> None:
    """Horizontal bar chart — Top 10 artists by listener count.

    Chosen because artist names are long strings that read naturally left-to-right
    on horizontal bars. Inline annotations eliminate the need to read the x-axis.
    Tufte: high data-ink ratio; every bar encodes a distinct magnitude.
    """
    data = (
        df.dropna(subset=["name", "listeners"])
        .drop_duplicates(subset="name")
        .nlargest(10, "listeners")[["name", "listeners"]]
        .sort_values("listeners")
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(data["name"], data["listeners"] / 1e6, color=sns.color_palette("muted", len(data)))
    ax.set_xlabel("Listeners (millions)")
    ax.set_title("Top 10 Artists by Listener Count", fontsize=14, fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.1fM"))

    for bar, val in zip(bars, data["listeners"] / 1e6):
        ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}M", va="center", fontsize=9)

    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    _save(fig, out_dir, "top_artists_by_listeners")


def plot_playcount_by_source(df: pd.DataFrame, out_dir: Path) -> None:
    """Grouped bar chart — Average play count per source collection.

    Bar charts are optimal for comparing discrete categories (data sources).
    Each bar's height encodes mean playcount, giving an immediate magnitude comparison.
    Tufte: axes start at zero to preserve proportional perception.
    """
    data = (
        df.dropna(subset=["source_collection", "playcount"])
        .groupby("source_collection")["playcount"]
        .mean()
        .reset_index()
        .sort_values("playcount", ascending=False)
    )

    fig, ax = plt.subplots(figsize=(8, 5))
    palette = sns.color_palette("muted", len(data))
    bars = ax.bar(data["source_collection"], data["playcount"] / 1e6, color=palette)
    ax.set_ylabel("Avg Play Count (millions)")
    ax.set_xlabel("Source Collection")
    ax.set_title("Average Play Count by Data Source", fontsize=14, fontweight="bold")

    for bar in bars:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{bar.get_height():.0f}M", ha="center", va="bottom", fontsize=9)

    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    _save(fig, out_dir, "avg_playcount_by_source")


def plot_listeners_distribution(df: pd.DataFrame, out_dir: Path) -> None:
    """Histogram — Distribution of listener counts.

    Histograms show the shape of a continuous variable's distribution — whether it is
    skewed, bimodal, or normal. This is the correct chart for understanding spread and
    concentration of listeners across artists.
    Tufte: bins encode frequency directly; no extra grid lines.
    """
    data = df.dropna(subset=["listeners"])["listeners"] / 1e6

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.histplot(data, bins=30, kde=True, ax=ax, color=sns.color_palette("muted")[0])
    ax.set_xlabel("Listeners (millions)")
    ax.set_ylabel("Number of Artists")
    ax.set_title("Distribution of Artist Listener Counts", fontsize=14, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    _save(fig, out_dir, "listeners_distribution")


def plot_playcount_distribution(df: pd.DataFrame, out_dir: Path) -> None:
    """Histogram — Distribution of play counts.

    A second histogram on the play-count axis shows whether the distribution mirrors
    listeners (hinting at proportional engagement) or diverges (indicating replay behaviour).
    Tufte: KDE overlay makes the underlying density visible without adding chartjunk.
    """
    data = df.dropna(subset=["playcount"])["playcount"] / 1e9

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.histplot(data, bins=30, kde=True, ax=ax, color=sns.color_palette("muted")[2])
    ax.set_xlabel("Play Count (billions)")
    ax.set_ylabel("Number of Artists")
    ax.set_title("Distribution of Artist Play Counts", fontsize=14, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    _save(fig, out_dir, "playcount_distribution")


def plot_listeners_boxplot_by_source(df: pd.DataFrame, out_dir: Path) -> None:
    """Box plot — Listener counts grouped by data source.

    Box plots compare distributions across categories by showing median, IQR, and outliers.
    This is superior to a simple bar chart here because it reveals spread and skew within
    each source — not just the mean.
    Tufte: whiskers and box carry five summary statistics in minimal ink.
    """
    data = df.dropna(subset=["source_collection", "listeners"]).copy()
    data["listeners_m"] = data["listeners"] / 1e6

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.boxplot(
        data=data,
        x="source_collection",
        y="listeners_m",
        hue="source_collection",
        palette="muted",
        legend=False,
        ax=ax,
    )
    ax.set_xlabel("Source Collection")
    ax.set_ylabel("Listeners (millions)")
    ax.set_title("Listener Count Distribution by Source", fontsize=14, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    _save(fig, out_dir, "listeners_boxplot_by_source")


def plot_listeners_vs_playcount_scatter(df: pd.DataFrame, out_dir: Path) -> None:
    """Scatter plot — Listeners vs play count coloured by source.

    Scatter plots reveal the relationship (and correlation) between two continuous
    variables. Colour encodes a third dimension (source) without distorting position.
    Tufte: no grid lines inside the plot area; axis labels are sufficient.
    """
    data = df.dropna(subset=["listeners", "playcount"]).copy()
    data["listeners_m"] = data["listeners"] / 1e6
    data["playcount_b"] = data["playcount"] / 1e9
    sources = data["source_collection"].unique()
    palette = dict(zip(sources, sns.color_palette("muted", len(sources))))

    fig, ax = plt.subplots(figsize=(9, 6))
    for src, grp in data.groupby("source_collection"):
        ax.scatter(grp["listeners_m"], grp["playcount_b"], label=src,
                   color=palette[src], alpha=0.7, edgecolors="white", linewidths=0.4, s=50)

    ax.set_xlabel("Listeners (millions)")
    ax.set_ylabel("Play Count (billions)")
    ax.set_title("Listeners vs Play Count by Source", fontsize=14, fontweight="bold")
    ax.legend(title="Source", frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    _save(fig, out_dir, "listeners_vs_playcount_scatter")


def plot_correlation_heatmap(df: pd.DataFrame, out_dir: Path) -> None:
    """Heatmap — Correlation matrix of numeric columns.

    A heatmap is the canonical chart for pairwise correlation matrices; colour encodes
    the correlation coefficient on a diverging scale, making strong positive and negative
    relationships immediately visible.
    Tufte: annotation inside cells replaces a separate colour bar lookup.
    """
    numeric_df = df.select_dtypes(include="number").dropna(how="all", axis=1)
    if numeric_df.empty or numeric_df.shape[1] < 2:
        numeric_df = pd.DataFrame({"listeners": df.get("listeners", pd.Series(dtype=float)),
                                   "playcount": df.get("playcount", pd.Series(dtype=float))})

    corr = numeric_df.corr()

    fig, ax = plt.subplots(figsize=(7, 5))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0,
                linewidths=0.5, ax=ax, square=True)
    ax.set_title("Numeric Feature Correlation Matrix", fontsize=14, fontweight="bold")
    fig.tight_layout()
    _save(fig, out_dir, "correlation_heatmap")


def plot_dashboard_subplots(df: pd.DataFrame, out_dir: Path) -> None:
    """2×2 multi-panel dashboard combining the four most informative static views.

    A multi-panel layout lets a single shareable image tell the whole story.
    Each panel uses the chart type that best fits its data characteristic.
    Tufte: consistent theme across panels; shared figure title anchors the narrative.
    """
    data = df.dropna(subset=["name", "listeners", "playcount", "source_collection"]).copy()
    data["listeners_m"] = data["listeners"] / 1e6
    data["playcount_b"] = data["playcount"] / 1e9
    sources = data["source_collection"].unique()
    palette = dict(zip(sources, sns.color_palette("muted", len(sources))))

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Music Analytics Dashboard", fontsize=16, fontweight="bold", y=1.01)

    # Panel 1 — Top 10 artists bar
    top10 = (
        data.drop_duplicates(subset="name")
        .nlargest(10, "listeners_m")[["name", "listeners_m"]]
        .sort_values("listeners_m")
    )
    axes[0, 0].barh(top10["name"], top10["listeners_m"],
                    color=sns.color_palette("muted", len(top10)))
    axes[0, 0].set_title("Top 10 by Listeners")
    axes[0, 0].set_xlabel("Listeners (M)")
    axes[0, 0].spines[["top", "right"]].set_visible(False)

    # Panel 2 — Listeners distribution histogram
    sns.histplot(data["listeners_m"], bins=25, kde=True, ax=axes[0, 1],
                 color=sns.color_palette("muted")[0])
    axes[0, 1].set_title("Listener Distribution")
    axes[0, 1].set_xlabel("Listeners (M)")
    axes[0, 1].spines[["top", "right"]].set_visible(False)

    # Panel 3 — Scatter listeners vs playcount
    for src, grp in data.groupby("source_collection"):
        axes[1, 0].scatter(grp["listeners_m"], grp["playcount_b"],
                           label=src, color=palette[src], alpha=0.6, s=30)
    axes[1, 0].set_title("Listeners vs Play Count")
    axes[1, 0].set_xlabel("Listeners (M)")
    axes[1, 0].set_ylabel("Play Count (B)")
    axes[1, 0].legend(title="Source", fontsize=7, frameon=False)
    axes[1, 0].spines[["top", "right"]].set_visible(False)

    # Panel 4 — Boxplot by source
    sns.boxplot(data=data, x="source_collection", y="listeners_m",
                hue="source_collection", palette="muted", legend=False, ax=axes[1, 1])
    axes[1, 1].set_title("Listeners by Source")
    axes[1, 1].set_xlabel("Source")
    axes[1, 1].set_ylabel("Listeners (M)")
    axes[1, 1].spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    _save(fig, out_dir, "dashboard_subplots")
