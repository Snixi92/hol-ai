# Rapport d'Investigation Architectural : Backend & Core Engine HoL AI
**Auteur** : Survey Explorer 2 (Backend & Core Engine Architecture)  
**Date** : 2026-11-03  
**Périmètre** : `services/core-engine` (FastAPI Server, Cognitive Engine, Tool Calling Engine, Public Registry, Multi-Agent Bus, Persistence, Harness & Test Suites)  
**Statut** : Investigation Complète & Blueprints d'Intégration R2 / R3 Prêts

---

## 1. Executive Summary

Le backend de **HoL AI** situé dans `services/core-engine` constitue une architecture hybride hautement résiliente combinant :
1. **Un serveur FastAPI & Gateway WebSocket** (`src/api/server.py`, 1 998 lignes) servant à la fois une Single Page Application (SPA) riche (`src/api/static/index.html`), des points d'accès conversationnels SSE en streaming (`/api/chat/stream`) et synchrones (`/api/chat`), et plus de 25 endpoints REST d'orchestration, de supervision matérielle, de téléphonie, de vision et d'automatisation OS.
2. **Un Cerveau Cognitif Autonome ReAct** (`src/services/cognitive_engine.py`, 1 373 lignes) piloté par les modèles Gemini (famille `gemini-3.5-flash-lite`, `gemini-flash-latest`), doté d'un Automatic Function Calling natif sur **45+ outils enregistrés**, d'un système de *Thinking Budget* dynamique (modes `fast`, `standard`, `deep`, `ultra`), et d'un harnais de sécurité anti-boucle (`AgentRuntimeHarness`).
3. **Un Moteur de Tool Calling & Registre d'APIs Publiques** (`src/tools/public_registry.py` & `src/tools/tool_calling_engine.py`) indexant **1 079 APIs publiques gratuites sans clé** réparties en 49 catégories, avec recherche inversée sub-milliseconde (<1 ms) et exécution asynchrone non-bloquante avec résilience HTTP et pool de connexions `httpx`.
4. **Un Cluster Multi-Agents Événementiel** reposant sur Redis Streams (`StreamBus` avec fallback `fakeredis`) reliant 6 agents spécialisés (`Canvas`, `Ingestion`, `Logistics`, `Finance`, `Content`, `Execution`) coordonnés par un superviseur central (`AgentManager`) avec ordonnancement topologique acyclique (`DAGPlanner`).
5. **État Actuel de la Persistance (R2)** : La gestion des sessions est **strictement éphémère** en mémoire vive via `SessionManager` (`_sessions: Dict[str, ConversationSession]`). Tout redémarrage ou plantage du serveur efface l'intégralité des discussions. Il n'existe actuellement aucune base SQLite, aucun endpoint d'archivage, d'épinglage, de génération automatique de titre ou d'export Markdown/JSON.
6. **Benchmark des Chatbots Leaders (R3)** : HoL AI intègre déjà des atouts majeurs (streaming SSE avec statuts cognitifs progressifs, réflexion avancée, grounding factuel en direct, 1 079 outils d'APIs publiques, parité linguistique et Big Sis Energy). Cependant, pour atteindre la parité totale avec ChatGPT, Claude et Perplexity, il convient d'ajouter la sélection dynamique de modèle, le choix de persona/ton, la mise en forme standardisée des citations et sources web, et la gestion interactive des artefacts de code.
7. **Bilan des Tests** : La suite de tests existante (`services/core-engine/tests/`) compte 28 fichiers. Les suites maîtresses (`test_chat_stream.py`, `test_api_server.py`, `test_cognitive_engine_tools.py`, `test_public_api_tool_calling.py`) passent à 100% (48/48 tests validés). Une fragilité d'indexation (`cards[0]` vs filtrage par type `type == 'deal'`) a été découverte et documentée dans `test_chatbot_multiturn.py`.

---

## 2. Architecture du Serveur FastAPI & Points d'Accès

### 2.1 Cycle de Vie et Middleware (`src/api/server.py`)
- **Gestionnaire de cycle de vie (`lifespan`)** (l. 72–123) :
  - Initialise un client Redis simulé en mémoire via `fakeredis.aioredis.FakeRedis(decode_responses=True)`.
  - Connecte le `StreamBus` pour la communication inter-agents.
  - Instancie et démarre les 6 agents réels (`CanvasAgent`, `IngestionMemoryAgent`, `LogisticsAgent`, `FinanceAgent`, `ContentSocialAgent`, `ExecutionAgent`).
  - Démarre le superviseur central `AgentManager` et le gardien de tâches d'arrière-plan `BackgroundWatcher` (`guardian.start()`).
  - Arrêt gracieux propre lors de la fermeture de FastAPI.
- **Middleware CORS** (l. 126–132) :
  - `allow_origins=["*"]`, `allow_credentials=True`, `allow_methods=["*"]`, `allow_headers=["*"]`.
- **Montage Statique & SPA** (l. 1902–1997) :
  - Route racine `GET /` : lit et renvoie directement `src/api/static/index.html` en UTF-8 (`HTMLResponse`).
  - `GET /manifest.json` : sert la configuration PWA Web App Manifest.
  - `GET /icon.svg` : icône vectorielle officielle.
  - `GET /qr_phone.png` : génération dynamique ou fallback PNG du QR code d'appairage mobile LAN.
  - `GET /sw.js` : Service Worker PWA pour cache et mode hors-ligne.
  - `app.mount("/apps", StaticFiles(directory="src/api/static/apps", html=True))` : sert les applications interactives générées à chaud (ex: morpion HTML/JS).
  - `app.mount("/backgrounds", StaticFiles(...))` : arrière-plans animés interactifs 21st.dev (canvas, shaders).
  - `app.mount("/assets", StaticFiles(...))` : icônes vectorielles et illustrations.
  - `app.mount("/static", StaticFiles(...))` : ressources statiques racine.

### 2.2 Passerelles Temps Réel (WebSockets)
1. `WS /ws/canvas` (l. 1502–1610) :
   - Synchronisation bidirectionnelle du canevas spatial.
   - Diffuse les créations, déplacements et connexions de nœuds spatiaux entre clients connectés (`ConnectionManager.broadcast`).
2. `WS /ws/browser-stream` (l. 1612–1658) :
   - Streaming d'images de navigation web en direct (Computer-Use) pour observer ou prendre le contrôle distant ("Take Over").

### 2.3 Matrice Exhaustive des Endpoints REST
| Méthode | URL | Description & Rôle | Dépendance de Service |
|---|---|---|---|
| `POST` | `/api/chat/stream` | Endpoint conversationnel SSE streaming (statuts dynamiques + réponse) | `CognitiveAgentEngine`, `SessionManager` |
| `POST` | `/api/chat` | Endpoint conversationnel standard JSON synchrone multi-tours | `CognitiveAgentEngine`, `SessionManager` |
| `POST` | `/api/orchestrate` | Orchestration multi-agents directe et création de blocs sur canevas | `AgentManager`, `StreamBus` |
| `GET` | `/api/state` | État global du cluster et des nœuds du canevas spatial | `StreamBus`, `CanvasAgent` |
| `GET` | `/api/agents/status` | Télémétrie et état de santé des 7 agents du cluster | `AgentManager`, `agents_registry` |
| `POST` | `/api/actions/execute` | Exécution Human-in-the-Loop avec signature cryptographique sha256 | `SecureVaultService` |
| `GET` | `/api/settings/api-key` | Consultation du statut de configuration de la clé Gemini | `LLMBrain` |
| `POST` | `/api/settings/api-key` | Mise à jour à chaud de la clé API Gemini | `LLMBrain` |
| `GET` | `/api/connectors/status` | Statut des connecteurs externes (Gmail, Calendar, Notion, Stripe) | `ConnectorsManager` |
| `POST` | `/api/connectors/configure` | Configuration des identifiants et tokens de connecteurs | `ConnectorsManager` |
| `POST` | `/api/connectors/test/{id}` | Test de connectivité unitaire sur un connecteur | `ConnectorsManager` |
| `GET` | `/api/tools/public-apis/stats`| Statistiques du catalogue d'APIs publiques (1 079 outils, 49 catégories) | `PublicApiRegistry` |
| `GET` | `/api/tools/public-apis/categories` | Liste des 49 catégories d'APIs publiques avec compteurs | `PublicApiRegistry` |
| `GET` | `/api/tools/public-apis` | Recherche inversée et filtrage multicritères d'APIs publiques | `PublicApiRegistry` |
| `POST` | `/api/tools/public-apis/execute` | Exécution directe d'un outil d'API publique avec paramètres | `AutonomousToolCallingEngine` |
| `GET` | `/api/background/status` | Surveillance 24/7 des missions actives d'arrière-plan | `BackgroundWatcher` |
| `GET` | `/api/background/cron` | Liste des tâches planifiées d'arrière-plan | `BackgroundWatcher` |
| `POST` | `/api/background/cron/{id}/trigger` | Déclenchement forcé manuel d'une tâche cron | `BackgroundWatcher` |
| `POST` | `/api/background/mission` | Enregistrement d'une nouvelle mission autonome | `BackgroundWatcher` |
| `GET` | `/api/jarvis/briefing` | Briefing matinal complet (météo, emails, agenda, métriques) | `JarvisBriefingService` |
| `GET` | `/api/vault/ledger` | Journal d'audit immuable des actions sensibles de l'Enclave | `SecureVaultService` |
| `POST` | `/api/vault/sandbox` | Exécution sécurisée de code Python en bac à sable | `SecureVaultService` |
| `GET` | `/api/telegram/status` | État de la passerelle Telegram | `TelegramGatewayService` |
| `POST` | `/api/telegram/settings` | Paramètres du bot Telegram | `TelegramGatewayService` |
| `POST` | `/api/sourcing/compare` | Comparateur e-commerce multi-fournisseurs avec marges | `ProductHunterService` |
| `POST` | `/api/logistics/track` | Suivi de colis multi-transporteurs (UPS, Mondial Relay, etc.) | `LogisticsAgent` |
| `POST` | `/api/cfo/margin` | Calculateur de marge nette e-commerce et TVA 20% | `FinanceAgent` |
| `GET` | `/api/cfo/affiliate-reconciliation` | Réconciliation des commissions d'affiliation | `FinanceAgent` |
| `POST` | `/api/cfo/receipt` | OCR et analyse de facture / ticket de caisse | `FinanceAgent` |
| `POST` | `/api/canvas/upload` | Ingestion multimodale de fichiers (PDF, PNG, JPG, JSON) | `IngestionMemoryAgent` |
| `GET` | `/api/workspace/goals` | Consultation des objectifs utilisateur (Goals space) | `WorkspaceNavigatorAgent` |
| `POST` | `/api/workspace/goals` | Ajout d'un objectif de vie ou professionnel | `WorkspaceNavigatorAgent` |
| `GET` | `/api/memory/facts` | Consultation de la mémoire biographique persistante | `BiographicalMemoryAgent` |
| `POST` | `/api/memory/facts` | Enregistrement d'un fait permanent sur l'utilisateur | `BiographicalMemoryAgent` |
| `DELETE` | `/api/memory/facts/{cat}/{key}` | Suppression d'un fait biographique | `BiographicalMemoryAgent` |
| `POST` | `/api/voice/synthesize` | Synthèse vocale TTS (voix française Hortense) | `LiveVoiceAgent` |
| `GET` | `/api/voice/capabilities` | Capacités audio et microphones disponibles | `LiveVoiceAgent` |
| `POST` | `/api/notifications/dispatch` | Émission d'une notification Windows 11 Toast native | `ProactiveNotifierAgent` |
| `GET` | `/api/desktop/windows` | Liste des fenêtres actives sur le PC hôte | `DesktopAutomationAgent` |
| `POST` | `/api/desktop/focus` | Mise au premier plan d'une application | `DesktopAutomationAgent` |
| `POST` | `/api/desktop/launch` | Lancement natif d'une application Windows | `DesktopAutomationAgent` |
| `POST` | `/api/desktop/close` | Fermeture propre d'une application Windows | `DesktopAutomationAgent` |
| `POST` | `/api/desktop/keys` | Envoi de raccourcis clavier | `DesktopAutomationAgent` |
| `GET` | `/api/desktop/telemetry` | Télémétrie CPU, RAM, batterie et OS du PC hôte | `DesktopAutomationAgent` |
| `POST` | `/api/vision/camera-scan` | Analyse vision de photo caméra (repas, ticket, produit) | `MobilePWAVisionAgent` |
| `GET` | `/api/system/network-info` | Détection de l'IP LAN locale pour accès mobile PWA | Network socket helper |

---

## 3. Streaming SSE vs Requêtes JSON Standard

### 3.1 Protocole SSE (`/api/chat/stream`)
Le endpoint `/api/chat/stream` implémente un flux **Server-Sent Events (SSE)** conforme aux interfaces modernes de ChatGPT, Claude et Gemini.
- **Requête entrante (`ChatMessageRequest`)** :
  ```json
  {
    "message": "Compare l'iPhone XR et le Galaxy S20",
    "user_id": "user_main",
    "session_id": "sess_12345",
    "history": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}],
    "thinking_level": "deep"
  }
  ```
- **Événements émis en temps réel (`data: {...}\n\n`)** :
  1. **Événements de statut progressif (`type: "status"`)** :
     ```json
     {"type": "status", "text": "🔬 Deep Thinking : Décomposition logique du problème...", "step": "thinking"}
     {"type": "status", "text": "🛍️ Recherche des offres pour 'iPhone XR'...", "step": "shopping", "product": "iPhone XR"}
     {"type": "status", "text": "🌐 Données en direct récupérées...", "step": "tool_calling"}
     {"type": "status", "text": "✍️ Rédaction de la réponse...", "step": "writing"}
     ```
  2. **Événement de complétion finale (`type: "complete"`)** :
     ```json
     {
       "type": "complete",
       "reply": "Voici le comparatif complet entre l'iPhone XR et le Galaxy S20...",
       "cards": [
         {"type": "tool_calls_section", "data": {"tool_calls": [...]}},
         {"type": "second_hand_deals", "data": {...}}
       ],
       "thoughts": "L'utilisateur cherche un comparatif objectif...",
       "thinking_level": "deep",
       "session_id": "sess_12345",
       "engine": "autonomous_cognitive_agent"
     }
     ```
  3. **Pings de maintien de connexion (`: ping\n\n`)** émis toutes les 25 secondes si le traitement LLM ou les outils externes prennent du temps, évitant tout timeout de proxy ou navigateur.
  4. **Annulation proactive (`proc_task.cancel()`)** dans le bloc `finally` si le client interrompt sa connexion SSE avant la fin.

### 3.2 Endpoint Synchrone (`/api/chat`)
- Point d'accès direct renvoyant l'objet complet en un seul bloc JSON (`application/json`).
- Traitement identique du contexte conversationnel, de la résolution d'anaphores, du ReAct loop et des cartes interactives.
- Utilisé comme repli automatique par le frontend si le lecteur SSE rencontre une rupture réseau (`index.html` l. 3615).

---

## 4. Moteur Cognitif, Tool-Calling & Thinking Budget

### 4.1 Cerveau ReAct Autonome (`src/services/cognitive_engine.py`)
Le moteur cognitif s'affranchit des anciens entonnoirs rigides à base de regex au profit d'un véritable agent autonome avec **Automatic Function Calling** :
- **Intégration du SDK Google GenAI officiel** (`google.genai`, `from google.genai import types`).
- **Initialisation du client** avec gestion de timeout (`timeout=45000`) et stratégie de repli multi-modèles (`CANDIDATE_MODELS = ["gemini-3.5-flash-lite", "gemini-flash-latest"]`).
- **Instructions système dynamiques (`_build_system_prompt`)** :
  - **Persona** : "Big Sis Energy & Best Friend" — drôle, complice, énergique, bienveillante, zéro posture robotique corporate.
  - **Parité linguistique stricte** : Détection de la langue via `LLMBrain.detect_language`. Si l'utilisateur parle en Français, interdiction formelle d'insérer des mots en Darija/Arabe ; s'il parle en Darija marocaine (script arabe ou latin Arabizi), réponse exclusive en Darija marocaine authentique ; si anglais, anglais pur.
  - **Ancrage temporel réel** : Injection de la date et de l'heure locale réelles à chaque tour pour neutraliser les décalages de millésime sur le sport, les sorties tech et l'actualité.
  - **Interdiction des apartés théâtraux** : Règles strictes bannissant les phrases d'attente narratives entre parenthèses (`*(Silence radio... Je vais vérifier...)*`) avec filet de sauvetage automatique (`is_theatrical_placeholder`).

### 4.2 Thinking Levels & Budget de Réflexion
Le moteur gère 4 paliers de réflexion configurables par l'utilisateur :
| Niveau (`thinking_level`) | Budget Tokens (`thinking_budget`) | Température | Comportement & Directives |
|---|---|---|---|
| **`fast`** | 0 tokens | 0.3 | Vitesse maximale, réponses percutantes en 1 à 2 paragraphes, sans blabla. |
| **`standard`** | 2 048 tokens | 0.2 | Équilibre naturel, bienveillant, vérification factuelle standard. |
| **`deep`** | 8 192 tokens | 0.1 | Raisonnement logique approfondi, analyse méthodique étape par étape, pesée des pour/contre. |
| **`ultra`** | 16 384 tokens | 0.1 | Mode chercheur extrême, croisement rigoureux de sources multiples, diagnostic complet et synthèse argumentée. |

Les pensées internes générées par le modèle (`part.thought == True`) sont extraites des candidats et encapsulées dans le champ `thoughts` pour restitution visuelle dans l'interface (accordéon Liquid Glass).

### 4.3 Harnais de Surveillance Runtime (`AgentRuntimeHarness`)
Situé dans `src/core/agent_harness.py`, ce composant encapsule chaque outil de la boucle ReAct :
- Plafond maximal de 10 appels d'outils par tour.
- Plafond de 3 appels répétés consécutifs sur un même outil avec les mêmes arguments pour bloquer les boucles infinies.
- Enregistrement chronologique de chaque invocation (outil, paramètres, durée d'exécution, statut de succès, résumé de sortie).
- Synthèse automatique sous forme de carte interactive `tool_calls_section` (conforme au standard 21st.dev `heygaia/tool-calls-section`).

### 4.4 Catalogue d'APIs Publiques Autonomes (`src/tools/`)
- **`public_registry.py`** :
  - Index en mémoire inversé de 1 079 APIs publiques gratuites et sans authentification.
  - 49 catégories (Weather, Cryptocurrency, Currency Exchange, Animals, Entertainment, Geocoding, Science, etc.).
  - Aliasing multilingue (ex: "meteo", "taqs", "chta", "tiempo" pointent vers `weather_open_meteo` ; "flous", "crypto", "sarf" vers `crypto_coingecko` et `finance_exchangerate_api`).
  - Schématisation OpenAPI/Gemini (`to_gemini_schema()`).
- **`tool_calling_engine.py`** :
  - Client asynchrone singleton `httpx.AsyncClient` avec pool de 50 connexions et timeout strict de 5.0s.
  - Matrice de résilience traitant sans crash les codes HTTP 404, 429, 500, les coupures réseau et les retours HTML inattendus.
  - Tronquage sécurisé des charges utiles à 2 500 caractères pour ne pas saturer la fenêtre de contexte du LLM.
  - Génération de cartes cockpit HUD interactives (`public_api_data`).

---

## 5. Évaluation et Blueprint Architectural du Besoin R2 (Persistance des Conversations)

### 5.1 Analyse des Lacunes Actuelles
Le système actuel repose sur `src/services/session_manager.py` :
- `SessionManager._sessions` est un dictionnaire Python en mémoire vive.
- Aucune écriture sur disque n'est effectuée.
- En cas de redémarrage du processus FastAPI, **toutes les conversations sont irrémédiablement perdues**.
- Aucun identifiant de titre de conversation persistant n'est généré.
- Aucun mécanisme de filtrage temporel (Aujourd'hui, 7 derniers jours, 30 jours).
- Aucune fonctionnalité d'épinglage (`pin`), d'archivage, de renommage manuel, ou d'export Markdown/JSON.

### 5.2 Architecture de Persistance Cible (SQLite Hybride + Sync Client)
Pour concilier robustesse industrielle, zéro configuration externe (aucun serveur lourd requis) et compatibilité multiplateforme Windows/Linux/Docker, la solution recommandée est **un gestionnaire SQLite asynchrone avec journalisation WAL (Write-Ahead Logging)**, couplé à une synchronisation locale (IndexedDB / LocalStorage) côté frontend.

#### Schéma Relationnel Proposé (`data/conversations.db`)
```sql
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,               -- ex: "conv_a8f92b" ou session_id
    user_id TEXT NOT NULL,             -- ex: "mobile_user" ou "user_main"
    title TEXT NOT NULL,              -- Titre généré ou personnalisé
    created_at REAL NOT NULL,          -- Timestamp Unix (secondes)
    updated_at REAL NOT NULL,          -- Timestamp Unix dernier message
    is_pinned INTEGER DEFAULT 0,       -- 1 = épinglé en haut de liste
    is_archived INTEGER DEFAULT 0,     -- 1 = archivé (masqué par défaut)
    thinking_level TEXT DEFAULT 'standard',
    model TEXT DEFAULT 'gemini-3.5-flash-lite',
    tags_json TEXT DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_pinned ON conversations(user_id, is_pinned DESC, updated_at DESC);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL,                -- 'user' | 'assistant' | 'system'
    content TEXT NOT NULL,
    cards_json TEXT DEFAULT '[]',      -- Cartes interactives sérialisées
    thoughts TEXT DEFAULT NULL,        -- Pensées internes / chaîne de réflexion
    thinking_level TEXT DEFAULT 'standard',
    timestamp REAL NOT NULL,
    FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id, timestamp ASC);
```

### 5.3 Contrats d'Interface REST pour l'Agent 1 (Persistance)

#### 1. Lister les discussions (`GET /api/conversations`)
- **Query Params** : `user_id=mobile_user&include_archived=false&search=`
- **Réponse HTTP 200** :
  ```json
  {
    "conversations": [
      {
        "id": "conv_98213a",
        "title": "Comparatif PC Gamer Lenovo & RTX 4060",
        "is_pinned": true,
        "is_archived": false,
        "created_at": 1730662800.0,
        "updated_at": 1730663400.0,
        "time_bucket": "today",
        "turns_count": 6,
        "last_preview": "Le Lenovo LOQ 15 est disponible à 799,99 € sur Cdiscount..."
      }
    ],
    "buckets": {
      "today": 1,
      "last_7_days": 3,
      "last_30_days": 8,
      "older": 2
    }
  }
  ```
  *Calcul automatique du `time_bucket` en backend pour simplifier le rendu de la sidebar frontend :*
  - `today` : timestamp >= minuit aujourd'hui.
  - `last_7_days` : timestamp >= 7 jours et < minuit aujourd'hui.
  - `last_30_days` : timestamp >= 30 jours et < 7 jours.
  - `older` : timestamp < 30 jours.

#### 2. Récupérer l'historique complet (`GET /api/conversations/{conversation_id}`)
- **Réponse HTTP 200** :
  ```json
  {
    "id": "conv_98213a",
    "title": "Comparatif PC Gamer Lenovo & RTX 4060",
    "user_id": "mobile_user",
    "is_pinned": true,
    "is_archived": false,
    "created_at": 1730662800.0,
    "updated_at": 1730663400.0,
    "messages": [
      {
        "id": 1,
        "role": "user",
        "content": "Trouve-moi un PC portable gamer avec une bonne carte graphique sous 800€",
        "cards": [],
        "thoughts": null,
        "timestamp": 1730662800.0
      },
      {
        "id": 2,
        "role": "assistant",
        "content": "J'ai trouvé exactement ce qu'il te faut ! Le Lenovo LOQ 15 avec RTX 4060...",
        "cards": [
          {"type": "deal", "data": {"product": "PC Portable Gamer Lenovo LOQ...", "current_drop_price_eur": 799.99, "platform": "Cdiscount"}}
        ],
        "thoughts": "Analyse du budget (<800€) et de la puissance GPU requise...",
        "timestamp": 1730662805.0
      }
    ]
  }
  ```

#### 3. Mettre à jour les métadonnées (`PATCH /api/conversations/{conversation_id}`)
- **Corps de requête (`ConversationUpdateRequest`)** :
  ```json
  {
    "title": "Mon super PC Gamer",
    "is_pinned": true,
    "is_archived": false
  }
  ```
- **Réponse HTTP 200** : conversation mise à jour.

#### 4. Supprimer une conversation (`DELETE /api/conversations/{conversation_id}`)
- **Réponse HTTP 200** : `{"success": true, "deleted_id": "conv_98213a"}`.

#### 5. Génération automatique du titre (`POST /api/conversations/{conversation_id}/generate-title`)
- **Algorithme** :
  - Dès le 1er ou 2e échange, appel de l'endpoint ou déclenchement automatique en tâche de fond.
  - Prompt court ciblé : `"À partir du message utilisateur suivant : '{msg}', génère un titre ultra-concis de 3 à 5 mots maximum sans ponctuation ni guillemets."`
  - Fallback déterministe hors-ligne : extraction des 4 premiers mots substantifs après suppression des mots vides.

#### 6. Exportation (`GET /api/conversations/{conversation_id}/export?format=markdown|json`)
- **Format Markdown (`format=markdown`)** :
  - En-tête : `# {title}` + Métadonnées (Date, Modèle, Total tours).
  - Corps : Sections claires `## 👤 Utilisateur` et `## 🤖 HoL AI` avec formatage soigné des blocs de code, citations et cartes de données récapitulatives.
  - En-têtes HTTP de téléchargement : `Content-Disposition: attachment; filename="{slug}_{id}.md"`, `Content-Type: text/markdown; charset=utf-8`.
- **Format JSON (`format=json`)** :
  - Schéma standard d'export conforme JSON exportable et réimportable.

---

## 6. Évaluation et Benchmark du Besoin R3 (Fonctionnalités IA Autonomes)

### 6.1 Matrice Comparative avec les Chatbots Leaders
| Fonctionnalité Clé | ChatGPT (OpenAI) | Claude (Anthropic) | Perplexity AI | Google Gemini | HoL AI Actuel | HoL AI Cible (Production) |
|---|---|---|---|---|---|---|
| **Modes de Réflexion (Reasoning)** | o1 / o3-mini (Reasoning effort low/med/high) | Extended Thinking (visible thoughts collapsible) | Pro Search (Multi-step reasoning trace) | Thinking Budget (0 à 16k tokens) | 4 modes implémentés (`fast`, `standard`, `deep`, `ultra`) | **Complet** : Restitution UI en accordéon Liquid Glass + bascule rapide sur l'Input Dock. |
| **Grounding Web & Citations** | Web search intégré avec pastilles sources | Recherche web contextuelle | Citations numérotées `[1]`, badges domaines, aperçus | Google Search Grounding direct | `WebResearchAgent` (DDG / Brave) + Pre-grounding | **À enrichir** : Formatage des citations numérotées `[1]` et cartes de métadonnées de sources cliquables. |
| **Artefacts & Generative UI** | Canvas (édition de texte et code côte à côte) | Artifacts (HTML/JS/SVG/Mermaid live preview) | Pages & Collections | Canvas Workspace | `ArtifactsUIAgent` (fichiers `.html`, `.mmd`, `.md` dans `artifacts/`) | **À valoriser** : Volet rétractable Liquid Glass avec exécution temps réel et boutons Copier/Télécharger. |
| **Interpréteur de Code / Sandbox** | Python Code Interpreter (sandbox isolée) | Exécution de code dans les Artifacts | Exécution Python Pro Search | Code execution sandboxed | `execute_python_code` et `SecureVaultService` | **Complet** : Déjà opérationnel avec sortie standard stdout/stderr et audit Enclave. |
| **Choix de Personnalité / Ton** | Custom Instructions / GPTs | Projects & System Prompts | Focus Modes (Writing, Web, Math) | Gems / System Instructions | "Big Sis Energy & Best Friend" codé en dur | **À enrichir** : Sélecteur de Persona (Big Sis, Architecte Senior, Analyste Exécutif, Pédagogue). |
| **Bascule de Modèles** | Menu déroulant GPT-4o, o1, o3-mini | Menu Opus, Sonnet, Haiku | Bascule Claude / GPT / Sonar | 2.5 Pro, Flash, Flash-Lite | Liste de repli interne hardcodée | **À ajouter** : Paramètre `model` dans l'API et endpoint de découverte `/api/models`. |

### 6.2 Spécification des Extensions Requises pour R3

#### 1. Sélecteur Dynamique de Modèle (`GET /api/models` & paramètre dans `ChatMessageRequest`)
- Nouveau modèle de requête :
  ```python
  class ChatMessageRequest(BaseModel):
      message: str
      user_id: str = "mobile_user"
      session_id: Optional[str] = None
      history: Optional[List[Dict[str, Any]]] = None
      thinking_level: Optional[str] = "standard"  # fast | standard | deep | ultra
      model: Optional[str] = "gemini-3.5-flash-lite"
      persona: Optional[str] = "big_sis"          # big_sis | architect | executive | tutor
  ```
- Endpoint `/api/models` :
  ```json
  {
    "available_models": [
      {"id": "gemini-3.5-flash-lite", "name": "Gemini 3.5 Flash-Lite", "provider": "Google", "speed": "Ultra Rapide", "capabilities": ["tools", "thinking", "vision"]},
      {"id": "gemini-flash-latest", "name": "Gemini Flash Latest", "provider": "Google", "speed": "Rapide", "capabilities": ["tools", "thinking", "vision", "code"]},
      {"id": "gemini-pro-latest", "name": "Gemini Pro 2.5", "provider": "Google", "speed": "Raisonnement Élevé", "capabilities": ["deep_thinking", "complex_math"]}
    ],
    "default": "gemini-3.5-flash-lite"
  }
  ```

#### 2. Presets de Persona / Ton Réfléchi
- **`big_sis`** (défaut) : complice, drôle, énergique, protectrice, encourageante ("Big Sis Energy").
- **`architect`** : rigoureux, technique, orienté code/systèmes, pragmatique, concis.
- **`executive`** : orienté ROI, stratégique, synthétique avec points d'impact et ratios financiers.
- **`tutor`** : didactique, explicatif étape par étape, vulgarisation bienveillante.

#### 3. Standardisation des Citations Web Perplexity-Style
Pour les requêtes de recherche web, transformer les snippets bruts en une structure de citations enrichie :
```json
{
  "citations": [
    {
      "index": 1,
      "title": "GTA 6 : Date de sortie officielle et plateformes",
      "domain": "rockstargames.com",
      "url": "https://www.rockstargames.com/newswire/...",
      "favicon": "https://www.google.com/s2/favicons?domain=rockstargames.com",
      "snippet": "Rockstar Games confirme la sortie à l'automne 2025 sur PlayStation 5 et Xbox Series X|S."
    }
  ]
}
```
Dans le texte de réponse de l'IA, les mentions sont indexées via des pastilles cliquables `[1]`, `[2]` que le frontend restitue en badges Liquid Glass interactifs.

---

## 7. R5, R6, R7 : Analyse d'Impact et Synergies Backend

### 7.1 R5 — Automatisation Matinale & Live News (Morning Briefing)
- **Constat** : `src/services/jarvis_briefing.py` possède déjà l'appel API direct à `Open-Meteo` (`get_live_weather`), mais les e-mails, l'agenda et les tâches sont des bouchons simulés. De plus, il n'y a **aucune connexion aux flux d'actualités réelles du web** en direct.
- **Solution Backend** :
  - Connecter `JarvisBriefingService` au moteur `WebResearchAgent` pour requêter les dernières actualités majeures du matin (3 titres factuels chauds du jour).
  - Passer la synthèse vocale orale (`generate_spoken_script`) dans une passe LLM créative avec instruction d'angle variable (style dynamique, orientation business vs tech vs lifestyle), garantissant que deux exécutions consécutives ne présentent jamais la même structure textuelle.

### 7.2 R6 — Recherche Visuelle & Enrichissement Image
- **Constat** : `SocialMediaAgentService.generate_or_search_media` renvoie actuellement une URL Unsplash unique codée en dur.
- **Solution Backend** :
  - Détecter les entités visuelles fortes (monuments, lieux touristiques, modèles d'appareils, concepts artistiques) soit en amont via regex/entités, soit via un outil d'agent dédié `fetch_contextual_visual_card`.
  - Effectuer une recherche d'image réelle haute résolution via les APIs publiques disponibles ou un connecteur d'images sans clé (Wikimedia Commons / Openverse / Unsplash Source) et renvoyer une carte `visual_card` structurée avec titre, badge de provenance, dimensions et URL HD pour agrandissement dans une modal Liquid Glass.

### 7.3 R7 — Sourcing E-commerce & Décision Monochand
- **Constat** : `StealthProductScraper` et `ProductHunterService` comparent déjà plusieurs plateformes (Amazon, Cdiscount, Fnac, Leboncoin, Vinted).
- **Solution Backend** :
  - Implémenter la règle d'arbitrage stricte exigée par R7 : plutôt que d'afficher un patchwork multi-sites confus, le backend arbitre en coulisses, retient **un unique marchand de référence cohérent** pour la requête (ex: Amazon OU Cdiscount), et agrège plusieurs variantes et alternatives pertinentes issues de ce même marchand avec leurs spécificités distinctes (prix, finitions, stocks, livraison).

---

## 8. Analyse du Harnais de Tests et Découverte d'une Régression d'Indexation

### 8.1 Cartographie de la Suite de Tests Existante
Le dossier `services/core-engine/tests/` regroupe 28 fichiers de tests :
- `test_api_server.py` : Tests d'intégration des endpoints REST et WebSocket du serveur.
- `test_chat_stream.py` : Validation du streaming SSE, des événements de statut et du thinking_level.
- `test_cognitive_engine_tools.py` : Vérification unitaire de la présence et de l'exécutabilité des outils.
- `test_public_api_tool_calling.py` : Validation des 1 079 APIs, de l'index inversé et de la résilience HTTP.
- `test_chatbot_multiturn.py` : Résolution d'anaphores, dialogues multi-tours et contextes e-commerce.
- `test_antigravity_parity_agents.py` : Parité des agents de développement, shell, web et artefacts.
- `test_chaos_fuzzing.py`, `test_challenger1_stress.py`, `test_challenger2_stress.py` : Tests de charge et de robustesse.

### 8.2 Découverte Majeure : Fragilité d'Indexation des Cartes
Lors de l'exécution de `tests/test_chatbot_multiturn.py`, 3 tests ont échoué avec l'erreur `KeyError: 'product'` :
- `test_api_chat_multiturn_dialogue` (ligne 134)
- `test_macbook_neo_clarification_and_real_macbook_offer` (ligne 206)
- `test_api_chat_iphone_xr_e2e_no_iphone_15_hijack` (ligne 293)

#### Cause Racine
Dans `src/services/cognitive_engine.py` (l. 1279–1284) :
```python
# Injection prioritaire de la carte Tool Calls Section générée par le Harnais
harness_card = harness.build_tool_calls_card()
if harness_card:
    unique_cards.append(harness_card)
    seen_types.add("tool_calls_section")
    seen_types.add("tool_calls")
```
Lorsque le harnais d'agent est actif, il injecte une carte interactive de type `tool_calls_section` **en position 0** (`cards[0]`).
Les tests en échec effectuaient l'hypothèse erronée que la carte de produit (`deal`) se trouverait toujours à l'index 0 :
```python
# CODE FRAGILE DANS LE TEST :
deal = data["cards"][0]["data"]
assert "PlayStation 5" in deal["product"]  # Lève KeyError: 'product' car cards[0] est tool_calls_section !
```
À l'inverse, dans `tests/test_api_server.py` (l. 130), le testeur a correctement écrit :
```python
# CODE ROBUSTE :
deal_cards = [c for c in data["cards"] if c["type"] == "deal"]
assert len(deal_cards) == 1
assert "Cdiscount" in deal_cards[0]["data"]["platform"]
```
Ce test passe à 100%.

#### Règle de Robustesse pour les Développeurs
1. **Ne jamais supposer l'ordre d'indexation des cartes** dans les réponses de `/api/chat` ou `/api/chat/stream`. Les cartes retournées forment une collection hétérogène (`tool_calls_section`, `deal`, `second_hand_deals`, `web_research`, `interactive_clarification`, `public_api_data`).
2. Tout code client ou de test doit filtrer explicitement par type : `deal = next((c["data"] for c in cards if c.get("type") == "deal"), None)`.

---

## 9. Plan d'Implémentation & Recommandations pour les Agents Travailleurs

### 9.1 Phase 1 : Système de Persistance des Conversations (Agent 1 / R2)
1. **Créer `src/services/conversation_store.py`** :
   - Initialiser la base SQLite `data/conversations.db` avec tables `conversations` et `messages`.
   - Fournir les méthodes asynchrones : `create_conversation`, `get_conversation`, `list_conversations`, `update_conversation`, `delete_conversation`, `add_message`.
2. **Brancher la persistance dans `server.py` & `session_manager.py`** :
   - À chaque appel à `/api/chat` ou `/api/chat/stream`, enregistrer les messages utilisateur et assistant ainsi que les cartes associées dans la base SQLite.
   - Si `session_id` est nouveau, créer l'entrée de conversation correspondante.
3. **Exposer les 6 endpoints REST** :
   - `GET /api/conversations` (avec pagination, recherche et métadonnées temporelles `time_bucket`).
   - `GET /api/conversations/{id}` (restitution complète avec reprise de contexte immédiate).
   - `PATCH /api/conversations/{id}` (renommer, épingler, archiver).
   - `DELETE /api/conversations/{id}` (suppression avec cascade sur les messages).
   - `POST /api/conversations/{id}/generate-title` (génération de titre percutant).
   - `GET /api/conversations/{id}/export` (exports formats `.md` et `.json`).
4. **Écrire la suite de tests dédiée** `tests/test_conversation_persistence.py` validant chaque endpoint et la résistance aux redémarrages serveur.

### 9.2 Phase 2 : Enrichissement des Fonctionnalités IA (Agent 2 / R3)
1. **Ajouter `GET /api/models` et le paramètre `model`** dans `ChatMessageRequest`.
2. **Intégrer le sélecteur de Persona (`persona`)** dans `CognitiveAgentEngine._build_system_prompt`.
3. **Améliorer la mise en forme des citations de recherche web** (`[1]`, `[2]` avec métadonnées enrichies de sources).
4. **Connecter l'affichage des artefacts** générés par `ArtifactsUIAgent` avec un volet rétractable dédié dans l'UI.
5. **Écrire `tests/test_autonomous_ai_features.py`** pour vérifier la bascule de modèles, le formatage des citations et les personas.

---

## 10. Conclusion de l'Enquête Backend

Le backend de HoL AI dispose d'un socle technique exceptionnellement riche et fonctionnel : le streaming SSE, l'intégration du SDK Gemini avec Thinking Budget, le catalogue de 1 079 outils d'APIs publiques et le cluster multi-agents sont parfaitement opérationnels et validés par tests unitaires et d'intégration.

Le travail à réaliser est clairement délimité et sans ambiguïté :
- **Combler le vide de persistance (R2)** en remplaçant la mémoire volatile par un stockage SQLite structuré avec les 6 endpoints de gestion d'historique.
- **Finaliser les critères d'excellence IA (R3)** en formalisant le choix de modèles, de personas, de citations Perplexity-style et d'artefacts interactifs.
- **Conserver la stricte rétrocompatibilité** avec les endpoints existants pour ne casser aucun des 48 tests déjà validés.
