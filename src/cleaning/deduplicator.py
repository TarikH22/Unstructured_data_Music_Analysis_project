import pandas as pd
from typing import List

def remove_exact_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates()

def remove_duplicate_ids(df: pd.DataFrame, id_col: str = "id") -> pd.DataFrame:
    if id_col in df.columns:
        return df.drop_duplicates(subset=[id_col], keep="first")
    return df

def remove_duplicate_title_date(df: pd.DataFrame, title_col: str = "title", date_col: str = "release_date") -> pd.DataFrame:
    if title_col in df.columns and date_col in df.columns:
        return df.drop_duplicates(subset=[title_col, date_col], keep="first")
    return df

def count_duplicates(df: pd.DataFrame, subset: List[str] = None) -> int:
    return df.duplicated(subset=subset).sum()
