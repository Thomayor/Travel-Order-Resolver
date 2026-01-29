# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an EPITECH NLP project building a **Travel Order Resolver** that processes French text commands to extract departure/destination cities and generate train itineraries using SNCF data. The system is 70% NLP-focused with a secondary pathfinding component.

**Core Challenge**: Extract origin and destination from French sentences with missing capitals, accents, hyphens, misspellings, and ambiguous city names (e.g., "Paris" the person vs "Paris" the city).

## Architecture

The project follows a **4-layer pipeline architecture**:

```
Input Text → Preprocessing → Gazetteer Matching → Entity Extraction → Pathfinding → Output CSV
```

### Module Organization

#### NLP Module (Phases 1-6)
- **`src/nlp/preprocessing.py`** (383 lines): Text normalization for French (accents, hyphens, case)
- **`src/nlp/gazetteer.py`** (432 lines): Location database (66 cities/stations) with fuzzy matching
- **`src/nlp/baseline.py`** (420 lines): Rule-based extraction using keywords and heuristics (70% accuracy)
- **`src/nlp/transformer.py`**: CamemBERT NER model (85%+ target accuracy) - Ready for training
- **`src/nlp/postprocessing.py`**: Entity extraction cleanup and gazetteer validation

#### Pathfinding Module (Phase 7)
- **`src/pathfinding/graph_loader.py`**: Load SNCF network from CSV into NetworkX graph
- **`src/pathfinding/dijkstra.py`**: Dijkstra's algorithm implementation (planned)
- **Graph Library**: NetworkX (Python in-memory graphs)
- **Data Source**: SNCF network data (2,782 stations, ~200 connections)
- **Status**: Graph structure complete, pathfinding algorithm pending

### Data Flow

1. **Preprocessing**: Normalize French text (remove accents, fix hyphens, lowercase)
2. **Gazetteer**: Match against 50 cities + 18 multi-word stations (e.g., "Port-Boulet")
3. **Extraction Strategies** (baseline):
   - Keyword matching: "de X à Y" → origin=X, dest=Y
   - Direct format: "billet X Y" → origin=X, dest=Y
   - Heuristic fallback: first location=origin, last=destination

## Common Commands

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific module tests
python -m pytest tests/test_preprocessing.py -v
python -m pytest tests/test_gazetteer.py -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Current status: 74 tests, 100% passing
# Coverage: preprocessing (42 tests), gazetteer (32 tests)
```

### Installing Dependencies
```bash
# Core dependencies (preprocessing, gazetteer, baseline)
pip install pandas numpy networkx pytest

# CamemBERT training dependencies
pip install -r requirements_camembert.txt

# Key packages: transformers, torch, datasets, evaluate, seqeval
```

### Demo Scripts
```bash
# Demo preprocessing normalization
python demo_preprocessing.py

# Demo gazetteer location matching
python demo_gazetteer.py

# Demo baseline NLP extraction (shows origin/destination extraction)
python demo_baseline.py
```

### Dataset Generation

**Current Dataset: 10,000 sentences (7K valid + 3K invalid) - KAN-23 ✓**
**Location**: `data/dataset_10k.csv`

```bash
# Generate expanded 10K dataset (~11,900 before dedup)
python generate_dataset_10k.py

# Validate and deduplicate (removes ~2K duplicates)
python validate_dataset_10k.py

# Finalize to exactly 10,000 phrases
python finalize_dataset_10k.py

# Generate statistics report
python generate_report_10k.py
```

**Legacy (Initial 4.9K dataset):**
```bash
# Generate initial dataset (4,956 sentences: ~3k valid + 2k invalid)
# Location: data/dataset_final.csv
python generate_dataset_final.py
```

### SNCF Network Processing
```bash
# Clean raw SNCF station data
python scripts/clean_sncf_stations.py

# Extract connections from GeoJSON/GTFS
python scripts/extract_connections_from_geojson.py
python scripts/extract_tgv_from_gtfs.py

# Add bidirectional connections
python scripts/add_bidirectional_connections.py

# Validate network connectivity
python scripts/validate_network.py

# Build city → station mapping
python scripts/build_city_mapping.py
```

### Module Isolation (Critical Requirement)
The NLP module MUST be independently testable per EPITECH requirements:

```bash
# Test NLP module in isolation (without pathfinding)
cd src/nlp
python baseline.py  # Runs demo extraction
```

## Input/Output Format

**Input**: CSV with format `sentenceID,sentence` (UTF-8 encoding)
```csv
1,Je veux aller de Paris à Lyon
2,Quel temps fait-il?
```

**Output**:
- Valid orders: `sentenceID,Departure,Destination`
- Invalid orders: `sentenceID,INVALID,INVALID`

```csv
1,Paris,Lyon
2,INVALID,INVALID
```

## Dataset Difficulty Levels

The 10K dataset includes **3 difficulty levels** for valid orders, critically impacting model performance:

### Distribution
- **Easy (20.3%)**: Clear structure, correct spelling, unambiguous → Baseline: **87% accuracy**
- **Medium (59.7%)**: Questions, inverted order, one name ambiguity → Baseline: **73% accuracy**
- **Hard (20.0%)**: Misspellings, multiple ambiguous names, complex → Baseline: **35% accuracy**

### Key Insight: Misspellings are ALWAYS Hard
The category `misspelling` (721 sentences, 10.3% of valid orders) is **always classified as hard** and represents the **biggest performance gap**:
- Baseline accuracy on misspellings: **7.6%** ❌
- Root cause: Fuzzy matching not enabled in gazetteer
- Quick fix: Enable `fuzzy_match(max_distance=2)` → Expected **+40-50%** on this category

**Full documentation**: See [docs/DIFFICULTY_LEVELS.md](docs/DIFFICULTY_LEVELS.md) for complete criteria and examples.

## Key Implementation Details

### Preprocessing Pipeline
The `preprocess_for_matching()` function applies all normalizations:
1. Normalize hyphens (en dash → hyphen: Port–Boulet → Port-Boulet)
2. Remove accents (À → A, é → e)
3. Lowercase + whitespace cleanup
4. Remove non-alphanumeric (except spaces, hyphens, apostrophes)

### Gazetteer Fuzzy Matching
Handles common misspellings using edit distance:
```python
gaz.fuzzy_match("Parris", max_distance=3)  # Returns: [('Paris', 0)]
gaz.fuzzy_match("Lyyon", max_distance=3)   # Returns: [('Lyon', 1)]
```

### Baseline Extraction Strategy
1. **Keyword-based**: Look for "de/depuis" (origin) and "à/vers/pour" (destination)
2. **Direct format**: Pattern "billet X Y" where X=origin, Y=destination
3. **Heuristic**: If no keywords, first location=origin, last=destination

### Multi-word Station Handling
The system correctly handles hyphenated stations:
- Port-Boulet, Aix-en-Provence, Saint-Étienne
- Works with various hyphen types (en dash, em dash, regular hyphen)

## Performance Metrics

### Baseline Model (Rule-based)
**Overall Accuracy**: 55.64% on 10K dataset (F1: 85.36%, Precision: 89.94%, Recall: 81.23%)

**By Difficulty Level**:
- **Easy** (2,309 sentences): 79.47% accuracy (target: ~87%, gap: -8%)
- **Medium** (2,300 sentences): 62.70% accuracy (target: ~73%, gap: -10%)
- **Hard** (2,391 sentences): 36.76% accuracy (target: ~35%, ✅ on target!)

**By Category** (strengths):
- Invalid detection (no intent): 100% ✅
- Garbage detection: 91.22% ✅
- Additional info handling: 86.11% ✅
- No markers format: 84.57% ✅
- Name ambiguity (context): 81.54% ✅

**By Category** (weaknesses):
- Misspellings: 9.27% ❌ (biggest gap - needs fuzzy matching)
- Ambiguous names (person vs city): 0.95% ❌
- Incomplete origin: 0.0% ❌
- Incomplete destination: 5.5% ❌
- Complex questions: 43.23% ⚠️

**Evaluation Script**:
```bash
# Evaluate baseline on 10K dataset
python evaluate_baseline_10k.py

# Shows breakdown by difficulty, category, and detailed metrics
```

### CamemBERT Model (Target)
- **Target Accuracy**: 85%+ (15% improvement over baseline)
- **Expected Gains**: Hard difficulty (+50%), misspellings (+40-50%)
- **Metrics**: Precision, Recall, F1 per entity type (ORIGIN, DEST)

### Test Coverage
- **103 unit tests total (100% passing)**
- Preprocessing: 42 tests (normalization, encoding, edge cases)
- Gazetteer: 32 tests (exact match, fuzzy match, multi-word)
- **Baseline: 29 tests** (keyword extraction, heuristics, invalid detection, edge cases)

## Development Workflow

### Adding New Locations
1. **Add to Gazetteer**: Edit [src/nlp/gazetteer.py](src/nlp/gazetteer.py)
   - Single-word cities: Add to `MAIN_CITIES` list
   - Multi-word stations: Add to `COMPOUND_STATIONS` list
   - Aliases (optional): Add to `CITY_ALIASES` dict

2. **Update SNCF Network**: If adding pathfinding support
   - Add station to `data/processed/sncf/stations_clean.csv`
   - Add connections to `data/processed/sncf/connections_final_fixed.csv`
   - Regenerate mapping: `python scripts/build_city_mapping.py`

### Testing New Extraction Logic
1. Quick test: Add to demo script and run
   ```bash
   # Edit demo_baseline.py with test sentence
   python demo_baseline.py
   ```

2. Formal test: Add to test suite
   ```bash
   # Add test to tests/test_baseline.py (when created)
   python -m pytest tests/test_baseline.py -v
   ```

### Dataset Iteration
**Reproducibility**: All generators use `seed=42` for consistent output

**Workflow**:
1. Modify templates in generation scripts
2. Generate new dataset: `python generate_dataset_10k.py`
3. Validate & deduplicate: `python validate_dataset_10k.py`
4. Finalize: `python finalize_dataset_10k.py`
5. Generate report: `python generate_report_10k.py`
6. Inspect: Check `data/generation_report.json` and `data/statistics.txt`

**Template Distribution**:
- Easy: ~200 templates (33% of dataset)
- Medium: ~200 templates (33% of dataset)
- Hard: ~200 templates (34% of dataset)
- Invalid: ~100 templates

### Network Graph Updates
After modifying SNCF network data:
```bash
# 1. Validate connectivity
python scripts/validate_network.py

# 2. Check for isolated components
python test_complete_network.py

# 3. Regenerate visualizations
python visualize_graph.py
python scripts/generate_network_map.py
```

## Critical Constraints

1. **UTF-8 Encoding**: All I/O MUST use UTF-8 (French characters)
2. **Module Isolation**: NLP module must be testable independently from pathfinding
3. **French Language**: Primary requirement - handles accents, hyphens, French grammar
4. **No Web App**: CLI is sufficient, no web interface required

## Advanced NLP: CamemBERT Transformer (Implemented)

**Status**: ✅ READY FOR TRAINING (KAN-53)
**Module**: `src/nlp/transformer.py`
**Target**: 85%+ accuracy (vs 70% baseline)

### Training Pipeline
```bash
# Step 1: Convert dataset to NER format (BIO labels)
python scripts/convert_dataset_to_ner.py

# Step 2: Train CamemBERT model
python scripts/train_camembert.py

# Step 3: Evaluate on test set
python scripts/evaluate_camembert.py

# Step 4: Demo inference
python scripts/demo_camembert.py
```

### NER Label Schema
- **B-ORIGIN**: Beginning of origin city
- **I-ORIGIN**: Inside origin city (multi-word cities)
- **B-DEST**: Beginning of destination city
- **I-DEST**: Inside destination city
- **O**: Outside (not part of any entity)

### Training Data Split
- Train: 7,000 sentences (70%)
- Validation: 1,500 sentences (15%)
- Test: 1,500 sentences (15%)
- Files: `data/train_ner.json`, `data/val_ner.json`, `data/test_ner.json`

### Key Features
- Subword token alignment for SentencePiece tokenization
- Post-processing with gazetteer validation
- GPU/CPU support with automatic detection
- Metrics: Precision, Recall, F1, Accuracy per entity type

**Full documentation**: [CAMEMBERT_IMPLEMENTATION.md](CAMEMBERT_IMPLEMENTATION.md)

## Pathfinding Module (Implemented)

**Status**: ✅ GRAPH STRUCTURE COMPLETE (KAN-28)
**Module**: `src/pathfinding/graph_loader.py`

### Network Data
- **Stations**: 2,782 stations from SNCF Open Data
- **Connections**: ~200 bidirectional connections
- **Data Source**: `data/processed/sncf/`
  - `stations_clean.csv`: Station metadata (UIC codes, names, coordinates)
  - `connections_final_fixed.csv`: Bidirectional connections with durations
  - `city_station_mapping.json`: City name → station UIC code mapping

### Graph Loading
```python
import networkx as nx
from src.pathfinding.graph_loader import load_stations, load_connections

G = nx.Graph()
load_stations(G, 'data/processed/sncf/stations_clean.csv')
load_connections(G, 'data/processed/sncf/connections_final_fixed.csv')
```

### Visualization and Validation
```bash
# Visualize network graph
python visualize_graph.py

# Validate network connectivity
python scripts/validate_network.py

# Test complete network paths
python test_complete_network.py

# Generate network map
python scripts/generate_network_map.py
```

### Next Steps (Not Yet Implemented)
- **Dijkstra Implementation**: Shortest path algorithm
- **A* variant**: Future optimization with GPS coordinates
- **Output Format**: `sentenceID,Origin,Stop1,Stop2,...,Destination`

**Full documentation**: [docs/pathfinding_algorithm_comparison.md](docs/pathfinding_algorithm_comparison.md)

## Project Structure

```
T-AIA-911-TRAVEL-ORDER-RESOLVER/
├── src/
│   ├── nlp/                      # NLP pipeline modules
│   │   ├── preprocessing.py      # French text normalization
│   │   ├── gazetteer.py          # Location database & fuzzy matching
│   │   ├── baseline.py           # Rule-based extraction (70% accuracy)
│   │   ├── transformer.py        # CamemBERT NER model
│   │   └── postprocessing.py     # Entity cleanup
│   └── pathfinding/              # Graph pathfinding
│       └── graph_loader.py       # NetworkX graph construction
│
├── data/
│   ├── dataset_10k.csv           # Main 10K training dataset
│   ├── train_ner.json            # NER training data (7K)
│   ├── val_ner.json              # NER validation (1.5K)
│   ├── test_ner.json             # NER test data (1.5K)
│   └── processed/sncf/           # SNCF network data
│       ├── stations_clean.csv    # 2,782 stations
│       ├── connections_final_fixed.csv  # Bidirectional connections
│       └── city_station_mapping.json    # City → UIC code mapping
│
├── scripts/                      # Utility scripts
│   ├── train_camembert.py        # Train CamemBERT model
│   ├── evaluate_camembert.py     # Evaluate on test set
│   ├── convert_dataset_to_ner.py # CSV → NER conversion
│   ├── validate_network.py       # Check graph connectivity
│   └── build_city_mapping.py     # Generate city mappings
│
├── tests/
│   ├── test_preprocessing.py     # 42 tests
│   └── test_gazetteer.py         # 32 tests
│
├── demo_*.py                     # Interactive demos
├── generate_*.py                 # Dataset generation scripts
└── visualize_*.py                # Visualization tools
```

## Documentation

- **NLP Module**: [docs/nlp_module_documentation.md](docs/nlp_module_documentation.md) - Architecture, examples, experiments
- **CamemBERT Setup**: [CAMEMBERT_IMPLEMENTATION.md](CAMEMBERT_IMPLEMENTATION.md) - Training pipeline guide
- **Difficulty Levels**: [docs/DIFFICULTY_LEVELS.md](docs/DIFFICULTY_LEVELS.md) - Dataset complexity breakdown
- **Pathfinding**: [docs/pathfinding_algorithm_comparison.md](docs/pathfinding_algorithm_comparison.md) - Algorithm analysis
- **Network Validation**: [docs/NETWORK_VALIDATION_REPORT.md](docs/NETWORK_VALIDATION_REPORT.md) - Graph connectivity report
- **Project Plan**: [PROJECT_PLAN.md](PROJECT_PLAN.md) - 8-week roadmap
- **Complete Summary**: [SYNTHESE_COMPLETE_PROJET.md](SYNTHESE_COMPLETE_PROJET.md) - Full project overview

## Important Notes

### French Language Handling
This project is **French-specific** with critical requirements:
- **Accents**: System handles à, é, è, ô, etc. (removal in preprocessing)
- **Hyphens**: Supports en dash (–), em dash (—), regular hyphen (-)
- **Multi-word cities**: Port-Boulet, Aix-en-Provence, La Rochelle
- **Grammar**: French prepositions (de, depuis, à, vers, pour, en partance de)
- **Ambiguous names**: Paris (city vs person), Albert, Florence, Lourdes

### NER Dataset Format
When working with NER data, understand the label structure:
```python
# BIO tagging scheme
# B-ORIGIN: First token of origin city
# I-ORIGIN: Continuation tokens (for "La Rochelle")
# B-DEST: First token of destination
# I-DEST: Continuation tokens
# O: Outside any entity

# Example: "Je veux aller de Port Boulet à La Rochelle"
# Tokens:  Je veux aller de Port  Boulet à  La    Rochelle
# Labels:  O  O    O     O  B-ORIG I-ORIG O  B-DEST I-DEST
```

### Network Graph Structure
- **Nodes**: UIC codes (8-digit station identifiers, not city names)
- **Edges**: Bidirectional connections with duration_minutes attribute
- **Mapping**: Use `city_station_mapping.json` to convert city name → UIC code
- **Important**: Some cities have multiple stations (Paris has Gare de Lyon, Gare du Nord, etc.)

### Performance Optimization Tips
1. **Baseline improvement**: Enable fuzzy matching with `max_distance=2` for +40% on misspellings
2. **CamemBERT training**: Use GPU for 10x faster training (check `torch.cuda.is_available()`)
3. **Dataset generation**: Pre-compute and cache for faster iteration
4. **Graph queries**: NetworkX is sufficient for 2,782 stations (no need for Neo4j)

## Troubleshooting

### Import Errors
The project uses relative imports. Always run from project root:
```bash
# ✅ Correct
python demo_baseline.py
python scripts/train_camembert.py

# ❌ Incorrect (import errors)
cd src/nlp && python baseline.py
cd scripts && python train_camembert.py
```

### Character Encoding Issues
**CRITICAL**: All file I/O MUST use UTF-8 (not system default):
```python
# ✅ Correct
with open('data.csv', 'r', encoding='utf-8') as f:
    data = f.read()

# ❌ Wrong - will fail on accents
with open('data.csv', 'r') as f:  # Uses system encoding
    data = f.read()
```

### Fuzzy Matching Not Finding Locations
Default `max_distance=2`. Increase carefully (performance trade-off):
```python
gaz.fuzzy_match("Parus", max_distance=3)     # Still fails (distance > 3)
gaz.fuzzy_match("Parris", max_distance=2)    # ✅ Works (via alias)
gaz.fuzzy_match("Lyyon", max_distance=2)     # ✅ Works (edit distance = 1)
```

### CamemBERT Training Issues
```bash
# Out of memory error
# Solution: Reduce batch size in scripts/train_camembert.py
# Default: 16 → Try: 8 or 4

# Slow training without GPU
# Check: python -c "import torch; print(torch.cuda.is_available())"
# If False: Install CUDA-enabled PyTorch

# Tokenization mismatch
# Issue: Subword tokens not aligned with word-level labels
# Solution: Use align_labels_with_tokens() in transformer.py
```

### Graph Connectivity Issues
```bash
# Error: "No path found between X and Y"
# Diagnosis: Run python scripts/validate_network.py
# Shows isolated components and unreachable stations

# Fix: Add strategic connections in data/processed/sncf/connections_final_fixed.csv
# Then reload graph: G = load_graph()
```
