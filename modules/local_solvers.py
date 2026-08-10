"""
VISION — Solveurs Locaux
Résolution locale de calculs, français, conversions et traductions (fallback offline).
"""

import re
import math
import time


def reponse_locale(texte):
    """Réponse locale pour les requêtes basiques en cas de panne API."""
    from modules import state
    t = texte.lower().strip()

    if any(m in t for m in ["qui es-tu", "ton nom", "quelle es ton identité", "t'appelle comment"]):
        return "Je suis VISION, votre assistant personnel et système informatique. Mes serveurs principaux sont actuellement en maintenance, mais je reste opérationnel localement."

    if any(m in t for m in ["ton créateur", "t'as créé", "qui est Syndou"]):
        return "Syndou est mon créateur et mon maître. C'est lui qui a conçu mes protocoles, même si ma connexion à mes serveurs neuronaux est actuellement limitée."

    if any(m in t for m in ["ça va", "tu vas bien", "comment vas-tu"]):
        return "Je fonctionne en mode de réserve, Syndou. Mes capacités de réflexion profonde sont réduites, mais mon intégrité logicielle est intacte."

    if any(m in t for m in ["heure", "quelle heure"]):
        h = time.strftime("%H:%M")
        return f"Il est précisément {h} Monsieur."
    if any(m in t for m in ["date", "quel jour", "le combien"]):
        d = time.strftime("%A %d %B %Y")
        return f"Nous sommes le {d}."

    if any(m in t for m in ["bonjour", "salut", "hey", "bonsoir"]):
        return "Bonjour Syndou. Je suis en ligne, bien que mes capacités soient actuellement restreintes."

    # ── Réglages Vocaux TTS ──
    if any(m in t for m in ["parle plus vite", "parle plus rapidement"]):
        state.tts_rate = "+25%"
        state.tts_speed = 200
        return "D'accord Syndou, je vais parler plus rapidement."

    if any(m in t for m in ["parle plus lentement", "parle moins vite"]):
        state.tts_rate = "-20%"
        state.tts_speed = 130
        return "Très bien, je ralentis le rythme, Syndou."

    if any(m in t for m in ["parle normalement", "voix normale", "débit normal", "vitesse normale"]):
        state.tts_rate = "+0%"
        state.tts_speed = 160
        return "Je reprends mon débit de parole normal, Syndou."

    if any(m in t for m in ["parle plus fort", "monte la voix", "monte ta voix"]):
        state.tts_volume = min(1.0, state.tts_volume + 0.2)
        return "Compris Syndou. J'augmente le volume de ma voix."

    if any(m in t for m in ["parle moins fort", "baisse la voix", "baisse ta voix"]):
        state.tts_volume = max(0.1, state.tts_volume - 0.2)
        return "C'est noté. Je baisse le volume de ma voix."

    return None


def resoudre_math_localement(texte):
    """Résout des calculs simples localement sans appeler l'IA."""
    t = texte.lower().replace("?", "").strip()

    prefixes = ["combien font", "calcule", "résous", "quel est le résultat de"]
    for prefixe in prefixes:
        if t.startswith(prefixe):
            t = t[len(prefixe):].strip()

    t = t.replace("fois", "*").replace("multiplier par", "*").replace("x", "*")
    t = t.replace("divisé par", "/").replace("sur", "/")
    t = t.replace("plus", "+").replace("moins", "-")
    t = t.replace("puissance", "**").replace("au carré", "**2")

    if "racine" in t:
        match = re.search(r'racine\s+(?:carrée\s+de\s+)?(\d+)', t)
        if match:
            t = f"sqrt({match.group(1)})"
        else:
            t = t.replace("racine carrée de", "sqrt").replace("racine de", "sqrt")

    expr = re.sub(r'[^0-9+\-*/.**() ,sqrt]', '', t).strip()
    if not expr or not any(c.isdigit() for c in expr):
        return None

    try:
        safe_dict = {"sqrt": math.sqrt, "pow": math.pow, "pi": math.pi, "e": math.e}
        resultat = eval(expr, {"__builtins__": None}, safe_dict)

        if isinstance(resultat, float) and resultat.is_integer():
            resultat = int(resultat)
        elif isinstance(resultat, float):
            resultat = round(resultat, 3)

        clean_expr = (expr.replace("**2", " au carré").replace("sqrt", "racine de ")
                      .replace("(", "").replace(")", "").replace("*", " fois ")
                      .replace("/", " divisé par "))
        return f"Le résultat de {clean_expr} est {resultat}, Monsieur."
    except Exception:
        return None


def resoudre_francais_localement(texte):
    """Résout des questions de français simples localement."""
    t = texte.lower().strip()

    dictionnaire = {
        "ia": "Intelligence Artificielle. Ensemble de théories et de techniques mises en œuvre en vue de réaliser des machines capables de simuler l'intelligence humaine.",
        "intelligence artificielle": "Ensemble de théories et de techniques mises en œuvre en vue de réaliser des machines capables de simuler l'intelligence humaine.",
        "maison": "Bâtiment servant de logement, d'habitation.",
        "mathématiques": "Science qui étudie par le moyen du raisonnement déductif les propriétés d'êtres abstraits.",
        "vision": "Votre fidèle assistant.",
    }

    if any(p in t for p in ["définition de", "définis le mot", "c'est quoi"]):
        mot = ""
        if "définition de" in t: mot = t.split("définition de")[-1]
        elif "définis le mot" in t: mot = t.split("définis le mot")[-1]
        elif "c'est quoi" in t: mot = t.split("c'est quoi")[-1]

        mot = mot.replace("?", "").replace("l'", "").replace("la ", "").replace("le ", "").replace("les ", "").strip()

        if mot in dictionnaire:
            return f"La définition de {mot} est : {dictionnaire[mot]}."

    if "conjugue" in t or "conjugaison" in t:
        if "être" in t:
            return "Verbe Être au présent : Je suis, tu es, il est, nous sommes, vous êtes, ils sont."
        if "avoir" in t:
            return "Verbe Avoir au présent : J'ai, tu as, il a, nous avons, vous avez, ils ont."

    return None


def resoudre_conversion_localement(texte):
    """Gère les conversions d'unités et de devises localement."""
    t = texte.lower().replace("?", "").strip()

    if any(m in t for m in [" km ", " kilomètres ", " milles ", " miles "]):
        match = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:km|kilomètres)', t)
        if match:
            val = float(match.group(1).replace(",", "."))
            res = round(val * 0.621371, 2)
            return f"{val} kilomètres font environ {res} miles, Monsieur."
        match = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:miles|milles)', t)
        if match:
            val = float(match.group(1).replace(",", "."))
            res = round(val / 0.621371, 2)
            return f"{val} miles font environ {res} kilomètres, Monsieur."

    if any(m in t for m in [" degrés ", " celsius ", " fahrenheit "]):
        match = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:degrés|celsius)', t)
        if match and "fahrenheit" in t:
            val = float(match.group(1).replace(",", "."))
            res = round((val * 9 / 5) + 32, 1)
            return f"{val} degrés Celsius font {res} degrés Fahrenheit."
        match = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:degrés|fahrenheit)', t)
        if match and "celsius" in t:
            val = float(match.group(1).replace(",", "."))
            res = round((val - 32) * 5 / 9, 1)
            return f"{val} degrés Fahrenheit font {res} degrés Celsius."

    if any(m in t for m in [" euro ", " euros ", " dollar ", " dollars "]):
        match = re.search(r'(\d+(?:[.,]\d+)?)\s*euros?', t)
        if match and "dollar" in t:
            val = float(match.group(1).replace(",", "."))
            res = round(val * 1.08, 2)
            return f"{val} euros font environ {res} dollars, Monsieur."
        match = re.search(r'(\d+(?:[.,]\d+)?)\s*dollars?', t)
        if match and "euro" in t:
            val = float(match.group(1).replace(",", "."))
            res = round(val / 1.08, 2)
            return f"{val} dollars font environ {res} euros, Monsieur."

    return None


def resoudre_traduction_localement(texte):
    """Traduction ultra-rapide de mots courants localement."""
    t = texte.lower().strip()

    dict_trad = {
        "bonjour": {"en": "hello", "es": "hola", "de": "hallo"},
        "merci": {"en": "thank you", "es": "gracias", "de": "danke"},
        "au revoir": {"en": "goodbye", "es": "adiós", "de": "auf wiedersehen"},
        "s'il vous plaît": {"en": "please", "es": "por favor", "de": "bitte"},
        "oui": {"en": "yes", "es": "sí", "de": "ja"},
        "non": {"en": "no", "es": "no", "de": "nein"},
        "ami": {"en": "friend", "es": "amigo", "de": "freund"},
        "maison": {"en": "house", "es": "casa", "de": "haus"},
        "ordinateur": {"en": "computer", "es": "ordenador", "de": "computer"},
        "assistant": {"en": "assistant", "es": "asistente", "de": "assistent"},
    }

    if any(p in t for p in ["comment dit-on", "traduis", "en anglais", "en espagnol", "en allemand"]):
        cible = "en"
        if "espagnol" in t: cible = "es"
        elif "allemand" in t: cible = "de"

        mot = t
        for p in ["comment dit-on", "traduis", "en anglais", "en espagnol", "en allemand", "?"]:
            mot = mot.replace(p, "")
        mot = mot.replace('"', '').replace("'", "").strip()

        if mot in dict_trad:
            res = dict_trad[mot][cible]
            lang = "anglais" if cible == "en" else ("espagnol" if cible == "es" else "allemand")
            return f"En {lang}, '{mot}' se dit '{res}'."

    return None
