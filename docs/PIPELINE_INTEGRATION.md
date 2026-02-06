# Pipeline Integration - NLP + Pathfinding

## Overview

The pipeline module (`src/utils/pipeline.py`) provides an end-to-end solution for processing travel orders by integrating:

1. **NLP Extraction** - Extract origin and destination from French sentences
2. **City Mapping** - Map city names to SNCF station UIC codes
3. **Pathfinding** - Find optimal routes using Dijkstra's algorithm

## Architecture

```
┌─────────────────┐
│  Input CSV      │
│  (sentenceID,   │
│   sentence)     │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  NLP Module     │
│  (Baseline)     │ ──> Extract: origin, destination
└────────┬────────┘
         │
         v
┌─────────────────┐
│  City Mapping   │
│  Module         │ ──> Map: city name → UIC code
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Pathfinding    │
│  Module         │ ──> Find: shortest route (Dijkstra)
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Output CSV     │
│  (sentenceID,   │
│   Departure,    │
│   Destination)  │
└─────────────────┘
```

## Features

### Processing Modes

1. **NLP Mode** (`mode='nlp'`)
   - Extracts origin and destination only
   - Output format: `sentenceID,Departure,Destination`
   - Fast processing (no route computation)
   - Use case: Validate NLP extraction accuracy

2. **Route Mode** (`mode='route'`)
   - Computes complete route with intermediate stops
   - Output format: `sentenceID,Departure,Step1,Step2,...,Destination`
   - Includes pathfinding
   - Use case: Generate complete travel itineraries

### Error Handling

The pipeline handles multiple error types gracefully:

- **Invalid sentences** - Not travel orders (e.g., "Quel temps fait-il?")
- **Missing locations** - Incomplete orders (e.g., "Je pars demain")
- **Unknown cities** - Cities not in SNCF database
- **No route** - Stations not connected in network
- **Encoding errors** - Non-UTF-8 characters

All errors are logged and result in `INVALID,INVALID` output for that sentence.

## Usage

### Command Line

```bash
# NLP mode only
python -m src.utils.pipeline input.csv output_nlp.csv nlp

# Full route mode
python -m src.utils.pipeline input.csv output_route.csv route
```

### Python API

```python
from src.utils.pipeline import process_pipeline

# Process input file
stats = process_pipeline(
    input_file='data/input.csv',
    output_file='data/output.csv',
    mode='nlp'  # or 'route'
)

# Check statistics
print(f"Processed {stats['total']} sentences")
print(f"Valid orders: {stats['valid']}")
print(f"Success rate: {stats['success']/stats['total']*100:.1f}%")
```

### Single Sentence Processing

```python
from src.utils.pipeline import (
    process_single_sentence,
    load_city_mapping
)
from src.nlp.baseline import load_extractor
from src.pathfinding.graph_loader import get_or_build_graph

# Setup
extractor = load_extractor()
city_mapping = load_city_mapping()
graph = get_or_build_graph()

# Process one sentence
result = process_single_sentence(
    sentence_id="1",
    sentence="Je veux aller de Paris à Lyon",
    extractor=extractor,
    city_mapping=city_mapping,
    graph=graph,
    include_route=True
)

# Check results
print(f"Origin: {result['origin']}")
print(f"Destination: {result['destination']}")
print(f"Route: {' → '.join(result['route'])}")
print(f"Travel time: {result['total_time']:.0f} minutes")
```

## Demo

Run the interactive demo to see the pipeline in action:

```bash
python demo_pipeline.py
```

This will:
1. Create sample input with 10 test sentences
2. Run pipeline in NLP mode
3. Run pipeline in route mode
4. Display results and statistics

Output files saved to: `data/demo/`

## Testing

The pipeline includes comprehensive integration tests:

```bash
# Run all pipeline tests
python -m pytest tests/test_pipeline.py -v

# Run specific test
python -m pytest tests/test_pipeline.py::test_process_pipeline_nlp_mode -v

# Run with coverage
python -m pytest tests/test_pipeline.py --cov=src.utils.pipeline --cov-report=html
```

**Test Coverage**:
- 25 integration tests
- 100% pass rate
- Tests cover: city mapping, error handling, NLP+pathfinding integration, edge cases

## Input Format

CSV file with UTF-8 encoding:

```csv
sentenceID,sentence
1,Je veux aller de Paris à Lyon
2,Train pour Marseille depuis Toulouse
3,Quel temps fait-il?
```

**Requirements**:
- UTF-8 encoding (required for French accents)
- Header row: `sentenceID,sentence`
- sentenceID: Unique identifier (string or number)
- sentence: French travel order text

## Output Formats

### NLP Mode Output

```csv
sentenceID,Departure,Destination
1,Paris,Lyon
2,Toulouse,Marseille
3,INVALID,INVALID
```

### Route Mode Output

```csv
sentenceID,Departure,Step1,Step2,Destination
1,Paris,Dijon,Mâcon,Lyon
2,Toulouse,Montpellier,Nîmes,Marseille
3,INVALID,INVALID,,
```

**Note**: Route mode includes all intermediate stations in the optimal path.

## Performance

### Processing Speed

- **NLP mode**: ~100 sentences/second
- **Route mode**: ~50 sentences/second (with pathfinding)
- **Graph loading**: ~0.1s (cached) or ~2-3s (from CSV)

### Accuracy (on 10K dataset)

- **NLP extraction**: 55.64% exact match accuracy
  - Easy difficulty: 79.47%
  - Medium difficulty: 62.70%
  - Hard difficulty: 36.76%

- **Pathfinding**: 100% success rate (when cities are in network)

### Bottlenecks

1. **Graph loading** - Mitigated by caching to `models/train_network.pkl`
2. **City mapping** - Mitigated by loading once and reusing
3. **Pathfinding** - O((V+E) log V) complexity, fast for 2,782 stations

## Error Statistics

From the demo run (10 test sentences):

```
Total sentences:        10
Valid travel orders:    6 (60.0%)
Invalid orders:         4 (40.0%)
Successful routes:      6 (100% of valid orders)
Total errors:           0
  - NLP errors:         0
  - Mapping errors:     0
  - Pathfinding errors: 0
```

## Module Functions

### Core Functions

| Function | Description | Returns |
|----------|-------------|---------|
| `process_pipeline()` | Main entry point for batch processing | Statistics dict |
| `process_single_sentence()` | Process one sentence | Result dict |
| `load_city_mapping()` | Load city → UIC mapping | Dict[str, str] |
| `map_city_to_uic()` | Map city name to UIC code | Optional[str] |
| `handle_errors()` | Centralized error handling | Error dict |

### Configuration

The pipeline can be configured with custom file paths:

```python
stats = process_pipeline(
    input_file='custom_input.csv',
    output_file='custom_output.csv',
    mode='nlp',
    cache_path='models/custom_network.pkl',
    stations_file='data/custom_stations.csv',
    connections_file='data/custom_connections.csv',
    mapping_file='data/custom_mapping.csv'
)
```

## Integration with Other Modules

### NLP Module
- Uses `BaselineExtractor` from `src.nlp.baseline`
- Calls `extract()` method for origin/destination extraction
- Can be swapped with CamemBERT transformer model

### Pathfinding Module
- Uses `dijkstra()` from `src.pathfinding.algorithms`
- Uses `get_or_build_graph()` from `src.pathfinding.graph_loader`
- Supports custom graph implementations

### I/O Module
- Uses `read_input_file()` from `src.utils.io_handler`
- Uses `write_nlp_output()` and `write_route_output()`
- Ensures UTF-8 encoding throughout

## Troubleshooting

### Common Issues

1. **UnicodeDecodeError**
   - Ensure input file is UTF-8 encoded
   - Check: `file.encoding` in editor settings

2. **CityMappingError**
   - City not in SNCF database
   - Check: `data/processed/sncf/city_station_mapping.csv`

3. **NoPathError**
   - Stations not connected in network
   - Check: `python scripts/validate_network.py`

4. **FileNotFoundError**
   - Check paths are relative to project root
   - Ensure data files exist in `data/processed/sncf/`

## Future Enhancements

- [ ] Add CamemBERT transformer model integration
- [ ] Support multiple route options (top-K paths)
- [ ] Add travel time estimation
- [ ] Cache city mapping for faster repeated lookups
- [ ] Add progress bar for large files
- [ ] Support parallel processing for multiple files
- [ ] Add JSON output format option

## Related Documentation

- [NLP Module Documentation](nlp_module_documentation.md)
- [Pathfinding Algorithm Comparison](pathfinding_algorithm_comparison.md)
- [Testing Guide](TESTING_GUIDE.md)
- [Project Plan](../PROJECT_PLAN.md)

## Authors

- Integration implemented as part of KAN-XX ticket
- NLP module: BaselineExtractor (KAN-21, KAN-22)
- Pathfinding module: Dijkstra implementation (KAN-35)
- I/O Handler: UTF-8 support (KAN-34)

## License

EPITECH Project - Travel Order Resolver
