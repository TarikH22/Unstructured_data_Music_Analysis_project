import pandas as pd

def clean_titles(df: pd.DataFrame, title_col: str = "title") -> pd.DataFrame:
    df_clean = df.copy()
    if title_col in df_clean.columns:
        df_clean[title_col] = df_clean[title_col].astype(str).str.strip().str.title()
    return df_clean

def normalize_language_codes(df: pd.DataFrame, lang_col: str = "language") -> pd.DataFrame:
    df_clean = df.copy()
    if lang_col in df_clean.columns:
        df_clean[lang_col] = df_clean[lang_col].astype(str).str.strip().str.lower()
    return df_clean

def clean_overview(df: pd.DataFrame, overview_col: str = "overview") -> pd.DataFrame:
    df_clean = df.copy()
    if overview_col in df_clean.columns:
        df_clean[overview_col] = df_clean[overview_col].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()
    return df_clean
