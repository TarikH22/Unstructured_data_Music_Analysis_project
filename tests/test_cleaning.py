import pytest
import pandas as pd
from src.cleaning.missing_handler import report_missing, drop_missing_identifiers
from src.cleaning.string_cleaner import clean_titles, normalize_language_codes
from src.cleaning.deduplicator import remove_exact_duplicates, remove_duplicate_ids, count_duplicates
from src.cleaning.type_converter import convert_to_numeric, convert_to_datetime

@pytest.fixture
def sample_df():
    data = {
        'id': [1, 2, 2, 3, None],
        'title': [' The Matrix ', 'inception', 'Inception', ' Avatar ', 'Unknown'],
        'language': ['EN', ' en ', 'FR', 'es', 'de'],
        'revenue': ['1000', '2000', 'not_a_number', 0, '1500'],
        'release_date': ['1999-03-31', '2010-07-16', 'invalid_date', '2009-12-18', '2000-01-01']
    }
    return pd.DataFrame(data)

def test_drop_missing_identifiers(sample_df):
    df_clean = drop_missing_identifiers(sample_df, ['id'])
    assert len(df_clean) == 4
    assert df_clean['id'].isnull().sum() == 0

def test_clean_titles(sample_df):
    df_clean = clean_titles(sample_df, 'title')
    assert df_clean['title'].iloc[0] == 'The Matrix'
    assert df_clean['title'].iloc[1] == 'Inception'

def test_normalize_language_codes(sample_df):
    df_clean = normalize_language_codes(sample_df, 'language')
    assert df_clean['language'].iloc[0] == 'en'
    assert df_clean['language'].iloc[1] == 'en'
    assert df_clean['language'].iloc[2] == 'fr'

def test_deduplicator(sample_df):
    df_clean = remove_duplicate_ids(sample_df, 'id')
    # id=2 is duplicated, plus there's a None. drop_duplicates normally keeps the first.
    assert len(df_clean) == 4

def test_type_converter_numeric(sample_df):
    df_clean = convert_to_numeric(sample_df, ['revenue'])
    assert pd.api.types.is_numeric_dtype(df_clean['revenue'])
    assert pd.isna(df_clean['revenue'].iloc[2])

def test_type_converter_datetime(sample_df):
    df_clean = convert_to_datetime(sample_df, ['release_date'])
    assert pd.api.types.is_datetime64_any_dtype(df_clean['release_date'])
    assert pd.isna(df_clean['release_date'].iloc[2])

