# Définition des Niveaux de Difficulté

## Vue d'ensemble

Les phrases du dataset sont classées en **3 niveaux de difficulté** basés sur plusieurs critères linguistiques et structurels. Cette classification aide à évaluer les performances des modèles NLP sur différents types de complexité.

---

## Distribution dans le Dataset (10K)

| Difficulté | Count | Pourcentage | Baseline Accuracy |
|------------|-------|-------------|-------------------|
| **Easy** | 1,423 | 20.3% | **87.14%** ✅ |
| **Medium** | 4,179 | 59.7% | **73.39%** ✅ |
| **Hard** | 1,398 | 20.0% | **34.84%** ⚠️ |

---

## 1. EASY (Facile)

### Critères d'attribution
✅ **Structure claire et standard**
✅ **Keywords bien définis** ("de", "à", "depuis", "vers")
✅ **Villes correctement orthographiées**
✅ **Capitalisation correcte**
✅ **Pas d'ambiguïté**
✅ **Syntaxe simple et directe**

### Exemples de templates EASY

**Catégorie: Standard**
```
"Je voudrais un billet de {origin} à {dest}"
"Un aller simple de {origin} à {dest}"
"Je veux aller de {origin} à {dest}"
"Un billet {origin} {dest} s'il vous plaît"
"Départ {origin} arrivée {dest}"
```

**Catégorie: No Markers**
```
"Train {origin} {dest}"
"Billet {origin} {dest} svp"
```

**Catégorie: No Capitals** (lowercase mais structure claire)
```
"je veux aller de paris à lyon"         # Easy car structure claire
"un billet marseille nice"              # Easy car format direct
```

### Exemples concrets

```csv
"Je voudrais un billet de Paris à Lyon",Paris,Lyon,1,easy,standard
"Un aller simple de Marseille à Nice",Marseille,Nice,1,easy,standard
"Billet Toulouse Bordeaux",Toulouse,Bordeaux,1,easy,no_markers
"je veux aller de nantes à angers",Nantes,Angers,1,easy,no_capitals
```

### Pourquoi EASY?
- Les keywords sont présents et non ambigus
- L'ordre origine → destination est clair
- Aucune distraction (noms de personnes, fautes, etc.)
- Le modèle baseline peut utiliser des règles simples

---

## 2. MEDIUM (Moyen)

### Critères d'attribution
⚠️ **Structure légèrement plus complexe**
⚠️ **Questions au lieu d'affirmations**
⚠️ **Informations supplémentaires** (temps, passagers)
⚠️ **Ordre inversé** possible ("à X depuis Y")
⚠️ **Ambiguïté légère** (un prénom mentionné)
⚠️ **Noms composés sans traits d'union**

### Exemples de templates MEDIUM

**Catégorie: Standard (questions)**
```
"Quand part le prochain train de {origin} vers {dest}"
"À quelle heure y a-t-il des trains de {origin} à {dest}"
"Combien coûte un billet de train de {origin} à {dest}"
"Quel est le temps de trajet de {origin} à {dest}"
```

**Catégorie: Inverted Order**
```
"Je voudrais aller à {dest} depuis {origin}"
"Comment me rendre à {dest} en partant de {origin}"
```

**Catégorie: Name Ambiguity (légère)**
```
"Je vais à {dest} voir mon ami Albert en partant de {origin}"
"Avec mon ami Florence je voudrais aller de {origin} à {dest}"
```

**Catégorie: Additional Info**
```
"Je voudrais un billet de {origin} à {dest} pour demain"
"Deux billets de {origin} à {dest} s'il vous plaît"
```

**Catégorie: Compound Names**
```
"Comment me rendre à Port Boulet depuis Tours"  # Sans trait d'union
"Un billet Paris Aix en Provence"
```

### Exemples concrets

```csv
"Quand part le prochain train de Paris vers Lyon",Paris,Lyon,1,medium,standard
"Je voudrais aller à Nice depuis Marseille",Marseille,Nice,1,medium,inverted_order
"Je vais à Tours voir mon ami Albert en partant de Bordeaux",Bordeaux,Tours,1,medium,name_ambiguity
"Un billet Paris Lyon pour demain",Paris,Lyon,1,medium,additional_info
"Comment aller a Port Boulet depuis Tours",Tours,Port-Boulet,1,medium,compound_name
```

### Pourquoi MEDIUM?
- Structure plus complexe nécessitant une analyse plus fine
- Présence de distracteurs légers (prénoms, info temporelle)
- Keywords non-standard ou ordre inversé
- Noms composés sans formatage correct

---

## 3. HARD (Difficile)

### Critères d'attribution
❌ **Fautes d'orthographe dans les villes**
❌ **Ambiguïté forte** (plusieurs prénoms qui sont aussi des villes)
❌ **Lowercase + ambiguïté combinées**
❌ **Questions complexes nécessitant inférence**
❌ **Noms composés avec fautes d'orthographe**
❌ **Multiple distracteurs**

### Exemples de templates HARD

**Catégorie: Misspelling** (TOUJOURS hard)
```
"Je veux aller de {origin_misspelled} à {dest_misspelled}"
"Un billet {origin_misspelled} {dest_misspelled}"
"bilet lile reim"                          # Multiple fautes
"Comment aller a Anneecy depuis Perpignan" # Faute + lowercase
```

**Catégorie: Name Ambiguity (forte)**
```
"Avec mes amis {name1} et {name2}, je voudrais aller de {origin} à {dest}"
"avec mes amis florence et paris, je voudrais aller de paris a florence"  # Lowercase + 2 villes-prénoms
"Retrouver Paris à {dest} en partant de {origin}"  # Paris = prénom
```

**Catégorie: Complex Questions**
```
"Quel est le moyen le plus rapide pour aller de {origin} à {dest}"
"Combien de correspondances entre {origin} et {dest}"
"Quel est le train le plus rapide de {origin} à {dest}"
```

**Catégorie: Compound Names (avec fautes)**
```
"Un billet Paris Aix-en-Proovence"         # Faute dans nom composé
"je veux aller a saint etienn"            # Faute + lowercase + pas de trait d'union
```

### Exemples concrets

```csv
"Je veux aller de Bordeau à Limogees",Bordeaux,Limoges,1,hard,misspelling
"avec mes amis florence et paris, je voudrais aller de paris a florence",Paris,Florence,1,hard,name_ambiguity
"bilet lile reim",Lille,Reims,1,hard,misspelling
"Quel est le moyen le plus rapide pour aller de Paris à Lyon",Paris,Lyon,1,hard,complex_question
"Albert, Rémy et moi voulons aller de Annecy à Amiens",Annecy,Amiens,1,hard,name_ambiguity
"Un billet Saint-Étienn Lyon",Saint-Étienne,Lyon,1,hard,misspelling
```

### Pourquoi HARD?
- Fautes d'orthographe empêchent le matching direct dans le gazetteer
- Ambiguïté forte nécessite compréhension du contexte
- Combinaison de plusieurs facteurs de difficulté
- Le modèle baseline échoue systématiquement (34.84%)

---

## Logique d'Attribution par Catégorie

### Catégories TOUJOURS hard
- ❌ **misspelling**: 100% hard (fautes d'orthographe)
- ❌ **complex_question**: 80%+ hard (questions nécessitant inférence)

### Catégories MAJORITAIREMENT medium
- ⚠️ **inverted_order**: 90% medium (ordre inversé)
- ⚠️ **name_ambiguity**: 60% medium, 40% hard (selon nombre de prénoms)
- ⚠️ **compound_name**: 70% medium, 30% hard (selon fautes)
- ⚠️ **additional_info**: 90% medium (info supplémentaire)

### Catégories MIXTES
- ✅ **standard**: 70% easy, 30% medium (selon complexité syntaxique)
- ✅ **no_markers**: 60% easy, 40% medium (selon clarté)
- ✅ **no_capitals**: 80% easy, 20% medium (lowercase seul n'est pas dur)

---

## Facteurs Aggravants

Certains facteurs transforment une phrase medium en hard:

1. **Lowercase + Ambiguïté de nom**
   ```
   "avec mes amis florence et paris..."  # hard (lowercase + 2 villes-prénoms)
   vs
   "Avec mon ami Florence..."            # medium (1 seul prénom, capitalisé)
   ```

2. **Faute d'orthographe + Lowercase**
   ```
   "bilet lile reim"                     # hard (fautes + lowercase)
   vs
   "Un billet Lile Reim"                 # hard (fautes mais capitalisé)
   ```

3. **Nom composé + Faute**
   ```
   "saint etienn"                        # hard (pas de trait d'union + faute)
   vs
   "Saint Etienne"                       # medium (pas de trait d'union seulement)
   ```

---

## Impact sur les Performances

### Baseline Model (Rule-based)
| Difficulté | Accuracy | Raison |
|------------|----------|--------|
| Easy | **87.14%** | Les règles simples fonctionnent bien |
| Medium | **73.39%** | Nécessite règles plus sophistiquées |
| Hard | **34.84%** | Les règles échouent (fautes, ambiguïté) |

### CamemBERT (Target)
| Difficulté | Target Accuracy | Raison |
|------------|-----------------|--------|
| Easy | **95%+** | Devrait être quasi-parfait |
| Medium | **90%+** | Contexte aide à résoudre ambiguïtés |
| Hard | **70-80%** | Nécessite compréhension sémantique |

---

## Recommandations pour Nouveaux Datasets

### Si vous générez de nouvelles phrases:

**Pour EASY:**
- Structure: "de X à Y" ou "X Y"
- Orthographe correcte
- Capitalisation correcte
- Pas de distracteurs

**Pour MEDIUM:**
- Questions au lieu d'affirmations
- Ordre inversé: "à Y depuis X"
- Un prénom mentionné
- Info supplémentaire (temps, passagers)
- Noms composés sans trait d'union

**Pour HARD:**
- Fautes d'orthographe obligatoires
- 2+ prénoms qui sont aussi des villes
- Lowercase + ambiguïté
- Questions complexes
- Combinaison de facteurs

---

## Distribution Recommandée

Pour un dataset équilibré:
- **20-25% Easy**: Valider que le modèle fonctionne sur cas simples
- **55-65% Medium**: Majorité des cas réels
- **15-25% Hard**: Pousser les limites du modèle

Notre dataset 10K: **20.3% Easy / 59.7% Medium / 20.0% Hard** ✅

---

**Date**: 2026-01-09
**Dataset**: 10,000 sentences (7,000 valid)
**Source**: generate_valid_orders.py
