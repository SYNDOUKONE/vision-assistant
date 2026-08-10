# 🚀 V.I.S.I.O.N — Roadmap Améliorations & Nouvelles Fonctionnalités

> Analyse basée sur le code source complet. Priorités définies en fonction de l'impact utilisateur.

---

## 🔴 BUGS CRITIQUES À CORRIGER

| # | Problème | Cause | Fix |
|---|---|---|---|
| 1 | **Historique de conversation infini** | `state.historique` grossit sans limite → crash mémoire après des heures | Limiter à 20 derniers échanges |
| 2 | **Multi-commandes JSON cassées** | Si Gemini génère 2 JSON collés sans espace, `re.findall` les rate | Améliorer le parser regex |
| 3 | **Session vocale qui reste active indéfiniment** | `SESSION_TIMEOUT = 120s` mais `dernier_message` non mis à jour pendant le cooldown | Corriger le calcul du timeout |
| 4 | **Crash si `pygame.mixer` pas init avant [parler()](file:///c:/VISION/modules/voice.py#36-106)** | [init_mixer()](file:///c:/VISION/modules/voice.py#22-25) vérifie `get_init()` mais pygame.init() peut échouer silencieusement | Ajouter try/except avec TTS de secours |
| 5 | **Fichier TTS non supprimé si erreur** | Si `pygame` plante pendant la lecture, le `finally` peut rater `os.remove()` | Utiliser un nom fixe + nettoyage au démarrage |

---

## 🟠 AMÉLIORATIONS PRIORITAIRES (Impact Direct)

### 🎙️ 1. Reconnaissance Vocale Améliorée

**Problème actuel :** Google Speech API = dépendant d'internet, lent (1-2s de latence), pas de VAD local.

**Solutions :**
- [ ] **Ajouter Whisper local** (OpenAI Whisper via `faster-whisper`) comme fallback offline — reconnaissance hors-ligne ultra-précise
- [ ] **Réduire `phrase_time_limit`** de 10s à 7s pour des commandes plus réactives
- [ ] **Ajouter des variantes du mot-clé** : "hey vision", "ok vision", "dis vision" en plus de juste "vision"
- [ ] **Indicateur visuel "Je vous entends"** dès la détection vocale, avant le traitement IA

### 🧠 2. Mémoire Long-Terme Intelligente

**Problème actuel :** La mémoire est un simple JSON clé-valeur. Pas de catégories, pas de recherche, et l'IA ne mémorise pas automatiquement les infos importantes de la conversation.

**Solutions :**
- [ ] **Mémorisation automatique** : Si VISION apprend quelque chose d'important sur Syndou en conversation, il le sauvegarde sans qu'on lui demande
- [ ] **Catégories de mémoire** : préférences, famille, habitudes, projets, anniversaires
- [ ] **Résumé de session** : À chaque fin de session, sauvegarder un résumé de ce qui a été dit
- [ ] **Mémoire épisodique** : "La semaine dernière tu m'as demandé..." (avec dates)

### 🔊 3. TTS Amélioré

**Problème actuel :** Edge TTS fonctionne bien mais est monotone et connecté. Pas de personnalité vocale.

**Solutions :**
- [ ] **Mode streaming TTS** : Commencer à parler pendant que la phrase est encore générée (réduire la latence de ~2s)
- [ ] **Variation de voix selon le contexte** : ton plus énergique pour les commandes, plus doux pour les réponses
- [ ] **Pyttsx3 en fallback offline** : Si edge_tts échoue, utiliser la voix système Windows
- [ ] **Contrôle vitesse/volume** vocal : "parle plus vite", "parle moins fort"

### ⚡ 4. Performance & Réactivité

**Problème actuel :** Gemini a 12s de timeout, puis cascade longue. L'utilisateur attend en silence.

**Solutions :**
- [ ] **Phrases d'attente dynamiques** : "Je cherche...", "Un instant Syndou...", "Laissez-moi réfléchir..." pendant le chargement IA
- [ ] **Cache des réponses** : Mettre en cache les questions méteo/sport récentes (valide 10 min) pour éviter les appels API répétés
- [ ] **Timeout Gemini réduit à 8s** et bascule plus rapide sur Groq (gratuit + rapide)
- [ ] **Traitement en parallèle** : Lancer la synthèse TTS pendant que la prochaine action JSON est traitée

---

## 🟡 NOUVELLES FONCTIONNALITÉS (Court Terme)

### 📱 5. Notifications & Rappels

- [ ] **Rappels temporels** : `"Vision, rappelle-moi dans 30 minutes de sortir le linge"` → timer local + alarme vocale
- [ ] **Rappels quotidiens** : `"Chaque matin à 8h, dis-moi la météo"` → planificateur cron interne
- [ ] **Minuterie cuisine** : `"Mets un minuteur de 10 minutes"` → compte à rebours avec alerte vocale
- [ ] **Réveil** : `"Réveille-moi à 7h30"` → alarme avec musique

### 📊 6. Dashboard Web Amélioré

**Problème actuel :** L'interface ne montre que l'orbe + le texte. Pas d'info contextuelle.

- [ ] **Panneau d'état maison** : température, consommation, qui est à la maison — visible en permanence
- [ ] **Historique de conversation** en bas de l'écran (scrollable)
- [ ] **Raccourcis rapides** : boutons cliquables pour les commandes fréquentes (lumières, météo, musique)
- [ ] **Visualisation des graphiques data science** directement dans l'interface web
- [ ] **Mode nuit automatique** : interface sombre atténuée après 22h

### 🔔 7. Alertes Intelligentes

- [ ] **Alerte si batterie téléphone < 20%** → notification vocale automatique
- [ ] **Alerte météo automatique le matin** (pluie prévue → "prenez un parapluie")
- [ ] **Alerte boîte aux lettres** (si capteur HA détecte ouverture)
- [ ] **Alerte consommation anormale** (si consommation > seuil configuré)

### 🗺️ 8. Navigation & Transport

- [ ] **Temps de trajet** : `"Combien de temps pour aller à Paris ?"` (Google Maps API)
- [ ] **Trafic en temps réel** : `"Il y a des bouchons sur la A10 ?"` (Waze API)
- [ ] **Horaires transports** : bus, RER, train depuis l'adresse

### 📸 9. Vision Caméra Améliorée

- [ ] **Surveillance continue** : mode "garde" avec détection de mouvement via webcam
- [ ] **Reconnaissance de personnes** : "Qui est devant moi ?" (avec entraînement sur photos)
- [ ] **Lecture de documents** : `"Lis ce que j'ai dans la main"` → OCR sur image webcam
- [ ] **Analyse d'objet** : pointer un objet devant la webcam → identification

---

## 🟢 NOUVELLES FONCTIONNALITÉS (Moyen Terme)

### 🏠 10. Domotique Avancée

- [ ] **Routines automatiques** : "Mode matin" → ouvre volets + allume cuisine + météo + musique
- [ ] **Scènes personnalisées** : créer et nommer ses propres scènes d'ambiance
- [ ] **Suivi présence** : "Qui est à la maison ?" (via téléphones sur le réseau WiFi)
- [ ] **Mode vacances amélioré** : simulation aléatoire des lumières + alertes intrusion

### 🤖 11. Agent IA Autonome

- [ ] **Tâches multi-étapes** : "Trouve le meilleur prix pour une PS5 et envoie-moi le lien par email"
- [ ] **Navigation web autonome** : VISION ouvre Chrome, navigue, remplit des formulaires
- [ ] **Automatisation de tâches répétitives** : "Chaque vendredi, génère un rapport de mes dépenses"
- [ ] **Mode assistant personnel** : agenda, liste de tâches, suivi des objectifs

### 🎮 12. Jeux & Divertissement

- [ ] **Jeux vocaux** : Quiz, devinettes, 20 questions
- [ ] **Histoires interactives** : VISION raconte une histoire adaptative
- [ ] **Blague du jour** au réveil
- [ ] **Contrôle de jeux** : "Mets le jeu en pause" via simulation clavier racing

### 📧 13. Communication Avancée

- [ ] **Envoi d'emails** : `"Envoie un email à maman pour dire que je rentre ce soir"`
- [ ] **Rédaction de messages WhatsApp** (sans appel, juste message texte)
- [ ] **Lecture des SMS** (via Android Debug Bridge ou application mobile)
- [ ] **Résumé de la boîte mail** : "J'ai des emails importants aujourd'hui ?"

### 💰 14. Finance & Crypto

- [ ] **Prix cryptos** : `"Prix du Bitcoin maintenant ?"` (API CoinGecko gratuite)
- [ ] **Taux de change** en temps réel (API Fixer.io)
- [ ] **Suivi budget** : noter les dépenses vocalement et générer un rapport mensuel
- [ ] **Prix actions** (API Alpha Vantage gratuite)

---

## 🔵 VISION LONG TERME (3-6 mois)

### 🌐 15. Mode Serveur Distribué

- [ ] **Backend cloud** léger pour les commandes texte (sans micro) via Cloudflare Tunnel
- [ ] **App Android native** avec reconnexion auto et notifications push
- [ ] **Multi-utilisateurs** : profil Syndou + profil famille avec permissions différentes
- [ ] **Synchronisation** de la mémoire sur le cloud (chiffré)

### 🔌 16. Intégrations Tierces

- [ ] **Notion** : créer des pages, lire des listes de tâches
- [ ] **Todoist / Things** : gérer les tâches
- [ ] **Trello** : déplacer des cartes, créer des tickets
- [ ] **Discord** : envoyer des messages dans des serveurs
- [ ] **Telegram Bot** : VISION accessible partout via Telegram

### 🧩 17. Système de Plugins

- [ ] **Architecture plugin** : chaque fonctionnalité = un plugin activable/désactivable
- [ ] **Marketplace** : créer ses propres commandes personnalisées en YAML
- [ ] **API publique locale** : permettre à d'autres apps de dialoguer avec VISION via REST

---

## 📋 AMÉLIORATIONS TECHNIQUES (Architecture)

| # | Amélioration | Bénéfice |
|---|---|---|
| A | **Logger structuré** (fichier `vision.log` quotidien) | Diagnostic des erreurs sans regarder le terminal |
| B | **Tests unitaires** pour les modules critiques | Éviter les régressions lors des mises à jour |
| C | **Gestion de version automatique** | Savoir exactement quelle version tourne |
| D | **Hot-reload des modules** | Modifier un module sans redémarrer VISION |
| E | **Tableau de bord d'état** dans le terminal | CPU, mémoire, uptime, modèle IA actif |
| F | **Historique limité et compressé** | Résumé des anciennes conversations pour économiser les tokens |
| G | **Watchdog auto-restart** | Si VISION plante, il redémarre automatiquement |
| H | **Configuration via interface web** | Changer les paramètres sans toucher au code |

---

## 🎯 PLAN D'ACTION RECOMMANDÉ

```
SEMAINE 1 (Corrections)
  ✅ Anti-écho (fait ✔)
  ⬜ Limiter historique à 20 échanges
  ⬜ TTS fallback pyttsx3
  ⬜ Logger structuré

SEMAINE 2 (Impact max)
  ⬜ Rappels + minuteries
  ⬜ Phrases d'attente pendant IA
  ⬜ Alertes batterie/météo auto

SEMAINE 3 (Interface)
  ⬜ Dashboard état maison
  ⬜ Historique conversation dans l'UI
  ⬜ Mode nuit automatique

SEMAINE 4-8 (Nouvelles fonctions)
  ⬜ Prix cryptos & finance
  ⬜ Navigation/trafic
  ⬜ Rappels quotidiens programmés
  ⬜ WhatsApp messages texte
```
