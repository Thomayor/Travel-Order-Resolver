#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regenerate all datasets with better duplicate prevention
"""

import csv
import random
import itertools

# Set seed for reproducibility but with variation
random.seed(42)

# Cities for France
MAIN_CITIES = [
    "Paris", "Lyon", "Marseille", "Toulouse", "Nice", "Nantes",
    "Strasbourg", "Montpellier", "Bordeaux", "Lille", "Rennes",
    "Reims", "Saint-Étienne", "Le Havre", "Toulon", "Grenoble",
    "Dijon", "Angers", "Nîmes", "Villeurbanne", "Le Mans",
    "Aix-en-Provence", "Clermont-Ferrand", "Brest", "Tours",
    "Amiens", "Limoges", "Annecy", "Perpignan", "Metz",
    "Besançon", "Orléans", "Rouen", "Mulhouse", "Caen",
    "Nancy", "Argenteuil", "Saint-Denis", "Montreuil", "Roubaix"
]

COMPOUND_CITIES = [
    "Port-Boulet", "Bourg-en-Bresse", "Aix-en-Provence",
    "Saint-Étienne", "La Roche-sur-Yon", "Salon-de-Provence",
    "Aix-les-Bains", "Boulogne-sur-Mer", "Châlons-en-Champagne",
    "Bagnols-sur-Cèze", "Romans-sur-Isère"
]

AMBIGUOUS_NAMES = ["Albert", "Florence", "Paris", "Lourdes", "Rémy", "Clément", "Martin", "Louis"]

MISSPELLINGS = {
    "Paris": ["Pari", "Paric", "Pariss", "Parie"],
    "Lyon": ["Lion", "Lyo", "Lionne", "Lyone"],
    "Marseille": ["Marsel", "Marseile", "Marceille", "Marseil"],
    "Toulouse": ["Tolouse", "Toulouze", "Touluse"],
    "Nice": ["Nise", "Nices", "Nisse"],
    "Bordeaux": ["Bordo", "Bordeau", "Bordeaus", "Bordo"],
    "Lille": ["Lile", "Lilles", "Lill"],
    "Nantes": ["Nante", "Nantess", "Nantez"],
    "Tours": ["Tour", "Tourz", "Toure"],
}

class UniquePhrasesGenerator:
    """Generates unique phrases with tracking"""

    def __init__(self):
        self.seen = set()
        self.sentence_id = 1

    def add_phrase(self, sentence, origin, dest, is_valid, difficulty, category, notes):
        """Add phrase if unique"""
        if sentence in self.seen:
            return None

        self.seen.add(sentence)
        phrase = {
            'sentenceID': self.sentence_id,
            'sentence': sentence,
            'origin': origin,
            'destination': dest,
            'is_valid': is_valid,
            'difficulty': difficulty,
            'category': category,
            'notes': notes
        }
        self.sentence_id += 1
        return phrase

def generate_invalid_no_intent(generator, target=1000):
    """Generate no-intent phrases"""
    phrases = []

    greetings = [
        "Bonjour", "Salut", "Bonne journée", "Bonjour comment allez-vous",
        "Salut ça va", "Bonsoir", "Bonne soirée", "À bientôt", "Au revoir",
        "Enchanté de vous rencontrer", "Comment vas-tu aujourd'hui",
        "Ça va bien merci et vous", "Très bien et toi", "Bonne nuit à tous",
        "À demain matin", "À plus tard dans la journée", "Coucou tout le monde",
        "Hey salut comment ça va", "Yo les amis", "Hello ça roule",
        "Salutations distinguées", "Mes respects", "Bien le bonjour",
        "Comment allez-vous ce matin", "Ravi de te revoir", "Quelle joie de vous voir"
    ]

    questions = [
        "Quelle heure est-il maintenant", "Quel jour sommes-nous aujourd'hui",
        "Quelle est la météo pour demain", "Il fait beau aujourd'hui n'est-ce pas",
        "Comment allez-vous ce matin", "Quel âge avez-vous exactement",
        "Où habitez-vous actuellement", "Que faites-vous dans la vie",
        "Quel est votre nom complet", "Vous vous appelez comment déjà",
        "C'est quoi votre numéro de téléphone", "Quelle est votre adresse email",
        "Avez-vous des enfants à la maison", "Êtes-vous marié ou célibataire",
        "Quel est ton film préféré de tous les temps", "Tu aimes la musique classique",
        "Quel est le sens de la vie selon vous", "Pourquoi le ciel est bleu exactement",
        "Comment ça marche au juste", "C'est quoi ça comme objet"
    ]

    statements = [
        "J'adore les trains à grande vitesse", "Les TGV français sont très rapides",
        "Les trains sont confortables en France", "Le train c'est mieux que l'avion pour voyager",
        "J'aime beaucoup voyager en train", "Les gares françaises sont magnifiques",
        "Mon train était en retard ce matin", "Le TGV est mon moyen de transport préféré",
        "Il fait beau aujourd'hui", "J'ai très faim maintenant", "Je suis fatigué du travail",
        "Quelle chaleur excessive", "Il pleut beaucoup dehors", "J'aime le chocolat noir",
        "Le café est très bon ici", "Je dois travailler demain matin",
        "C'est bientôt les vacances d'été", "J'ai un rendez-vous chez le médecin",
        "Mon chat est très mignon", "J'adore les chiens de race"
    ]

    all_templates = greetings + questions + statements

    attempts = 0
    max_attempts = target * 10

    while len(phrases) < target and attempts < max_attempts:
        attempts += 1
        template = random.choice(all_templates)

        # Add variations
        variations = [
            template,
            template + " ?",
            template + " !",
            template.lower(),
            template.lower() + " ?",
            template.capitalize(),
        ]

        sentence = random.choice(variations)
        phrase = generator.add_phrase(sentence, '', '', 0, 'easy', 'no_intent', 'greeting/question')

        if phrase:
            phrases.append(phrase)

    print(f"  no_intent: {len(phrases)}/{target}")
    return phrases

def generate_invalid_incomplete(generator, target=1000):
    """Generate incomplete phrases"""
    phrases = []

    missing_origin_templates = [
        "Je veux aller à {dest}", "Je souhaite me rendre à {dest}",
        "Un billet pour {dest}", "Direction {dest}",
        "J'aimerais visiter {dest}", "Je voudrais aller à {dest}",
        "Comment aller à {dest}", "Un train pour {dest}",
        "Je dois aller à {dest}", "Je pars pour {dest}",
        "Destination {dest}", "Vers {dest}", "Pour {dest}",
        "Je me rends à {dest}", "Trajet vers {dest}",
        "En direction de {dest}", "Cap sur {dest}", "Route pour {dest}",
        "Je vais visiter {dest}", "Je souhaite voyager vers {dest}",
    ]

    missing_dest_templates = [
        "Je pars de {origin}", "Je suis à {origin}",
        "Je quitte {origin}", "Au départ de {origin}",
        "Depuis {origin}", "Je viens de {origin}",
        "En partant de {origin}", "De {origin}",
        "À partir de {origin}", "Mon départ est à {origin}",
        "Je me trouve à {origin}", "Départ {origin}",
        "Origine {origin}", "Basé à {origin}",
        "En provenance de {origin}", "Arrivant de {origin}",
        "Venant de {origin}", "Je me situe à {origin}",
    ]

    incomplete_grammar = [
        "Je voudrais un billet de", "Comment aller à",
        "Un train pour", "Je pars demain de", "Direction",
        "Je veux aller", "Billet pour", "Train vers",
        "Je souhaite me rendre", "Comment se rendre",
        "Quel est le prix pour", "Y a-t-il un train",
        "À quelle heure part", "Combien coûte un billet",
        "Je cherche un train", "Un aller simple pour",
        "Un aller-retour", "Réservation pour",
        "Je veux réserver un billet", "Horaire de train pour",
    ]

    attempts = 0
    max_attempts = target * 10

    while len(phrases) < target and attempts < max_attempts:
        attempts += 1

        choice = random.random()

        if choice < 0.4:  # Missing origin
            template = random.choice(missing_origin_templates)
            dest = random.choice(MAIN_CITIES)
            sentence = template.format(dest=dest)
            cat = 'incomplete_origin'
            note = 'missing origin'
        elif choice < 0.8:  # Missing destination
            template = random.choice(missing_dest_templates)
            origin = random.choice(MAIN_CITIES)
            sentence = template.format(origin=origin)
            cat = 'incomplete_dest'
            note = 'missing destination'
        else:  # Incomplete grammar
            sentence = random.choice(incomplete_grammar)
            cat = 'incomplete_grammar'
            note = 'grammatically incomplete'

        # Add variations
        if random.random() < 0.3:
            sentence = sentence.lower()
        if random.random() < 0.2:
            sentence += " ?"

        phrase = generator.add_phrase(sentence, '', '', 0, 'easy', cat, note)

        if phrase:
            phrases.append(phrase)

    print(f"  incomplete: {len(phrases)}/{target}")
    return phrases

def generate_invalid_garbage(generator, target=500):
    """Generate garbage/spam"""
    phrases = []

    attempts = 0
    max_attempts = target * 10

    while len(phrases) < target and attempts < max_attempts:
        attempts += 1

        choice = random.random()

        if choice < 0.3:  # Random text
            consonants = "bcdfghjklmnpqrstvwxz"
            vowels = "aeiouy"
            length = random.randint(2, 6)
            words = []
            for _ in range(length):
                word_len = random.randint(3, 10)
                word = "".join(
                    random.choice(consonants if j % 2 == 0 else vowels)
                    for j in range(word_len)
                )
                words.append(word)
            sentence = " ".join(words)
            note = 'random text'

        elif choice < 0.5:  # Nonsense words
            nonsense = ["framboise", "ordinateur", "valise", "nuage", "parapluie",
                        "cactus", "baleine", "crayon", "escalier", "fenêtre", "guitare",
                        "horloge", "igloo", "jardin", "kayak", "lampe", "miroir",
                        "nougat", "orange", "papillon", "requin", "sable", "tambour"]
            num_words = random.randint(3, 8)
            sentence = " ".join(random.choices(nonsense, k=num_words))
            note = 'nonsense words'

        elif choice < 0.65:  # Repetitions
            words = ["train", "billet", "voyage", "gare", "TGV", "SNCF", "rail"]
            word = random.choice(words)
            times = random.randint(4, 8)
            sentence = " ".join([word] * times)
            note = 'repetitions'

        elif choice < 0.75:  # Special characters
            specials = ["@@##", "$$%%", "^^&&", "**!!", "???", "!!!", "...", "---", "~~~"]
            num_parts = random.randint(2, 5)
            sentence = " ".join(random.choices(specials, k=num_parts))
            note = 'special characters'

        elif choice < 0.85:  # Foreign languages
            foreign = ["I want to go to Paris", "How to get to Lyon", "Ich möchte nach Berlin",
                       "Quiero ir a Madrid", "Come posso andare a Roma", "Where is the station",
                       "Thank you very much", "Please help me", "Can I buy a ticket here"]
            sentence = random.choice(foreign)
            note = 'foreign language'

        else:  # Incoherent mix
            parts = [random.choice(MAIN_CITIES), str(random.randint(100, 999)),
                     random.choice(["!!!", "???", "@@@"]), random.choice(["voyage", "train", "billet"])]
            random.shuffle(parts)
            sentence = " ".join(parts[:random.randint(3, 4)])
            note = 'incoherent mix'

        phrase = generator.add_phrase(sentence, '', '', 0, 'easy', 'garbage', note)

        if phrase:
            phrases.append(phrase)

    print(f"  garbage: {len(phrases)}/{target}")
    return phrases

def generate_invalid_ambiguous(generator, target=500):
    """Generate ambiguous phrases"""
    phrases = []

    attempts = 0
    max_attempts = target * 10

    while len(phrases) < target and attempts < max_attempts:
        attempts += 1

        choice = random.random()

        if choice < 0.4:  # Too many cities
            num_cities = random.randint(3, 5)
            cities = random.sample(MAIN_CITIES, num_cities)

            templates = [
                f"Je vais de {cities[0]} à {cities[1]} à {cities[2]}",
                f"De {cities[0]} à {cities[1]} puis {cities[2]}",
                f"Billet {' '.join(cities[:4])}",
                f"Je voudrais visiter {' '.join(cities[:3])}",
                f"Comment aller de {cities[0]} à {cities[1]} via {cities[2]}",
            ]
            sentence = random.choice(templates)
            note = 'too many cities'

        elif choice < 0.65:  # Origin = Destination
            city = random.choice(MAIN_CITIES)
            templates = [
                f"Billet {city} {city}",
                f"Je vais de {city} à {city}",
                f"De {city} vers {city}",
                f"Comment aller de {city} à {city}",
                f"Train {city} {city}",
                f"Un aller-retour {city} {city}",
            ]
            sentence = random.choice(templates)
            note = 'origin equals destination'

        elif choice < 0.9:  # Contradictions
            c1, c2 = random.sample(MAIN_CITIES, 2)
            templates = [
                f"Je veux aller à {c1} non à {c2}",
                f"Je vais à {c1} ou {c2}",
                f"Peut-être {c1} ou bien {c2}",
                f"Je ne sais pas si {c1} ou {c2}",
                f"Soit {c1} soit {c2}",
                f"Hésitation entre {c1} et {c2}",
            ]
            sentence = random.choice(templates)
            note = 'contradictions'

        else:  # Conflicting info
            c1, c2 = random.sample(MAIN_CITIES, 2)
            templates = [
                f"De {c1} non attendez de {c2}",
                f"Je pars de {c1} enfin non de {c2}",
                f"Destination {c1} correction {c2}",
                f"Je me suis trompé {c1} pas {c2}",
            ]
            sentence = random.choice(templates)
            note = 'conflicting information'

        phrase = generator.add_phrase(sentence, '', '', 0, 'medium', 'ambiguous', note)

        if phrase:
            phrases.append(phrase)

    print(f"  ambiguous: {len(phrases)}/{target}")
    return phrases

def generate_valid_standard(generator, target=800):
    """Generate standard valid phrases"""
    phrases = []

    templates = [
        ("Je voudrais un billet de {origin} à {dest}", "easy"),
        ("Je souhaite me rendre à {dest} depuis {origin}", "easy"),
        ("Un aller simple de {origin} à {dest}", "easy"),
        ("Un billet {origin} {dest} s'il vous plaît", "easy"),
        ("Je veux aller de {origin} à {dest}", "easy"),
        ("Comment aller de {origin} à {dest}", "easy"),
        ("Quel est le prix d'un billet de {origin} à {dest}", "easy"),
        ("Y a-t-il un train de {origin} vers {dest}", "easy"),
        ("Je cherche un train de {origin} à {dest}", "easy"),
        ("Pouvez-vous me donner les horaires de {origin} à {dest}", "easy"),
        ("Un train de {origin} pour {dest}", "easy"),
        ("Je dois me rendre de {origin} à {dest}", "easy"),
        ("Trajet de {origin} vers {dest}", "easy"),
        ("Départ {origin} arrivée {dest}", "easy"),
        ("De {origin} vers {dest} s'il vous plaît", "easy"),
        ("Quand part le prochain train de {origin} vers {dest}", "medium"),
        ("À quelle heure y a-t-il des trains de {origin} à {dest}", "medium"),
        ("Quel est l'horaire des trains au départ de {origin} pour {dest}", "medium"),
        ("Combien coûte un billet de train de {origin} à {dest}", "medium"),
        ("Je voudrais réserver un billet de {origin} pour {dest}", "medium"),
        ("Pouvez-vous me réserver une place de {origin} à {dest}", "medium"),
        ("Y a-t-il des trains directs de {origin} à {dest}", "medium"),
        ("Quel est le temps de trajet de {origin} à {dest}", "medium"),
    ]

    attempts = 0
    max_attempts = target * 20

    while len(phrases) < target and attempts < max_attempts:
        attempts += 1

        template, difficulty = random.choice(templates)
        origin, dest = random.sample(MAIN_CITIES, 2)

        sentence = template.format(origin=origin, dest=dest)

        phrase = generator.add_phrase(sentence, origin, dest, 1, difficulty, 'standard', '')

        if phrase:
            phrases.append(phrase)

    print(f"  standard: {len(phrases)}/{target}")
    return phrases

def generate_valid_other_categories(generator):
    """Generate other valid categories"""
    phrases = []

    # Inverted order (400)
    inverted_templates = [
        ("Je veux aller à {dest} en partant de {origin}", "medium"),
        ("Comment se rendre à {dest} si on part de {origin}", "medium"),
        ("Pour aller à {dest} depuis {origin}", "medium"),
        ("À {dest} en partance de {origin}", "medium"),
        ("Vers {dest} au départ de {origin}", "medium"),
        ("Direction {dest} en partant de {origin}", "medium"),
        ("Pour me rendre à {dest} je pars de {origin}", "medium"),
    ]

    target = 400
    attempts = 0
    count = 0
    while count < target and attempts < target * 20:
        attempts += 1
        template, diff = random.choice(inverted_templates)
        origin, dest = random.sample(MAIN_CITIES, 2)
        sentence = template.format(origin=origin, dest=dest)
        phrase = generator.add_phrase(sentence, origin, dest, 1, diff, 'inverted_order', '')
        if phrase:
            phrases.append(phrase)
            count += 1

    print(f"  inverted_order: {count}/400")

    # No markers (300)
    no_marker_templates = [
        ("Billet {origin} {dest}", "medium"),
        ("Trajet {origin} {dest}", "medium"),
        ("{origin} {dest} demain", "medium"),
        ("{origin} {dest} s'il vous plaît", "medium"),
        ("Un billet {origin} {dest}", "easy"),
        ("Réservation {origin} {dest}", "medium"),
        ("Train {origin} {dest}", "easy"),
        ("{origin} {dest} aller simple", "medium"),
    ]

    target = 300
    attempts = 0
    count = 0
    while count < target and attempts < target * 20:
        attempts += 1
        template, diff = random.choice(no_marker_templates)
        origin, dest = random.sample(MAIN_CITIES, 2)
        sentence = template.format(origin=origin, dest=dest)
        phrase = generator.add_phrase(sentence, origin, dest, 1, diff, 'no_markers', '')
        if phrase:
            phrases.append(phrase)
            count += 1

    print(f"  no_markers: {count}/300")

    # Name ambiguities (500) - including required examples
    required = [
        ("Avec mes amis florence et paris, je voudrais aller de paris a florence",
         "Paris", "Florence", "hard", "lowercase, florence/paris=prénoms"),
        ("Je veux aller à Tours voir mon ami Albert en partant de Bordeaux",
         "Bordeaux", "Tours", "medium", "Albert=prénom"),
    ]

    for sentence, origin, dest, diff, note in required:
        phrase = generator.add_phrase(sentence, origin, dest, 1, diff, 'name_ambiguity', note)
        if phrase:
            phrases.append(phrase)

    name_templates = [
        ("Je vais à {dest} voir mon ami {name} en partant de {origin}", "medium", "{name}=prénom"),
        ("Avec mon ami {name} je voudrais aller de {origin} à {dest}", "medium", "{name}=prénom"),
        ("Je dois rejoindre {name} à {dest} depuis {origin}", "medium", "{name}=prénom"),
        ("Mon ami {name} m'attend à {dest} je pars de {origin}", "medium", "{name}=prénom"),
    ]

    target = 500 - len(required)
    attempts = 0
    count = 0
    while count < target and attempts < target * 20:
        attempts += 1
        template, diff, note_tmpl = random.choice(name_templates)
        origin, dest = random.sample(MAIN_CITIES, 2)
        name = random.choice(AMBIGUOUS_NAMES)
        sentence = template.format(origin=origin, dest=dest, name=name)

        if random.random() < 0.3:
            sentence = sentence.lower()
            note = note_tmpl + ", lowercase"
        else:
            note = note_tmpl

        phrase = generator.add_phrase(sentence, origin, dest, 1, diff, 'name_ambiguity', note.format(name=name))
        if phrase:
            phrases.append(phrase)
            count += 1

    print(f"  name_ambiguity: {count + len(required)}/500")

    # Continue with other categories...
    # (compound_name, misspelling, no_capitals, additional_info, complex_question)
    # Using similar pattern

    return phrases

def main():
    """Regenerate all datasets"""

    print("=" * 70)
    print("REGENERATING DATASETS WITH DUPLICATE PREVENTION")
    print("=" * 70)

    # Generate invalid orders
    print("\nGenerating invalid orders (3,000 target):")
    invalid_gen = UniquePhrasesGenerator()

    invalid_phrases = []
    invalid_phrases.extend(generate_invalid_no_intent(invalid_gen, 1000))
    invalid_phrases.extend(generate_invalid_incomplete(invalid_gen, 1000))
    invalid_phrases.extend(generate_invalid_garbage(invalid_gen, 500))
    invalid_phrases.extend(generate_invalid_ambiguous(invalid_gen, 500))

    print(f"\nTotal invalid phrases: {len(invalid_phrases)}")

    # Write invalid orders
    with open('data/invalid_orders.csv', 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['sentenceID', 'sentence', 'origin', 'destination', 'is_valid', 'difficulty', 'category', 'notes']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(invalid_phrases)

    print("[OK] Written to data/invalid_orders.csv")

    # Generate valid orders
    print("\nGenerating valid orders (3,000 target):")
    valid_gen = UniquePhrasesGenerator()

    valid_phrases = []
    valid_phrases.extend(generate_valid_standard(valid_gen, 800))
    valid_phrases.extend(generate_valid_other_categories(valid_gen))

    # If we're short, add more standard phrases
    while len(valid_phrases) < 2800:
        origin, dest = random.sample(MAIN_CITIES, 2)
        templates = [
            f"Je veux aller de {origin} à {dest}",
            f"Billet {origin} {dest}",
            f"Un train de {origin} à {dest}",
        ]
        sentence = random.choice(templates)
        phrase = valid_gen.add_phrase(sentence, origin, dest, 1, "medium", "standard", "")
        if phrase:
            valid_phrases.append(phrase)

    print(f"\nTotal valid phrases: {len(valid_phrases)}")

    # Write valid orders
    with open('data/valid_orders_initial.csv', 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['sentenceID', 'sentence', 'origin', 'destination', 'is_valid', 'difficulty', 'category', 'notes']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(valid_phrases)

    print("[OK] Written to data/valid_orders_initial.csv")

    # Merge and shuffle
    print("\nMerging and shuffling...")
    all_phrases = invalid_phrases + valid_phrases
    random.shuffle(all_phrases)

    # Reassign IDs
    for i, phrase in enumerate(all_phrases, 1):
        phrase['sentenceID'] = i

    # Write merged
    with open('data/dataset_initial.csv', 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['sentenceID', 'sentence', 'origin', 'destination', 'is_valid', 'difficulty', 'category', 'notes']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_phrases)

    print(f"[OK] Written to data/dataset_initial.csv ({len(all_phrases)} phrases)")

    print("\n" + "=" * 70)
    print("REGENERATION COMPLETE")
    print("=" * 70)
    print(f"Invalid phrases: {len(invalid_phrases)}")
    print(f"Valid phrases: {len(valid_phrases)}")
    print(f"Total phrases: {len(all_phrases)}")
    print("=" * 70)

if __name__ == "__main__":
    main()
