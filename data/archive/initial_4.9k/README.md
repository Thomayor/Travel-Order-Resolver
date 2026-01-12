# Initial 4.9K Dataset (Legacy)

This is the initial dataset from the first phase of the Travel Order Resolver project.

## Dataset Overview

- **Total sentences**: 4,956
- **Valid orders**: 2,956 (59.6%)
- **Invalid orders**: 2,000 (40.4%)
- **Generation date**: December 11, 2025
- **Status**: Legacy / Archived

## Files

| File | Size | Description |
|------|------|-------------|
| `dataset_initial.csv` | 421K | Complete shuffled dataset |
| `valid_orders_initial.csv` | 285K | Valid travel orders only |
| `invalid_orders.csv` | 135K | Invalid orders only |
| `statistics_4.9k.txt` | 3.2K | Statistical summary |
| `generation_report_4.9k.json` | 2.3K | JSON generation report |
| `dataset_initial_raw.csv` | 421K | Raw copy from data/raw/ |

## Distribution

### Valid Orders by Category
- standard: 783 (26.5%)
- name_ambiguity: 496 (16.8%)
- inverted_order: 390 (13.2%)
- misspelling: 299 (10.1%)
- no_markers: 297 (10.0%)
- no_capitals: 247 (8.4%)
- compound_name: 244 (8.3%)
- additional_info: 150 (5.1%)
- complex_question: 50 (1.7%)

### Invalid Orders by Category
- no_intent: 454 (22.7%)
- garbage: 416 (20.8%)
- ambiguous: 410 (20.5%)
- incomplete_dest: 329 (16.4%)
- incomplete_origin: 323 (16.2%)
- incomplete_grammar: 68 (3.4%)

## Historical Context

This dataset was the proof of concept that demonstrated:
- ✅ Feasibility of template-based generation
- ✅ Category distribution strategy
- ✅ French language handling (accents, hyphens)
- ✅ Multi-word station names support

**Baseline model evaluation**: ~70% accuracy on this dataset

## Migration to 10K

This dataset was superseded by the 10K dataset (KAN-23) which:
- Expanded from 4,956 to 10,000 sentences
- Adjusted distribution to 70% valid / 30% invalid
- Improved category proportions
- Enhanced deduplication process

## Current Production Dataset

The active dataset is located in `../../`:
- `dataset_final.csv` - 10,000 sentences
- See `../../README.md` for current dataset documentation

## Archived On

January 9, 2026 - Moved to archive as part of KAN-23 completion
