# Archive Directory

This directory contains archived datasets from previous versions of the Travel Order Resolver project.

## Subdirectories

### `initial_4.9k/`
Legacy dataset from the initial dataset generation phase.
- **Total**: 4,956 sentences
- **Valid**: 2,956 (59.6%)
- **Invalid**: 2,000 (40.4%)
- **Date**: December 2025
- **Purpose**: Initial proof of concept

### `intermediate_10k/`
Intermediate files from the 10K dataset generation process (before deduplication and finalization).
- **Purpose**: Generation artifacts
- **Note**: These files contain duplicates and were processed to create the final production dataset
- **Can be deleted**: These files are kept for reproducibility but can be safely removed to save space

## Production Dataset

The current production dataset is located in the parent directory (`data/`):
- `dataset_final.csv` - 10,000 sentences (7,000 valid + 3,000 invalid)
- `valid_orders_final.csv` - 7,000 valid travel orders
- `invalid_orders_final.csv` - 3,000 invalid orders

Refer to `../README.md` for details on the production dataset.
