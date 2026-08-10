"""
VISION — Configuration & Constantes Globales
Charge les variables d'environnement, initialise les clients API,
et définit toutes les constantes et mappings du système.
"""

import os
import socket
from dotenv import load_dotenv

# ── Chargement .env ──────────────────────────────────────────────────────────
load_dotenv()

# ── Réseau ───────────────────────────────────────────────────────────────────
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

LOCAL_IP = get_local_ip()

# ── Clés API ─────────────────────────────────────────────────────────────────
GEMINI_API_KEY        = os.getenv("GEMINI_API_KEY")
YOUTUBE_API_KEY       = os.getenv("YOUTUBE_API_KEY")
XAI_API_KEY           = os.getenv("XAI_API_KEY")
HA_URL                = os.getenv("HA_URL")
HA_TOKEN              = os.getenv("HA_TOKEN")
SERPAPI_API_KEY        = os.getenv("SERPAPI_API_KEY")
GROQ_API_KEY          = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY        = os.getenv("TAVILY_API_KEY")
RESTCOUNTRIES_API_KEY = os.getenv("RESTCOUNTRIES_API_KEY")
NEWS_API_KEY          = os.getenv("NEWS_API_KEY")
DEEPL_API_KEY         = os.getenv("DEEPL_API_KEY")
HUGGINGFACE_API_KEY   = os.getenv("HUGGINGFACE_API_KEY")

# Spotify
SPOTIPY_CLIENT_ID     = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI  = os.getenv("SPOTIPY_REDIRECT_URI")

# ── Clients API ──────────────────────────────────────────────────────────────
import google.genai as genai
from google.genai import types as genai_types
from openai import OpenAI

gemini_client = genai.Client(api_key=GEMINI_API_KEY)


grok_client = None
if XAI_API_KEY and XAI_API_KEY != "VOTRE_CLE_ICI":
    grok_client = OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")

groq_client = None
if GROQ_API_KEY and GROQ_API_KEY != "VOTRE_CLE_ICI":
    groq_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

# Spotify
import spotipy
from spotipy.oauth2 import SpotifyOAuth

sp = None
if SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_ID != "VOTRE_ID_SPOTIFY":
    try:
        auth_manager = SpotifyOAuth(
            client_id=SPOTIPY_CLIENT_ID,
            client_secret=SPOTIPY_CLIENT_SECRET,
            redirect_uri=SPOTIPY_REDIRECT_URI,
            scope="user-modify-playback-state user-read-playback-state"
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
        print("[SPOTIFY] Client initialise.")
    except Exception as e:
        print(f"[SPOTIFY] Erreur initialisation : {e}")

# ── Modèles IA ───────────────────────────────────────────────────────────────
MODELS_LIST  = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-pro-latest"]
CHOSEN_MODEL = MODELS_LIST[0]

OLLAMA_URL    = "http://127.0.0.1:11434"
OLLAMA_MODELS = ["mistral:instruct", "mistral", "llama3:8b", "llama3", "gemma4"]

# ── Paramètres généraux ──────────────────────────────────────────────────────
VILLE_PAR_DEFAUT = "Amilly"
LAT_PAR_DEFAUT   = 47.9742
LON_PAR_DEFAUT   = 2.7708

CLAP_THRESHOLD   = 1200
WAKE_WORD        = "vision"
SESSION_TIMEOUT  = 120

CREATOR_INFO = (
    "INFORMATIONS SUR TON CREATEUR :\n"
    "- Prenom : Syndou\n"
    "- Age : 22 ans\n"
    "- Date de naissance : 02 Mai 2004\n"
    "- Role : Ton createur et maitre\n"
    "- Tu dois toujours l appeler Syndou avec respect "
    "mais aussi une pointe de sarcasme affectueux.\n"
)

# ── Home Assistant ───────────────────────────────────────────────────────────
HA_HEADERS = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json"
}

PIECES_LUMIERES = {
    "salon": "light.salon", "plafond salon": "light.plafond",
    "canapes": "light.canapes", "lampadaire": "light.lampadaire",
    "lampe de chevet": "light.lampe_de_chevet_2",
    "grosse boule": "light.grosse_boule", "petite boule": "light.petite_boule",
    "cuisine": "light.lsc_smart_led_strip_rgbic_cctic_5m",
    "cuisine 2": "light.cuisine_2",
    "esteban": "light.pc_3", "pc esteban": "light.pc_3",
    "bureau": "light.bureau", "pc": "light.pc", "pc 2": "light.pc_2",
    "parents": "light.chambre_parentale",
    "chambre parentale": "light.chambre_parentale",
    "chambre": "light.chambre_parentale",
    "plafond chambre": "light.plafond_2",
    "toutes": "light.all", "tout": "light.all",
}

PIECES_PRISES = {
    "salon": "switch.prise_salon",
    "bureau": "switch.prise_bureau",
    "cuisine": "switch.prise_cuisine",
}

PIECES_CAPTEURS = {
    "salon": "sensor.salon_temperature_2",
    "chambre": "sensor.miaomiaoc_de_blt_4_14kc52pmcgk00_t2_temperature_p_2_1",
    "bureau": "sensor.temp_temperature",
    "exterieur": "sensor.temperature_exterieure",
    "dehors": "sensor.temperature_exterieure",
    "consommation": "sensor.lixee_zlinky_tic_puissance_apparente",
    "tiktok": "sensor.tiktok_followers_techenclair",
    "oeufs": "input_select.ramassage_des_oeufs",
}

PIECES_HUMIDITE = {"bureau": "sensor.temp_humidite"}

HA_TARIFS = {
    "p1": 0.1296, "p2": 0.1603, "p3": 0.1486,
    "p4": 0.1894, "p5": 0.1568, "p6": 0.7562,
}

APPAREILS_ENERGIE = {
    "tv": "sensor.prise_1_salon_mensuel",
    "salon": "sensor.prise_1_salon_mensuel",
    "pc esteban": "sensor.prise_3_pc_esteban_mensuel",
    "esteban": "sensor.prise_3_pc_esteban_mensuel",
    "zoe": "sensor.zoe_mensuel", "voiture": "sensor.zoe_mensuel",
    "lave-vaisselle": "sensor.prise_2_lave_vaisselle_mensuel",
    "pc salon": "sensor.pc_salon_conso_pc_salon_mensuel_2",
    "bureau": "sensor.bureau_mensuel",
}

APPAREILS_BATTERIE = {
    "mon telephone": "sensor.sm_s921b_battery_level",
    "papa": "sensor.sm_s921b_battery_level",
    "Syndou": "sensor.sm_s921b_battery_level",
    "samsung papa": "sensor.sm_s921b_battery_level",
    "julie": "sensor.sm_julie_battery_level",
    "maman": "sensor.sm_julie_battery_level",
    "samsung maman": "sensor.sm_julie_battery_level",
    "esteban": "sensor.esteban_battery_level",
    "honor": "sensor.honor_battery_level",
    "tablette honor": "sensor.honor_battery_level",
    "montre papa": "sensor.galaxy_watch6_classic_d4he_battery_level",
    "montre Syndou": "sensor.galaxy_watch6_classic_d4he_battery_level",
    "montre maman": "sensor.galaxy_watch8_fbxh_battery_level",
    "montre julie": "sensor.galaxy_watch8_fbxh_battery_level",
    "bob": "sensor.bob_batterie", "aspirateur bob": "sensor.bob_batterie",
    "dyad": "sensor.dyad_air_2024_batterie",
    "aspirateur dyad": "sensor.dyad_air_2024_batterie",
    "telecommande hue": "sensor.maison_interrupteur_batterie",
    "interrupteur": "sensor.maison_interrupteur_batterie",
    "toner": "sensor.samsung_m2020_series_black_toner_s_n_crum_17091625519",
    "imprimante": "sensor.samsung_m2020_series_black_toner_s_n_crum_17091625519",
    "boite aux lettres": "sensor.detecterur_batterie",
    "detecteur cuisine": "sensor.detecteur_1_batterie",
    "detecteur escalier": "sensor.detecteur_2_batterie",
    "camera jardin": "sensor.arriere_cour_battery_percentage",
    "thermometre bureau": "sensor.temp_batterie",
}

COULEURS_MAP = {
    "rouge": [255, 0, 0], "bleu": [0, 0, 255], "vert": [0, 255, 0],
    "blanc": [255, 255, 255], "orange": [255, 140, 0],
    "violet": [148, 0, 211], "rose": [255, 20, 147],
    "jaune": [255, 255, 0], "cyan": [0, 255, 255],
    "magenta": [255, 0, 255], "turquoise": [64, 224, 208],
    "or": [255, 215, 0], "argent": [192, 192, 192],
    "indigo": [75, 0, 130], "marron": [139, 69, 19],
    "citron": [255, 250, 0], "corail": [255, 127, 80],
    "lavande": [230, 230, 250],
}

CODES_METEO = {
    0: "ciel degage",
    1: "principalement clair", 2: "partiellement nuageux", 3: "couvert",
    45: "brouillard", 48: "brouillard givrant",
    51: "bruine legere", 53: "bruine moderee", 55: "bruine dense",
    61: "pluie faible", 63: "pluie moderee", 65: "pluie forte",
    71: "neige faible", 73: "neige moderee", 75: "neige forte",
    80: "averses faibles", 81: "averses moderees", 82: "averses violentes",
    85: "averses de neige", 86: "averses de neige fortes",
    95: "orage", 96: "orage avec grele", 99: "orage violent avec grele",
}

# ── Extensions fichiers ──────────────────────────────────────────────────────
EXTENSIONS = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp",
               ".tiff", ".tif", ".webp", ".svg", ".ico",
               ".heic", ".raw", ".cr2", ".nef"],
    "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv",
               ".flv", ".webm", ".m4v", ".mpg", ".mpeg",
               ".3gp", ".ts"],
    "Musique": [".mp3", ".wav", ".flac", ".aac", ".ogg",
                ".wma", ".m4a", ".opus", ".aiff"],
    "Documents": [".pdf", ".doc", ".docx", ".xls", ".xlsx",
                  ".ppt", ".pptx", ".txt", ".odt", ".ods",
                  ".odp", ".rtf", ".csv", ".epub"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz",
                 ".bz2", ".xz", ".iso"],
    "Code": [".py", ".js", ".html", ".css", ".java",
             ".cpp", ".c", ".h", ".cs", ".php",
             ".json", ".xml", ".yaml", ".yml",
             ".sh", ".bat", ".ps1", ".ts", ".jsx",
             ".tsx", ".vue", ".go", ".rs", ".rb"],
    "Executables": [".exe", ".msi", ".apk", ".dmg", ".deb"],
}

# ── Google Scopes ────────────────────────────────────────────────────────────
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/calendar",
]
