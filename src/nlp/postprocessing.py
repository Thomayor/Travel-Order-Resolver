"""
Post-processing Module for Entity Extraction

Extracts origin and destination entities from token-level NER predictions.
Handles multi-word city names (e.g., "Port-Boulet", "Aix-en-Provence").
Validates extracted entities against the SNCF gazetteer with fuzzy matching.
"""

from typing import Dict, List, Optional, Tuple


def extract_entities(tokens: List[str], labels: List[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract origin and destination from tokens and labels.

    Reconstructs multi-word entities using BIO tags:
    - B-ORIGIN/B-DEST: Beginning of entity
    - I-ORIGIN/I-DEST: Inside entity (continuation)

    Args:
        tokens: List of tokens (words)
        labels: List of BIO labels (same length as tokens)

    Returns:
        Tuple of (origin, destination)
        Returns (None, None) if no entities found

    Examples:
        tokens:  ["de", "Port", "-", "Boulet", "à", "Lyon"]
        labels:  ["O", "B-ORIGIN", "I-ORIGIN", "I-ORIGIN", "O", "B-DEST"]
        result:  ("Port-Boulet", "Lyon")

        tokens:  ["de", "Aix", "-", "en", "-", "Provence", "à", "Paris"]
        labels:  ["O", "B-DEST", "I-DEST", "I-DEST", "I-DEST", "I-DEST", "O", "B-ORIGIN"]
        result:  ("Paris", "Aix-en-Provence")  # Note inverted order
    """
    if len(tokens) != len(labels):
        raise ValueError(f"Tokens and labels must have same length: {len(tokens)} vs {len(labels)}")

    origin = None
    destination = None

    # Find origin entity
    origin_tokens = []
    in_origin = False

    for token, label in zip(tokens, labels):
        if label == "B-ORIGIN":
            # Start of origin entity
            origin_tokens = [token]
            in_origin = True
        elif label == "I-ORIGIN" and in_origin:
            # Continuation of origin entity
            origin_tokens.append(token)
        elif in_origin:
            # End of origin entity
            break

    if origin_tokens:
        origin = reconstruct_city_name(origin_tokens)
        # Clean prepositions that were incorrectly extracted (e.g., "de Paris" → "Paris")
        origin = _clean_prepositions(origin)

    # Find destination entity
    dest_tokens = []
    in_dest = False

    for token, label in zip(tokens, labels):
        if label == "B-DEST":
            # Start of dest entity
            dest_tokens = [token]
            in_dest = True
        elif label == "I-DEST" and in_dest:
            # Continuation of dest entity
            dest_tokens.append(token)
        elif in_dest:
            # End of dest entity
            break

    if dest_tokens:
        destination = reconstruct_city_name(dest_tokens)
        # Clean prepositions that were incorrectly extracted
        destination = _clean_prepositions(destination)

    return origin, destination


def _clean_prepositions(entity: str) -> str:
    """
    Remove French prepositions that were incorrectly extracted by the NER model.

    Args:
        entity: Extracted city name (may start with preposition)

    Returns:
        Cleaned city name without leading prepositions

    Examples:
        >>> _clean_prepositions("de Paris")
        'Paris'
        >>> _clean_prepositions("depuis Lyon")
        'Lyon'
        >>> _clean_prepositions("à Nice")
        'Nice'
    """
    if not entity:
        return entity

    # French prepositions that sometimes get extracted by mistake
    prepositions = ['de', 'depuis', 'à', 'a', 'pour', 'vers', 'du', 'des', 'au', 'aux']

    words = entity.strip().split()
    if not words:
        return entity

    # Remove leading prepositions
    while words and words[0].lower() in prepositions:
        words.pop(0)

    return ' '.join(words) if words else entity


def reconstruct_city_name(token_list: List[str]) -> str:
    """
    Reconstruct city name from list of tokens.

    Handles hyphens correctly:
    - ["Port", "-", "Boulet"] -> "Port-Boulet"
    - ["Aix", "-", "en", "-", "Provence"] -> "Aix-en-Provence"
    - ["Paris"] -> "Paris"

    Args:
        token_list: List of tokens forming a city name

    Returns:
        Reconstructed city name as string
    """
    if not token_list:
        return ""

    result = []
    for token in token_list:
        if token == "-":
            # Don't add space before hyphen, just append it
            if result:
                result[-1] += "-"
        else:
            # Check if previous token ended with hyphen
            if result and result[-1].endswith("-"):
                result[-1] += token
            else:
                result.append(token)

    return " ".join(result)


def extract_all_entities(tokens: List[str], labels: List[str]) -> List[Tuple[str, str, int, int]]:
    """
    Extract all entities from tokens (including multiple entities of same type).

    This is useful for debugging and analysis when there are multiple cities mentioned.

    Args:
        tokens: List of tokens
        labels: List of BIO labels

    Returns:
        List of tuples: (entity_text, entity_type, start_idx, end_idx)
        entity_type is either "ORIGIN" or "DEST"

    Example:
        tokens:  ["de", "Paris", "à", "Lyon", "via", "Dijon"]
        labels:  ["O", "B-ORIGIN", "O", "B-DEST", "O", "B-DEST"]
        result:  [("Paris", "ORIGIN", 1, 2), ("Lyon", "DEST", 3, 4), ("Dijon", "DEST", 5, 6)]
    """
    entities = []
    current_entity = []
    current_type = None
    start_idx = None

    for i, (token, label) in enumerate(zip(tokens, labels)):
        if label.startswith("B-"):
            # Save previous entity if any
            if current_entity and current_type:
                entity_text = reconstruct_city_name(current_entity)
                entities.append((entity_text, current_type, start_idx, i))

            # Start new entity
            entity_type = label.split("-")[1]  # "ORIGIN" or "DEST"
            current_entity = [token]
            current_type = entity_type
            start_idx = i

        elif label.startswith("I-") and current_entity:
            # Continue current entity
            entity_type = label.split("-")[1]
            if entity_type == current_type:
                current_entity.append(token)
            else:
                # Type mismatch, save previous and start new
                entity_text = reconstruct_city_name(current_entity)
                entities.append((entity_text, current_type, start_idx, i))
                current_entity = [token]
                current_type = entity_type
                start_idx = i

        elif current_entity:
            # End of entity (label is "O" or different type)
            entity_text = reconstruct_city_name(current_entity)
            entities.append((entity_text, current_type, start_idx, i))
            current_entity = []
            current_type = None
            start_idx = None

    # Save last entity if any
    if current_entity and current_type:
        entity_text = reconstruct_city_name(current_entity)
        entities.append((entity_text, current_type, start_idx, len(tokens)))

    return entities


def validate_against_gazetteer(entity: str, gazetteer) -> Optional[str]:
    """
    Validate an extracted entity against the SNCF gazetteer.

    First tries an exact (normalized) match, then falls back to fuzzy matching
    to handle residual misspellings from the NER model.

    Args:
        entity: Extracted city name (may be misspelled or unnormalized)
        gazetteer: Gazetteer instance with is_valid_location / fuzzy_match methods

    Returns:
        Canonical city name if found, None otherwise
    """
    if not entity:
        return None

    from .preprocessing import preprocess_for_matching

    # Exact match (normalized)
    canonical = gazetteer.get_canonical_name(entity)
    if canonical:
        return canonical

    # Prefix matching BEFORE fuzzy match for short/incomplete names
    # This prevents "saint-lau" from fuzzy-matching to "Saint-Ay"
    # instead of prefix-matching to "Saint-Laurent-*"
    if len(entity) <= 15:
        entity_norm = preprocess_for_matching(entity)
        prefix_matches = []

        for norm_name, canonical_name in gazetteer.normalized_to_original.items():
            if norm_name.startswith(entity_norm) and norm_name != entity_norm:
                prefix_matches.append((canonical_name, len(norm_name) - len(entity_norm)))

        if prefix_matches:
            prefix_matches.sort(key=lambda x: x[1])
            closest_diff = prefix_matches[0][1]
            # If closest match is only 1-2 chars longer, it's a typo — resolve directly
            # e.g. "pari" → "paris" (diff=1), not ambiguous
            if closest_diff <= 2:
                return prefix_matches[0][0]
            # Multiple matches with longer differences = genuinely ambiguous prefix
            # e.g. "saint-lau" → Saint-Laurent-du-Var, Saint-Laurent-de-Mure, etc.
            if len(prefix_matches) > 1:
                return None  # Ambiguous - triggers suggestion system
            return prefix_matches[0][0]  # Single match - auto-correct

    # Fuzzy match fallback (Levenshtein distance ≤ 2)
    matches = gazetteer.fuzzy_match(entity, max_distance=2)
    if matches:
        return matches[0][0]  # Best match (closest distance)

    return None


def get_all_matches(entity: str, gazetteer) -> List[str]:
    """
    Get all possible matches for an entity (for suggestions).

    Returns all cities that could match the entity, useful for
    interactive disambiguation.

    Args:
        entity: Extracted city name (may be misspelled or unnormalized)
        gazetteer: Gazetteer instance

    Returns:
        List of all matching canonical city names (empty if no match)
    """
    if not entity:
        return []

    from .preprocessing import preprocess_for_matching

    all_matches = []
    entity_norm = preprocess_for_matching(entity)

    # SPECIAL CASE: Saint-* names are often ambiguous (220 cities!)
    # If entity starts with "saint", use the FULL normalized prefix for matching
    # Example: "saint lau" → normalized "saintlau" → matches "saintlaurent*"
    if entity_norm.startswith("saint") and len(entity_norm) <= 15:
        # Normalize: replace spaces AND hyphens with empty string for flexible matching
        # "saint lau" → "saintlau", "saint-laurent-du-var" → "saintlaurentduvar"
        prefix = entity_norm.replace(" ", "").replace("-", "")  # e.g., "saintlau"

        for norm_name, canonical_name in gazetteer.normalized_to_original.items():
            # Normalize gazetteer entry the same way for comparison
            norm_name_clean = norm_name.replace(" ", "").replace("-", "")
            if norm_name_clean.startswith(prefix):
                all_matches.append(canonical_name)

        # If we found multiple matches, return them for disambiguation
        if len(all_matches) > 1:
            return list(dict.fromkeys(all_matches))  # Remove duplicates, preserve order

    # Exact match (normalized)
    canonical = gazetteer.get_canonical_name(entity)
    if canonical:
        return [canonical]  # Exact match, return immediately

    # Fuzzy match (all matches within distance 2)
    fuzzy_matches = gazetteer.fuzzy_match(entity, max_distance=2)
    all_matches.extend([match[0] for match in fuzzy_matches])

    # Prefix matching for short names
    if len(entity) <= 10:
        entity_norm = preprocess_for_matching(entity)
        prefix_matches = []

        for norm_name, canonical_name in gazetteer.normalized_to_original.items():
            if norm_name.startswith(entity_norm) and canonical_name not in all_matches:
                prefix_matches.append((canonical_name, len(norm_name) - len(entity_norm)))

        # Sort by length difference (shorter first)
        prefix_matches.sort(key=lambda x: x[1])
        all_matches.extend([match[0] for match in prefix_matches])

    return all_matches


def fuzzy_match(entity: str, candidates: List[str], max_distance: int = 2) -> Optional[str]:
    """
    Find the closest matching candidate for an entity string.

    Uses Levenshtein distance on normalized forms (no accents, lowercase).

    Args:
        entity: Input string to match
        candidates: List of candidate strings to compare against
        max_distance: Maximum edit distance to accept

    Returns:
        Best matching candidate, or None if no match within max_distance
    """
    from .preprocessing import preprocess_for_matching

    if not entity or not candidates:
        return None

    entity_norm = preprocess_for_matching(entity)
    best_match = None
    best_distance = max_distance + 1

    for candidate in candidates:
        candidate_norm = preprocess_for_matching(candidate)
        distance = _levenshtein(entity_norm, candidate_norm)
        if distance < best_distance:
            best_distance = distance
            best_match = candidate

    return best_match if best_distance <= max_distance else None


def _levenshtein(s1: str, s2: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if s1 == s2:
        return 0
    if not s1:
        return len(s2)
    if not s2:
        return len(s1)

    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1, 1):
        curr = [i]
        for j, c2 in enumerate(s2, 1):
            curr.append(min(
                prev[j] + 1,        # deletion
                curr[j - 1] + 1,    # insertion
                prev[j - 1] + (c1 != c2),  # substitution
            ))
        prev = curr
    return prev[-1]


# Context keywords indicating the preceding word is a person name, not a city
PERSON_CONTEXT_KEYWORDS = {
    "avec", "chez", "pour", "monsieur", "madame", "mademoiselle",
    "mr", "mme", "mlle", "docteur", "dr", "professeur", "prof",
    "ami", "amie", "copain", "copine", "frere", "soeur", "pere", "mere",
    "oncle", "tante", "cousin", "cousine", "collegue",
    "mon", "ma", "notre", "votre", "son", "sa",
}

# City names that are also common person names
AMBIGUOUS_NAMES = {
    "florence", "albert", "lourdes", "nancy", "leon",
    "victor", "eugene", "charlotte", "alice", "rose",
    "marguerite", "colette", "jean", "pierre",
}


def disambiguate_person_vs_city(
    tokens: List[str],
    labels: List[str],
    origin: Optional[str],
    destination: Optional[str],
) -> Tuple[Optional[str], Optional[str]]:
    """
    Post-process NER results to detect when an ambiguous name
    is a person name rather than a city.

    Rules:
    - If an entity is an ambiguous name preceded by a person-context keyword
      (e.g., "avec Florence"), it is likely a person name → remove that entity.
    - If the same ambiguous name appears as both origin and destination,
      keep only the one in a clear travel context (e.g., "de X", "a X").

    Args:
        tokens: Original tokens from the sentence
        labels: BIO labels from NER
        origin: Extracted origin city name
        destination: Extracted destination city name

    Returns:
        Tuple of (origin, destination) after disambiguation
    """
    if not tokens or not labels:
        return origin, destination

    tokens_lower = [t.lower() for t in tokens]

    for entity_type, entity_value in [("ORIGIN", origin), ("DEST", destination)]:
        if not entity_value:
            continue
        if entity_value.lower() not in AMBIGUOUS_NAMES:
            continue

        # Find the B-tag position for this entity
        tag = f"B-{entity_type}"
        for i, label in enumerate(labels):
            if label == tag:
                # Check preceding token(s) for person context
                if i > 0 and tokens_lower[i - 1] in PERSON_CONTEXT_KEYWORDS:
                    if entity_type == "ORIGIN":
                        origin = None
                    else:
                        destination = None
                break

    return origin, destination


def validate_extraction(origin: Optional[str], destination: Optional[str]) -> bool:
    """
    Validate that extraction is valid (both origin and destination found).

    Args:
        origin: Extracted origin city
        destination: Extracted destination city

    Returns:
        True if both origin and destination are non-empty, False otherwise
    """
    return bool(origin and destination)


if __name__ == '__main__':
    # Demo
    print("Post-processing Module Demo")
    print("=" * 50)

    # Test case 1: Simple extraction
    tokens1 = ["Je", "veux", "aller", "de", "Paris", "à", "Lyon"]
    labels1 = ["O", "O", "O", "O", "B-ORIGIN", "O", "B-DEST"]
    origin1, dest1 = extract_entities(tokens1, labels1)
    print(f"\nTest 1:")
    print(f"  Tokens: {tokens1}")
    print(f"  Labels: {labels1}")
    print(f"  Result: {origin1} -> {dest1}")

    # Test case 2: Multi-word city with hyphens
    tokens2 = ["de", "Port", "-", "Boulet", "à", "Aix", "-", "en", "-", "Provence"]
    labels2 = ["O", "B-ORIGIN", "I-ORIGIN", "I-ORIGIN", "O", "B-DEST", "I-DEST", "I-DEST", "I-DEST", "I-DEST"]
    origin2, dest2 = extract_entities(tokens2, labels2)
    print(f"\nTest 2:")
    print(f"  Tokens: {tokens2}")
    print(f"  Labels: {labels2}")
    print(f"  Result: {origin2} -> {dest2}")

    # Test case 3: Invalid (no entities)
    tokens3 = ["Bonjour", "comment", "allez", "-", "vous"]
    labels3 = ["O", "O", "O", "O", "O"]
    origin3, dest3 = extract_entities(tokens3, labels3)
    print(f"\nTest 3:")
    print(f"  Tokens: {tokens3}")
    print(f"  Labels: {labels3}")
    print(f"  Result: {origin3} -> {dest3}")
    print(f"  Valid: {validate_extraction(origin3, dest3)}")

    # Test case 4: Extract all entities
    tokens4 = ["de", "Paris", "à", "Lyon", "via", "Dijon"]
    labels4 = ["O", "B-ORIGIN", "O", "B-DEST", "O", "B-DEST"]
    all_entities = extract_all_entities(tokens4, labels4)
    print(f"\nTest 4 (all entities):")
    print(f"  Tokens: {tokens4}")
    print(f"  Labels: {labels4}")
    print(f"  All entities: {all_entities}")
