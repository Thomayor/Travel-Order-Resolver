"""
Post-processing Module for Entity Extraction

Extracts origin and destination entities from token-level NER predictions.
Handles multi-word city names (e.g., "Port-Boulet", "Aix-en-Provence").
"""

from typing import List, Tuple, Optional


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

    return origin, destination


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
