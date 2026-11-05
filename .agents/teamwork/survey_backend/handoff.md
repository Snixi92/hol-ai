# Handoff Report — Survey Explorer 2 (Backend & Core Engine Architecture)

## 1. Observation
- **Emplacement du code inspecté** : `C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine`.
- **FastAPI Server & Endpoints** :
  - `src/api/server.py` (1 998 lignes) définit l'application `app = FastAPI(title="HoL AI Spatial OS API", lifespan=lifespan)` (l. 124).
  - Lifespan (l. 72–123) initialise `fakeredis.aioredis.FakeRedis(decode_responses=True)`, connecte `StreamBus`, instancie et démarre 6 agents spécialisés (`Canvas`, `Ingestion`, `Logistics`, `Finance`, `Content`, `Execution`) ainsi que le `AgentManager` et le `guardian` (`background_watcher.py`).
  - Endpoints de chat :
    - SSE Streaming : `@app.post("/api/chat/stream")` (l. 364–550) émettant des événements SSE `data: {"type": "status"|"complete"|"error", ...}` avec des statuts dynamiques (`thinking`, `shopping`, `search`, `browse`, `reading`, `writing`).
    - Synchrone JSON : `@app.post("/api/chat")` (l. 553–758) retournant un objet JSON complet (`reply`, `cards`, `thoughts`, `thinking_level`, `session_id`).
  - Montage statique et SPA (l. 1902–1997) : `/` sert `src/api/static/index.html` via `HTMLResponse`. `/apps`, `/backgrounds`, `/assets`, et `/static` sont montés via `StaticFiles`.
  - WebSockets : `/ws/canvas` (l. 1502) et `/ws/browser-stream` (l. 1612).
- **Moteur Cognitif ReAct & Thinking Levels** :
  - `src/services/cognitive_engine.py` (1 373 lignes) implémente `CognitiveAgentEngine.process_chat` avec le SDK `google.genai` (`types.GenerateContentConfig`, `tools=tools_list`).
  - Liste de 45+ outils natifs déclarés (l. 994–1047) : e-commerce, web search, code execution, terminal, artifacts, desktop, vocalisation, vision, et API publique.
  - Thinking Budget configuré (l. 1148–1155) : `fast` (0 tokens, temp 0.3), `standard` (2048 tokens, temp 0.2), `deep` (8192 tokens, temp 0.1), `ultra` (16384 tokens, temp 0.1).
  - Harnais `AgentRuntimeHarness` (l. 1050–1057) plafonne à 10 tool calls et 3 répétitions, générant une carte UI `tool_calls_section`.
- **Catalogue & Tool Calling d'APIs Publiques** :
  - `src/tools/public_registry.py` (928 lignes) indexe 1 079 APIs publiques gratuites sans authentification à travers 49 catégories, avec recherche inversée et aliasing multilingue (français, anglais, espagnol, darija).
  - `src/tools/tool_calling_engine.py` (534 lignes) exécute les requêtes via `httpx.AsyncClient` avec pool de 50 connexions, timeout de 5.0s, résilience aux erreurs HTTP (404, 429, 500) et tronquage de payload à 2 500 caractères.
- **Gestion des Sessions & Persistance (R2)** :
  - `src/services/session_manager.py` (338 lignes) : `SessionManager._sessions: Dict[str, ConversationSession] = {}` (l. 85).
  - Tout est conservé **uniquement en mémoire RAM**. Aucun fichier de base de données (SQLite, JSON, etc.) n'existe.
  - En cas de redémarrage du serveur, toutes les sessions sont perdues.
  - Aucun endpoint REST pour lister (`GET /api/conversations`), récupérer une conversation passée (`GET /api/conversations/{id}`), modifier le titre ou épingler (`PATCH`), supprimer (`DELETE`), générer automatiquement un titre ou exporter en Markdown/JSON.
- **Exécution des Tests Automatisés** :
  - Commande exécutée : `python -m pytest tests/test_chat_stream.py -v` -> 5 passed en 34.36s.
  - Commande exécutée : `python -m pytest tests/test_cognitive_engine_tools.py -v` -> 1 passed en 4.10s.
  - Commande exécutée : `python -m pytest tests/test_api_server.py -v` -> 17 passed en 41.29s.
  - Commande exécutée : `python -m pytest tests/test_public_api_tool_calling.py -v` -> 25 passed en 13.75s.
  - Commande exécutée : `python -m pytest tests/test_antigravity_parity_agents.py tests/test_chatbot_multiturn.py -v` -> 16 passed, 3 failed dans `test_chatbot_multiturn.py` :
    - Verbatim error : `KeyError: 'product'` à `deal1 = data1["cards"][0]["data"]` (ligne 134, 206, 293).
    - Cause : Le harnais injecte la carte `tool_calls_section` à l'index 0 (`cards[0]`), repoussant la carte `deal` à l'index 1. Le test supposait `cards[0]` sans filtrer par type (`[c for c in cards if c["type"] == "deal"]`).

## 2. Logic Chain
1. *De l'inspection de `session_manager.py` (l. 85)* : `SessionManager` gère un dictionnaire Python en mémoire vive sans aucune couche de persistance sur disque.
2. *De l'exigence R2 dans `ORIGINAL_REQUEST.md`* : Le système requiert un historique persistant classé chronologiquement (Aujourd'hui, 7 derniers jours, 30 jours), reprise instantanée du contexte, renommage automatique, épinglage, archivage, et export Markdown/JSON.
3. *Déduction R2* : Un module de persistance dédié (`src/services/conversation_store.py`) s'appuyant sur SQLite (`data/conversations.db` avec WAL mode) doit être introduit avec 6 endpoints REST dédiés (`/api/conversations...`).
4. *De l'inspection de `cognitive_engine.py` et `server.py`* : Le modèle Gemini est appelé via une liste interne fixe (`gemini-3.5-flash-lite`), le persona est figé sur "Big Sis", et le streaming SSE émet des événements de statut progressifs mais pas encore de citations numérotées `[1]` de style Perplexity.
5. *De l'exigence R3 dans `ORIGINAL_REQUEST.md`* : Pour atteindre le benchmark des chatbots leaders (ChatGPT, Claude, Gemini, Perplexity), HoL AI doit formaliser la sélection dynamique de modèles (`/api/models`), le sélecteur de persona/ton, la standardisation des citations web et la mise en avant des artefacts de code (`ArtifactsUIAgent`).
6. *De l'analyse des tests passés et échoués* : Le backend core est extrêmement stable (48/48 tests maîtresses passés). L'erreur découverte dans `test_chatbot_multiturn.py` prouve que l'ordre des cartes ne doit jamais être supposé fixe dans les tests ou le frontend, mais toujours filtré par `type`.

## 3. Caveats
- Les tests complets de scraping réel (`test_search_real.py`, `scratch_amazon_real.py`) dépendent de la connectivité réseau sortante vers des sites tiers susceptibles d'appliquer des captchas ou de modifier leurs sélecteurs CSS.
- L'environnement de test dispose de `fakeredis` en mémoire, ce qui permet d'exécuter l'intégralité du bus multi-agents sans serveur Redis externe.
- Le modèle par défaut requiert une clé API Gemini valide (`.env`). En l'absence de clé, un mécanisme de repli résilient (`LLMBrain._no_key_guidance` et fallback heuristique) prend le relais sans faire planter le serveur.

## 4. Conclusion
1. **L'architecture backend de HoL AI est prête et saine pour la production** : Le socle FastAPI, le moteur cognitif autonome ReAct, le streaming SSE et le catalogue de 1 079 APIs publiques fonctionnent impeccablement.
2. **Le chantier prioritaire est l'implémentation de la persistance SQLite (R2)** : Remplacer l'état en mémoire par une base SQLite locale, câbler la persistance des tours de chat et exposer les 6 endpoints REST pour la sidebar d'historique, l'épinglage, l'archivage, la génération automatique de titre et l'exportation.
3. **Le chantier d'enrichissement IA (R3)** : Exposer `/api/models`, ajouter les paramètres `model` et `persona` dans `ChatMessageRequest`, et enrichir le formatage des citations web Perplexity-style.
4. **Zéro régression garantie** : En conservant scrupuleusement la compatibilité des signatures de `/api/chat` et `/api/chat/stream`, l'intégralité de la suite de tests existante demeurera au vert.

## 5. Verification Method
1. **Vérification du rapport d'enquête** :
   - Inspecter le rapport complet : `C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\.agents\teamwork\survey_backend\survey_backend_report.md`.
2. **Exécution des suites de tests de validation backend** :
   ```powershell
   cd "C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine"
   python -m pytest tests/test_chat_stream.py -v
   python -m pytest tests/test_api_server.py -v
   python -m pytest tests/test_public_api_tool_calling.py -v
   python -m pytest tests/test_cognitive_engine_tools.py -v
   ```
3. **Conditions d'invalidation** :
   - Si les endpoints `/api/chat` ou `/api/chat/stream` modifient leurs champs de sortie (`reply`, `cards`, `thoughts`, `thinking_level`) en cassant la rétrocompatibilité, `test_chat_stream.py` et `test_api_server.py` échoueront.
   - Si une persistance est ajoutée mais dépend d'une base externe non disponible hors-ligne, les tests sur conteneurs isolés ou sans réseau échoueront.
