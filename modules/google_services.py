"""
VISION — Services Google
Google Docs, Sheets, Gmail, Calendar.
"""

import os
import pickle
import base64
from email.message import EmailMessage

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from modules import state
from modules.config import GOOGLE_SCOPES
from modules.file_manager import ouvrir_navigateur


def get_google_creds():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                print("[GOOGLE] Pas de credentials.json - fonctions Google desactivees.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", GOOGLE_SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as f:
            pickle.dump(creds, f)
    return creds


def get_docs_service():
    creds = get_google_creds()
    return build("docs", "v1", credentials=creds) if creds else None


def get_drive_service():
    creds = get_google_creds()
    return build("drive", "v3", credentials=creds) if creds else None


def get_gmail_service():
    creds = get_google_creds()
    return build("gmail", "v1", credentials=creds) if creds else None


def get_sheets_service():
    creds = get_google_creds()
    return build("sheets", "v4", credentials=creds) if creds else None


def get_calendar_service():
    creds = get_google_creds()
    return build("calendar", "v3", credentials=creds) if creds else None


def creer_google_doc(titre="Nouveau Document", contenu=""):
    try:
        service = get_docs_service()
        if not service:
            return "Google Docs non disponible."
        doc = service.documents().create(body={"title": titre}).execute()
        doc_id = doc["documentId"]
        state.dernier_doc_id = doc_id
        state.dernier_doc_titre = titre
        if contenu:
            requests_body = [{"insertText": {"location": {"index": 1}, "text": contenu}}]
            service.documents().batchUpdate(documentId=doc_id, body={"requests": requests_body}).execute()
        ouvrir_navigateur(f"https://docs.google.com/document/d/{doc_id}/edit")
        return f"Document {titre} cree et ouvert, Syndou."
    except Exception as e:
        return f"Erreur Google Docs : {e}"


def modifier_google_doc(contenu, doc_id=None):
    try:
        service = get_docs_service()
        if not service:
            return "Google Docs non disponible."
        target_id = doc_id or state.dernier_doc_id
        if not target_id:
            return "Aucun document ouvert en memoire."
        doc = service.documents().get(documentId=target_id).execute()
        end_index = doc["body"]["content"][-1]["endIndex"] - 1
        requests_body = [{"insertText": {"location": {"index": end_index}, "text": "\n" + contenu}}]
        service.documents().batchUpdate(documentId=target_id, body={"requests": requests_body}).execute()
        ouvrir_navigateur(f"https://docs.google.com/document/d/{target_id}/edit")
        return f"Texte ajoute dans le document {state.dernier_doc_titre}."
    except Exception as e:
        return f"Erreur modification doc : {e}"


def lire_emails(max_results=3):
    try:
        service = get_gmail_service()
        if not service:
            return "Gmail non disponible."
        results = service.users().messages().list(userId="me", maxResults=max_results, labelIds=["INBOX"]).execute()
        messages = results.get("messages", [])
        if not messages:
            return "Aucun email trouve."
        reponse = ""
        for msg in messages:
            m = service.users().messages().get(userId="me", id=msg["id"], format="metadata").execute()
            headers = {h["name"]: h["value"] for h in m["payload"]["headers"]}
            reponse += f"De: {headers.get('From', '?')} | Sujet: {headers.get('Subject', '?')}\n"
        return reponse.strip()
    except Exception as e:
        return f"Erreur Gmail : {e}"


def envoyer_email(destinataire, sujet, corps):
    try:
        service = get_gmail_service()
        if not service:
            return "Gmail non disponible."
        message = EmailMessage()
        message.set_content(corps)
        message["To"] = destinataire
        message["From"] = "me"
        message["Subject"] = sujet

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {"raw": encoded_message}
        send_message = service.users().messages().send(userId="me", body=create_message).execute()
        return f"Email envoyé avec succès à {destinataire}."
    except Exception as e:
        return f"Erreur lors de l'envoi de l'email : {e}"


def lister_evenements_calendar():
    try:
        service = get_calendar_service()
        if not service:
            return "Google Calendar non disponible."
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        events = service.events().list(calendarId="primary", timeMin=now, maxResults=5, singleEvents=True, orderBy="startTime").execute()
        items = events.get("items", [])
        if not items:
            return "Aucun evenement a venir."
        reponse = ""
        for e in items:
            start = e["start"].get("dateTime", e["start"].get("date"))
            reponse += f"{start} : {e['summary']}\n"
        return reponse.strip()
    except Exception as e:
        return f"Erreur Calendar : {e}"


def creer_google_sheet(titre="Nouvelle Feuille"):
    try:
        service = get_sheets_service()
        if not service:
            return "Google Sheets non disponible."
        sheet = service.spreadsheets().create(body={"properties": {"title": titre}}).execute()
        sheet_id = sheet["spreadsheetId"]
        ouvrir_navigateur(f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit")
        return f"Feuille {titre} creee et ouverte."
    except Exception as e:
        return f"Erreur Google Sheets : {e}"
