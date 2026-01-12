# Documentation

This directory contains comprehensive technical documentation for the Travel Order Resolver project.

## 📚 Available Documentation

### Core Documentation

#### 1. **DIFFICULTY_LEVELS.md** ⭐ NEW
**Purpose**: Complete guide to the 3 difficulty levels in the dataset

**Contents**:
- Definition of Easy/Medium/Hard criteria
- Distribution in 10K dataset (20% / 60% / 20%)
- Baseline performance by difficulty (87% / 73% / 35%)
- Attribution rules by category
- Examples for each level
- Impact on model performance
- Recommendations for dataset generation

**Key Insight**: Misspellings are ALWAYS hard and represent the biggest performance gap (7.6% accuracy vs 87% for easy)

**When to read**:
- Understanding dataset composition
- Evaluating model performance
- Identifying improvement priorities
- Creating new training data

---

#### 2. **nlp_module_documentation.md**
**Purpose**: Complete technical documentation for the NLP module

**Contents**:
- Module architecture and components
- Preprocessing pipeline details
- Gazetteer implementation
- Baseline extractor algorithms
- API reference
- Usage examples
- Performance metrics

**When to read**:
- Working with the NLP module
- Understanding preprocessing
- Implementing new extraction strategies
- Debugging extraction issues

---

#### 3. **pathfinding_algorithm_comparison.md**
**Purpose**: Analysis and comparison of pathfinding algorithms

**Contents**:
- Algorithm comparison (Dijkstra, A*, Bellman-Ford, Floyd-Warshall)
- Complexity analysis
- Implementation recommendations
- Graph database considerations (Neo4j vs NetworkX)
- SNCF data integration strategy

**When to read**:
- Implementing the pathfinding module (Phase 7)
- Choosing the right algorithm
- Understanding trade-offs

---

#### 4. **comparaison_algorithmes_pathfinding_FR.md**
**Purpose**: French version of pathfinding algorithm comparison

**Contents**: Same as English version, in French

**When to read**: If you prefer French documentation for pathfinding

---

#### 5. **sentence_templates.md**
**Purpose**: Reference for dataset generation templates

**Contents**:
- All sentence templates used in generation
- Template variations by category
- French language patterns
- Generation strategy

**When to read**:
- Extending the dataset
- Understanding generation logic
- Creating new categories

---

## 📊 Dataset Documentation

Located in `../data/`:

- **data/README.md**: Complete 10K dataset documentation
- **data/archive/README.md**: Archive overview
- **data/archive/initial_4.9k/README.md**: Legacy dataset documentation
- **data/archive/intermediate_10k/README.md**: Generation artifacts documentation

---

## 📈 Evaluation Documentation

Located in project root:

- **EVALUATION_ANALYSIS.md**: In-depth baseline model evaluation
  - Performance metrics by category
  - Error analysis
  - Comparison to target (CamemBERT)
  - Recommendations for improvement

---

## 🎯 Project Planning

Located in project root:

- **PROJECT_PLAN.md**: 8-week implementation roadmap
  - Phases breakdown
  - Technology stack
  - Success criteria
  - Risk management
  - **Section 2.5**: Difficulty levels (references this doc)

---

## 🚀 Quick Start Guide

Located in project root:

- **CLAUDE.md**: Main developer guide
  - Project overview
  - Common commands
  - Architecture details
  - Module organization
  - Key implementation details
  - **Dataset Difficulty Levels section**: Quick reference to difficulty system

---

## 📑 Cross-References

### Difficulty Levels Referenced In:
1. **DIFFICULTY_LEVELS.md** (this file) - Complete definition
2. **CLAUDE.md** - Quick reference and key insights
3. **data/README.md** - Dataset composition context
4. **EVALUATION_ANALYSIS.md** - Performance analysis by difficulty
5. **PROJECT_PLAN.md** - Section 2.5 with implementation status

### Key Findings Propagated To:
- ⚠️ Misspelling weakness (7.6% accuracy) documented in ALL files
- ✅ Quick fix (fuzzy matching) mentioned in CLAUDE.md and PROJECT_PLAN.md
- 📊 Baseline performance (65.01%) with difficulty breakdown in EVALUATION_ANALYSIS.md

---

## 🔍 Finding Information

### "How do I...?"

| Task | Document |
|------|----------|
| Understand dataset difficulty | **DIFFICULTY_LEVELS.md** |
| Use the NLP module | **nlp_module_documentation.md** |
| Evaluate model performance | **EVALUATION_ANALYSIS.md** |
| Plan project phases | **PROJECT_PLAN.md** |
| Get started quickly | **CLAUDE.md** |
| Understand dataset composition | **data/README.md** |
| Choose pathfinding algorithm | **pathfinding_algorithm_comparison.md** |
| Generate new sentences | **sentence_templates.md** |

---

## 📝 Documentation Standards

All documentation in this project follows these principles:

1. **Clarity**: Technical accuracy with clear explanations
2. **Examples**: Concrete examples for every concept
3. **Cross-references**: Links between related documents
4. **Metrics**: Quantitative data where applicable
5. **Status**: Clear indication of implementation status
6. **Recommendations**: Actionable next steps

---

## 🔄 Recent Updates

### 2026-01-09 (KAN-23)
- ✅ Added **DIFFICULTY_LEVELS.md** (comprehensive difficulty guide)
- ✅ Updated **CLAUDE.md** with difficulty levels section
- ✅ Updated **data/README.md** with difficulty performance
- ✅ Updated **EVALUATION_ANALYSIS.md** with difficulty context
- ✅ Updated **PROJECT_PLAN.md** with Section 2.5

---

## 📮 Contributing to Documentation

When adding new documentation:

1. Add entry to this README
2. Cross-reference from relevant existing docs
3. Include practical examples
4. Specify when to read/use it
5. Follow the documentation standards above

---

**Last Updated**: 2026-01-09
**Project**: EPITECH T-AIA-911 Travel Order Resolver
