# Survey Report — FastAPI Core Engine Architecture & Tool-Calling Insertion Points

**Author**: Survey Agent 2 (`teamwork_explorer`)  
**Target**: Orchestrator (`bf81d29e-5f76-455c-ba30-996e91487317`) & Implementer Agents  
**Date**: 2026-10-31T20:45:00Z  
**Target File**: `services/core-engine`  

---

## 1. Observation

### 1.1 Architecture of `services/core-engine`

#### Entry Point
- **File**: `services/core-engine/main.py` (36 lines)
  - Sets Windows stdout to UTF-8 (`sys.stdout.reconfigure(encoding="utf-8")`, lines 8-9).
  - Injects `BASE_DIR` into `sys.path` (lines 12-14).
  - Starts Uvicorn server:
    ```python
    uvicorn.run(
        "src.api.server:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )
    ```

#### Application Setup & Lifespan
- **File**: `services/core-engine/src/api/server.py` (1721 lines)
  - Uses FastAPI with an `asynccontextmanager` `lifespan(app: FastAPI)` (lines 72-122).
  - Initializes Redis Streams via `fakeredis.aioredis.FakeRedis(decode_responses=True)` and `StreamBus` (lines 79-81).
  - Initializes 6 core agents (lines 84-98):
    1. `CanvasAgent` (`AgentID.AGENT_1_CANVAS`)
    2. `IngestionMemoryAgent` (`AgentID.AGENT_2_INGESTION`)
    3. `LogisticsAgent` (`AgentID.AGENT_3_LOGISTICS`)
    4. `FinanceAgent` (`AgentID.AGENT_4_FINANCE`)
    5. `ContentSocialAgent` (`AgentID.AGENT_5_CONTENT`)
    6. `ExecutionAgent` (`AgentID.AGENT_6_EXECUTION`)
  - Starts `AgentManager` supervisor (lines 101-104) and `background_watcher.guardian` (lines 108-109).
  - Configures CORS middleware with `allow_origins=["*"]` (lines 126-132).

#### Router Configuration & Existing Endpoints
There are **45 routes** registered directly on the `app` instance in `server.py`:
- **Chat Endpoints**:
  - `POST /api/chat/stream` (line 244) -> `chat_stream_endpoint` (Real-time SSE streaming)
  - `POST /api/chat` (line 411) -> `chat_endpoint` (Standard JSON request/response)
- **Settings & Config**:
  - `POST /api/settings/api-key` (line 594) -> `set_api_key_endpoint`
  - `GET /api/settings/api-key` (line 601) -> `get_api_key_status_endpoint`
- **Actions & Agents**:
  - `POST /api/actions/execute` (line 622) -> `execute_action_endpoint`
  - `POST /api/orchestrate` (line 908) -> `orchestrate_intent`
  - `GET /api/state` (line 874) -> `get_system_state`
  - `GET /api/agents/status` (line 887) -> `get_agents_status`
- **Specialized Services**:
  - `POST /api/sourcing/compare` (line 761)
  - `POST /api/logistics/track` (line 782)
  - `POST /api/cfo/margin` (line 812), `GET /api/cfo/affiliate-reconciliation` (line 827), `POST /api/cfo/receipt` (line 856)
  - `GET /api/jarvis/briefing` (line 680)
  - `GET /api/vault/ledger` (line 687), `POST /api/vault/sandbox` (line 703)
  - `GET /api/telegram/status` (line 710), `POST /api/telegram/settings` (line 721)
  - `GET /api/whatsapp/webhook` (line 1416), `POST /api/whatsapp/webhook` (line 1424)
  - `GET /api/memory/facts` (line 1441), `POST /api/memory/facts` (line 1451), `DELETE /api/memory/facts/{category}/{key}` (line 1465)
  - `POST /api/voice/synthesize` (line 1485), `POST /api/voice/transcribe` (line 1496), `GET /api/voice/capabilities` (line 1511), `POST /api/voice/hands-free` (line 1518)
  - `POST /api/notifications/dispatch` (line 1533), `GET /api/notifications/history` (line 1546)
  - `GET /api/desktop/windows` (line 1559), `POST /api/desktop/focus` (line 1567), `POST /api/desktop/launch` (line 1574), `POST /api/desktop/close` (line 1581), `POST /api/desktop/keys` (line 1588), `GET /api/desktop/telemetry` (line 1595)
  - `POST /api/vision/camera-scan` (line 1609)
  - `POST /api/canvas/upload` (line 1082)
- **WebSockets**:
  - `WS /ws/canvas` (line 1238) -> Canvas spatial updates
  - `WS /ws/browser-stream` (line 1348) -> Live browser/Computer-Use streaming
- **Static & Web UI**:
  - `GET /` (line 1639) -> Serves Canvas cockpit
  - `GET /manifest.json`, `GET /icon.svg`, `GET /sw.js`, `GET /qr_phone.png`, `GET /api/pwa/manifest`

---

### 1.2 Current Chat Flow and LLM Service

#### Request & Response Models
- **Request Model**: `ChatMessageRequest` in `server.py` (lines 162-175):
  ```python
  class ChatMessageRequest(BaseModel):
      message: str = Field(..., min_length=1, max_length=20000)
      user_id: str = Field(default="mobile_user", max_length=100)
      session_id: Optional[str] = Field(default=None, max_length=100)
      history: Optional[List[Dict[str, Any]]] = Field(default=None)
      thinking_level: Optional[str] = Field(default="standard", max_length=50)
  ```
- **Session Management**: `SessionManager.get_or_create(session_id, user_id)` (`src.services.session_manager`) tracks user/assistant turns and card payloads.
- **Anaphora Resolution**: `SessionManager.resolve_anaphora_and_context(session, req.message)` resolves elliptical queries (e.g. "et sur cdiscount ?").

#### Dual Execution Path in Chat Endpoints
Both `/api/chat` (lines 410-580) and `/api/chat/stream` (lines 244-408) implement the exact same 2-stage execution strategy:

1. **Primary Stage: Autonomous Cognitive ReAct Engine** (`CognitiveAgentEngine.process_chat`)
   - Checked via `CognitiveAgentEngine.is_available()` (verifies API key presence).
   - If available, calls:
     ```python
     cog_res = await CognitiveAgentEngine.process_chat(
         user_message=effective_message,
         session_id=session.session_id,
         context_history=session.get_formatted_history(max_turns=10),
         status_callback=sync_status_emitter, # in stream endpoint
         thinking_level=thinking_level
     )
     ```
   - If successful, returns:
     ```json
     {
         "reply": cleaned_reply,
         "cards": final_cards,
         "thoughts": cog_res.get("thoughts"),
         "thinking_level": thinking_level,
         "correlation_id": "...",
         "duration_ms": 320,
         "llm_connected": true,
         "session_id": session.session_id,
         "engine": "autonomous_cognitive_agent"
     }
     ```
2. **Fallback Stage: Resilient Multi-Agent Orchestrator**
   - Triggered if no API key is set or if `CognitiveAgentEngine` raises an unhandled exception.
   - Calls `await manager.orchestrate(effective_message, context=context)` across Redis Streams.
   - Synthesizes response via `LLMBrain.generate_conversational_response(...)` or `result.synthesized_summary`.
   - Returns response with `"engine": "resilient_orchestrator"`.

#### LLM Provider, Client & Models
- **Provider**: Google Gemini via official modern SDK `google-genai` (version `2.33.0`).
- **SDK Import**: `from google import genai; from google.genai import types` (in `cognitive_engine.py` line 1023 and `llm_engine.py` line 356).
- **Client Instantiation**:
  ```python
  client = genai.Client(
      api_key=api_key,
      http_options=types.HttpOptions(
          timeout=45000,
          retry_options=types.HttpRetryOptions(attempts=1)
      )
  )
  ```
- **Candidate Models** (with automatic fallback on failure, lines 1072-1076):
  1. `gemini-3.5-flash-lite`
  2. `gemini-flash-lite-latest`
  3. `gemini-flash-latest`
- **Thinking Configuration**:
  Supports 4 levels (`fast`: 0 tokens, `standard`: 2048 tokens, `deep`: 8192 tokens, `ultra`: 16384 tokens) via `types.ThinkingConfig(thinking_budget=budget, include_thoughts=True)`.
- **Chat Call**:
  ```python
  gen_cfg = types.GenerateContentConfig(
      system_instruction=system_prompt,
      temperature=temp,
      tools=tools_list
  )
  chat = client.chats.create(model=model_name, history=genai_history, config=gen_cfg)
  response = await asyncio.wait_for(
      asyncio.to_thread(chat.send_message, effective_user_message),
      timeout=90.0
  )
  ```

---

### 1.3 Existing Tools & Agents Architecture

1. **Native Gemini Tool Calling in `CognitiveAgentEngine`**:
   - `tools_list` in `cognitive_engine.py` (lines 917-968) currently contains **47 statically declared Python functions**.
   - These functions cover:
     - E-commerce / scrapers (`hunt_product_deals`, `scrape_live_store_offer`)
     - System automation (`launch_application`, `close_application`, `control_desktop_window`)
     - Web research (`search_internet_live`, `search_web_research`, `read_webpage_content`)
     - Antigravity dev agents (`read_code_file`, `write_code_file`, `edit_code_file`, `execute_terminal_command`, `delegate_to_subagent`, `create_visual_artifact`, `diagnose_system_error`, `create_architectural_plan`)
     - Meta Muse parity (`audit_subscriptions`, `scan_meal_nutrition`, `manage_user_goals`, `send_whatsapp_message`, `synthesize_dynamic_tool`, `set_avatar_mood_and_speech`, `generate_virtual_card`, `launch_visual_computer_use`)
     - Next-gen agents (`record_biographical_fact`, `get_biographical_memory`, `synthesize_speech_voice`, `send_desktop_notification`, `scan_camera_multimodal`)
   - Inside each function, interactive UI cards are appended to `collected_cards: List[Dict[str, Any]]` (e.g. `collected_cards.append({"type": "...", "data": ...})`).
2. **Proactive Pre-Query Grounding Hook**:
   - Lines 973-1020 of `cognitive_engine.py`: Before calling Gemini, if the user query mentions factual/date/news keywords, `WebResearchAgent.search_web` runs synchronously and prefixes the prompt with `[INFORMATIONS FRAÎCHES DU WEB EN DIRECT DU ...]`.
3. **Dynamic Tool Synthesizer**:
   - `src/agents/meta_muse_parity/dynamic_tool_synthesizer_agent.py` can parse Python code with `ast.parse`, write to `src/tools/dynamic/{clean_name}.py`, and import via `importlib.util.spec_from_file_location`.
4. **Interactive Cards System**:
   - More than 20 card types are supported in the frontend and `server.py` (`deal`, `second_hand_deals`, `web_research`, `terminal_exec`, `finance`, `app_launcher`, `chart`, etc.).

---

### 1.4 Dependencies & Libraries Present

From `services/core-engine/requirements.txt`:
```
fastapi>=0.111.0
uvicorn[standard]>=0.30.0
pydantic>=2.7.0
pydantic-settings>=2.2.0
redis>=5.0.0
fakeredis>=2.23.0
pytest>=8.2.0
pytest-asyncio>=0.23.0
python-dotenv>=1.0.0
colorama>=0.4.6
```

From live environment inspection (`python -c ...`):
| Package | Version | Status | Notes |
|---|---|---|---|
| **Python** | 3.10.7 | Installed | Windows console UTF-8 reconfigured |
| **FastAPI** | 0.162.0 | Installed | Compatible with standard Pydantic v2 routes |
| **Pydantic** | 2.14.1 | Installed | V2 with `BaseModel`, `Field`, `field_validator` |
| **httpx** | 0.28.1 | Installed | High-performance async HTTP client ready for API calls |
| **requests** | 2.34.2 | Installed | Synchronous HTTP client available |
| **google-genai** | 2.33.0 | Installed | Official current Google GenAI SDK |
| **ddgs** / **duckduckgo_search** | Installed | Active | Fallback web search |
| **sqlite3** | Built-in | Active | Available for SQLite FTS5 / metadata indexing |

---

## 2. Logic Chain

1. **Catalog Scale vs LLM Tool Context Limit**:
   - The user requested integration of **1,079 public no-auth APIs** (`HOL_AI_PUBLIC_APIS_CATALOG.md` and `parsed_apis.json`).
   - Observations show that Gemini `tools_list` in `cognitive_engine.py` currently holds 47 functions.
   - Passing 1,079 function declarations directly in `types.GenerateContentConfig(tools=tools_list)` would blow up the prompt context, induce massive latency, and likely fail or exceed Gemini tool declaration limits.
   - **Deduction**: We must implement a **Two-Tier Tool Registry & Dynamic Retrieval Architecture**:
     - *Tier 1 (Indexing & Semantic/Keyword Search)*: An in-memory/SQLite registry (`PublicApiRegistry`) indexes all 1,079 APIs by category, name, description, tags, and endpoints.
     - *Tier 2 (Autonomous Execution & Injection)*: Either via a Universal Tool-Calling Meta-Tool (`query_public_api`) exposed to Gemini, or via dynamic candidate tool injection (routing top 2-5 candidate tools into `tools_list`), or via deterministic query interception with live API data context injection.

2. **Insertion Point Analysis**:
   - **Insertion Point A (Inside `CognitiveAgentEngine.process_chat`)**:
     - *Where*: Lines 917-968 of `cognitive_engine.py` (Tool definition) and lines 176-231 (System Prompt).
     - *What to insert*:
       1. Register a native tool in `tools_list`:
          `query_public_api(api_name: str, endpoint: str, params: Optional[dict] = None, search_query: Optional[str] = None) -> str`
          or `fetch_live_api_data(category: str, query: str) -> str`.
       2. In the System Prompt (lines 176-221), add rule:
          "Si l'utilisateur demande des informations factuelles ou données en direct (cours de devises, météo, cryptos, dictionnaires, statistiques, données spatiales, faits publics) : appelle `fetch_live_api_data` pour interroger les 1 079 APIs publiques de HoL AI."
       3. In the tool execution:
          Invoke `ToolCallingEngine.execute_api(...)` using `httpx.AsyncClient`, capture the JSON response, format the output, emit an interactive card `collected_cards.append({"type": "public_api_data", "data": ...})`, and return the data to Gemini.
   - **Insertion Point B (Pre-LLM Autonomous Grounding / Interceptor)**:
     - *Where*: Lines 973-1020 of `cognitive_engine.py`.
     - *What to insert*:
       Right before invoking Gemini, if the user query requests real-time data matching an indexed public API (e.g., "donne-moi le cours du bitcoin en direct", "quel temps fait-il à Tokyo", "trouve-moi une citation aléatoire", "cours de l'or"), the `ToolCallingEngine` matches the API, performs a fast pre-flight request (<2s), appends the card to `collected_cards`, and injects `[DONNÉES EN DIRECT DE L'API PUBLIQUE <Nom>] : <Données>` directly into `effective_user_message`.
   - **Insertion Point C (Resilient Orchestrator Fallback)**:
     - *Where*: Lines 310-366 in `chat_stream_endpoint` and lines 469-575 in `chat_endpoint`.
     - *What to insert*:
       If Gemini is unreachable or no API key is set, the fallback orchestrator checks `ToolCallingEngine.match_and_execute(effective_message)` and appends the resulting card to `interactive_cards` so the chat NEVER fails to supply live data even offline.
   - **Insertion Point D (REST Management Endpoints in `server.py`)**:
     - *Where*: After line 601 in `src/api/server.py`.
     - *What to insert*:
       - `GET /api/tools/public-apis` -> List/filter the 1,079 APIs by category/keyword.
       - `POST /api/tools/public-apis/execute` -> Manually or programmatically execute any public API tool.
       - `GET /api/tools/public-apis/stats` -> Health, category counts, execution latency.

3. **HTTP Client & Resilience**:
   - `httpx` (v0.28.1) is installed and should be used with an `httpx.AsyncClient` singleton configured with a strict timeout (e.g. 5.0 seconds), user-agent header, and SSL verification bypass options for tricky public endpoints.
   - Safe error handling: If an API returns HTTP 4xx/5xx or times out, the engine catches the exception gracefully, logs a warning, and returns a graceful message without breaking the chat stream.

---

## 3. Caveats

1. **No External Network in Certain Testing Environments**:
   Some third-party public APIs may be temporarily unreachable or blocked by firewalls/DNS. The engine must mock or handle HTTP timeouts gracefully.
2. **Schema Uniformity of 1,079 APIs**:
   The 1,079 catalog in `HOL_AI_PUBLIC_APIS_CATALOG.md` / `parsed_apis.json` contains names, descriptions, categories, and root URLs. Some APIs have parameterized query strings, while others have REST paths. The engine must support flexible parameter mapping (query params, path params, or generic HTTP GET).
3. **Existing Test Suite Stability**:
   Existing tests (`test_chat_stream.py`, `test_cognitive_engine_tools.py`, `test_api_server.py`) must remain 100% green without regressions.

---

## 4. Conclusion

1. The FastAPI backend in `services/core-engine` has a robust architecture with 45 endpoints, a central `lifespan`, and a dual chat pipeline (`/api/chat` and `/api/chat/stream`).
2. The current LLM client is `google-genai` (v2.33.0) communicating with `gemini-3.5-flash-lite` using native tool calling and thinking levels.
3. The optimal design for the Autonomous Tool-Calling Engine is a **Two-Tier Engine**:
   - `src/services/tool_registry.py`: Loads and indexes the 1,079 public APIs from `parsed_apis.json` / catalog, provides category/keyword/BM25-style search.
   - `src/services/tool_calling_engine.py`: Intercepts user requests, selects the matching API, executes HTTP GET via `httpx.AsyncClient`, handles errors/circuit breaking, emits `public_api_data` UI cards, and injects fresh data into the LLM context.
   - Exposure via `fetch_public_api_data` native tool in `CognitiveAgentEngine.process_chat` AND REST endpoints (`/api/tools/public-apis/...`) in `server.py`.
4. Dependencies (`fastapi`, `pydantic`, `httpx`, `requests`, `google-genai`, `pytest`) are fully installed and verified.

---

## 5. Verification Method

To verify these architectural findings independently:

1. **Inspect Server Endpoints & Lifespan**:
   ```powershell
   python -c "from src.api.server import app; print('Total routes:', len(app.routes))"
   ```
2. **Verify Installed Packages & Versions**:
   ```powershell
   python -c "import fastapi, pydantic, httpx, google.genai; print('FastAPI:', fastapi.__version__, 'Pydantic:', pydantic.__version__, 'httpx:', httpx.__version__, 'GenAI:', getattr(google.genai, '__version__', 'OK'))"
   ```
3. **Run Existing Chat Tests**:
   ```powershell
   cd 'C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine'
   pytest tests/test_chat_stream.py -v
   pytest tests/test_cognitive_engine_tools.py -v
   ```
4. **Invalidation Conditions**:
   - If `CognitiveAgentEngine` no longer uses `google.genai` or switches to another provider.
   - If `/api/chat` and `/api/chat/stream` change their `ChatMessageRequest` model.
