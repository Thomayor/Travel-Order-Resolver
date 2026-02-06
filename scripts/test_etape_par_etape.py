#!/usr/bin/env python3
"""
Script de test complet pour l'intervenant

Execute tous les tests essentiels du projet en une seule commande.
Temps d'execution: ~2-3 minutes
"""

import sys
import subprocess
from pathlib import Path

def print_section(title):
    """Print a formatted section header."""
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)
    print()

def run_test(description, command):
    """Run a test command and report success/failure."""
    print(f"[TEST] {description}")
    print(f"  Commande: {command}")
    print()

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print("[OK] Test reussi")
            # Show relevant output (first 10 lines)
            if result.stdout:
                lines = result.stdout.strip().split('\n')[:10]
                for line in lines:
                    print(f"  {line}")
            return True
        else:
            print("[ERREUR] Test echoue")
            if result.stderr:
                print(result.stderr[:500])
            return False

    except subprocess.TimeoutExpired:
        print("[ERREUR] Timeout (>60s)")
        return False
    except Exception as e:
        print(f"[ERREUR] {e}")
        return False
    finally:
        print()

def main():
    """Run all essential tests."""

    print()
    print("*" * 70)
    print("  TEST COMPLET - TRAVEL ORDER RESOLVER")
    print("  Temps estime: 2-3 minutes")
    print("*" * 70)

    results = []

    # Test 1: NLP Preprocessing
    print_section("1/6 - Module NLP: Preprocessing")
    results.append(run_test(
        "Normalisation de texte francais",
        "python scripts/demos/demo_preprocessing.py"
    ))

    # Test 2: NLP Gazetteer
    print_section("2/6 - Module NLP: Gazetteer")
    results.append(run_test(
        "Base de donnees de locations (66 villes/gares)",
        "python scripts/demos/demo_gazetteer.py"
    ))

    # Test 3: NLP Baseline
    print_section("3/6 - Module NLP: Baseline Extractor")
    results.append(run_test(
        "Extraction origine/destination",
        "python scripts/demos/demo_baseline.py"
    ))

    # Test 4: Pathfinding
    print_section("4/6 - Module Pathfinding: Graph & Dijkstra")
    pathfinding_test = '''
import sys
sys.path.insert(0, ".")
from src.pathfinding.graph_loader import get_or_build_graph
from src.pathfinding.algorithms import dijkstra

# Load graph
graph = get_or_build_graph()
print(f"Graph charge: {graph.number_of_nodes()} stations, {graph.number_of_edges()} connexions")

# Test routes
routes = [
    ("87686006", "87723197", "Paris Gare de Lyon -> Lyon Part Dieu"),
    ("87611004", "87751008", "Toulouse -> Marseille"),
]

for origin, dest, desc in routes:
    path, time = dijkstra(graph, origin, dest)
    print(f"{desc}: {len(path)} stations, {time} min")

print("[OK] Pathfinding tests passed!")
'''
    results.append(run_test(
        "Chargement graph et algorithme de plus court chemin",
        f'python -c "{pathfinding_test}"'
    ))

    # Test 5: Unit tests
    print_section("5/6 - Tests Unitaires (103 tests)")
    results.append(run_test(
        "Pytest - preprocessing, gazetteer, baseline",
        "pytest tests/ -v --tb=short"
    ))

    # Test 6: Integration test
    print_section("6/6 - Test Integration Complete")
    test_code = '''
import sys
sys.path.insert(0, ".")
from src.nlp.baseline import load_extractor
from src.pathfinding.graph_loader import get_or_build_graph
from src.pathfinding.algorithms import dijkstra

# Test NLP
extractor = load_extractor()
result = extractor.extract("Je veux aller de Paris a Lyon")
assert result["origin"] == "Paris" and result["destination"] == "Lyon"
print("[OK] NLP: Paris -> Lyon extraits correctement")

# Test Pathfinding
graph = get_or_build_graph()
path, time = dijkstra(graph, "87686006", "87723197")
assert len(path) > 0 and time > 0
print(f"[OK] Pathfinding: Paris -> Lyon = {time} min, {len(path)} stations")

print("[SUCCESS] Integration test passed!")
'''

    results.append(run_test(
        "Test d'integration NLP + Pathfinding",
        f'python -c "{test_code}"'
    ))

    # Summary
    print_section("RESULTAT FINAL")

    passed = sum(results)
    total = len(results)

    print(f"Tests reussis: {passed}/{total}")
    print()

    if passed == total:
        print("[SUCCESS] Tous les tests sont passes!")
        print()
        print("Le projet est pret pour la presentation.")
        return 0
    else:
        print(f"[WARNING] {total - passed} test(s) echoue(s)")
        print()
        print("Verifiez les erreurs ci-dessus.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
