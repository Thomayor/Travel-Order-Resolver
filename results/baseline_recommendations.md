# Baseline Model - Improvement Recommendations

**Test Set Performance**: 67.81% exact match accuracy

---

## 1. Invalid Order Detection [CRITICAL]

**Finding**: 101 false positives (invalid orders predicted as valid)

**Recommendation**: Implement validation logic: require both origin AND destination, check for duplicates, add confidence thresholds

**Expected Impact**: +20-30% validity detection accuracy

---

## 2. Misspelling Handling [CRITICAL]

**Finding**: Only 1.2% accuracy on misspelled text

**Recommendation**: Enable fuzzy matching in gazetteer with max_distance=2 or 3

**Expected Impact**: +40-50% on misspelling category, +10-15% overall

---

## 3. Compound Name Matching [HIGH]

**Finding**: Only 41.3% accuracy on compound names

**Recommendation**: Add space-to-hyphen normalization for patterns like "sur Mer", "en Provence"

**Expected Impact**: +20-30% on compound names, +5% overall

---

## 4. Duplicated City Predictions [MEDIUM]

**Finding**: 231 cases where same city predicted for both origin and dest

**Recommendation**: Add heuristic validation: if only one city found, mark as INVALID instead of duplicating

**Expected Impact**: +5-10% on no_markers and inverted_order categories

---

## 5. Inverted Order Pattern [MEDIUM]

**Finding**: Only 65.2% accuracy on inverted order

**Recommendation**: Add patterns for "Cap sur X", "Vers X depuis Y", "à X en partance de Y"

**Expected Impact**: +15-20% on inverted_order category

---

## 6. Baseline Ceiling [STRATEGIC]

**Finding**: Baseline plateaus at 67.8% exact match accuracy

**Recommendation**: Transition to CamemBERT NER model for context-aware extraction

**Expected Impact**: Target 85%+ accuracy (vs current ~69%)

---

