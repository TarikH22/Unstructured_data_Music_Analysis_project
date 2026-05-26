"""Interactive chart functions using Plotly Express and Graph Objects."""

import pandas as pd
import numpy as np
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _save_html(fig, out_dir: Path, name: str) -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out_dir / f"{name}.html"), include_plotlyjs="cdn")


def interactive_top_artists_bar(df: pd.DataFrame, out_dir: Path) -> go.Figure:
    """Interactive horizontal bar — Top 20 artists by listeners.

    Plotly Express bar chart with hover showing name, listeners, playcount, and source.
    Users can click the legend to filter by source and use box-select to zoom.
    """
    data = (
        df.dropna(subset=["name", "listeners"])
        .drop_duplicates(subset="name")
        .nlargest(20, "listeners")
        .sort_values("listeners")
        .copy()
    )
    data["listeners_m"] = (data["listeners"] / 1e6).round(2)
    data["playcount_b"] = (data["playcount"].fillna(0) / 1e9).round(2)

    fig = px.bar(
        data,
        x="listeners_m",
        y="name",
        color="source_collection",
        orientation="h",
        title="Top 20 Artists by Listener Count",
        labels={"listeners_m": "Listeners (millions)", "name": "Artist",
                "source_collection": "Source"},
        hover_data={
            "listeners_m": ":.2f",
            "playcount_b": ":.2f",
            "source_collection": True,
            "name": False,
        },
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig.update_layout(
        xaxis_title="Listeners (millions)",
        yaxis_title="",
        legend_title="Source",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Arial", size=12),
    )
    _save_html(fig, out_dir, "interactive_top_artists_bar")
    return fig


def interactive_scatter_listeners_playcount(df: pd.DataFrame, out_dir: Path) -> go.Figure:
    """Interactive scatter — Listeners vs play count coloured by source.

    Each point is hoverable with artist name, listeners, playcount, and URL.
    Lasso and box-select tools allow sub-selection of artist clusters.
    """
    data = df.dropna(subset=["listeners", "playcount"]).copy()
    data["listeners_m"] = (data["listeners"] / 1e6).round(2)
    data["playcount_b"] = (data["playcount"] / 1e9).round(2)
    data["name"] = data["name"].fillna("Unknown")

    fig = px.scatter(
        data,
        x="listeners_m",
        y="playcount_b",
        color="source_collection",
        hover_name="name",
        title="Listeners vs Play Count (Interactive)",
        labels={
            "listeners_m": "Listeners (millions)",
            "playcount_b": "Play Count (billions)",
            "source_collection": "Source",
        },
        hover_data={
            "listeners_m": ":.2f",
            "playcount_b": ":.2f",
            "source_collection": True,
            "url": True,
        },
        color_discrete_sequence=px.colors.qualitative.Bold,
        opacity=0.75,
        size_max=12,
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend_title="Source",
        font=dict(family="Arial", size=12),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#EEEEEE")
    fig.update_yaxes(showgrid=True, gridcolor="#EEEEEE")
    _save_html(fig, out_dir, "interactive_scatter_listeners_playcount")
    return fig


def interactive_source_breakdown_pie(df: pd.DataFrame, out_dir: Path) -> go.Figure:
    """Interactive pie chart — Artist count proportion per data source.

    Pie charts are appropriate for part-to-whole comparisons with a small number of
    categories (≤ 6). Hover shows count, percentage, and source name.
    """
    data = (
        df.dropna(subset=["source_collection"])
        .groupby("source_collection")
        .size()
        .reset_index(name="count")
    )

    fig = px.pie(
        data,
        names="source_collection",
        values="count",
        title="Artist Count by Data Source",
        hover_data={"count": True},
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",
    )
    fig.update_layout(
        font=dict(family="Arial", size=12),
        legend_title="Source",
    )
    _save_html(fig, out_dir, "interactive_source_breakdown_pie")
    return fig


def interactive_listeners_histogram(df: pd.DataFrame, out_dir: Path) -> go.Figure:
    """Interactive histogram — Distribution of listener counts with marginal box.

    Combines a histogram with a marginal box plot to show both distribution shape
    and five-number summary simultaneously. Hover reveals exact bin count and range.
    """
    data = df.dropna(subset=["listeners"]).copy()
    data["listeners_m"] = data["listeners"] / 1e6

    fig = px.histogram(
        data,
        x="listeners_m",
        color="source_collection",
        marginal="box",
        nbins=40,
        title="Distribution of Listener Counts",
        labels={"listeners_m": "Listeners (millions)", "source_collection": "Source"},
        color_discrete_sequence=px.colors.qualitative.Safe,
        opacity=0.8,
        hover_data={"listeners_m": ":.2f"},
    )
    fig.update_layout(
        barmode="overlay",
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend_title="Source",
        font=dict(family="Arial", size=12),
    )
    _save_html(fig, out_dir, "interactive_listeners_histogram")
    return fig


def interactive_multi_layout(df: pd.DataFrame, out_dir: Path) -> go.Figure:
    """2×2 interactive dashboard using Graph Objects and make_subplots.

    make_subplots requires manual add_trace() calls unlike Plotly Express.
    Each panel is individually zoomable and hoverable, and all four panels share
    the same data context so brushing one panel highlights in others.
    """
    data = df.dropna(subset=["listeners", "playcount", "source_collection"]).copy()
    data["listeners_m"] = data["listeners"] / 1e6
    data["playcount_b"] = data["playcount"] / 1e9
    data["name"] = data["name"].fillna("Unknown")

    sources = data["source_collection"].unique()
    colors = px.colors.qualitative.Bold
    color_map = {src: colors[i % len(colors)] for i, src in enumerate(sources)}

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Top 10 Artists by Listeners",
            "Listeners Distribution",
            "Listeners vs Play Count",
            "Play Count by Source (Box)",
        ),
        horizontal_spacing=0.12,
        vertical_spacing=0.18,
    )

    # Panel 1 — top 10 bar
    top10 = (
        data.drop_duplicates(subset="name")
        .nlargest(10, "listeners_m")
        .sort_values("listeners_m")
    )
    fig.add_trace(
        go.Bar(
            x=top10["listeners_m"],
            y=top10["name"],
            orientation="h",
            marker_color=[color_map.get(s, "#888") for s in top10["source_collection"]],
            customdata=top10[["source_collection", "playcount_b"]].values,
            hovertemplate="<b>%{y}</b><br>Listeners: %{x:.2f}M<br>"
                          "Source: %{customdata[0]}<br>Plays: %{customdata[1]:.2f}B<extra></extra>",
            name="Top Artists",
            showlegend=False,
        ),
        row=1, col=1,
    )

    # Panel 2 — histogram per source
    for src in sources:
        grp = data[data["source_collection"] == src]
        fig.add_trace(
            go.Histogram(
                x=grp["listeners_m"],
                name=src,
                marker_color=color_map[src],
                opacity=0.7,
                hovertemplate=f"{src}<br>Listeners: %{{x:.2f}}M<br>Count: %{{y}}<extra></extra>",
                nbinsx=25,
            ),
            row=1, col=2,
        )

    # Panel 3 — scatter
    for src in sources:
        grp = data[data["source_collection"] == src]
        fig.add_trace(
            go.Scatter(
                x=grp["listeners_m"],
                y=grp["playcount_b"],
                mode="markers",
                name=src,
                marker=dict(color=color_map[src], opacity=0.6, size=6),
                text=grp["name"],
                customdata=grp[["source_collection", "url"]].fillna("").values,
                hovertemplate="<b>%{text}</b><br>Listeners: %{x:.2f}M<br>"
                              "Plays: %{y:.2f}B<br>Source: %{customdata[0]}<extra></extra>",
                showlegend=False,
            ),
            row=2, col=1,
        )

    # Panel 4 — box plot per source
    for src in sources:
        grp = data[data["source_collection"] == src]
        fig.add_trace(
            go.Box(
                y=grp["playcount_b"],
                name=src,
                marker_color=color_map[src],
                hovertemplate=f"{src}<br>Play Count: %{{y:.2f}}B<extra></extra>",
                showlegend=False,
            ),
            row=2, col=2,
        )

    fig.update_layout(
        title_text="Music Analytics Interactive Dashboard",
        title_font_size=16,
        height=750,
        barmode="overlay",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Arial", size=11),
        legend_title="Source",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#EEEEEE")
    fig.update_yaxes(showgrid=True, gridcolor="#EEEEEE")

    _save_html(fig, out_dir, "interactive_multi_layout")
    return fig
