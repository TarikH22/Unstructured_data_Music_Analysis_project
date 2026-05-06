import pandas as pd
from typing import List

def convert_to_datetime(df: pd.DataFrame, date_columns: List[str]) -> pd.DataFrame:
    df_clean = df.copy()
    for col in date_columns:
        if col in df_clean.columns:
            df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
    return df_clean

def convert_to_numeric(df: pd.DataFrame, numeric_columns: List[str], downcast: str = None) -> pd.DataFrame:
    df_clean = df.copy()
    for col in numeric_columns:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce', downcast=downcast)
    return df_clean

def convert_to_category(df: pd.DataFrame, category_columns: List[str]) -> pd.DataFrame:
    df_clean = df.copy()
    for col in category_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype('category')
    return df_clean

def memory_report(df_before: pd.DataFrame, df_after: pd.DataFrame) -> dict:
    mem_before = df_before.memory_usage(deep=True).sum() / (1024 ** 2)
    mem_after = df_after.memory_usage(deep=True).sum() / (1024 ** 2)
    return {
        "before_mb": mem_before,
        "after_mb": mem_after,
        "reduction_mb": mem_before - mem_after,
        "reduction_pct": (mem_before - mem_after) / mem_before * 100 if mem_before > 0 else 0
    }
