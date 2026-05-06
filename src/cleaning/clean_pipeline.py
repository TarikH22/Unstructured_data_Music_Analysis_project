import pandas as pd
from pathlib import Path
from utils.logger import logger
from src.cleaning.missing_handler import (
    drop_missing_identifiers, fill_text_placeholders, replace_zero_with_nan, fill_numeric_medians, drop_high_missing_columns, report_missing
)
from src.cleaning.string_cleaner import clean_titles, normalize_language_codes, clean_overview
from src.cleaning.deduplicator import remove_exact_duplicates, remove_duplicate_ids, count_duplicates
from src.cleaning.type_converter import convert_to_datetime, convert_to_numeric, convert_to_category, memory_report
from src.cleaning.validator import validate_positive_numeric

def run_cleaning_pipeline(raw_csv_path: str | Path, output_dir: str | Path) -> pd.DataFrame:
    logger.info("Cleaning stage started")
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    df = pd.read_csv(raw_csv_path)
    df_original = df.copy()
    
    # 1. Missing values report and column drop
    missing_report = report_missing(df)
    missing_report.to_csv(out_dir / "missing_report.csv")
    df = drop_high_missing_columns(df, threshold=80.0)
    
    # 2. Deduplicate
    exact_dups = count_duplicates(df)
    df = remove_exact_duplicates(df)
    logger.info(f"Removed {exact_dups} exact duplicates")
    
    id_col = next((c for c in ["id", "tmdb_id", "movie_id", "metadata.id"] if c in df.columns), None)
    if id_col:
        id_dups = count_duplicates(df, subset=[id_col])
        df = remove_duplicate_ids(df, id_col)
        logger.info(f"Removed {id_dups} duplicate IDs based on {id_col}")
        
    # 3. Missing values
    if id_col:
        df = drop_missing_identifiers(df, [id_col])
        
    text_cols = [c for c in ["overview", "description", "summary"] if c in df.columns]
    df = fill_text_placeholders(df, text_columns=text_cols)
    
    numeric_cols = list(df.select_dtypes(include='number').columns)
    df = replace_zero_with_nan(df, numeric_columns=numeric_cols)
    df = fill_numeric_medians(df, numeric_columns=numeric_cols)
    
    # 4. String cleaning
    title_col = next((c for c in ["title", "name", "metadata.file_name"] if c in df.columns), None)
    if title_col:
        df = clean_titles(df, title_col=title_col)
        
    lang_col = next((c for c in ["language", "original_language"] if c in df.columns), None)
    if lang_col:
        df = normalize_language_codes(df, lang_col=lang_col)
        
    for txt_col in text_cols:
        df = clean_overview(df, overview_col=txt_col)
        
    # 5. Type conversion
    date_cols = [c for c in ["release_date", "date", "metadata.release_date"] if c in df.columns]
    df = convert_to_datetime(df, date_columns=date_cols)
    
    df = convert_to_numeric(df, numeric_columns=numeric_cols)
    
    cat_cols = [c for c in [lang_col, "status", "source_collection"] if c and c in df.columns]
    df = convert_to_category(df, category_columns=cat_cols)
    
    mem_rep = memory_report(df_original, df)
    logger.info(f"Cleaning memory reduction: {mem_rep['reduction_pct']:.2f}%")
    
    # 6. Validation
    val_cols = [c for c in ["popularity", "vote_count", "revenue", "budget", "wins"] if c in df.columns]
    for c in val_cols:
        validate_positive_numeric(df, c)
        
    # Save
    out_path = out_dir / "clean.csv"
    df.to_csv(out_path, index=False)
    logger.info(f"Cleaning stage finished. Clean dataset saved to {out_path}")
    
    return df
