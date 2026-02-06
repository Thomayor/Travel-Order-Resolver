# Project Structure - Travel Order Resolver

## Directory Organization

```
T-AIA-911-TRAVEL-ORDER-RESOLVER/
│
├── src/                                  # Source code
│   ├── nlp/                             # NLP extraction module
│   │   ├── baseline.py                  # Rule-based extractor
│   │   ├── transformer.py               # CamemBERT NER model
│   │   ├── preprocessing.py             # Text normalization
│   │   ├── gazetteer.py                 # Location database
│   │   └── postprocessing.py            # Entity cleanup
│   │
│   ├── pathfinding/                     # Pathfinding module
│   │   ├── graph_loader.py              # NetworkX graph construction
│   │   └── algorithms.py                # Dijkstra implementation
│   │
│   └── utils/                           # Utility modules
│       ├── pipeline.py                  # ✨ End-to-end pipeline (NEW)
│       └── io_handler.py                # I/O utilities
│
├── scripts/                             # Utility scripts
│   ├── demos/                           # Demo scripts
│   │   ├── demo_pipeline.py             # ✨ Pipeline demo (NEW)
│   │   ├── demo_baseline.py             # Baseline NLP demo
│   │   ├── demo_gazetteer.py            # Gazetteer demo
│   │   ├── demo_preprocessing.py        # Preprocessing demo
│   │   └── demo_visualize_route.py      # Route visualization
│   │
│   ├── camembert/                       # CamemBERT training
│   │   ├── train_camembert.py
│   │   ├── evaluate_camembert.py
│   │   └── demo_camembert.py
│   │
│   ├── merge_tgv_connections.py         # ✨ Merge TGV data (NEW)
│   ├── prioritize_main_stations.py      # ✨ Prioritize TGV hubs (NEW)
│   ├── add_missing_intercity_connections.py  # ✨ Add intercity links (NEW)
│   ├── test_etape_par_etape.py          # Integration test script
│   ├── clean_sncf_stations.py           # Clean station data
│   ├── validate_network.py              # Validate graph connectivity
│   └── build_city_mapping.py            # Build city→station mapping
│
├── tests/                               # Test suite
│   ├── test_pipeline.py                 # ✨ Pipeline integration tests (NEW)
│   ├── test_preprocessing.py            # Preprocessing tests (42 tests)
│   ├── test_gazetteer.py                # Gazetteer tests (32 tests)
│   ├── test_baseline.py                 # Baseline NLP tests (29 tests)
│   └── test_io_handler.py               # I/O handler tests
│
├── data/                                # Data files
│   ├── dataset_10k.csv                  # Main training dataset
│   ├── train_ner.json                   # NER training data
│   ├── val_ner.json                     # NER validation data
│   ├── test_ner.json                    # NER test data
│   │
│   ├── processed/sncf/                  # SNCF network data
│   │   ├── stations_clean.csv           # 2,782 stations
│   │   ├── connections_final_fixed.csv  # ✨ 26,662 connections (UPDATED)
│   │   └── city_station_mapping.csv     # ✨ City→UIC mapping (UPDATED)
│   │
│   ├── archive/                         # Archived data
│   │   └── old_connections/
│   │       └── connections_tgv.csv      # TGV connections archive
│   │
│   └── demo/                            # Demo output
│       ├── input_demo.csv               # Demo input
│       ├── output_nlp.csv               # NLP results
│       └── output_route.csv             # Route results
│
├── models/                              # Cached models
│   └── train_network.pkl                # ✨ Cached graph (UPDATED)
│
├── docs/                                # Documentation
│   ├── PIPELINE_INTEGRATION.md          # ✨ Pipeline documentation (NEW)
│   ├── PROJECT_STRUCTURE.md             # ✨ This file (NEW)
│   ├── nlp_module_documentation.md      # NLP module guide
│   ├── DIFFICULTY_LEVELS.md             # Dataset difficulty levels
│   ├── pathfinding_algorithm_comparison.md  # Algorithm analysis
│   └── TESTING_GUIDE.md                 # Testing guide
│
├── CLAUDE.md                            # Project instructions for Claude
├── PROJECT_PLAN.md                      # 8-week roadmap
├── SYNTHESE_COMPLETE_PROJET.md          # Complete project summary
└── README.md                            # Project README

```

## Key Files Created/Modified (This Session)

### New Files ✨

1. **Pipeline Module** (`src/utils/pipeline.py`)
   - End-to-end integration NLP + Pathfinding
   - 590 lines, fully documented
   - Handles errors gracefully

2. **Pipeline Tests** (`tests/test_pipeline.py`)
   - 25 integration tests (100% passing)
   - Tests city mapping, error handling, end-to-end flow
   - 537 lines

3. **Pipeline Demo** (`scripts/demos/demo_pipeline.py`)
   - Interactive demo with 11 test cases
   - Shows NLP and route modes
   - 158 lines

4. **Data Correction Scripts**
   - `scripts/merge_tgv_connections.py` - Merges TGV connections (+627)
   - `scripts/prioritize_main_stations.py` - Prioritizes TGV hubs
   - `scripts/add_missing_intercity_connections.py` - Adds intercity links (+6)

5. **Documentation**
   - `docs/PIPELINE_INTEGRATION.md` - Complete pipeline guide
   - `docs/PROJECT_STRUCTURE.md` - This file

### Updated Files 🔄

1. **SNCF Network Data**
   - `data/processed/sncf/connections_final_fixed.csv`
     - Added 627 TGV connections
     - Added 6 intercity connections
     - Total: 26,662 connections (was 26,196)

2. **City Mapping**
   - `data/processed/sncf/city_station_mapping.csv`
     - Reordered to prioritize TGV hubs
     - Paris: Gare de Lyon first (was Austerlitz)
     - Lyon: Saint-Exupéry TGV first (was Gorge de Loup)

3. **Graph Cache**
   - `models/train_network.pkl`
     - Rebuilt with corrected connections
     - 2,782 nodes, 13,340 edges

## File Naming Conventions

### Scripts (`scripts/`)
- **Action-based naming**: `verb_object.py`
  - Example: `merge_tgv_connections.py`, `validate_network.py`
- **Category subdirectories**: `scripts/camembert/`
- **Test scripts**: Prefixed with `test_`

### Modules (`src/`)
- **Functionality-based naming**: `module_name.py`
  - Example: `pipeline.py`, `preprocessing.py`
- **Class per file**: Main class matches filename

### Tests (`tests/`)
- **Prefix with `test_`**: `test_module_name.py`
- **Mirrors source structure**: `test_pipeline.py` tests `src/utils/pipeline.py`

### Documentation (`docs/`)
- **Uppercase titles**: `PIPELINE_INTEGRATION.md`
- **Descriptive names**: Focus on content, not structure

## Important Notes

### What NOT to Put at Project Root
- ❌ Debug scripts (e.g., `debug_*.py`) - Use `scripts/` or delete after use
- ❌ Temporary test files - Use `scripts/` or `tests/`
- ❌ Data files - Use `data/`
- ❌ Generated outputs - Use `data/demo/` or appropriate subdirectory

### What IS OK at Project Root
- ✅ Configuration files (e.g., `CLAUDE.md`, `README.md`)
- ✅ Project documentation (e.g., `PROJECT_PLAN.md`)
- ✅ Python package files (e.g., `setup.py`)
- ✅ Main entry points only (if truly top-level, prefer `scripts/` otherwise)

## Statistics

### Code Distribution
- **Source code**: ~2,500 lines
  - NLP module: ~1,200 lines
  - Pathfinding: ~500 lines
  - Pipeline: ~600 lines
  - Utils: ~200 lines

- **Tests**: ~1,800 lines
  - 103 unit tests (preprocessing, gazetteer, baseline, I/O)
  - 25 integration tests (pipeline)
  - 100% pass rate

- **Scripts**: ~2,000 lines
  - Data processing: ~1,000 lines
  - Training/evaluation: ~800 lines
  - Utilities: ~200 lines

### Data Files
- **Network data**: 2,782 stations, 26,662 connections
- **Training data**: 10,000 sentences (7K train, 1.5K val, 1.5K test)
- **Graph cache**: 1.0 MB (fast loading)

## Quick Navigation

### To run the pipeline:
```bash
python scripts/demos/demo_pipeline.py
```

### To run tests:
```bash
python -m pytest tests/test_pipeline.py -v
```

### To rebuild graph:
```bash
python -c "from src.pathfinding.graph_loader import get_or_build_graph; get_or_build_graph(force_rebuild=True)"
```

### To train CamemBERT:
```bash
python scripts/camembert/train_camembert.py
```

## Related Documentation

- [Pipeline Integration Guide](PIPELINE_INTEGRATION.md) - Complete usage guide
- [CLAUDE.md](../CLAUDE.md) - Project instructions
- [PROJECT_PLAN.md](../PROJECT_PLAN.md) - Development roadmap
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Testing guidelines
