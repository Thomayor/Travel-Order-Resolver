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

#### NLP Module (Phase 1-5)
- **`src/nlp/preprocessing.py`** (383 lines): Text normalization for French (accents, hyphens, case)
- **`src/nlp/gazetteer.py`** (432 lines): Location database (66 cities/stations) with fuzzy matching
- **`src/nlp/baseline.py`** (420 lines): Rule-based extraction using keywords and heuristics (70% accuracy)
- **Future**: `src/nlp/transformer.py` - CamemBERT fine-tuning for 85%+ accuracy

#### Pathfinding Module (Phase 7)
- **`src/pathfinding/graph_loader.py`**: Load SNCF network from CSV into NetworkX graph
- **`src/pathfinding/dijkstra.py`**: Dijkstra's algorithm implementation for shortest path
- **Algorithm**: Dijkstra (O((V+E) log V) complexity)
- **Graph Library**: NetworkX (Python in-memory graphs)
- **Data Source**: SNCF connection data (66 stations, ~200 connections)

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

# Current status: 74 tests, 100% passing
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

```bash
# Generate expanded 10K dataset (~11,900 before dedup)
python3 generate_dataset_10k.py

# Validate and deduplicate (removes ~2K duplicates)
python3 validate_dataset_10k.py

# Finalize to exactly 10,000 phrases
python3 finalize_dataset_10k.py

# Generate statistics report
python3 generate_report_10k.py
```

**Legacy (Initial 4.9K dataset):**
```bash
# Generate initial dataset (4,956 sentences: ~3k valid + 2k invalid)
python3 generate_dataset_final.py
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

## Current Performance

**Baseline Model (Rule-based)**:
- Accuracy: 70% on test sentences (7/10 correct)
- Strengths: Direct format (93%), keyword-based (90%), multi-word stations (100%)
- Weaknesses: Question format (60%), complex sentences with ambiguous names (40%)

**Test Coverage**:
- 74 unit tests total
- Preprocessing: 42 tests
- Gazetteer: 32 tests
- All passing (100%)

## Development Workflow

### Adding New Locations
Edit [src/nlp/gazetteer.py](src/nlp/gazetteer.py) and add to `MAIN_CITIES` or `COMPOUND_STATIONS` constants.

### Testing New Extraction Logic
1. Add test sentence to [demo_baseline.py](demo_baseline.py)
2. Run: `python demo_baseline.py`
3. Add formal test to `tests/test_baseline.py` (when created)

### Dataset Iteration
The dataset generator uses seed=42 for reproducibility. To generate variations:
- Modify templates in [generate_dataset_final.py](generate_dataset_final.py)
- Run generator → validator → report pipeline

## Critical Constraints

1. **UTF-8 Encoding**: All I/O MUST use UTF-8 (French characters)
2. **Module Isolation**: NLP module must be testable independently from pathfinding
3. **French Language**: Primary requirement - handles accents, hyphens, French grammar
4. **No Web App**: CLI is sufficient, no web interface required

## Planned Features (Not Yet Implemented)

### Phase 6: Advanced NLP (CamemBERT)
- Fine-tune CamemBERT for Named Entity Recognition
- Token classification: B-ORIGIN, I-ORIGIN, B-DEST, I-DEST, O
- Target accuracy: 85%+
- Requires: 10,000-sentence training dataset

### Phase 7: Pathfinding Module (SELECTED APPROACH)
- **Algorithm Selected**: Dijkstra (guaranteed optimal, O((V+E) log V) complexity)
- **Graph Library**: NetworkX (simple, sufficient for 66 stations)
- **Rationale**:
  - Positive weights only (train durations) → Dijkstra optimal
  - NetworkX simpler than Neo4j for project scale
  - A* considered for future (requires GPS coordinates)
  - Bellman-Ford rejected (100x slower, handles negative weights unnecessarily)
- **Implementation**: From-scratch Dijkstra + NetworkX validation
- **Data**: SNCF connection CSV (origin, destination, duration_minutes)
- **Output**: `sentenceID,Origin,Stop1,Stop2,...,Destination`
- **Documentation**: [docs/pathfinding_algorithm_comparison.md](docs/pathfinding_algorithm_comparison.md)

## Documentation

- **Technical Details**: [docs/nlp_module_documentation.md](docs/nlp_module_documentation.md) - Comprehensive module docs with examples
- **Pathfinding Analysis**: [docs/pathfinding_algorithm_comparison.md](docs/pathfinding_algorithm_comparison.md) - Algorithm comparison and Dijkstra implementation guide
- **Project Plan**: [PROJECT_PLAN.md](PROJECT_PLAN.md) - 8-week implementation roadmap
- **Sentence Templates**: [docs/sentence_templates.md](docs/sentence_templates.md) - Dataset generation patterns

## Troubleshooting

### Import Errors
The project uses relative imports. Always run from project root:
```bash
# Correct
python demo_baseline.py

# Incorrect (will fail with import errors)
cd src/nlp && python baseline.py  # May fail
```

### Character Encoding Issues
Ensure Python uses UTF-8 for file I/O:
```python
with open('data.csv', 'r', encoding='utf-8') as f:
    # ...
```

### Fuzzy Matching Not Finding Locations
Default max_distance=2. Increase for more tolerance:
```python
gaz.fuzzy_match("Parus", max_distance=3)  # Still fails (too different)
gaz.fuzzy_match("Parris", max_distance=3)  # Works (distance=0 after alias)
```
