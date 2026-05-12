import pandas as pd
import numpy as np

def parse_dates(df, date_col):
    if date_col not in df.columns:
        # Mock release_date if it doesn't exist
        np.random.seed(42)
        dates = pd.date_range(start='2018-01-01', end='2024-01-01', periods=len(df))
        df[date_col] = np.random.choice(dates, size=len(df))
        
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df['year'] = df[date_col].dt.year
    df['month'] = df[date_col].dt.month
    df['weekday'] = df[date_col].dt.weekday
    df['quarter'] = df[date_col].dt.quarter
    return df

def calculate_rolling_avg(df, col, window):
    return df[col].rolling(window=window).mean()

def resample_data(df, date_col, col, rule='YE'):
    return df.set_index(date_col)[[col]].resample(rule).sum().reset_index()
