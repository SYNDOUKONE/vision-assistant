"""
VISION — Détection d'Émotions
Analyse le sentiment et les émotions dans les messages de l'utilisateur.
Inspiré de emotion_config.json de Jarvis AI.
"""

# Dictionnaire d'émotions basé sur des mots-clés français
EMOTIONS = {
    "joie": ["super", "génial", "excellent", "merci", "parfait", "bravo", "incroyable",
             "content", "heureux", "ravi", "fantastique", "top", "cool", "bien"],
    "colère": ["nul", "horrible", "bug", "erreur", "raté", "ne marche pas", "problème",
               "merde", "ça ne fonctionne pas", "pourquoi", "encore", "toujours"],
    "tristesse": ["triste", "déprimé", "seul", "fatigue", "fatigué", "dommage",
                  "malheureusement", "hélas", "déçu", "perdu"],
    "curiosité": ["comment", "pourquoi", "qu'est-ce", "explique", "dis-moi", "c'est quoi",
                  "je veux savoir", "apprends-moi", "montres-moi"],
    "urgence": ["urgent", "vite", "rapidement", "maintenant", "tout de suite",
                "immédiatement", "dépêche-toi", "aide", "au secours"],
    "neutral": []
}

# Réponses adaptées par émotion
REPONSES_ADAPTEES = {
    "joie": ["Excellent ! Votre enthousiasme est contagieux, Monsieur.", 
             "Je suis ravi que tout se passe bien !"],
    "colère": ["Je comprends votre frustration, Monsieur. Laissez-moi résoudre cela immédiatement.",
               "Mes excuses pour ce désagrément. Je m'en occupe sur-le-champ."],
    "tristesse": ["Je suis là pour vous, Monsieur. Comment puis-je vous aider ?",
                  "Tout va bien ? Je suis à votre disposition."],
    "curiosité": ["Excellente question ! Je vais vous expliquer cela en détail.",
                  "Je vois que vous êtes curieux. Permettez-moi de vous éclairer."],
    "urgence": ["Message reçu 5/5, Monsieur. J'agis immédiatement.",
                "Très bien, je m'en occupe en priorité absolue."],
    "neutral": ["Bien reçu, Monsieur.", "Je m'en occupe."]
}


def detecter_emotion(texte: str) -> str:
    """Détecte l'émotion dominante dans un texte."""
    t = texte.lower()
    scores = {emotion: 0 for emotion in EMOTIONS}
    
    for emotion, mots in EMOTIONS.items():
        for mot in mots:
            if mot in t:
                scores[emotion] += 1
    
    # Retirer "neutral" avant de chercher le max
    scores_sans_neutral = {k: v for k, v in scores.items() if k != "neutral"}
    
    if not any(scores_sans_neutral.values()):
        return "neutral"
    
    return max(scores_sans_neutral, key=scores_sans_neutral.get)


def adapter_reponse_emotion(emotion: str) -> str:
    """Retourne une phrase d'introduction adaptée à l'émotion détectée."""
    import random
    reponses = REPONSES_ADAPTEES.get(emotion, REPONSES_ADAPTEES["neutral"])
    return random.choice(reponses)


def analyser_sentiment(texte: str) -> dict:
    """Analyse complète du sentiment d'un texte."""
    emotion = detecter_emotion(texte)
    mots_positifs = sum(1 for m in EMOTIONS.get("joie", []) if m in texte.lower())
    mots_negatifs = sum(1 for m in EMOTIONS.get("colère", []) if m in texte.lower())
    
    score = mots_positifs - mots_negatifs
    if score > 0:
        polarite = "positif"
    elif score < 0:
        polarite = "négatif"
    else:
        polarite = "neutre"
    
    return {
        "emotion": emotion,
        "polarite": polarite,
        "score": score,
        "intensite": "forte" if abs(score) > 2 else "faible"
    }


def obtenir_emoji_emotion(emotion: str) -> str:
    """Retourne un emoji correspondant à l'émotion."""
    emojis = {
        "joie": "😊",
        "colère": "😤",
        "tristesse": "😔",
        "curiosité": "🤔",
        "urgence": "⚡",
        "neutral": "🤖"
    }
    return emojis.get(emotion, "🤖")
