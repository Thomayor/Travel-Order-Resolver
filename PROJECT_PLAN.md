# Travel Order Resolver - Project Implementation Plan

## Project Overview

Build an NLP-based system that processes French text commands to generate appropriate train itineraries using SNCF schedules. The system must extract origin and destination from natural language sentences and provide optimal train routes.

---

## Architecture Components

### 1. NLP Module (Core Component - MUST BE ISOLATED)
- **Purpose**: Extract departure and destination from French text
- **Input**: Text file with format `sentenceID,sentence` (UTF-8 encoding)
- **Output**:
  - Valid orders: `sentenceID,Departure,Destination`
  - Invalid orders: `sentenceID,INVALID` or more specific error code
- **Key Challenges**:
  - Handle cities/stations with common word names (Port-Boulet)
  - Distinguish cities from people names (Paris, Albert, Florence)
  - Handle missing capitals, accents, hyphens
  - Support various grammatical structures
  - Handle misspellings

### 2. Pathfinding Module
- **Purpose**: Find optimal train route between stations
- **Input**: `sentenceID,Departure,Destination`
- **Output**: `sentenceID,Departure,Step1,Step2,...,Destination`
- **Implementation**: Graph algorithms (Dijkstra, A*, etc.)
- **Data Source**: SNCF open data

### 3. Voice Recognition Module (BONUS - Optional)
- **Purpose**: Convert speech to text
- **Note**: Not the core focus, use existing libraries

---

## Phase 1: Research & Planning (Week 1)

### 1.1 NLP Research
- [ ] Study NLP techniques for Named Entity Recognition (NER)
- [ ] Research French language models:
  - CamemBERT (French BERT variant)
  - FlauBERT
  - spaCy French models
- [ ] Review transformer architecture ("Attention is All You Need")
- [ ] Investigate simpler baseline approaches:
  - Bag of words
  - Rule-based pattern matching
  - spaCy NER

### 1.2 Graph Algorithm Research
- [ ] Review pathfinding algorithms:
  - Dijkstra's algorithm
  - A* algorithm
  - Bellman-Ford
- [ ] Study Neo4j graph database
- [ ] Understand complexity trade-offs

### 1.3 Technology Stack Selection
**Recommended Stack:**
- **Language**: Python 3.9+
- **NLP Libraries**:
  - Baseline: spaCy, NLTK
  - Advanced: transformers (HuggingFace), CamemBERT
- **Graph/Pathfinding**:
  - Neo4j (graph database)
  - NetworkX (Python graph library)
- **Data Processing**: pandas, numpy
- **Evaluation**: scikit-learn (metrics)

---

## Phase 2: Dataset Creation (Week 1-2)

### 2.1 Training Dataset Requirements
- **Target**: ~10,000 sentences
- **Diversity**: ~300 different sentence structures
- **Collaboration**: Work with other groups to get diverse writing styles

### 2.2 Dataset Categories

#### Valid Travel Orders (70%)
**Sentence Structures to Include:**

1. **Direct format**: "Je voudrais un billet Toulouse Paris"
2. **With prepositions**: "Je souhaite me rendre à Paris depuis Toulouse"
3. **Question format**: "A quelle heure y a-t-il des trains vers Paris en partance de Toulouse?"
4. **Inverted order**: "Comment me rendre à Port Boulet depuis Tours?"
5. **Complex sentences**: "Avec mes amis florence et paris, je voudrais aller de paris a florence"
6. **Informal**: "Je veux aller à Tours voir mon ami Albert en partant de Bordeaux"

**Variations to Include:**
- Missing capitals, accents, hyphens
- Different verb forms (aller, partir, voyager, se rendre)
- Different prepositions (de, depuis, à, vers, en partance de)
- Time references (demain, ce soir, lundi prochain)
- Cities that are also common names (Albert, Paris, Florence, Lourdes)
- Multi-word station names (Port-Boulet, La Rochelle)

#### Invalid Orders (30%)
- General questions not about travel
- Incomplete sentences
- Ambiguous requests (missing origin or destination)
- Complete nonsense

### 2.3 Dataset Format
```csv
sentenceID,sentence,origin,destination,is_valid
1,"Je voudrais un billet de Paris à Lyon",Paris,Lyon,1
2,"Bonjour comment allez-vous",,,0
3,"je veux aller a tours voir albert depuis bordeaux",Bordeaux,Tours,1
```

### 2.4 Dataset Split
- Training: 70% (~7,000 sentences)
- Validation: 15% (~1,500 sentences)
- Test: 15% (~1,500 sentences)

### 2.5 Difficulty Levels ⭐ (KAN-23 - Completed)

**Status**: ✅ Implemented in 10K dataset

Valid orders are classified into 3 difficulty levels based on linguistic complexity:

| Difficulty | % | Baseline Accuracy | Criteria |
|------------|---|-------------------|----------|
| **Easy** | 20% | 87% | Clear structure, correct spelling, unambiguous |
| **Medium** | 60% | 73% | Questions, inverted order, one name ambiguity |
| **Hard** | 20% | 35% | Misspellings, multiple ambiguous names, complex |

**Critical Findings**:
- The `misspelling` category is **ALWAYS classified as hard** (721 sentences)
- Baseline accuracy on misspellings: **7.6%** (catastrophic)
- Root cause: Fuzzy matching not enabled
- Quick fix available: Enable `gazetteer.fuzzy_match(max_distance=2)`
- Expected improvement: +40-50% on misspellings → +3-4% overall accuracy

**Documentation**: See [docs/DIFFICULTY_LEVELS.md](docs/DIFFICULTY_LEVELS.md) for:
- Complete difficulty criteria and decision rules
- Examples for each level
- Attribution logic by category
- Impact on model performance
- Recommendations for new datasets

**Importance**: Understanding difficulty levels is crucial for:
1. Evaluating model performance across complexity levels
2. Identifying model weaknesses (e.g., misspelling handling)
3. Prioritizing improvements (fuzzy matching = quick win)
4. Setting realistic targets for advanced models (CamemBERT)

---

## Phase 3: SNCF Data Integration (Week 2)

### 3.1 Data Sources
- **SNCF Open Data Portal**: https://data.sncf.com/
- Required datasets:
  - Station list (with coordinates, city names)
  - Train schedules/timetables
  - Station connections

### 3.2 Data Processing
- [ ] Download SNCF CSV files
- [ ] Clean and normalize station names
- [ ] Map stations to cities
- [ ] Import into Neo4j graph database
- [ ] Create station-to-station connections with weights (time/distance)

### 3.3 Graph Database Schema
```
Nodes:
- Station (id, name, city, latitude, longitude)
- City (name, stations[])

Relationships:
- CONNECTS_TO (from_station, to_station, duration, distance, line_name)
```

---

## Phase 4: Baseline Implementation (Week 2-3)

### 4.1 Simple NLP Solution
**Approach**: Rule-based + spaCy NER

**Implementation Steps:**
1. [ ] Use spaCy French model for tokenization and NER
2. [ ] Load SNCF city/station names as gazetteer
3. [ ] Implement pattern matching for common structures
4. [ ] Rules for determining origin vs destination:
   - Keywords: "de/depuis" → origin, "à/vers" → destination
   - Position: first location = origin (if no keywords)
5. [ ] Handle basic text normalization (lowercase, remove accents)

**Expected Performance**: 60-70% accuracy

### 4.2 Basic Pathfinding
1. [ ] Implement Dijkstra's algorithm
2. [ ] Use NetworkX for graph operations
3. [ ] Create CLI interface for input/output

### 4.3 Integration
1. [ ] Create command-line interface
2. [ ] Read input from file/stdin
3. [ ] Output in required format
4. [ ] Handle UTF-8 encoding

---

## Phase 5: Evaluation Metrics Setup (Week 3)

### 5.1 Define Metrics

**For NLP Component:**
- **Accuracy**: % of correctly identified origin-destination pairs
- **Precision/Recall/F1** for:
  - Valid order detection
  - Origin extraction
  - Destination extraction
- **Confusion Matrix**: Common error patterns
- **Robustness Metrics**:
  - Performance on sentences without capitals
  - Performance on sentences with misspellings
  - Performance on ambiguous city names

**For Pathfinding:**
- Route correctness
- Optimality (compared to known shortest paths)
- Computation time

### 5.2 Evaluation Framework
```python
def evaluate_nlp(predictions, ground_truth):
    # Calculate accuracy, precision, recall, F1
    # Track error types
    # Generate confusion matrix
    pass
```

### 5.3 Baseline Metrics
- Run baseline model on test set
- Document performance
- Identify common failure cases

---

## Phase 6: Advanced NLP Implementation (Week 4-5)

### 6.1 Transformer-Based Solution

**Model Selection**: CamemBERT (French BERT)

**Approach**: Fine-tune CamemBERT for Named Entity Recognition + Intent Classification

### 6.2 Implementation Steps

1. [ ] **Data Preparation**
   - Convert dataset to token classification format
   - Label tokens: B-ORIGIN, I-ORIGIN, B-DEST, I-DEST, O
   - Create HuggingFace Dataset format

2. [ ] **Model Architecture**
   ```
   Input: Tokenized sentence
   ↓
   CamemBERT (pre-trained)
   ↓
   Token Classification Head
   ↓
   Output: NER tags for each token
   ```

3. [ ] **Training**
   - Load pre-trained CamemBERT
   - Add token classification head
   - Fine-tune on training dataset
   - Hyperparameters:
     - Learning rate: 2e-5 to 5e-5
     - Batch size: 16-32
     - Epochs: 3-5
     - Optimizer: AdamW

4. [ ] **Post-processing**
   - Extract entities from NER tags
   - Validate against SNCF station/city list
   - Fuzzy matching for misspellings

### 6.3 Alternative: Custom BiLSTM-CRF
If CamemBERT is too resource-intensive:
- Word embeddings (Word2Vec/FastText on French corpus)
- BiLSTM layer
- CRF layer for sequence tagging

---

## Phase 7: Fine-Tuning & Optimization (Week 5-6)

### 7.1 Iterative Improvement
1. [ ] Analyze errors on validation set
2. [ ] Add challenging examples to training set
3. [ ] Adjust hyperparameters
4. [ ] Experiment with:
   - Data augmentation (synonym replacement, back-translation)
   - Ensemble methods (combine multiple models)
   - Custom pre-processing rules

### 7.2 Handle Edge Cases
- [ ] Implement fuzzy matching for misspellings (Levenshtein distance)
- [ ] Handle cities with multiple stations
- [ ] Disambiguation logic for ambiguous names
- [ ] Normalize text (accents, hyphens, capitals)

### 7.3 Track Metrics Evolution
- Document performance improvements
- Create graphs showing metric progression
- Compare baseline vs advanced model

---

## Phase 8: Pathfinding Enhancement (Week 6)

### 8.1 Advanced Features
- [ ] Implement A* with heuristics
- [ ] Consider multiple optimization criteria:
  - Shortest time
  - Fewest connections
  - Earliest arrival
- [ ] Handle timetable integration (if time permits)

### 8.2 Neo4j Integration
- [ ] Set up Neo4j database
- [ ] Import SNCF data
- [ ] Use Cypher queries for pathfinding
- [ ] Compare performance with NetworkX

---

## Phase 9: Documentation (Week 7)

### 9.1 Technical Documentation (PDF)

**Required Sections:**

1. **Architecture Overview**
   - System components diagram
   - Data flow diagram
   - Technology stack

2. **NLP Module Documentation**
   - Model architecture (baseline + advanced)
   - Training process description
   - Dataset statistics and examples
   - Hyperparameters and configuration
   - Detailed walkthrough of example sentence processing

3. **Evaluation Results**
   - Metrics definition
   - Baseline vs advanced model comparison
   - Performance on different test conditions
   - Error analysis
   - Graphs and visualizations

4. **Pathfinding Module**
   - Algorithm description
   - Complexity analysis
   - Graph structure
   - Example routes

5. **User Guide**
   - Installation instructions
   - Usage examples
   - Input/output format specification

6. **Experiments Log**
   - Different approaches tried
   - Results and lessons learned
   - Ablation studies

### 9.2 Code Documentation
- [ ] Docstrings for all functions/classes
- [ ] README.md with quick start guide
- [ ] requirements.txt / environment.yml
- [ ] Example scripts

---

## Phase 10: Testing & Validation (Week 7-8)

### 10.1 Unit Tests
- [ ] Test NLP module with known inputs
- [ ] Test pathfinding with sample graphs
- [ ] Test edge cases

### 10.2 Integration Tests
- [ ] End-to-end pipeline tests
- [ ] UTF-8 encoding tests
- [ ] Large batch processing

### 10.3 Cross-validation
- [ ] Run on test set (never used during training)
- [ ] Compare with other groups (if possible)
- [ ] Test on unseen sentence structures

---

## Bonus Features (If Time Permits)

### Priority 1: Robustness
- [ ] Handle intermediate stops
  - "Je voudrais aller de Toulouse à Paris en passant par Limoges"
  - Requires multi-stop pathfinding

### Priority 2: Speech-to-Text
- [ ] Integrate Google Speech API / Mozilla DeepSpeech
- [ ] Voice input pipeline
- [ ] Test with audio samples

### Priority 3: Advanced Optimization
- [ ] Consider waiting times in stations
- [ ] Real-time schedule integration
- [ ] Multiple transport modes

### Priority 4: Deployment
- [ ] Dockerize application
- [ ] Cloud deployment (Azure ML, AWS)
- [ ] REST API interface
- [ ] Monitor CPU/RAM usage

### Priority 5: Extended Coverage
- [ ] Handle destinations not in timetable
- [ ] Suggest alternatives
- [ ] Other transport modes (bus, plane)

---

## Project Structure

```
travel-order-resolver/
├── data/
│   ├── raw/                    # SNCF open data (CSV)
│   ├── processed/              # Cleaned datasets
│   ├── train.csv              # Training sentences
│   ├── val.csv                # Validation sentences
│   └── test.csv               # Test sentences
├── src/
│   ├── nlp/
│   │   ├── baseline.py        # Simple spaCy-based model
│   │   ├── transformer.py     # CamemBERT fine-tuning
│   │   ├── preprocessing.py   # Text normalization
│   │   └── postprocessing.py  # Entity extraction
│   ├── pathfinding/
│   │   ├── graph_builder.py   # Build graph from SNCF data
│   │   ├── algorithms.py      # Dijkstra, A*
│   │   └── neo4j_client.py    # Neo4j integration
│   ├── evaluation/
│   │   ├── metrics.py         # Evaluation metrics
│   │   └── visualize.py       # Result visualization
│   └── utils/
│       ├── io_handler.py      # Input/output processing
│       └── config.py          # Configuration
├── models/
│   ├── baseline/              # Saved baseline model
│   └── camembert/             # Fine-tuned CamemBERT
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_baseline_training.ipynb
│   ├── 03_transformer_training.ipynb
│   └── 04_evaluation.ipynb
├── docs/
│   ├── architecture.md
│   ├── technical_report.pdf   # Main deliverable
│   └── user_guide.md
├── tests/
│   ├── test_nlp.py
│   ├── test_pathfinding.py
│   └── test_integration.py
├── scripts/
│   ├── train_baseline.py
│   ├── train_transformer.py
│   └── inference.py
├── requirements.txt
├── README.md
└── main.py                     # CLI entry point
```

---

## Timeline Summary

| Week | Phase | Deliverables |
|------|-------|-------------|
| 1 | Research & Dataset Planning | Technology stack decision, dataset strategy |
| 2 | Dataset Creation & SNCF Data | Training dataset (initial), SNCF data imported |
| 3 | Baseline Implementation | Working baseline NLP + pathfinding |
| 4 | Advanced NLP - Part 1 | CamemBERT fine-tuning started |
| 5 | Advanced NLP - Part 2 | Fine-tuned model, improved metrics |
| 6 | Optimization & Enhancement | Edge cases handled, pathfinding complete |
| 7 | Documentation | Technical documentation (PDF) |
| 8 | Testing & Polish | Final testing, code cleanup |

---

## Risk Management

### Risk 1: Dataset Quality
- **Mitigation**: Start early, collaborate with other groups, use data augmentation

### Risk 2: Model Performance
- **Mitigation**: Implement baseline first, iterate based on metrics

### Risk 3: Computation Resources
- **Mitigation**: Use Google Colab for GPU, consider smaller models if needed

### Risk 4: Time Constraints
- **Mitigation**: Focus on core NLP component first, treat pathfinding as secondary

---

## Success Criteria

### Minimum Viable Product (MVP)
- [ ] NLP module extracts origin/destination with >70% accuracy
- [ ] Handles basic French sentences
- [ ] Basic pathfinding works
- [ ] Proper input/output format (UTF-8)
- [ ] Isolated NLP module for testing
- [ ] Basic documentation

### Target Success
- [ ] NLP accuracy >85% on test set
- [ ] Handles misspellings and missing capitals
- [ ] Fine-tuned transformer model
- [ ] Neo4j integration
- [ ] Comprehensive documentation with metrics
- [ ] Detailed error analysis

### Stretch Goals
- [ ] NLP accuracy >90%
- [ ] Speech-to-text integration
- [ ] Intermediate stops handling
- [ ] Cloud deployment
- [ ] Multiple language support

---

## Key Reminders

1. **NLP is the core focus** - Spend 70% of effort here
2. **Collaboration is essential** - Work with other groups on dataset
3. **Metrics are mandatory** - Document all experiments
4. **Baseline first** - Secure a working solution early
5. **Isolation required** - NLP module must be testable independently
6. **No web app needed** - CLI is sufficient
7. **UTF-8 encoding** - All files must use UTF-8
8. **Documentation is critical** - PDF report is a major deliverable

---

## Next Steps

1. Set up development environment
2. Create initial project structure
3. Download SNCF datasets
4. Begin collecting training sentences (collaborate!)
5. Implement baseline model
6. Start documentation from day 1
