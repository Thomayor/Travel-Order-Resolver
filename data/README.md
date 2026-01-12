# Travel Order Resolver - 10K Dataset

## Overview

This directory contains the **production-ready 10,000-phrase dataset** for the Travel Order Resolver NLP project. This expanded dataset provides comprehensive training data for machine learning models to extract travel orders from French language sentences.

## Files

### Main Dataset Files

- **`dataset_final.csv`** (10,000 phrases) - Complete shuffled dataset combining valid and invalid orders
- **`valid_orders_final.csv`** (7,000 phrases) - Valid travel orders with extracted origin/destination
- **`invalid_orders_final.csv`** (3,000 phrases) - Invalid orders (no travel intent, incomplete, garbage, ambiguous)

### Reports and Statistics

- **`statistics_10k.txt`** - Human-readable statistical summary
- **`generation_report_10k.json`** - Detailed generation statistics in JSON format

### Legacy/Intermediate Files

- `dataset_initial.csv` - Initial 4,956-phrase dataset (Phase 1)
- `dataset_10k.csv` - Pre-deduplication 11,898-phrase dataset
- `*_dedup.csv` files - Intermediate deduplicated versions

## Dataset Composition

### Distribution by Validity

| Type | Count | Percentage |
|------|-------|------------|
| Valid orders | 7,000 | 70.0% |
| Invalid orders | 3,000 | 30.0% |
| **Total** | **10,000** | **100%** |

### Valid Orders - Categories

| Category | Count | Percentage | Description |
|----------|-------|------------|-------------|
| standard | 1,838 | 26.3% | Clear origin-destination markers ("de X à Y") |
| name_ambiguity | 1,190 | 17.0% | Proper names that could be cities or people |
| inverted_order | 917 | 13.1% | Destination before origin |
| misspelling | 721 | 10.3% | Spelling errors in city names |
| no_markers | 696 | 9.9% | No prepositions ("billet X Y") |
| compound_name | 577 | 8.2% | Hyphenated city names (Port-Boulet) |
| no_capitals | 575 | 8.2% | Lowercase, missing accents |
| additional_info | 353 | 5.0% | Extra info (times, passengers) |
| complex_question | 133 | 1.9% | Complex travel queries |

### Valid Orders - Difficulty Distribution

| Difficulty | Count | Percentage | Baseline Accuracy | Description |
|------------|-------|------------|-------------------|-------------|
| Easy | 1,423 | 20.3% | **87.14%** ✅ | Clear structure, correct spelling, no ambiguity |
| Medium | 4,179 | 59.7% | **73.39%** ⚠️ | Questions, inverted order, one name ambiguity |
| Hard | 1,398 | 20.0% | **34.84%** ❌ | Misspellings, multiple ambiguous names, complex syntax |

**Important**: The `misspelling` category (721 sentences, 10.3%) is **always classified as hard** and represents the baseline model's biggest weakness (7.6% accuracy on this category alone). This is due to fuzzy matching not being enabled.

**Full difficulty criteria**: See [../docs/DIFFICULTY_LEVELS.md](../docs/DIFFICULTY_LEVELS.md) for complete definitions and examples.

### Invalid Orders - Categories

| Category | Count | Percentage | Description |
|----------|-------|------------|-------------|
| garbage | 855 | 28.5% | Random text, spam, foreign languages |
| ambiguous | 634 | 21.1% | Too many cities, contradictions |
| no_intent | 514 | 17.1% | No travel intention (greetings, questions) |
| incomplete_dest | 462 | 15.4% | Missing destination |
| incomplete_origin | 459 | 15.3% | Missing origin |
| incomplete_grammar | 76 | 2.5% | Grammatically incomplete |

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
- Average: 4.5 words

**Valid Orders:**
- Min: 3 words
- Max: 15 words
- Average: 7.5 words

### Top 20 Cities Used (Valid Orders)

1. Paris (580 occurrences)
2. Aix-en-Provence (511)
3. Saint-Étienne (473)
4. Le Mans (469)
5. Limoges (466)
6. Villeurbanne (464)
7. Toulouse (460)
8. Toulon (454)
9. Strasbourg (452)
10. Metz (445)
11. Bordeaux (445)
12. Lille (440)
13. Reims (439)
14. Marseille (439)
15. Brest (438)
16. Dijon (434)
17. Perpignan (434)
18. Lyon (433)
19. Grenoble (433)
20. Amiens (430)

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
df = pd.read_csv('data/dataset_final.csv', encoding='utf-8')

# Load only valid orders
valid_df = pd.read_csv('data/valid_orders_final.csv', encoding='utf-8')

# Load only invalid orders
invalid_df = pd.read_csv('data/invalid_orders_final.csv', encoding='utf-8')
```

### Train/Val/Test Split

Recommended split for machine learning (EPITECH Phase 2 requirements):

- **Training**: 70% (~7,000 phrases)
- **Validation**: 15% (~1,500 phrases)
- **Test**: 15% (~1,500 phrases)

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
All datasets have been rigorously deduplicated to ensure no sentence appears more than once.

### UTF-8 Encoding
All files use strict UTF-8 encoding to properly handle French accents and special characters.

### Validation
Multiple validation scripts were used to check:
- Correct file structure
- Required column presence
- Sequential IDs (1 to N)
- No duplicates
- Proper distribution across categories
- Target counts (7,000 valid + 3,000 invalid)

## Generation Process

This dataset was generated through a multi-stage pipeline:

1. **Initial Generation** (Phase 1): 4,956 phrases using template-based generators
2. **Expansion** (Phase 2 - KAN-23): Scaled up to ~11,900 phrases
3. **Deduplication**: Removed 2,154 duplicate sentences
4. **Finalization**: Adjusted to exactly 10,000 phrases (7,000 valid + 3,000 invalid)

### Generation Scripts

The following scripts were used to create this dataset:

- `generate_dataset_10k.py` - Main generation script (produces ~11,900 phrases)
- `validate_dataset_10k.py` - Deduplication and validation
- `finalize_dataset_10k.py` - Final adjustment to 10,000 phrases
- `generate_report_10k.py` - Statistics generation

All scripts are located in the project root directory.

## Comparison to Initial Dataset

| Metric | Initial (4.9K) | Final (10K) | Change |
|--------|----------------|-------------|--------|
| Total phrases | 4,956 | 10,000 | +102% |
| Valid orders | 2,956 (59.6%) | 7,000 (70.0%) | +137% |
| Invalid orders | 2,000 (40.4%) | 3,000 (30.0%) | +50% |
| Categories (valid) | 9 | 9 | Same |
| Categories (invalid) | 6 | 6 | Same |
| Avg sentence length (valid) | 7.5 words | 7.5 words | Same |

## Use Cases

This dataset is designed for:

1. **Named Entity Recognition (NER)** - Extract origin/destination from text
2. **Intent Classification** - Identify valid vs invalid travel orders
3. **Sequence Labeling** - Token-level classification (B-ORIGIN, I-ORIGIN, B-DEST, I-DEST, O)
4. **Transfer Learning** - Fine-tune CamemBERT or similar French language models
5. **Baseline Evaluation** - Test rule-based and keyword-based extractors

## License

This dataset was generated for the EPITECH T-AIA-911 Travel Order Resolver project (2025).

## Changelog

### Version 1.0 (2026-01-09) - 10K Dataset
- Expanded from 4,956 to 10,000 total phrases
- Adjusted distribution to 70% valid / 30% invalid (EPITECH Phase 2 target)
- Rigorous deduplication (removed 2,154 duplicates)
- Comprehensive validation and quality checks
- Generated detailed statistics reports

### Version 0.1 (2025-12-11) - Initial Dataset
- Created initial 4,956-phrase dataset
- 9 categories of valid orders
- 6 categories of invalid orders
- Basic template-based generation
