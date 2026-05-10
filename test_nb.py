import pandas as pd
import os
import sys
sys.path.append(os.path.abspath('src'))
import analytics.db_connector as db
import analytics.data_combiner as dc
import analytics.pivot_builder as pb
import analytics.aggregator as ag
import analytics.time_series as ts
import analytics.mongo_pipeline as mp
import analytics.insight_reporter as ir
import warnings
warnings.filterwarnings('ignore')

df = pd.read_csv('data/processed/cleaned/clean.csv')

try:
    conn = db.get_connection()
    db.populate_financials(df, conn)
    sql_df = db.query_financials(conn)
    print("Successfully queried MySQL. Rows:", len(sql_df))
    conn.close()
except Exception as e:
    print("MySQL not running or credentials invalid. Skipping DB step.")

df_part1 = df[['name', 'listeners']].head(50)
df_part2 = df[['name', 'playcount']].tail(50)
for join_type in ['inner', 'left', 'right', 'outer']:
    joined = dc.combine_data(df_part1, df_part2, on_key='name', how=join_type)

long_df = pb.convert_wide_to_long(df, ['name', 'source_collection'], ['listeners', 'playcount'])

summary = df.groupby('source_collection').agg(
    avg_listeners=('listeners', 'mean'),
    total_listeners=('listeners', 'sum'),
    count_artists=('name', 'count'),
    median_playcount=('playcount', 'median')
)

top_n = ag.top_n_per_group(df, group_col='source_collection', sort_col='listeners', n=3)

df = ts.parse_dates(df, 'release_date')
pivot = pb.build_pivot_table(df, 'year', 'source_collection', 'listeners', 'sum')

monthly = ts.resample_data(df, 'release_date', 'listeners', rule='ME')
monthly['rolling_3M'] = ts.calculate_rolling_avg(monthly, 'listeners', 3)

print(mp.build_aggregation_pipeline())

ir.run_all_questions(df)
ir.plot_genre_roi(df.head(20), output_path='data/processed/analytics/genre_roi.png')
