# Intermediate 10K Dataset Files

These files are intermediate artifacts from the 10K dataset generation process.

## Files

| File | Sentences | Description |
|------|-----------|-------------|
| `dataset_10k.csv` | 11,898 | Raw generated dataset (before deduplication) |
| `dataset_10k_dedup.csv` | 9,744 | After removing 2,154 duplicates |
| `valid_orders_10k.csv` | 7,300 | Raw valid orders (before deduplication) |
| `valid_orders_10k_dedup.csv` | 7,064 | After removing 236 duplicates |
| `invalid_orders_10k.csv` | 4,598 | Raw invalid orders (before deduplication) |
| `invalid_orders_10k_dedup.csv` | 2,680 | After removing 1,918 duplicates |

## Generation Process

1. **Generation** (`generate_dataset_10k.py`): Created ~11,900 sentences using scaled templates
2. **Deduplication** (`validate_dataset_10k.py`): Removed 2,154 duplicates → 9,744 unique
3. **Finalization** (`finalize_dataset_10k.py`): Adjusted to exactly 10,000 → `*_final.csv` files

## Why Keep These Files?

- **Reproducibility**: Shows the complete generation pipeline
- **Analysis**: Allows studying duplicate patterns
- **Debugging**: Useful for troubleshooting generation issues

## Can Be Deleted

These files are not required for model training or evaluation. They can be safely deleted to save ~3.7MB of disk space.

## Production Files

The final production dataset is in `../../`:
- `dataset_final.csv` - 10,000 sentences (exactly 7,000 valid + 3,000 invalid)
- `valid_orders_final.csv` - 7,000 valid orders
- `invalid_orders_final.csv` - 3,000 invalid orders
