import pandas as pd
from typing import List

def report_missing(df: pd.DataFrame) -> pd.DataFrame:
    missing = df.isnull().sum()
    missing_pct = (missing / len(df)) * 100
    report = pd.DataFrame({'missing_count': missing, 'missing_percentage': missing_pct})
    return report[report['missing_count'] > 0].sort_values(by='missing_count', ascending=False)

def drop_missing_identifiers(df: pd.DataFrame, id_columns: List[str]) -> pd.DataFrame:
    return df.dropna(subset=id_columns)

def fill_text_placeholders(df: pd.DataFrame, text_columns: List[str], placeholder: str = "Unknown") -> pd.DataFrame:
    df_clean = df.copy()
    for col in text_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna(placeholder)
    return df_clean

def replace_zero_with_nan(df: pd.DataFrame, numeric_columns: List[str]) -> pd.DataFrame:
    df_clean = df.copy()
    for col in numeric_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].replace(0, pd.NA)
    return df_clean

def fill_numeric_medians(df: pd.DataFrame, numeric_columns: List[str]) -> pd.DataFrame:
    df_clean = df.copy()
    for col in numeric_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna(df_clean[col].median())
    return df_clean

def drop_high_missing_columns(df: pd.DataFrame, threshold: float = 80.0) -> pd.DataFrame:
    missing_pct = (df.isnull().sum() / len(df)) * 100
    cols_to_keep = missing_pct[missing_pct <= threshold].index
    return df[cols_to_keep].copy()
