"""
NLP Module for Travel Order Resolver

This module contains all NLP-related functionality including:
- Text preprocessing and normalization
- Entity recognition and extraction
- Gazetteer matching
- Baseline rule-based approach
- Advanced transformer-based models
"""

from .preprocessing import (
    normalize_text,
    remove_accents,
    normalize_hyphens,
    normalize_apostrophes,
    remove_non_alphanumeric,
    tokenize_french,
    preprocess_for_matching,
    split_multi_word_name,
    fuzzy_normalize,
    extract_quoted_text,
    clean_sentence_id
)

from .gazetteer import (
    Gazetteer,
    load_gazetteer,
    MAJOR_FRENCH_CITIES,
    MULTI_WORD_STATIONS,
    AMBIGUOUS_CITY_NAMES
)

from .baseline import (
    BaselineExtractor,
    load_extractor
)

__all__ = [
    # Preprocessing
    'normalize_text',
    'remove_accents',
    'normalize_hyphens',
    'normalize_apostrophes',
    'remove_non_alphanumeric',
    'tokenize_french',
    'preprocess_for_matching',
    'split_multi_word_name',
    'fuzzy_normalize',
    'extract_quoted_text',
    'clean_sentence_id',
    # Gazetteer
    'Gazetteer',
    'load_gazetteer',
    'MAJOR_FRENCH_CITIES',
    'MULTI_WORD_STATIONS',
    'AMBIGUOUS_CITY_NAMES',
    # Baseline
    'BaselineExtractor',
    'load_extractor'
]

try:
    from .data_preparation import DataPreparator, prepare_split, prepare_all_splits
    __all__ += ['DataPreparator', 'prepare_split', 'prepare_all_splits']
except ImportError:
    pass  # transformers not installed

__version__ = '0.1.0'
