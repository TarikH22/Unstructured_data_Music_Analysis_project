"""Analytics utilities for array ops, loading, EDA, filtering, regex, and quality reports."""

from .numpy_ops import run_numpy_foundations
from .data_loader import (
    load_available_mongo_collections,
    load_csv_data,
    optimize_dataframe_dtypes,
    process_csv_in_chunks,
    save_dataframe_csv,
)
from .explorer import (
    dataframe_info_text,
    describe_dataframe,
    extract_release_year,
    inspect_structure,
    save_distribution_charts,
    value_counts_report,
)
from .selector import (
    filter_by_between,
    filter_by_isin,
    filter_with_loc,
    sample_with_iloc,
    select_columns,
)
from .regex_ops import (
    count_crime_terms,
    extract_numbers_from_titles,
    extract_year_from_titles,
    filter_titles_by_prefix,
    most_common_genres,
    short_overviews,
    validate_ids,
)
from .quality_report import run_full_quality_audit

__all__ = [
    "run_numpy_foundations",
    "load_available_mongo_collections",
    "load_csv_data",
    "optimize_dataframe_dtypes",
    "process_csv_in_chunks",
    "save_dataframe_csv",
    "dataframe_info_text",
    "describe_dataframe",
    "extract_release_year",
    "inspect_structure",
    "save_distribution_charts",
    "value_counts_report",
    "filter_by_between",
    "filter_by_isin",
    "filter_with_loc",
    "sample_with_iloc",
    "select_columns",
    "count_crime_terms",
    "extract_numbers_from_titles",
    "extract_year_from_titles",
    "filter_titles_by_prefix",
    "most_common_genres",
    "short_overviews",
    "validate_ids",
    "run_full_quality_audit",
]
