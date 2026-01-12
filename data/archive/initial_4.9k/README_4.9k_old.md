# Travel Order Resolver - Initial Dataset

## Overview

This directory contains the initial training/testing dataset for the Travel Order Resolver NLP project. The dataset consists of **4,956 unique French language phrases** for training and evaluating the travel order extraction system.

## Files

### Main Dataset Files

- **`dataset_initial.csv`** (4,956 phrases) - Complete shuffled dataset combining valid and invalid orders
- **`valid_orders_initial.csv`** (2,956 phrases) - Valid travel orders with extracted origin/destination
- **`invalid_orders.csv`** (2,000 phrases) - Invalid orders (no travel intent, incomplete, garbage, ambiguous)

### Reports and Statistics

- **`generation_report.json`** - Detailed generation statistics in JSON format
- **`statistics.txt`** - Human-readable statistical summary

## Dataset Composition

### Distribution by Validity

| Type | Count | Percentage |
|------|-------|------------|
| Valid orders | 2,956 | 59.6% |
| Invalid orders | 2,000 | 40.4% |
| **Total** | **4,956** | **100%** |

### Valid Orders - Categories

| Category | Count | Percentage | Description |
|----------|-------|------------|-------------|
| standard | 783 | 26.5% | Clear origin-destination markers ("de X à Y") |
| name_ambiguity | 496 | 16.8% | Proper names that could be cities or people |
| inverted_order | 390 | 13.2% | Destination before origin |
| misspelling | 299 | 10.1% | Spelling errors in city names |
| no_markers | 297 | 10.0% | No prepositions ("billet X Y") |
| no_capitals | 247 | 8.4% | Lowercase, missing accents |
| compound_name | 244 | 8.3% | Hyphenated city names (Port-Boulet) |
| additional_info | 150 | 5.1% | Extra info (times, passengers) |
| complex_question | 50 | 1.7% | Complex travel queries |

### Valid Orders - Difficulty Distribution

| Difficulty | Count | Percentage |
|------------|-------|------------|
| Easy | 604 | 20.4% |
| Medium | 1,777 | 60.1% |
| Hard | 575 | 19.5% |

### Invalid Orders - Categories

| Category | Count | Percentage | Description |
|----------|-------|------------|-------------|
| no_intent | 454 | 22.7% | No travel intention (greetings, questions) |
| garbage | 416 | 20.8% | Random text, spam, foreign languages |
| ambiguous | 410 | 20.5% | Too many cities, contradictions |
| incomplete_dest | 329 | 16.4% | Missing destination |
| incomplete_origin | 323 | 16.2% | Missing origin |
| incomplete_grammar | 68 | 3.4% | Grammatically incomplete |

## File Format

All CSV files use the following schema:

```
sentenceID, sentence, origin, destination, is_valid, difficulty, category, notes
```

### Column Descriptions

- **sentenceID**: Unique integer identifier (1, 2, 3, ...)
- **sentence**: The French language phrase
- **origin**: Departure city (empty for invalid orders)
- **destination**: Arrival city (empty for invalid orders)
- **is_valid**: 1 for valid travel orders, 0 for invalid
- **difficulty**: "easy", "medium", or "hard" (for valid orders)
- **category**: Category label (see tables above)
- **notes**: Additional annotations or comments

### Example Rows

**Valid order:**
```csv
1,"Je voudrais un billet de Paris à Lyon",Paris,Lyon,1,easy,standard,
```

**Invalid order (no intent):**
```csv
2,"Bonjour comment allez-vous",,,0,easy,no_intent,greeting
```

**Hard case (name ambiguity + lowercase):**
```csv
3,"avec mes amis florence et paris, je voudrais aller de paris a florence",Paris,Florence,1,hard,name_ambiguity,"lowercase, florence/paris=prénoms"
```

## Statistics

### Sentence Length

**Invalid Orders:**
- Min: 1 word
- Max: 11 words
- Average: 4.4 words

**Valid Orders:**
- Min: 3 words
- Max: 14 words
- Average: 7.5 words

### Top 20 Cities Used

1. Paris (253 occurrences)
2. Saint-Étienne (234)
3. Marseille (210)
4. Nice (208)
5. Angers (207)
6. Lyon (205)
7. Toulon (201)
8. Aix-en-Provence (199)
9. Toulouse (189)
10. Le Havre (186)
...and 10 more

## Key NLP Challenges Represented

### 1. Ambiguous Proper Names
Cities that are also common first names:
- "Je veux aller à **Tours** voir mon ami **Albert**" (Albert = person name)
- "Avec mes amis **florence** et **paris**, je voudrais aller de **paris** a **florence**" (lowercase confusion)

### 2. Compound City Names
Cities with hyphens, often written without:
- Port-Boulet → "Port Boulet"
- Aix-en-Provence → "Aix en Provence"
- Saint-Étienne → "Saint Étienne"

### 3. Missing Formatting
- No capitals: "je veux aller a paris"
- No accents: "marseille" instead of "Marseille"
- No hyphens: "saint etienne"

### 4. Spelling Errors
- "pari" → Paris
- "lion" → Lyon
- "marsel" → Marseille

### 5. Variable Syntax
- Standard: "de Paris à Lyon"
- Inverted: "à Lyon depuis Paris"
- No markers: "billet Paris Lyon"

## Usage

### Loading the Data

**Python (pandas):**
```python
import pandas as pd

# Load complete dataset
df = pd.read_csv('data/dataset_initial.csv', encoding='utf-8')

# Load only valid orders
valid_df = pd.read_csv('data/valid_orders_initial.csv', encoding='utf-8')

# Load only invalid orders
invalid_df = pd.read_csv('data/invalid_orders.csv', encoding='utf-8')
```

### Train/Val/Test Split

Recommended split for machine learning:
- **Training**: 70% (~3,470 phrases)
- **Validation**: 15% (~743 phrases)
- **Test**: 15% (~743 phrases)

```python
from sklearn.model_selection import train_test_split

# First split: separate test set
train_val, test = train_test_split(df, test_size=0.15, random_state=42, stratify=df['is_valid'])

# Second split: separate validation from training
train, val = train_test_split(train_val, test_size=0.176, random_state=42, stratify=train_val['is_valid'])
# 0.176 ≈ 0.15/0.85 to get 15% of original dataset

print(f"Train: {len(train)} ({len(train)/len(df)*100:.1f}%)")
print(f"Val:   {len(val)} ({len(val)/len(df)*100:.1f}%)")
print(f"Test:  {len(test)} ({len(test)/len(df)*100:.1f}%)")
```

## Quality Assurance

### Deduplication
All datasets have been deduplicated to ensure no sentence appears more than once.

### UTF-8 Encoding
All files use strict UTF-8 encoding to properly handle French accents and special characters.

### Validation
A validation script ([validate_dataset.py](../validate_dataset.py)) is provided to check:
- Correct file structure
- Required column presence
- Sequential IDs
- No duplicates
- Proper distribution across categories

## Next Steps

This initial dataset of ~5,000 phrases should be expanded to 10,000 total by:
1. Collaborating with other project groups to share datasets
2. Manually creating additional complex edge cases
3. Augmenting existing data with variations

The target distribution for 10,000 phrases:
- 7,000 valid orders (70%)
- 3,000 invalid orders (30%)

## License

This dataset was generated for the EPITECH T-AIA-911 Travel Order Resolver project.

## Generation Scripts

The following scripts were used to generate this dataset:
- `generate_invalid_orders.py` - Invalid orders generator
- `generate_valid_orders.py` - Valid orders generator
- `merge_datasets.py` - Merge and shuffle datasets
- `fix_duplicates.py` - Remove duplicate sentences
- `generate_report.py` - Generate statistics and reports
- `validate_dataset.py` - Validate dataset integrity

All scripts are located in the project root directory.
