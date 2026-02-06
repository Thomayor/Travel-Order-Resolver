# Baseline Validation Results

**Date**: 2026-02-06
**Dataset**: Validation set (1,500 sentences)
**System**: Baseline rule-based NLP extractor
**Mode**: NLP-only (no pathfinding)

---

## Executive Summary

The baseline system was evaluated on 1,500 validation sentences with the following key results:

- **Overall Extraction Accuracy**: **68.95%** (724/1050 valid orders correctly extracted)
- **Validity Detection Accuracy**: **70.00%** (1050/1500 sentences classified correctly)
- **Processing Performance**: ~1 second per sentence, all 1,500 processed successfully

### Performance by Difficulty
- **Easy**: 87.44% (181/207) ✅ Strong performance
- **Medium**: 74.80% (472/631) ✅ Good performance
- **Hard**: 33.49% (71/212) ⚠️ Needs improvement

---

## Detailed Metrics

### 1. Validity Detection

The system's ability to distinguish valid travel orders from invalid sentences:

```
Confusion Matrix:
  True Positives (valid→valid):     1,050  ✅
  True Negatives (invalid→invalid):     0  ❌ CRITICAL ISSUE
  False Positives (invalid→valid):    450  ❌ High error rate
  False Negatives (valid→invalid):      0  ✅

Metrics:
  Accuracy:   70.00%
  Precision:  70.00%
  Recall:    100.00%  (over-predicts validity)
  F1 Score:   82.35%
```

**Critical Finding**: The system predicted **ALL 1,500 sentences as valid**, when 450 should have been marked as INVALID. This indicates a major weakness in invalid order detection.

### 2. Extraction Accuracy (Valid Orders Only)

For the 1,050 valid travel orders, extraction performance:

```
Origin Accuracy:       81.14%  (852/1050)  ✅
Destination Accuracy:  79.52%  (835/1050)  ✅
Exact Match (both):    68.95%  (724/1050)  ⚠️
```

**Analysis**:
- The system is reasonably good at extracting **either** origin or destination (~80%)
- However, getting **both correct** drops to ~69%, showing room for improvement
- The gap between individual and exact match accuracy (81% → 69%) indicates errors are often on one entity, not both

---

## Performance by Category

### Top 3 Strengths

1. **no_capitals** (lowercase text): **90.3%** (84/93)
   - Example: "un train de annecy a limoges" ✅
   - Strong normalization handles missing capitals well

2. **additional_info** (extra temporal/passenger info): **88.9%** (48/54)
   - Example: "Billet Lyon Paris pour ce soir" ✅
   - System ignores additional context effectively

3. **standard** (clear structure): **85.3%** (221/259)
   - Example: "Je cherche un train de Toulon à Dijon" ✅
   - Rule-based patterns work well for standard phrases

### Top 3 Weaknesses

1. **misspelling**: **9.8%** (11/112) ❌ **CRITICAL**
   - Example: "trajet tours reeims" → Expected: Tours→Reims, Got: INVALID→Tours
   - Root cause: Fuzzy matching not enabled or insufficient distance threshold
   - Impact: 112 sentences (~10% of valid orders) completely fail

2. **compound_name** (multi-word cities): **46.1%** (41/89) ❌
   - Example: "Billet Nîmes Boulogne-sur-Mer" → Expected: Nîmes→Boulogne-sur-Mer, Got: INVALID→INVALID
   - Root cause: Gazetteer not matching hyphenated names correctly
   - Impact: Major cities like Boulogne-sur-Mer, Aix-en-Provence failing

3. **complex_question**: **46.7%** (7/15) ⚠️
   - Example: "Y a-t-il des trains directs entre Le Mans et Lyon" → Expected: Le Mans→Lyon, Got: Lyon→Le Mans
   - Root cause: "entre X et Y" pattern not handled (order confusion)
   - Impact: Small volume but indicates pattern coverage gaps

---

## Error Pattern Analysis

### Pattern 1: Destination-Only Extraction (Duplicated City)

**Frequency**: Very common in error samples

**Example**:
```
Sentence: "Je voudrais réserver un billet de Le Havre pour Nice"
Expected: Le Havre → Nice
Predicted: Nice → Nice  ❌
```

**Root Cause**:
- System extracts "Nice" as destination correctly
- Fails to extract "Le Havre" as origin (multi-word city issue)
- Heuristic fallback duplicates the only found location for both origin and destination

**Categories Affected**: standard, compound_name, no_capitals

### Pattern 2: Origin-Only Extraction (Same City for Both)

**Frequency**: Very common in inverted_order, no_markers

**Example**:
```
Sentence: "Cap sur Marseille depuis Lyon"
Expected: Lyon → Marseille
Predicted: Lyon → Lyon  ❌
```

**Root Cause**:
- "Cap sur" not recognized as destination marker
- Only "depuis Lyon" (origin) extracted
- Heuristic duplicates origin for destination

**Categories Affected**: inverted_order, no_markers, complex_question

### Pattern 3: Complete Failure on Misspellings

**Frequency**: 101/112 misspelling sentences (90.2% failure rate)

**Example**:
```
Sentence: "trajet tours reeims"
Expected: Tours → Reims
Predicted: INVALID → Tours  ❌
```

**Root Cause**:
- "reeims" (misspelled Reims) not recognized
- Fuzzy matching either disabled or insufficient threshold
- System only extracts correctly spelled "Tours"

**Impact**: This is the **#1 critical weakness** of the baseline system

### Pattern 4: Compound Name Failures

**Frequency**: 48/89 compound name sentences (53.9% failure rate)

**Example**:
```
Sentence: "Un billet de Boulogne sur Mer pour Nice"
Expected: Boulogne-sur-Mer → Nice
Predicted: Nice → Nice  ❌
```

**Root Cause**:
- Gazetteer stores "Boulogne-sur-Mer" (with hyphens)
- Input has "Boulogne sur Mer" (with spaces)
- Preprocessing doesn't normalize space-hyphen variations
- System fails to recognize compound name

**Impact**: Major French cities with hyphens systematically fail

---

## Critical Issues Identified

### Issue #1: Invalid Order Detection Completely Broken

**Severity**: CRITICAL ❌

**Description**: The system classified ALL 1,500 sentences as valid, when 450 (30%) should have been marked INVALID.

**Examples of Missed Invalid Orders**:
- "Lille Montpellier Toulouse Paris" (too many cities) → Predicted as valid ❌
- "basé à dijon" (missing destination) → Predicted as valid ❌
- "keneq gulyrosado potixad" (garbage text) → Predicted as valid ❌

**Root Cause**:
- The baseline extractor has no robust invalid detection logic
- If it finds ANY location, it marks the order as valid (even if incomplete)
- No validation for:
  - Missing origin or destination
  - Ambiguous patterns (multiple cities)
  - Non-travel intent sentences

**Impact**:
- False positive rate: 100% (450/450 invalid orders)
- System outputs garbage extractions for invalid sentences
- Downstream pathfinding receives invalid inputs

**Recommended Fix**:
1. Add validation checks:
   - Both origin AND destination must be extracted
   - Extracted entities must pass confidence threshold
   - Sentence must contain travel intent markers
2. Implement confidence scoring
3. Add explicit invalid patterns (negations, ambiguous structures)

### Issue #2: Fuzzy Matching Not Working for Misspellings

**Severity**: CRITICAL ❌

**Description**: Only 11/112 (9.8%) misspelling sentences correctly extracted.

**Examples**:
- "Dijo" (Dijon) → Not recognized ❌
- "reeims" (Reims) → Not recognized ❌
- "aler" (aller) → Not handled ❌

**Root Cause**:
- Fuzzy matching in gazetteer may not be enabled by default
- Edit distance threshold (if enabled) may be too strict
- Misspelled verbs ("aler" vs "aller") break pattern matching

**Impact**:
- 10% of valid validation set fails completely
- Real-world user input (typos common) will have high failure rate

**Recommended Fix**:
1. Enable fuzzy matching with `max_distance=2` (as documented in CLAUDE.md)
2. Test with `max_distance=3` for severe misspellings
3. Add common French verb variations to preprocessing

### Issue #3: Compound Name Normalization Insufficient

**Severity**: HIGH ⚠️

**Description**: Only 41/89 (46.1%) compound name sentences correctly extracted.

**Examples**:
- "Boulogne sur Mer" → Not matching "Boulogne-sur-Mer" ❌
- "Aix en Provence" → Not matching "Aix-en-Provence" ❌

**Root Cause**:
- Gazetteer stores names with hyphens
- Input text has spaces instead of hyphens
- Preprocessing normalizes hyphens but doesn't handle space→hyphen conversion

**Impact**:
- Major French cities systematically fail
- Affects ~6% of validation set (89 sentences)

**Recommended Fix**:
1. Add space→hyphen normalization for known compound patterns:
   - "sur Mer" → "-sur-Mer"
   - "en Provence" → "-en-Provence"
   - "les Bains" → "-les-Bains"
2. Update gazetteer to include space-separated aliases
3. Test fuzzy matching across compound parts

---

## Recommendations for Improvement

### Priority 1: Fix Invalid Order Detection (Immediate)

**Effort**: Medium
**Impact**: High (fixes 30% misclassification rate)

**Action Items**:
1. Implement validation logic in `baseline.py`:
   ```python
   def is_valid_extraction(origin, destination, confidence):
       # Both must be extracted
       if not origin or not destination:
           return False
       # No duplicates
       if origin == destination:
           return False
       # Confidence threshold
       if confidence < 0.5:
           return False
       return True
   ```

2. Add confidence scoring based on:
   - Pattern match strength (keyword vs heuristic)
   - Gazetteer match type (exact vs fuzzy)
   - Number of locations found (exactly 2 is ideal)

3. Test on validation set, target: 90%+ invalid detection

### Priority 2: Enable Fuzzy Matching (Quick Win)

**Effort**: Low
**Impact**: High (fixes 10% of validation set)

**Action Items**:
1. Enable fuzzy matching in gazetteer initialization:
   ```python
   # In baseline.py
   extractor = BaselineExtractor(fuzzy_match_distance=2)
   ```

2. Test with different distance thresholds (2, 3)

3. Re-evaluate on misspelling category, target: 50%+ accuracy

### Priority 3: Improve Compound Name Handling (Medium Priority)

**Effort**: Medium
**Impact**: Medium (fixes 6% of validation set)

**Action Items**:
1. Add compound name patterns to preprocessing
2. Create gazetteer aliases with space variations
3. Test on compound_name category, target: 70%+ accuracy

### Priority 4: Add Missing Patterns (Lower Priority)

**Effort**: Medium
**Impact**: Low (affects <1% of validation set)

**Action Items**:
1. Add "entre X et Y" pattern for complex questions
2. Add "Cap sur X" destination pattern
3. Test on complex_question and inverted_order categories

---

## Comparison with Baseline System Goals

| Metric | Target (from CLAUDE.md) | Validation Result | Status |
|--------|-------------------------|-------------------|--------|
| Overall Accuracy | 70% | **68.95%** | ⚠️ Slightly below |
| Easy Difficulty | ~87% | **87.44%** | ✅ On target |
| Medium Difficulty | ~73% | **74.80%** | ✅ Above target |
| Hard Difficulty | ~35% | **33.49%** | ✅ On target |
| Misspelling Handling | 7.6% → 50%+ (with fuzzy) | **9.8%** | ❌ Critical gap |

**Analysis**:
- The baseline performs **as expected** for most difficulty levels
- **Misspelling handling is the critical blocker** to reaching 70%+ overall accuracy
- Enabling fuzzy matching (as documented) should unlock +10-15% accuracy gain

---

## Next Steps

### Immediate Actions (This Week)

1. ✅ **Validation Testing Complete**
   - 1,500 sentences processed
   - Comprehensive metrics generated
   - Error patterns documented

2. **Fix Critical Issues** (Recommended order):
   - [ ] Enable fuzzy matching (1 hour)
   - [ ] Implement invalid order detection (4 hours)
   - [ ] Add compound name normalization (2 hours)

3. **Re-test on Validation Set**
   - Run evaluation script again
   - Compare metrics before/after
   - Document improvements

### Medium-Term (Next 2 Weeks)

4. **CamemBERT Training**
   - Use lessons from baseline error analysis
   - Focus on weak categories (misspelling, compound names)
   - Target: 85%+ accuracy

5. **Integration Testing**
   - Test fixed baseline with pathfinding module
   - End-to-end validation on full pipeline
   - Performance benchmarking

---

## Files Generated

### Reports
- `results/baseline_validation_report.txt` - Text summary
- `results/baseline_validation_metrics.json` - JSON metrics
- `results/baseline_validation_errors.json` - Error samples by category

### Output
- `results/baseline_validation_output.csv` - System predictions (1,500 rows)

### Scripts
- `scripts/evaluate_baseline_validation.py` - Evaluation tool (reusable)

---

## Conclusion

The baseline system demonstrates **solid performance on standard cases** (85%+ accuracy) but has **three critical weaknesses**:

1. **Invalid order detection**: 0% true negative rate (all sentences predicted as valid)
2. **Misspelling handling**: 9.8% accuracy (fuzzy matching not enabled)
3. **Compound name matching**: 46.1% accuracy (normalization insufficient)

**With the recommended fixes**, the baseline system should achieve:
- **75-80% overall accuracy** (from current 68.95%)
- **50%+ misspelling accuracy** (from current 9.8%)
- **90%+ invalid detection** (from current 0%)

These improvements will establish a **strong baseline** before transitioning to CamemBERT for the target 85%+ accuracy.

---

**Report Generated**: 2026-02-06
**Evaluation Script**: `scripts/evaluate_baseline_validation.py`
**Dataset**: `data/val.csv` (1,500 sentences)
