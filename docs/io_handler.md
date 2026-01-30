# I/O Handler Module Documentation

## Overview

The `io_handler` module provides a centralized interface for reading travel order input files and writing extraction results to CSV files with proper UTF-8 encoding support for French text.

**Module**: `src.utils.io_handler`

**Key Features**:
- UTF-8 encoding support for French accents (à, é, è, ô, etc.)
- Two output formats: NLP simple (Departure/Destination) and complete route
- Robust error handling with clear exception messages
- Automatic parent directory creation
- Comprehensive validation

---

## API Reference

### `read_input_file(file_path: str) -> List[Dict[str, str]]`

Read and parse a CSV input file containing travel order sentences.

**Parameters**:
- `file_path` (str): Path to the input CSV file

**Returns**:
- `List[Dict[str, str]]`: List of dictionaries with keys `'sentenceID'` and `'sentence'`

**Raises**:
- `FileNotFoundError`: If the file does not exist
- `ValueError`: If the CSV format is invalid (missing required columns or empty file)
- `UnicodeDecodeError`: If the file is not UTF-8 encoded

**Expected Input Format**:
```csv
sentenceID,sentence
1,Je voudrais un billet de Paris à Lyon
2,Comment aller à Marseille depuis Toulouse?
```

**Example**:
```python
from src.utils.io_handler import read_input_file

data = read_input_file('data/input.csv')
for row in data:
    print(f"ID: {row['sentenceID']}, Text: {row['sentence']}")
```

---

### `write_nlp_output(results: List[Dict[str, str]], file_path: str) -> None`

Write NLP extraction results to a CSV file (simple format).

**Parameters**:
- `results` (List[Dict]): List of dictionaries with keys `'sentenceID'`, `'departure'`, `'destination'`
- `file_path` (str): Path to the output CSV file

**Raises**:
- `ValueError`: If results list is empty or missing required keys
- `OSError`: If the file cannot be written

**Output Format**:
```csv
sentenceID,Departure,Destination
1,Paris,Lyon
2,Toulouse,Marseille
3,INVALID,INVALID
```

**Example**:
```python
from src.utils.io_handler import write_nlp_output

results = [
    {'sentenceID': '1', 'departure': 'Paris', 'destination': 'Lyon'},
    {'sentenceID': '2', 'departure': 'Toulouse', 'destination': 'Marseille'},
    {'sentenceID': '3', 'departure': 'INVALID', 'destination': 'INVALID'}
]
write_nlp_output(results, 'results/nlp_output.csv')
```

---

### `write_route_output(results: List[Dict], file_path: str) -> None`

Write complete route results to a CSV file (with intermediate stops).

**Parameters**:
- `results` (List[Dict]): List of dictionaries with keys `'sentenceID'` and `'route'` (list of cities)
- `file_path` (str): Path to the output CSV file

**Raises**:
- `ValueError`: If results list is empty, missing required keys, or route is not a list
- `OSError`: If the file cannot be written

**Output Format**:
```csv
sentenceID,Departure,Destination
1,Paris,Lyon
2,Toulouse,Montpellier,Marseille
```

With more stops:
```csv
sentenceID,Departure,Step1,Step2,Destination
3,Paris,Dijon,Lyon,Marseille
```

**Example**:
```python
from src.utils.io_handler import write_route_output

results = [
    {'sentenceID': '1', 'route': ['Paris', 'Lyon']},
    {'sentenceID': '2', 'route': ['Toulouse', 'Montpellier', 'Marseille']},
    {'sentenceID': '3', 'route': ['Paris', 'Dijon', 'Lyon', 'Marseille']}
]
write_route_output(results, 'results/route_output.csv')
```

**Notes**:
- The number of `Step` columns is determined by the longest route in the results
- Shorter routes will have empty cells for unused step columns
- Routes with only 2 cities (direct connection) will only have Departure and Destination columns

---

### `format_route(route: List[str]) -> str`

Format a route (list of cities) as a comma-separated string.

**Parameters**:
- `route` (List[str]): List of city names representing a route

**Returns**:
- `str`: Comma-separated string of cities

**Raises**:
- `ValueError`: If route is empty or not a list

**Example**:
```python
from src.utils.io_handler import format_route

route1 = ['Paris', 'Lyon']
print(format_route(route1))  # Output: 'Paris,Lyon'

route2 = ['Toulouse', 'Montpellier', 'Marseille']
print(format_route(route2))  # Output: 'Toulouse,Montpellier,Marseille'
```

---

### `validate_utf8(file_path: str) -> None`

Validate that a file is properly UTF-8 encoded.

**Parameters**:
- `file_path` (str): Path to the file to validate

**Raises**:
- `FileNotFoundError`: If the file does not exist
- `UTF8ValidationError`: If the file is not properly UTF-8 encoded (includes details about the error)

**Example**:
```python
from src.utils.io_handler import validate_utf8, UTF8ValidationError

try:
    validate_utf8('data/input.csv')
    print("File is valid UTF-8")
except UTF8ValidationError as e:
    print(f"Encoding error: {e}")
except FileNotFoundError as e:
    print(f"File not found: {e}")
```

**Use Case**:
Call this function before `read_input_file()` to provide clear error messages about encoding issues.

---

## Exception Handling

### Custom Exception

**`UTF8ValidationError`**: Raised when a file is not properly UTF-8 encoded. Inherits from `Exception`.

### Recommended Error Handling Pattern

```python
from src.utils.io_handler import (
    read_input_file,
    write_nlp_output,
    validate_utf8,
    UTF8ValidationError
)

try:
    # Validate encoding first
    validate_utf8('input.csv')

    # Read input file
    data = read_input_file('input.csv')

    # Process data (NLP extraction)
    results = process_sentences(data)

    # Write output
    write_nlp_output(results, 'output.csv')

except FileNotFoundError as e:
    print(f"Error: File not found - {e}")
except ValueError as e:
    print(f"Error: Invalid format - {e}")
except UTF8ValidationError as e:
    print(f"Error: Encoding issue - {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## File Format Specifications

### Input File Format

**Encoding**: UTF-8
**Format**: CSV with header row
**Required Columns**: `sentenceID`, `sentence`

**Example**:
```csv
sentenceID,sentence
1,Je voudrais un billet de Paris à Lyon
2,Comment aller à Marseille depuis Toulouse?
3,Quel temps fait-il?
```

**Important Notes**:
- First row MUST be the header with column names
- `sentenceID` can be any string identifier (typically numeric)
- `sentence` can contain any French text with accents, hyphens, apostrophes
- File MUST be UTF-8 encoded (not Latin-1, Windows-1252, etc.)

---

### Output File Format - NLP Simple

**Encoding**: UTF-8
**Format**: CSV with header row
**Columns**: `sentenceID`, `Departure`, `Destination`

**Example**:
```csv
sentenceID,Departure,Destination
1,Paris,Lyon
2,Toulouse,Marseille
3,INVALID,INVALID
```

**Notes**:
- `INVALID` is used for sentences that do not contain valid travel orders
- Both `Departure` and `Destination` should be city names from the gazetteer
- City names preserve French accents (e.g., "Aix-en-Provence", "Saint-Étienne")

---

### Output File Format - Complete Route

**Encoding**: UTF-8
**Format**: CSV with header row
**Columns**: `sentenceID`, `Departure`, `Step1`, `Step2`, ..., `Destination`

**Example with varying route lengths**:
```csv
sentenceID,Departure,Step1,Step2,Destination
1,Paris,Lyon,,
2,Toulouse,Montpellier,Marseille,
3,Paris,Dijon,Lyon,Marseille
```

**Notes**:
- Number of `Step` columns depends on the longest route in the dataset
- Shorter routes have empty cells for unused step columns
- Routes with only 2 cities (direct connection) skip intermediate step columns

---

## Common Use Cases

### Use Case 1: Process Single Input File

```python
from src.utils.io_handler import read_input_file, write_nlp_output
from src.nlp.baseline import extract_locations  # Example NLP module

# Read input
data = read_input_file('data/input.csv')

# Process each sentence
results = []
for row in data:
    origin, destination = extract_locations(row['sentence'])
    results.append({
        'sentenceID': row['sentenceID'],
        'departure': origin,
        'destination': destination
    })

# Write output
write_nlp_output(results, 'data/output.csv')
```

---

### Use Case 2: Generate Complete Route with Pathfinding

```python
from src.utils.io_handler import read_input_file, write_route_output
from src.nlp.baseline import extract_locations
from src.pathfinding.dijkstra import find_shortest_path  # Example pathfinding

# Read input
data = read_input_file('data/input.csv')

# Process each sentence
results = []
for row in data:
    origin, destination = extract_locations(row['sentence'])

    if origin != 'INVALID' and destination != 'INVALID':
        route = find_shortest_path(origin, destination)
    else:
        route = ['INVALID', 'INVALID']

    results.append({
        'sentenceID': row['sentenceID'],
        'route': route
    })

# Write output
write_route_output(results, 'data/route_output.csv')
```

---

### Use Case 3: Validate Input Files Before Processing

```python
from src.utils.io_handler import validate_utf8, UTF8ValidationError

def process_input_safely(file_path):
    """Process input file with validation."""
    try:
        # Validate encoding first
        validate_utf8(file_path)
        print(f"✓ File '{file_path}' is valid UTF-8")

        # Safe to read
        data = read_input_file(file_path)
        print(f"✓ Read {len(data)} sentences")

        return data

    except FileNotFoundError:
        print(f"✗ File not found: {file_path}")
        return None
    except UTF8ValidationError as e:
        print(f"✗ Encoding error: {e}")
        print("  → Please save the file with UTF-8 encoding")
        return None
    except ValueError as e:
        print(f"✗ Format error: {e}")
        return None
```

---

## Testing

The module includes 42 comprehensive unit tests covering:
- Valid input/output operations
- French accents and special characters
- Error handling (file not found, invalid format, encoding issues)
- Edge cases (empty files, missing columns, variable route lengths)
- Integration workflows

**Run tests**:
```bash
# Run all io_handler tests
python -m pytest tests/test_io_handler.py -v

# Run with coverage
python -m pytest tests/test_io_handler.py --cov=src.utils.io_handler --cov-report=html
```

---

## Best Practices

1. **Always use UTF-8 encoding**: Ensure all CSV files are saved with UTF-8 encoding (not Latin-1 or Windows-1252)

2. **Validate before processing**: Call `validate_utf8()` before reading files to catch encoding issues early

3. **Handle exceptions**: Always wrap file operations in try-except blocks to handle errors gracefully

4. **Use type hints**: The module uses type hints - leverage them in your IDE for better autocomplete and type checking

5. **Automatic directory creation**: The write functions automatically create parent directories, but ensure you have write permissions

6. **Preserve French characters**: The module preserves all French accents, hyphens, and special characters - don't strip them in preprocessing

---

## Troubleshooting

### Problem: `UnicodeDecodeError` when reading files

**Cause**: File is not UTF-8 encoded

**Solution**:
1. Open the file in a text editor (VS Code, Notepad++, etc.)
2. Save with UTF-8 encoding (usually an option in "Save As" dialog)
3. Re-run your script

**In Python**:
```python
# Check current encoding
import chardet
with open('file.csv', 'rb') as f:
    result = chardet.detect(f.read())
    print(result['encoding'])  # Should be 'utf-8'
```

---

### Problem: `ValueError: Invalid CSV format`

**Cause**: Input CSV is missing required columns (`sentenceID`, `sentence`)

**Solution**:
1. Verify your CSV has a header row: `sentenceID,sentence`
2. Check column names are exactly as expected (case-sensitive)
3. Ensure the file is not empty

---

### Problem: Output file not created

**Cause**: Parent directory doesn't exist or no write permissions

**Solution**:
1. Check that you have write permissions in the target directory
2. The module creates parent directories automatically, but ensure the drive/root path exists
3. Try writing to a different location (e.g., temp directory)

---

## Integration with Project Modules

### NLP Module Integration

```python
from src.utils.io_handler import read_input_file, write_nlp_output
from src.nlp.baseline import BaselineExtractor

# Initialize NLP extractor
extractor = BaselineExtractor()

# Read input
data = read_input_file('data/input.csv')

# Extract locations
results = []
for row in data:
    origin, destination = extractor.extract(row['sentence'])
    results.append({
        'sentenceID': row['sentenceID'],
        'departure': origin,
        'destination': destination
    })

# Write output
write_nlp_output(results, 'results/baseline_output.csv')
```

---

### Pathfinding Module Integration

```python
from src.utils.io_handler import write_nlp_output, write_route_output
from src.pathfinding.graph_loader import load_graph
from src.pathfinding.dijkstra import shortest_path

# Load graph
G = load_graph()

# Assume we have NLP results
nlp_results = [
    {'sentenceID': '1', 'departure': 'Paris', 'destination': 'Marseille'}
]

# Find routes
route_results = []
for result in nlp_results:
    if result['departure'] != 'INVALID':
        route = shortest_path(G, result['departure'], result['destination'])
    else:
        route = ['INVALID', 'INVALID']

    route_results.append({
        'sentenceID': result['sentenceID'],
        'route': route
    })

# Write complete route output
write_route_output(route_results, 'results/complete_route.csv')
```

---

## Version History

- **v1.0.0** (2024-01-30): Initial implementation
  - Basic read/write functionality
  - UTF-8 validation
  - Two output formats (NLP simple, complete route)
  - Comprehensive test suite (42 tests)

---

## License

This module is part of the Travel Order Resolver project (EPITECH T-AIA-911).

---

## Contact

For questions or issues with this module, please refer to the project maintainer or submit an issue in the project repository.
