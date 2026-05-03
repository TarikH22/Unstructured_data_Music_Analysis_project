import pandas as pd

def validate_positive_numeric(df: pd.DataFrame, column: str):
    if column in df.columns:
        invalid = df[(df[column].notna()) & (df[column] < 0)]
        assert invalid.empty, f"Found negative values in {column}"

def validate_value_ranges(df: pd.DataFrame, column: str, min_val: float, max_val: float):
    if column in df.columns:
        invalid = df[(df[column].notna()) & ((df[column] < min_val) | (df[column] > max_val))]
        assert invalid.empty, f"Found values outside range [{min_val}, {max_val}] in {column}"

def validate_completeness(df: pd.DataFrame, column: str):
    if column in df.columns:
        assert not df[column].isnull().any(), f"Found missing values in critical column {column}"
