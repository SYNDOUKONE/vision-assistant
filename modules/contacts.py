"""
VISION — Carnet d'Adresses Local
Gestion de contacts personnels sans dépendance cloud.
"""
import json
import os
from datetime import datetime

CONTACTS_FILE = os.path.expanduser("~/VISION/data/contacts.json")


def _charger():
    os.makedirs(os.path.dirname(CONTACTS_FILE), exist_ok=True)
    if os.path.exists(CONTACTS_FILE):
        with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _sauvegarder(contacts):
    os.makedirs(os.path.dirname(CONTACTS_FILE), exist_ok=True)
    with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
        json.dump(contacts, f, ensure_ascii=False, indent=2)


def ajouter_contact(nom: str, telephone: str = "", email: str = "", notes: str = "") -> str:
    contacts = _charger()
    # Vérifier si le contact existe déjà
    for c in contacts:
        if c["nom"].lower() == nom.lower():
            return f"⚠️ Un contact nommé '{nom}' existe déjà."
    contact = {
        "id": len(contacts) + 1,
        "nom": nom,
        "telephone": telephone,
        "email": email,
        "notes": notes,
        "cree_le": datetime.now().isoformat()
    }
    contacts.append(contact)
    _sauvegarder(contacts)
    return f"✅ Contact '{nom}' ajouté avec succès."


def chercher_contact(recherche: str) -> str:
    contacts = _charger()
    resultats = [c for c in contacts if recherche.lower() in c["nom"].lower()
                 or recherche.lower() in c.get("telephone", "")
                 or recherche.lower() in c.get("email", "").lower()]
    if not resultats:
        return f"Aucun contact trouvé pour '{recherche}'."
    lignes = []
    for c in resultats:
        info = f"📇 **{c['nom']}**"
        if c.get("telephone"):
            info += f"\n   📞 {c['telephone']}"
        if c.get("email"):
            info += f"\n   ✉️ {c['email']}"
        if c.get("notes"):
            info += f"\n   📝 {c['notes']}"
        lignes.append(info)
    return "\n\n".join(lignes)


def supprimer_contact(nom: str) -> str:
    contacts = _charger()
    avant = len(contacts)
    contacts = [c for c in contacts if nom.lower() not in c["nom"].lower()]
    if len(contacts) < avant:
        _sauvegarder(contacts)
        return f"✅ Contact '{nom}' supprimé."
    return f"Aucun contact nommé '{nom}' trouvé."


def lister_contacts() -> str:
    contacts = _charger()
    if not contacts:
        return "Votre carnet d'adresses est vide, Monsieur."
    lignes = [f"• {c['nom']}" + (f" — {c['telephone']}" if c.get("telephone") else "")
              for c in sorted(contacts, key=lambda x: x["nom"])]
    return f"📇 {len(contacts)} contact(s) :\n" + "\n".join(lignes)


def traiter_commande_contacts(texte: str) -> str | None:
    """Interprète les commandes vocales liées aux contacts."""
    t = texte.lower()

    if any(x in t for x in ["contact", "carnet", "adresse"]):

        # Lister
        if any(x in t for x in ["liste", "montre", "affiche", "tous mes"]):
            return lister_contacts()

        # Chercher
        if any(x in t for x in ["cherche", "trouve", "qui est", "numéro de"]):
            # Extraire le nom recherché
            for pattern in ["cherche le contact", "trouve le contact", "qui est", "numéro de"]:
                if pattern in t:
                    nom = texte.split(pattern, 1)[-1].strip()
                    return chercher_contact(nom)
            return chercher_contact(texte.replace("contact", "").strip())

        # Ajouter
        if any(x in t for x in ["ajoute", "crée", "enregistre", "nouveau contact"]):
            import re
            # Essayer d'extraire nom et téléphone
            # Exemple : "ajoute le contact Mamadou avec le numéro 07 12 34 56 78"
            nom_match = re.search(r'contact\s+([A-Za-zÀ-ÿ\s]+?)(?:\s+avec|\s+numéro|\s+email|$)', texte, re.IGNORECASE)
            tel_match = re.search(r'(\+?\d[\d\s]{8,14}\d)', texte)
            email_match = re.search(r'[\w.-]+@[\w.-]+\.\w+', texte)

            nom = nom_match.group(1).strip() if nom_match else "Inconnu"
            tel = tel_match.group(1).strip() if tel_match else ""
            email = email_match.group(0) if email_match else ""

            return ajouter_contact(nom, tel, email)

        # Supprimer
        if any(x in t for x in ["supprime", "efface", "retire"]):
            nom = texte.replace("supprime le contact", "").replace("efface le contact", "").strip()
            return supprimer_contact(nom)

    return None
