# Baseline Model Evaluation - Analysis Report

## Executive Summary

The rule-based baseline NLP model was evaluated on the complete 10,000-sentence dataset. The model achieved an overall accuracy of **65.01%**, which falls within the expected range for a baseline rule-based system (60-70%).

**Key Takeaways:**
- ✅ Strong performance on simple, well-formatted sentences (87%)
- ✅ Excellent at detecting invalid orders (F1 = 0.87)
- ⚠️ Struggles significantly with misspellings (7.6% accuracy)
- ⚠️ Moderate difficulty with compound city names (41.8%)
- ⚠️ Hard sentences remain challenging (34.8% accuracy)

---

## Overall Performance Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Overall Accuracy | **65.01%** | 60-70% | ✅ On Target |
| Precision (Valid Detection) | 90.18% | >85% | ✅ Excellent |
| Recall (Valid Detection) | 83.30% | >80% | ✅ Good |
| F1 Score | 0.8660 | >0.85 | ✅ Excellent |
| Correct Extractions | 6,501 / 10,000 | - | - |

### Classification Matrix

|  | Predicted Valid | Predicted Invalid |
|--|----------------|-------------------|
| **Actually Valid (7,000)** | 5,831 (TP) | 1,169 (FN) |
| **Actually Invalid (3,000)** | 635 (FP) | 2,365 (TN) |

**Interpretation:**
- **True Positives (5,831)**: Successfully extracted valid orders
- **True Negatives (2,365)**: Correctly rejected invalid orders
- **False Positives (635)**: Invalid orders mistakenly extracted (21% of invalid)
- **False Negatives (1,169)**: Valid orders missed (17% of valid)

---

## Performance by Category

### Valid Order Categories

#### Excellent Performance (>80% Accuracy)

| Category | Accuracy | Correct | Total | Notes |
|----------|----------|---------|-------|-------|
| `no_capitals` | **88.87%** | 511 | 575 | Lowercase text well-handled |
| `additional_info` | **87.54%** | 309 | 353 | Time/passenger info doesn't interfere |
| `no_markers` | **86.35%** | 601 | 696 | "billet X Y" format recognized |
| `standard` | **83.46%** | 1,534 | 1,838 | "de X à Y" works reliably |

**Analysis**: The baseline model excels at straightforward patterns where:
- Keywords are present and clear
- City names are correctly spelled
- Syntax follows expected patterns

#### Moderate Performance (60-80% Accuracy)

| Category | Accuracy | Correct | Total | Notes |
|----------|----------|---------|-------|-------|
| `inverted_order` | **70.34%** | 645 | 917 | "à Y depuis X" - keyword order matters |
| `name_ambiguity` | **70.92%** | 844 | 1,190 | Florence/Paris as names vs cities |

**Analysis**: Moderate difficulty due to:
- Non-standard keyword ordering
- Ambiguity between person names and city names
- Requires more sophisticated context understanding

#### Poor Performance (<50% Accuracy)

| Category | Accuracy | Correct | Total | Issues |
|----------|----------|---------|-------|--------|
| **`misspelling`** | **7.63%** | 55 | 721 | ⚠️ **CRITICAL WEAKNESS** |
| `compound_name` | **41.77%** | 241 | 577 | Hyphenated names problematic |
| `complex_question` | **40.60%** | 54 | 133 | Complex syntax confuses rules |

**Critical Issue - Misspellings (7.63%):**

The model almost completely fails on misspelled city names. Examples:
- "Bordeau" instead of "Bordeaux" → Not recognized
- "Lionne" instead of "Lyon" → Not recognized
- "bilet lile reim" → Complete failure

**Root Cause**: The gazetteer requires exact matches. While fuzzy matching is implemented, it's either:
- Not enabled by default
- Has too restrictive edit distance threshold
- Not applied during extraction

**Recommended Fix**: Enable fuzzy matching with `max_distance=2` or `max_distance=3` in gazetteer.

### Invalid Order Categories

| Category | Accuracy | Correct | Total | Notes |
|----------|----------|---------|-------|-------|
| `garbage` | **100.00%** | 855 | 855 | ✅ Perfect detection |
| `incomplete_grammar` | **100.00%** | 76 | 76 | ✅ Perfect detection |
| `no_intent` | **100.00%** | 514 | 514 | ✅ Perfect detection |
| `incomplete_dest` | **35.28%** | 163 | 462 | Partial detection |
| `incomplete_origin` | **17.65%** | 81 | 459 | Difficult to detect |
| **`ambiguous`** | **2.84%** | 18 | 634 | ⚠️ Very difficult |

**Analysis**:
- ✅ **Excellent** at rejecting obvious invalid orders (garbage, greetings)
- ⚠️ **Poor** at detecting subtle invalidity (ambiguous, incomplete)
- The model tends to over-extract (false positives) rather than under-extract

---

## Performance by Difficulty

| Difficulty | Accuracy | Correct | Total | Assessment |
|------------|----------|---------|-------|------------|
| **Easy** | **87.14%** | 1,240 | 1,423 | ✅ Excellent |
| **Medium** | **73.39%** | 3,067 | 4,179 | ✅ Good |
| **Hard** | **34.84%** | 487 | 1,398 | ⚠️ Expected but low |

**Difficulty Breakdown:**
- **Easy sentences** (87% accuracy): Well-formatted, clear keywords, no ambiguity
- **Medium sentences** (73% accuracy): Some ambiguity, non-standard patterns
- **Hard sentences** (35% accuracy): Misspellings, name ambiguity, complex syntax

**Hard Sentence Challenges:**
1. Misspellings combined with lowercase
2. Multiple proper names (Florence, Paris, Albert)
3. Complex question syntax
4. Compound names with misspellings

---

## Error Analysis

### Error Distribution

| Error Type | Count | Percentage | Description |
|------------|-------|------------|-------------|
| **Both Wrong** | 1,459 | 41.7% | Both origin AND destination incorrect |
| **Dest Wrong** | 1,204 | 34.4% | Only destination incorrect |
| **Origin Wrong** | 836 | 23.9% | Only origin incorrect |

**Total Errors**: 3,499 / 10,000 (34.99%)

**Insights:**
- **Both wrong** (41.7%): Complete extraction failure - usually due to misspellings or unrecognized patterns
- **Dest wrong** (34.4%): Origin extracted but destination failed - keyword-based heuristics may favor origin
- **Origin wrong** (23.9%): Rarest error type - suggests origin keywords are more reliable

### Sample Error Cases

#### Misspelling Failures
```
Sentence: "Je veux aller de Bordeau à Limogees"
Expected: Bordeaux → Limoges
Predicted: (empty) → (empty)
Issue: Neither misspelled city recognized
```

#### Name Ambiguity
```
Sentence: "avec mes amis rémy et paris, je voudrais aller de le havre à nantes"
Expected: Le Havre → Nantes
Predicted: Nantes → Nantes
Issue: "paris" (person name) confused with Paris (city)
```

#### Compound Name + Misspelling
```
Sentence: "Un billet Paris Aix-en-Proovence"
Expected: Paris → Aix-en-Provence
Predicted: (empty) → (empty)
Issue: Misspelled compound name not recognized
```

---

## Comparison to Target Performance

| Metric | Baseline (Rule-based) | Target (CamemBERT) | Gap |
|--------|----------------------|-------------------|-----|
| Overall Accuracy | 65.01% | 85%+ | -20% |
| Easy Sentences | 87.14% | 95%+ | -8% |
| Medium Sentences | 73.39% | 90%+ | -17% |
| Hard Sentences | 34.84% | 70%+ | -35% |
| Misspelling Category | 7.63% | 80%+ | -72% ⚠️ |

**Gap Analysis:**
- The baseline model is **20 percentage points** below the target for advanced NLP
- **Misspellings** represent the largest gap (-72%)
- Even on easy sentences, there's room for improvement (-8%)
- Hard sentences show the limitation of rule-based approaches (-35%)

---

## Strengths of Baseline Model

1. **High Precision (90%)**: When the model extracts a valid order, it's usually correct
2. **Excellent Invalid Detection**: Perfect (100%) at rejecting garbage, greetings, incomplete grammar
3. **Fast**: Rule-based extraction is computationally cheap
4. **Interpretable**: Easy to understand why extractions succeed or fail
5. **No Training Required**: Works immediately without ML training
6. **Good on Standard Patterns**: 83-89% on well-formatted sentences

---

## Weaknesses of Baseline Model

### 1. **Misspelling Catastrophe (7.6% accuracy)**
- **Impact**: 721 sentences (7.2% of dataset)
- **Current**: Almost complete failure
- **Quick Fix**: Enable fuzzy matching in gazetteer
- **Expected Improvement**: +40-50% on misspelling category → Overall +3-4%

### 2. **Compound Names Difficulty (41.8%)**
- **Impact**: 577 sentences (5.8% of dataset)
- **Issue**: Hyphenated names ("Port-Boulet", "Aix-en-Provence") not always recognized
- **Solution**: Better handling of hyphens in preprocessing

### 3. **Ambiguity Handling (2.8% on ambiguous)**
- **Impact**: 634 sentences (6.3% of dataset)
- **Issue**: Rule-based systems can't understand context
- **Solution**: Requires machine learning (CamemBERT)

### 4. **Complex Questions (40.6%)**
- **Impact**: 133 sentences (1.3% of dataset)
- **Issue**: Non-standard syntax breaks keyword patterns
- **Solution**: More sophisticated parsing or ML

### 5. **Inverted Order (70.3%)**
- **Impact**: 917 sentences (9.2% of dataset)
- **Issue**: "à Paris depuis Lyon" - destination keyword comes first
- **Solution**: Better bidirectional keyword search

---

## Recommendations for Improvement

### Immediate Fixes (Baseline v2)

1. **Enable Fuzzy Matching** (Priority: CRITICAL)
   - Add `max_distance=2` to gazetteer lookups
   - Expected gain: +3-4% overall accuracy
   - Impact: 721 misspelling sentences

2. **Improve Compound Name Handling**
   - Enhance hyphen normalization in preprocessing
   - Expected gain: +2% overall accuracy
   - Impact: 577 compound name sentences

3. **Bidirectional Keyword Search**
   - Check both "de X à Y" and "à Y depuis X" patterns
   - Expected gain: +2% overall accuracy
   - Impact: 917 inverted order sentences

**Potential Baseline v2 Accuracy**: 65% → **72%** (+7%)

### Medium-Term: Hybrid Approach

Combine baseline rules with lightweight ML:
- Use baseline for easy cases (87% accuracy)
- Apply ML classifier for ambiguous cases
- Expected accuracy: **75-80%**

### Long-Term: CamemBERT Fine-Tuning

- Fine-tune French BERT model on 10K dataset
- Token classification for NER (B-ORIGIN, I-ORIGIN, B-DEST, I-DEST)
- Expected accuracy: **85-90%**
- Requires: GPU, training time, larger dataset (ideally 15-20K)

---

## Conclusion

The baseline rule-based model achieves **65.01% accuracy**, successfully demonstrating:
- ✅ Proof of concept for travel order extraction
- ✅ Strong performance on well-formatted sentences (87%)
- ✅ Excellent invalid order detection (F1 = 0.87)

However, it reveals critical limitations:
- ❌ Misspelling handling (7.6% accuracy) is unacceptable for production
- ❌ Ambiguous sentences (2.8%) cannot be handled by rules alone
- ❌ Hard sentences (34.8%) need more sophisticated NLP

**Next Steps:**
1. **Immediate**: Enable fuzzy matching → Expected 72% accuracy
2. **Phase 2**: Fine-tune CamemBERT → Target 85%+ accuracy
3. **Evaluation**: Validate on held-out test set before deployment

---

**Report Generated**: 2026-01-09
**Dataset**: dataset_final.csv (10,000 sentences)
**Model**: Baseline Rule-Based Extractor v1.0
