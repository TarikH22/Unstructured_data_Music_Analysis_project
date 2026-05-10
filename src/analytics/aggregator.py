import pandas as pd

def summarize_artists(df, group_col='source_collection'):
    return df.groupby(group_col).agg(
        avg_listeners=('listeners', 'mean'),
        total_listeners=('listeners', 'sum'),
        avg_playcount=('playcount', 'mean'),
        count=('name', 'count')
    )

def top_n_per_group(df, group_col, sort_col, n=3):
    return df.groupby(group_col).apply(lambda x: x.nlargest(n, sort_col)).reset_index(drop=True)
