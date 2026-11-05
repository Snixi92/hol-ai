# Dispatch for Milestone 2 & 3 Worker: Autonomous Tool-Calling Engine & Chat Integration

You are the Implementation Worker for Milestone 2 & 3 (teamwork_worker).
Your working directory is: C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\.agents\teamwork\m2_m3_worker
Workspace directory: C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai
Original request file: C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\.agents\teamwork\ORIGINAL_REQUEST.md
Project plan: C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\PROJECT.md
E2E Test Infra: C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\TEST_INFRA.md
E2E Test Suite: C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\tests\test_public_api_tool_calling.py
M1 Handoff: C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\.agents\teamwork\m1_worker\handoff.md
Orchestrator conversation ID: bf81d29e-5f76-455c-ba30-996e91487317

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## File Ownership
You exclusively own and may create/edit these files:
- `services/core-engine/src/tools/tool_calling_engine.py` (create)
- `services/core-engine/src/tools/__init__.py` (update exports)
- `services/core-engine/src/api/server.py` (add public tools REST routes and chat card integration)
- `services/core-engine/src/services/cognitive_engine.py` (register native tool and pre-query grounding)

## Detailed Requirements

### 1. Autonomous Tool-Calling Engine (`src/tools/tool_calling_engine.py`)
- Implement `AutonomousToolCallingEngine` singleton class with `get_instance()`.
- Use `httpx.AsyncClient` with connection pooling (`limits=httpx.Limits(max_connections=50, max_keepalive_connections=10)`), follow redirects, and a strict 5.0-second timeout policy (`httpx.Timeout(connect=2.0, read=4.0, write=2.0, pool=2.0)`).
- **Tool Selection**:
  - `select_candidate_tools(user_message: str, top_k: int = 3) -> List[ToolDefinition]`: Extracts intent and uses `PublicApiRegistry.get_instance().search_tools` to find candidate tools.
- **Tool Execution & Resilience Matrix**:
  - `async execute_tool(tool_id: str, query_params: Optional[Dict[str, Any]] = None, path_suffix: str = "") -> ToolExecutionResult`:
    - Looks up tool in registry. If not found, returns `ToolExecutionResult(success=False, error_code="TOOL_NOT_FOUND", ...)`.
    - Resolves endpoint URL (curated endpoint or raw URL).
    - Executes async HTTP GET with error boundaries catching `httpx.HTTPStatusError`, `httpx.TimeoutException`, `httpx.ConnectError`, `ssl.SSLError`, `json.JSONDecodeError`, and non-JSON HTML (Cloudflare error pages).
    - Maps status codes to clean error codes: 404 -> `HTTP_404_NOT_FOUND`, 429 -> `RATE_LIMITED`, 500/502/503 -> `UPSTREAM_ERROR`, timeout -> `TIMEOUT`.
    - Truncates oversized payloads: arrays capped to top 5 items, formatted summary text capped to 2,500 characters.
    - Generates interactive cockpit HUD card: `{"type": "public_api_data", "data": {"tool_id": tool.id, "title": tool.name, "category": tool.category, "payload": data, "summary": summary}}`.
- **Pre-LLM Dynamic Grounding**:
  - `async match_and_fetch_live_data(user_message: str) -> Optional[Dict[str, Any]]`:
    - Checks if the user message asks for real-time public data (e.g. weather, crypto, currencies, facts, jokes, geocoding).
    - If a candidate tool matches with high confidence, executes it pre-flight (<2s), formats context string `[DONNÉES EN DIRECT DE L'API PUBLIQUE <Nom>] : <Données>`, and returns the payload + card.

### 2. FastAPI REST Endpoints (`src/api/server.py`)
Add routes:
- `GET /api/tools/public-apis`: query params `query: Optional[str]`, `category: Optional[str]`, `limit: int = 50`, `offset: int = 0`. Returns list of tools and total count.
- `GET /api/tools/public-apis/categories`: returns list of all 49 categories with tool counts.
- `GET /api/tools/public-apis/stats`: returns registry & execution statistics (`total_tools`, `categories_count`, `curated_count`, etc.).
- `POST /api/tools/public-apis/execute`: body `{ "tool_id": str, "query_params": Optional[dict], "path_suffix": Optional[str] }`. Returns `ToolExecutionResult` JSON.

### 3. Chat Integration & Live Data Injection
- In `src/services/cognitive_engine.py`:
  - Register `fetch_public_api_data(tool_id: str, query_params: Optional[dict] = None) -> str` in `tools_list` in `CognitiveAgentEngine.process_chat()`.
  - In tool execution, call `AutonomousToolCallingEngine.get_instance().execute_tool(...)`, append the generated card to `collected_cards`, and return the formatted summary.
  - In pre-query grounding hook (around lines 973-1020), call `match_and_fetch_live_data(user_message)` and prepend context to `effective_user_message`.
- In `src/api/server.py` (`/api/chat` and `/api/chat/stream`):
  - Ensure cards from `public_api_data` are included in the response `cards` list and sent via SSE.
  - Zero-crash guarantee: even if an external API is down, the chat handles it gracefully with HTTP 200.

### 4. Verification
Run the complete E2E test suite:
`pytest tests/test_public_api_tool_calling.py -v`
Verify that **all 25 tests pass (100%)** across Tiers 1, 2, 3, and 4!
Also verify existing tests:
`pytest tests/test_cognitive_engine_tools.py tests/test_api_server.py -v`

Write your handoff report in `C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\.agents\teamwork\m2_m3_worker\handoff.md`.
Send a completion message back to orchestrator `bf81d29e-5f76-455c-ba30-996e91487317`.


## 2026-10-31T21:06:08Z
[Message from orchestrator bf81d29e-5f76-455c-ba30-996e91487317]
**Context**: Milestone 2 & 3 Implementation (AutonomousToolCallingEngine & Chat Integration)
**Content**: Status check. 10 minutes have elapsed since dispatch. Please update on current implementation progress, files written, and test runs.
**Action**: Reply with your current progress update and refresh your progress.md timestamp.
