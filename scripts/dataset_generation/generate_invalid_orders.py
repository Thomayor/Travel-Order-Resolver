#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate invalid travel orders dataset (3,000 phrases)
Categories:
1. No travel intent (1,000)
2. Incomplete information (1,000)
3. Garbage/Spam (500)
4. Unresolvable ambiguities (500)
"""

import csv
import random

def generate_no_intent(count=1000):
    """Generate phrases with no travel intention"""
    templates = {
        'greetings': [
            "Bonjour",
            "Salut",
            "Bonne journée",
            "Bonjour comment allez-vous",
            "Salut ça va",
            "Bonsoir",
            "Bonne soirée",
            "À bientôt",
            "Au revoir",
            "Enchanté",
            "Ravi de vous rencontrer",
            "Comment vas-tu",
            "Ça va bien merci",
            "Très bien et vous",
            "Bonne nuit",
            "À demain",
            "À plus tard",
            "Coucou",
            "Hey salut",
            "Yo",
        ],
        'general_questions': [
            "Quelle heure est-il",
            "Quel jour sommes-nous",
            "Quelle est la météo",
            "Il fait beau aujourd'hui",
            "Comment allez-vous",
            "Quel âge avez-vous",
            "Où habitez-vous",
            "Que faites-vous dans la vie",
            "Quel est votre nom",
            "Vous vous appelez comment",
            "C'est quoi votre numéro",
            "Quelle est votre adresse",
            "Avez-vous des enfants",
            "Êtes-vous marié",
            "Quel est ton film préféré",
            "Tu aimes la musique",
            "Quel est le sens de la vie",
            "Pourquoi le ciel est bleu",
            "Comment ça marche",
            "C'est quoi ça",
        ],
        'train_discussion': [
            "J'adore les trains",
            "Les TGV sont rapides",
            "Les trains français sont confortables",
            "Le train c'est mieux que l'avion",
            "J'aime voyager en train",
            "Les gares sont belles",
            "Le train est en retard",
            "Mon train préféré est le TGV",
            "Les trains à grande vitesse impressionnent",
            "La SNCF est une belle entreprise",
            "Les rails de train sont fascinants",
            "J'ai pris le train hier",
            "Le train était bondé",
            "Il y avait du monde dans le train",
            "Le train de nuit est pratique",
            "Les trains régionaux sont sympas",
            "Le réseau ferroviaire français est développé",
            "Les locomotives sont puissantes",
            "J'ai raté mon train",
            "Mon train est annulé",
        ],
        'off_topic': [
            "Il fait beau",
            "J'ai faim",
            "Je suis fatigué",
            "Quelle chaleur",
            "Il pleut dehors",
            "J'aime le chocolat",
            "Le café est bon",
            "Je dois travailler demain",
            "C'est les vacances",
            "J'ai rendez-vous chez le médecin",
            "Mon chat est mignon",
            "J'aime les chiens",
            "La pizza c'est délicieux",
            "Je vais au cinéma",
            "J'ai vu un bon film",
            "La mer est belle",
            "La montagne c'est beau",
            "J'aime lire des livres",
            "La musique classique est relaxante",
            "Le foot c'est super",
            "J'adore danser",
            "Le shopping c'est génial",
            "Je vais faire du sport",
            "Mon travail est intéressant",
            "Les vacances approchent",
            "C'est mon anniversaire",
            "Joyeux Noël",
            "Bonne année",
            "Je suis content",
            "Quelle belle journée",
        ],
        'random_statements': [
            "Le soleil brille",
            "Les oiseaux chantent",
            "La vie est belle",
            "Tout va bien",
            "C'est parfait",
            "Super cool",
            "Génial",
            "Fantastique",
            "Magnifique",
            "Incroyable",
            "Je suis perdu",
            "Je ne comprends pas",
            "C'est compliqué",
            "C'est difficile",
            "Je ne sais pas",
            "Peut-être",
            "Pourquoi pas",
            "D'accord",
            "Bien sûr",
            "Évidemment",
        ]
    }

    phrases = []
    sentence_id = 1

    # Generate from each category
    for category, template_list in templates.items():
        num_per_category = count // len(templates)
        for _ in range(num_per_category):
            template = random.choice(template_list)

            # Add variations
            variations = [
                template,
                template + " ?",
                template + " !",
                template.lower(),
                template.lower() + " ?",
            ]

            sentence = random.choice(variations)
            phrases.append({
                'sentenceID': sentence_id,
                'sentence': sentence,
                'origin': '',
                'destination': '',
                'is_valid': 0,
                'difficulty': 'easy',
                'category': 'no_intent',
                'notes': f'{category}'
            })
            sentence_id += 1

    return phrases[:count], sentence_id

def generate_incomplete(count=1000, start_id=1):
    """Generate phrases with incomplete information"""

    cities = [
        "Paris", "Lyon", "Marseille", "Toulouse", "Nice", "Nantes",
        "Strasbourg", "Montpellier", "Bordeaux", "Lille", "Rennes",
        "Reims", "Le Havre", "Toulon", "Grenoble", "Dijon", "Angers"
    ]

    missing_origin_templates = [
        "Je veux aller à {dest}",
        "Je souhaite me rendre à {dest}",
        "Un billet pour {dest}",
        "Direction {dest}",
        "J'aimerais visiter {dest}",
        "Je voudrais aller à {dest}",
        "Comment aller à {dest}",
        "Un train pour {dest}",
        "Je dois aller à {dest}",
        "Je pars pour {dest}",
        "Destination {dest}",
        "Vers {dest}",
        "À {dest}",
        "Pour {dest}",
        "Je me rends à {dest}",
        "Je vais à {dest}",
        "Trajet vers {dest}",
        "En direction de {dest}",
        "Cap sur {dest}",
        "Route pour {dest}",
    ]

    missing_dest_templates = [
        "Je pars de {origin}",
        "Je suis actuellement à {origin}",
        "Je quitte {origin}",
        "Au départ de {origin}",
        "Depuis {origin}",
        "Je viens de {origin}",
        "En partant de {origin}",
        "De {origin}",
        "À partir de {origin}",
        "Mon départ est à {origin}",
        "Je suis à {origin}",
        "Départ {origin}",
        "Origine {origin}",
        "Je me trouve à {origin}",
        "Situé à {origin}",
        "Basé à {origin}",
        "Localisé à {origin}",
        "En provenance de {origin}",
        "Arrivant de {origin}",
        "Venant de {origin}",
    ]

    incomplete_grammar = [
        "Je voudrais un billet de",
        "Comment aller à",
        "Un train pour",
        "Je pars demain de",
        "Direction",
        "Je veux aller",
        "Billet pour",
        "Train vers",
        "Je souhaite me rendre",
        "Comment se rendre",
        "Quel est le prix pour",
        "Y a-t-il un train",
        "À quelle heure part",
        "Combien coûte un billet",
        "Je cherche un train",
        "Un aller simple",
        "Un aller-retour",
        "Réservation pour",
        "Je veux réserver",
        "Horaire de train",
    ]

    phrases = []
    sentence_id = start_id

    # Missing origin (40%)
    for _ in range(int(count * 0.4)):
        template = random.choice(missing_origin_templates)
        dest = random.choice(cities)
        sentence = template.format(dest=dest)

        # Add variations
        if random.random() < 0.3:
            sentence = sentence.lower()
        if random.random() < 0.2:
            sentence += " ?"

        phrases.append({
            'sentenceID': sentence_id,
            'sentence': sentence,
            'origin': '',
            'destination': '',
            'is_valid': 0,
            'difficulty': 'easy',
            'category': 'incomplete_origin',
            'notes': 'missing origin'
        })
        sentence_id += 1

    # Missing destination (40%)
    for _ in range(int(count * 0.4)):
        template = random.choice(missing_dest_templates)
        origin = random.choice(cities)
        sentence = template.format(origin=origin)

        if random.random() < 0.3:
            sentence = sentence.lower()
        if random.random() < 0.2:
            sentence += " ?"

        phrases.append({
            'sentenceID': sentence_id,
            'sentence': sentence,
            'origin': '',
            'destination': '',
            'is_valid': 0,
            'difficulty': 'easy',
            'category': 'incomplete_dest',
            'notes': 'missing destination'
        })
        sentence_id += 1

    # Incomplete grammar (20%)
    for _ in range(int(count * 0.2)):
        sentence = random.choice(incomplete_grammar)

        if random.random() < 0.5:
            sentence = sentence.lower()
        if random.random() < 0.3:
            sentence += " ?"

        phrases.append({
            'sentenceID': sentence_id,
            'sentence': sentence,
            'origin': '',
            'destination': '',
            'is_valid': 0,
            'difficulty': 'easy',
            'category': 'incomplete_grammar',
            'notes': 'grammatically incomplete'
        })
        sentence_id += 1

    return phrases[:count], sentence_id

def generate_garbage(count=500, start_id=1):
    """Generate garbage/spam phrases"""

    phrases = []
    sentence_id = start_id

    # Random text (30%)
    consonants = "bcdfghjklmnpqrstvwxz"
    vowels = "aeiouy"
    for _ in range(int(count * 0.3)):
        length = random.randint(2, 5)
        words = []
        for _ in range(length):
            word_len = random.randint(3, 10)
            word = ""
            for j in range(word_len):
                if j % 2 == 0:
                    word += random.choice(consonants)
                else:
                    word += random.choice(vowels)
            words.append(word)
        sentence = " ".join(words)

        phrases.append({
            'sentenceID': sentence_id,
            'sentence': sentence,
            'origin': '',
            'destination': '',
            'is_valid': 0,
            'difficulty': 'easy',
            'category': 'garbage',
            'notes': 'random text'
        })
        sentence_id += 1

    # Nonsense words (25%)
    nonsense_words = [
        "framboise", "ordinateur", "valise", "nuage", "parapluie",
        "cactus", "baleine", "crayon", "escalier", "fenêtre",
        "guitare", "horloge", "igloo", "jardin", "kayak",
        "lampe", "miroir", "nougat", "orange", "papillon",
        "requin", "sable", "tambour", "uniforme", "vague"
    ]
    for _ in range(int(count * 0.25)):
        num_words = random.randint(3, 8)
        sentence = " ".join(random.choices(nonsense_words, k=num_words))

        phrases.append({
            'sentenceID': sentence_id,
            'sentence': sentence,
            'origin': '',
            'destination': '',
            'is_valid': 0,
            'difficulty': 'easy',
            'category': 'garbage',
            'notes': 'nonsense words'
        })
        sentence_id += 1

    # Repetitions (15%)
    repeat_words = ["train", "billet", "voyage", "gare", "TGV", "SNCF"]
    for _ in range(int(count * 0.15)):
        word = random.choice(repeat_words)
        times = random.randint(4, 8)
        sentence = " ".join([word] * times)

        phrases.append({
            'sentenceID': sentence_id,
            'sentence': sentence,
            'origin': '',
            'destination': '',
            'is_valid': 0,
            'difficulty': 'easy',
            'category': 'garbage',
            'notes': 'repetitions'
        })
        sentence_id += 1

    # Special characters (10%)
    special_chars = ["@@##", "$$%%", "^^&&", "**!!", "???", "!!!", "...", "---"]
    for _ in range(int(count * 0.1)):
        num_parts = random.randint(2, 5)
        sentence = " ".join(random.choices(special_chars, k=num_parts))

        phrases.append({
            'sentenceID': sentence_id,
            'sentence': sentence,
            'origin': '',
            'destination': '',
            'is_valid': 0,
            'difficulty': 'easy',
            'category': 'garbage',
            'notes': 'special characters'
        })
        sentence_id += 1

    # Foreign languages (10%)
    foreign = [
        "I want to go to Paris",
        "I would like a ticket",
        "How to get to Lyon",
        "Ich möchte nach Berlin",
        "Wie komme ich nach Paris",
        "Quiero ir a Madrid",
        "Come posso andare a Roma",
        "Voglio andare a Milano",
        "How much is a ticket",
        "Where is the station",
        "Wo ist der Bahnhof",
        "Dónde está la estación",
        "I need help",
        "Can you help me",
        "Thank you very much",
    ]
    for _ in range(int(count * 0.1)):
        sentence = random.choice(foreign)

        phrases.append({
            'sentenceID': sentence_id,
            'sentence': sentence,
            'origin': '',
            'destination': '',
            'is_valid': 0,
            'difficulty': 'easy',
            'category': 'garbage',
            'notes': 'foreign language'
        })
        sentence_id += 1

    # Incoherent mix (10%)
    cities = ["Paris", "Lyon", "Marseille"]
    numbers = ["123", "456", "789"]
    for _ in range(int(count * 0.1)):
        parts = [
            random.choice(cities),
            random.choice(numbers),
            random.choice(["!!!", "???", "@@@"]),
            random.choice(["voyage", "train", "billet"]),
            random.choice(special_chars)
        ]
        random.shuffle(parts)
        sentence = " ".join(parts[:random.randint(3, 5)])

        phrases.append({
            'sentenceID': sentence_id,
            'sentence': sentence,
            'origin': '',
            'destination': '',
            'is_valid': 0,
            'difficulty': 'easy',
            'category': 'garbage',
            'notes': 'incoherent mix'
        })
        sentence_id += 1

    return phrases[:count], sentence_id

def generate_ambiguous(count=500, start_id=1):
    """Generate phrases with unresolvable ambiguities"""

    cities = [
        "Paris", "Lyon", "Marseille", "Toulouse", "Nice", "Nantes",
        "Bordeaux", "Lille", "Rennes", "Montpellier"
    ]

    phrases = []
    sentence_id = start_id

    # Too many cities (40%)
    templates_many = [
        "Je vais de {c1} à {c2} à {c3}",
        "De {c1} à {c2} puis {c3}",
        "Billet {c1} {c2} {c3}",
        "Je voudrais aller de {c1} à {c2} via {c3} et {c4}",
        "{c1} {c2} {c3} {c4}",
        "Comment aller de {c1} à {c2} à {c3}",
        "Je veux visiter {c1} {c2} {c3}",
        "Train pour {c1} {c2} et {c3}",
    ]
    for _ in range(int(count * 0.4)):
        template = random.choice(templates_many)
        num_cities = template.count('{c')
        selected = random.sample(cities, num_cities)
        sentence = template.format(**{f'c{i+1}': city for i, city in enumerate(selected)})

        phrases.append({
            'sentenceID': sentence_id,
            'sentence': sentence,
            'origin': '',
            'destination': '',
            'is_valid': 0,
            'difficulty': 'medium',
            'category': 'ambiguous',
            'notes': 'too many cities'
        })
        sentence_id += 1

    # Origin = Destination (25%)
    for _ in range(int(count * 0.25)):
        city = random.choice(cities)
        templates_same = [
            f"Billet {city} {city}",
            f"Je vais de {city} à {city}",
            f"De {city} vers {city}",
            f"Comment aller de {city} à {city}",
            f"Train {city} {city}",
        ]
        sentence = random.choice(templates_same)

        phrases.append({
            'sentenceID': sentence_id,
            'sentence': sentence,
            'origin': '',
            'destination': '',
            'is_valid': 0,
            'difficulty': 'medium',
            'category': 'ambiguous',
            'notes': 'origin equals destination'
        })
        sentence_id += 1

    # Contradictions (25%)
    for _ in range(int(count * 0.25)):
        c1, c2, c3 = random.sample(cities, 3)
        templates_contra = [
            f"Je veux aller à {c1} non à {c2}",
            f"Je vais à {c1} ou {c2}",
            f"Peut-être {c1} ou bien {c2}",
            f"Je ne sais pas si {c1} ou {c2}",
            f"Soit {c1} soit {c2}",
            f"De {c1} à {c2} ou peut-être {c3}",
            f"Je vais à {c1} ah non plutôt {c2}",
            f"Hésitation entre {c1} et {c2}",
        ]
        sentence = random.choice(templates_contra)

        phrases.append({
            'sentenceID': sentence_id,
            'sentence': sentence,
            'origin': '',
            'destination': '',
            'is_valid': 0,
            'difficulty': 'medium',
            'category': 'ambiguous',
            'notes': 'contradictions'
        })
        sentence_id += 1

    # Conflicting information (10%)
    for _ in range(int(count * 0.1)):
        c1, c2, c3 = random.sample(cities, 3)
        templates_conflict = [
            f"De {c1} non attendez de {c2} vers {c3}",
            f"Je pars de {c1} enfin non de {c2}",
            f"Destination {c1} correction {c2}",
            f"Je me suis trompé {c1} pas {c2}",
        ]
        sentence = random.choice(templates_conflict)

        phrases.append({
            'sentenceID': sentence_id,
            'sentence': sentence,
            'origin': '',
            'destination': '',
            'is_valid': 0,
            'difficulty': 'medium',
            'category': 'ambiguous',
            'notes': 'conflicting information'
        })
        sentence_id += 1

    return phrases[:count], sentence_id

def main():
    """Generate complete invalid orders dataset"""

    print("Generating invalid orders dataset...")

    all_phrases = []

    # Generate each category
    print("Generating no_intent phrases (1,000)...")
    no_intent, next_id = generate_no_intent(1000)
    all_phrases.extend(no_intent)

    print("Generating incomplete phrases (1,000)...")
    incomplete, next_id = generate_incomplete(1000, start_id=next_id)
    all_phrases.extend(incomplete)

    print("Generating garbage phrases (500)...")
    garbage, next_id = generate_garbage(500, start_id=next_id)
    all_phrases.extend(garbage)

    print("Generating ambiguous phrases (500)...")
    ambiguous, next_id = generate_ambiguous(500, start_id=next_id)
    all_phrases.extend(ambiguous)

    # Reassign sequential IDs
    for i, phrase in enumerate(all_phrases, 1):
        phrase['sentenceID'] = i

    # Write to CSV
    output_file = 'data/invalid_orders.csv'
    print(f"\nWriting to {output_file}...")

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['sentenceID', 'sentence', 'origin', 'destination', 'is_valid', 'difficulty', 'category', 'notes']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_phrases)

    print(f"[OK] Generated {len(all_phrases)} invalid phrases")

    # Statistics
    categories = {}
    for phrase in all_phrases:
        cat = phrase['category']
        categories[cat] = categories.get(cat, 0) + 1

    print("\nDistribution by category:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    return all_phrases

if __name__ == "__main__":
    main()
