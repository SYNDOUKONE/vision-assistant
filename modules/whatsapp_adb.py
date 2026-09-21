"""
VISION — WhatsApp / SMS via ADB
Envoie des messages WhatsApp et SMS depuis le PC via Android Debug Bridge.
Nécessite un téléphone Android connecté en USB ou en WiFi ADB.
"""
import subprocess
import time
import urllib.parse


def _adb(commande: list) -> tuple[int, str]:
    """Exécute une commande ADB et retourne (code, sortie)."""
    try:
        result = subprocess.run(
            ["adb"] + commande,
            capture_output=True, text=True, timeout=10
        )
        return result.returncode, result.stdout.strip()
    except FileNotFoundError:
        return -1, "ADB non installé. Installez Android Platform Tools."
    except subprocess.TimeoutExpired:
        return -1, "Timeout ADB."


def verifier_connexion() -> bool:
    """Vérifie si un téléphone Android est connecté via ADB."""
    code, sortie = _adb(["devices"])
    lignes = [l for l in sortie.split("\n") if "\tdevice" in l]
    return len(lignes) > 0


def envoyer_whatsapp(numero: str, message: str) -> str:
    """
    Envoie un message WhatsApp via ADB.
    Le numéro doit être au format international : ex. 2250712345678
    """
    if not verifier_connexion():
        return "❌ Aucun téléphone Android connecté. Branchez votre téléphone en USB avec le débogage USB activé."

    # Encoder le message pour l'URL
    msg_encode = urllib.parse.quote(message)
    numero_clean = numero.replace("+", "").replace(" ", "").replace("-", "")

    # Ouvrir WhatsApp avec le numéro et le message pré-rempli
    uri = f"whatsapp://send?phone={numero_clean}&text={msg_encode}"
    code, _ = _adb(["shell", "am", "start", "-a", "android.intent.action.VIEW",
                    "-d", uri])

    if code != 0:
        return "❌ Impossible d'ouvrir WhatsApp sur le téléphone."

    time.sleep(2)  # Attendre que WhatsApp s'ouvre

    # Simuler la touche "Entrée" pour envoyer
    _adb(["shell", "input", "keyevent", "66"])

    return f"✅ Message WhatsApp envoyé au {numero} : '{message[:50]}...'" if len(message) > 50 else f"✅ Message WhatsApp envoyé au {numero} : '{message}'"


def envoyer_sms(numero: str, message: str) -> str:
    """
    Envoie un SMS via ADB en ouvrant l'application SMS native.
    """
    if not verifier_connexion():
        return "❌ Aucun téléphone Android connecté."

    numero_clean = numero.replace(" ", "").replace("-", "")
    msg_encode = urllib.parse.quote(message)

    uri = f"sms:{numero_clean}?body={msg_encode}"
    code, _ = _adb(["shell", "am", "start", "-a", "android.intent.action.SENDTO",
                    "-d", uri])

    if code != 0:
        return "❌ Impossible d'ouvrir l'application SMS."

    time.sleep(2)
    _adb(["shell", "input", "keyevent", "66"])

    return f"✅ SMS envoyé au {numero}."


def lire_notifications() -> str:
    """Lit les notifications récentes du téléphone via ADB."""
    if not verifier_connexion():
        return "❌ Aucun téléphone Android connecté."

    code, sortie = _adb(["shell", "dumpsys", "notification", "--noredact"])
    if code != 0:
        return "❌ Impossible de lire les notifications."

    # Extraire les notifications WhatsApp
    lignes = sortie.split("\n")
    notifs = [l.strip() for l in lignes if "whatsapp" in l.lower() or "message" in l.lower()]
    if not notifs:
        return "Aucune notification WhatsApp récente."
    return "📱 Notifications :\n" + "\n".join(notifs[:5])


def statut_telephone() -> str:
    """Retourne le statut de connexion du téléphone."""
    connecte = verifier_connexion()
    if connecte:
        _, modele = _adb(["shell", "getprop", "ro.product.model"])
        _, batterie = _adb(["shell", "dumpsys", "battery", "|", "grep", "level"])
        return f"✅ Téléphone connecté : {modele}\n{batterie}"
    return "❌ Aucun téléphone Android connecté via ADB.\n\nPour connecter votre téléphone :\n1. Activez le débogage USB dans les options développeur\n2. Branchez le câble USB\n3. Acceptez la demande d'autorisation ADB sur votre téléphone"


def traiter_commande_whatsapp(texte: str) -> str | None:
    """Interprète les commandes WhatsApp/SMS vocales."""
    t = texte.lower()

    if "whatsapp" in t or "sms" in t or "message" in t:

        # Statut téléphone
        if any(x in t for x in ["statut téléphone", "état téléphone", "connecté", "mon téléphone"]):
            return statut_telephone()

        # Envoyer WhatsApp
        if "whatsapp" in t and any(x in t for x in ["envoie", "envoyer", "envoyer"]):
            import re
            tel_match = re.search(r'(\+?\d[\d\s]{7,14}\d)', texte)
            if tel_match:
                numero = tel_match.group(1)
                # Extraire le message après le numéro
                msg = texte.split(tel_match.group(1), 1)[-1].strip()
                msg = msg.replace("le message", "").replace("avec le texte", "").strip()
                if msg:
                    return envoyer_whatsapp(numero, msg)
            # Chercher le destinataire par nom dans les contacts
            from modules.contacts import chercher_contact
            # Extraire le nom potentiel
            for pattern in ["à ", "pour ", "envoie à "]:
                if pattern in t:
                    nom = t.split(pattern, 1)[1].split("le message")[0].strip()
                    # Chercher ce contact
                    return f"Quel est le numéro de {nom} ou quel message voulez-vous envoyer, Monsieur ?"

        # Lire notifications
        if any(x in t for x in ["notifications", "messages reçus", "lire les messages"]):
            return lire_notifications()

        # SMS
        if "sms" in t and any(x in t for x in ["envoie", "envoyer"]):
            import re
            tel_match = re.search(r'(\+?\d[\d\s]{7,14}\d)', texte)
            if tel_match:
                numero = tel_match.group(1)
                msg = texte.split(tel_match.group(1), 1)[-1].strip()
                return envoyer_sms(numero, msg)

    return None
