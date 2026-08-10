"""
VISION — Recherche Web & Service d'APIs tierces
Intègre Tavily, SerpAPI, NewsAPI, ArXiv, RestCountries et DeepL.
"""

import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote
from modules.config import (
    SERPAPI_API_KEY, TAVILY_API_KEY, RESTCOUNTRIES_API_KEY,
    NEWS_API_KEY, DEEPL_API_KEY
)

# ── 1. TAVILY SEARCH ──────────────────────────────────────────────────────────
def recherche_tavily(query, search_depth="basic"):
    """Effectue une recherche intelligente optimisée IA via l'API Tavily."""
    if not TAVILY_API_KEY:
        return None
    try:
        print(f"[TAVILY] Recherche pour : {query}")
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": search_depth,
            "include_answer": True,
            "max_results": 5
        }
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            answer = data.get("answer")
            results = data.get("results", [])
            out = ""
            if answer:
                out += f"Résumé Tavily : {answer}\n\n"
            out += "Sources :\n"
            for r in results[:4]:
                out += f"- {r.get('title')}: {r.get('content')[:200]}... ({r.get('url')})\n"
            return out
        else:
            print(f"[TAVILY] Code statut : {resp.status_code}")
            return None
    except Exception as e:
        print(f"[TAVILY ERROR] {e}")
        return None

# ── 2. SERPAPI SEARCH ─────────────────────────────────────────────────────────
def recherche_web_serpapi(query):
    """Effectue une recherche sur Google via SerpAPI."""
    if not SERPAPI_API_KEY or SERPAPI_API_KEY == "VOTRE_CLE_ICI":
        return None

    try:
        print(f"[WEB] Recherche SerpAPI pour : {query}")
        params = {
            "engine": "google",
            "q": query,
            "api_key": SERPAPI_API_KEY,
            "hl": "fr",
            "gl": "fr"
        }
        r = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
        data = r.json()

        if "news_results" in data:
            news = data["news_results"][:3]
            reponse = f"Voici les dernières actualités pour {query} :\n"
            for n in news:
                source = n.get("source", "Source inconnue")
                titre = n.get("title", "")
                reponse += f"- {titre} (via {source})\n"
            return reponse

        if "organic_results" in data:
            results = data["organic_results"][:3]
            reponse = f"Voici ce que j'ai trouvé sur le web pour {query} :\n"
            for r in results:
                titre = r.get("title", "")
                snippet = r.get("snippet", "")
                reponse += f"- {titre} : {snippet}\n"
            return reponse

        return None
    except Exception as e:
        print(f"[WEB] Erreur SerpAPI : {e}")
        return None

# ── 3. NEWS API ───────────────────────────────────────────────────────────────
def recherche_newsapi(query="top-headlines", language="fr"):
    """Interroge l'API NewsAPI pour obtenir les derniers articles de presse."""
    if not NEWS_API_KEY:
        return None
    try:
        print(f"[NEWSAPI] Recherche actualités pour : {query}")
        url = f"https://newsapi.org/v2/everything?q={quote(query)}&language={language}&sortBy=publishedAt&pageSize=4&apiKey={NEWS_API_KEY}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            articles = resp.json().get("articles", [])
            if not articles:
                return None
            out = f"Dernières actualités sur '{query}' :\n"
            for art in articles:
                out += f"- [{art.get('source', {}).get('name')}] {art.get('title')} : {art.get('description', '')}\n"
            return out
        return None
    except Exception as e:
        print(f"[NEWSAPI ERROR] {e}")
        return None

# ── 4. ARXIV API ──────────────────────────────────────────────────────────────
def recherche_arxiv(query, max_results=3):
    """Interroge l'API ArXiv pour trouver des publications scientifiques."""
    try:
        print(f"[ARXIV] Recherche scientifique pour : {query}")
        url = f"http://export.arxiv.org/api/query?search_query=all:{quote(query)}&start=0&max_results={max_results}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            root = ET.fromstring(resp.text)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entries = root.findall('atom:entry', ns)
            if not entries:
                return f"Aucun article scientifique trouvé sur ArXiv pour '{query}'."
            out = f"Publications scientifiques ArXiv pour '{query}' :\n"
            for entry in entries:
                title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
                summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')[:200]
                published = entry.find('atom:published', ns).text[:10]
                out += f"- **{title}** ({published}) : {summary}...\n"
            return out
        return None
    except Exception as e:
        print(f"[ARXIV ERROR] {e}")
        return None

# ── 5. RESTCOUNTRIES API ───────────────────────────────────────────────────────
def info_pays(country_name):
    """Obtient des informations géographiques et démographiques sur un pays."""
    try:
        print(f"[RESTCOUNTRIES] Recherche info pays : {country_name}")
        url = f"https://restcountries.com/v3.1/name/{quote(country_name)}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()[0]
            nom = data.get("name", {}).get("official", country_name)
            capitale = ", ".join(data.get("capital", ["Inconnue"]))
            population = f"{data.get('population', 0):,}"
            region = data.get("region", "Inconnue")
            subregion = data.get("subregion", "")
            devises = ", ".join([v.get("name") for v in data.get("currencies", {}).values()])
            drapeau = data.get("flag", "")
            return (
                f"{drapeau} **Informations sur {nom}** :\n"
                f"- Capitale : {capitale}\n"
                f"- Population : {population} habitants\n"
                f"- Région : {region} ({subregion})\n"
                f"- Monnaie : {devises}"
            )
        return f"Désolé Syndou, impossible d'obtenir des données sur le pays '{country_name}'."
    except Exception as e:
        print(f"[RESTCOUNTRIES ERROR] {e}")
        return None

# ── 6. DEEPL TRANSLATE API ────────────────────────────────────────────────────
def traduire_deepl(texte, target_lang="FR"):
    """Traduit du texte en utilisant l'API DeepL."""
    if not DEEPL_API_KEY:
        return None
    try:
        print(f"[DEEPL] Traduction texte vers {target_lang}...")
        url = "https://api-free.deepl.com/v2/translate"
        if not DEEPL_API_KEY.endswith(":fx"):
            url = "https://api.deepl.com/v2/translate"
        
        data = {
            "auth_key": DEEPL_API_KEY,
            "text": texte,
            "target_lang": target_lang
        }
        resp = requests.post(url, data=data, timeout=10)
        if resp.status_code == 200:
            translations = resp.json().get("translations", [])
            if translations:
                return translations[0].get("text")
        print(f"[DEEPL] Statut code : {resp.status_code}")
        return None
    except Exception as e:
        print(f"[DEEPL ERROR] {e}")
        return None

# ── 7. RECHERCHE GLOBALE AVEC FALLBACK ────────────────────────────────────────
def recherche_web_globale(query):
    """Orchestre la recherche web en utilisant les meilleures APIs disponibles."""
    # 1. Essayer Tavily (moteur IA haute précision)
    res_tavily = recherche_tavily(query)
    if res_tavily:
        return res_tavily

    # 2. Essayer SerpAPI (Google Search)
    res_serp = recherche_web_serpapi(query)
    if res_serp:
        return res_serp

    # 3. Essayer NewsAPI en secours
    res_news = recherche_newsapi(query)
    if res_news:
        return res_news

    return f"Désolé Syndou, aucune de mes sources web n'a pu trouver de résultats pour : {query}."
