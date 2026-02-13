# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EPITECH NLP project: a **Travel Order Resolver** that processes French text commands to extract departure/destination cities and generate train itineraries using SNCF data.

**Core Challenge**: Extract origin and destination from French sentences with missing capitals, accents, hyphens, misspellings, and ambiguous city names.

## Common Commands

```bash
# Run the main CLI
python main.py --input data/demo/input_demo.csv --output out.csv
python main.py --input data/demo/input_demo.csv --output out.csv --mode full-pipeline

# Run all tests
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_baseline.py -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Evaluate baseline on processed dataset
python scripts/baseline_evaluation/evaluate_baseline_10k.py

# CamemBERT training pipeline
python scripts/camembert/convert_dataset_to_ner.py
python scripts/camembert/train_camembert.py
python scripts/camembert/evaluate_camembert.py
python scripts/camembert/demo_camembert.py

# Dataset generation
python scripts/dataset_generation/generate_dataset_10k.py
python scripts/dataset_generation/validate_dataset_10k.py
python scripts/dataset_generation/finalize_dataset_10k.py

# Network validation
python scripts/validate_network.py
```

**Always run scripts from the project root** — relative imports break otherwise.

## Architecture

### Pipeline Flow
```
Input CSV → io_handler → baseline/transformer → pipeline → pathfinding → Output CSV
```

### Source Modules (`src/`)

| Module | File | Role |
|--------|------|------|
| NLP | `src/nlp/preprocessing.py` | French text normalization (accents, hyphens, case) |
| NLP | `src/nlp/gazetteer.py` | Location DB (66 cities/stations) + fuzzy matching |
| NLP | `src/nlp/baseline.py` | Rule-based extractor — keyword + heuristic strategies |
| NLP | `src/nlp/transformer.py` | CamemBERT NER model (fine-tuning + inference) |
| NLP | `src/nlp/postprocessing.py` | Post-extraction cleanup + gazetteer validation |
| Pathfinding | `src/pathfinding/graph_loader.py` | NetworkX graph from SNCF CSV data |
| Pathfinding | `src/pathfinding/algorithms.py` | Dijkstra implementation |
| Utils | `src/utils/pipeline.py` | End-to-end orchestration (NLP → mapping → routing) |
| Utils | `src/utils/io_handler.py` | CSV read/write (UTF-8 required) |
| Evaluation | `src/evaluation/metrics.py` | Precision/Recall/F1 per entity type |

### Entry Point

`main.py` — CLI with `--mode nlp-only` (default) or `--mode full-pipeline`. Calls `src/utils/pipeline.py::process_pipeline()`.

### Scripts (`scripts/`)

Organized in subdirectories:
- `scripts/camembert/` — CamemBERT training pipeline
- `scripts/dataset_generation/` — 10K dataset generation + validation
- `scripts/baseline_evaluation/` — Baseline accuracy measurement
- `scripts/demos/` — Interactive demos for each module

### Data Layout

```
data/
├── processed/
│   ├── train_ner.json          # Word-level BIO labels (7K sentences)
│   ├── val_ner.json            # (1.5K)
│   ├── test_ner.json           # (1.5K)
│   ├── train.csv / val.csv / test.csv
│   └── sncf/
│       ├── stations_clean.csv          # 2,782 stations
│       ├── connections_final_fixed.csv # Bidirectional connections
│       └── city_station_mapping.csv    # city_name_normalized → UIC code
├── train.csv / val.csv / test.csv      # Dataset splits
└── archive/                            # Historical datasets
```

NER JSON format: `{"tokens": [...], "labels": [...], "metadata": {...}}`

## I/O Format

**Input**: `sentenceID,sentence` (UTF-8)

**Output (nlp-only)**: `sentenceID,Departure,Destination` — `INVALID,INVALID` for non-travel sentences

**Output (full-pipeline)**: `sentenceID,Departure,Stop1,...,Destination`

## Key Implementation Details

### Preprocessing (`preprocess_for_matching`)
Applies in order: normalize hyphens (en/em dash → hyphen) → remove accents → lowercase → strip non-alphanumeric (except spaces, hyphens, apostrophes).

### Baseline Extraction Strategy (priority order)
1. Keyword: "de/depuis" → origin, "à/vers/pour" → destination
2. Direct: "billet X Y"
3. Heuristic fallback: first location = origin, last = destination

### Gazetteer Fuzzy Matching
Default `max_distance=2`. Enabling fuzzy match is the **biggest quick win** for misspellings (9% → ~50% accuracy on that category).

### CamemBERT Label Alignment
`tokenize_and_align_labels()` in `transformer.py`: first subword of a word keeps the original label; subsequent subwords get `-100` (ignored in loss).

### Graph Nodes
Nodes are **UIC codes** (8-digit), not city names. Use `city_station_mapping.csv` to convert. Paris has multiple stations — first mapping wins.

## Performance Baseline

| Category | Accuracy |
|----------|----------|
| Easy sentences | 79.5% |
| Medium sentences | 62.7% |
| Hard sentences | 36.8% |
| **Misspellings** | **9.3%** ← biggest gap |
| Invalid detection | 100% |

CamemBERT target: 85%+ overall.

## Critical Constraints

- **UTF-8 everywhere**: All file I/O must specify `encoding='utf-8'`
- **Module isolation**: `src/nlp/` must be testable without `src/pathfinding/`
- **No web app**: CLI only
- **Seeds**: All dataset generators use `seed=42`
- **Jira project**: `KAN` on `travel-order-resolver.atlassian.net` (cloudId: `64607d9d-c544-4d83-a0ad-24d2fea00482`)
