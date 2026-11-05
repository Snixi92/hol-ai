# Test Infrastructure & Verification Plan
# HoL AI: 1,079 Public APIs Catalog & Autonomous Tool-Calling Engine

## 1. Test Philosophy & Principles

### 1.1 Opaque-Box & Requirement-Driven
The test suite treats the Autonomous Tool-Calling Engine and Public API Registry as black-box/opaque-box components governed strictly by interface contracts and requirements defined in `ORIGINAL_REQUEST.md` and `PROJECT.md`. Tests validate behavioral outcomes, response schemas, error codes, and resilience policies rather than implementation internals.

### 1.2 Deterministic & Offline Stability
Public APIs are externally hosted, subject to network jitter, rate limiting, and downtime. Running tests against live external servers causes non-deterministic CI failures (as observed in initial surveys with Gemini 429 quota exhaustion).
Therefore, **all HTTP communication with external public APIs is mediated through `httpx.MockTransport`**. 
- Zero network requests are made to live external servers during test runs.
- Mocks simulate exact HTTP headers, status codes, JSON structures, delay conditions, and network anomalies.
- Test runs execute in < 5 seconds with 100% reproducibility.

### 1.3 Zero-Crash & Graceful Degradation
HoL AI operates an interactive chat interface (`/api/chat` and `/api/chat/stream`). The primary safety requirement is that **no external API failure (404, 429, 500, timeout, SSL error, malformed HTML) can crash the chat or trigger an unhandled HTTP 500**. Every edge case must degrade gracefully to a structured fallback message and allow the conversation to proceed smoothly.

---

## 2. Feature Inventory Mapping

| Feature # | Feature Name | Description | Test Class in `test_public_api_tool_calling.py` | Specific Test Methods |
|---|---|---|---|---|
| **F1** | No-Auth API Dataset Storage | Storage and loading of 1,079 verified no-auth APIs | `TestTier1RegistryAndCatalog` | `test_f1_dataset_loading_and_count` |
| **F2** | Tool Data Models | Pydantic validation of ToolDefinition, ToolParameter | `TestTier1RegistryAndCatalog` | `test_f2_tool_data_models_validation` |
| **F3** | Inverted Keyword Index | Fast token & category indexing across all 1,079 APIs | `TestTier1RegistryAndCatalog` | `test_f3_inverted_keyword_search` |
| **F4** | Multilingual Aliases | Query resolution in French, Darija, Spanish, English | `TestTier1RegistryAndCatalog` | `test_f4_multilingual_category_aliasing` |
| **F5** | Curated High-Value Tools | Pre-configured executable REST schemas (Weather, Crypto, etc.) | `TestTier1RegistryAndCatalog` | `test_f5_curated_high_value_tools_retrieval` |
| **F6** | Top-K Candidate Tool Selection | Query-to-tool matching returning top 3-5 tools | `TestTier3CrossFeatureExecution` | `test_f6_top_k_tool_selection_matching` |
| **F7** | Async HTTP Tool Executor | Non-blocking `httpx.AsyncClient` executor | `TestTier3CrossFeatureExecution` | `test_f7_async_http_tool_executor_success` |
| **F8** | Strict Timeouts & Circuit Breaking | 5s timeout enforcement and circuit-breaking | `TestTier2BoundaryAndResilience` | `test_f8_f9_http_timeout_circuit_breaking` |
| **F9** | Zero-Crash Error Handling Matrix | Fallback on 404, 429, 500, SSL, timeouts, non-JSON HTML | `TestTier2BoundaryAndResilience` | `test_f9_http_404_handling`<br>`test_f9_http_429_rate_limiting`<br>`test_f9_http_500_upstream_error`<br>`test_f9_non_json_html_response` |
| **F10** | Payload Truncation & Sanitization | Limit responses to 2,500 chars and top 5 items | `TestTier3CrossFeatureExecution` | `test_f10_payload_truncation_and_sanitization` |
| **F11** | REST Tool Inspection Endpoints | Endpoints `/api/tools/public-apis/...` in FastAPI server | `TestTier4ChatIntegration` | `test_f11_rest_api_tool_inspection_endpoints` |
| **F12** | Native Gemini Tool Declaration | Registration of `fetch_public_api_data` tool | `TestTier4ChatIntegration` | `test_f12_native_gemini_tool_declaration` |
| **F13** | Pre-LLM Dynamic Grounding | Query interception and live API data injection pre-flight | `TestTier4ChatIntegration` | `test_f13_pre_llm_dynamic_grounding_weather` |
| **F14** | Interactive Cockpit Card Generation | Emission of `public_api_data` UI cards | `TestTier3CrossFeatureExecution` | `test_f14_interactive_cockpit_card_generation` |
| **F15** | Chat Endpoint Data Injection | Dual-channel injection into `/api/chat` and `/api/chat/stream` | `TestTier4ChatIntegration` | `test_f15_chat_endpoint_json_injection`<br>`test_f15_chat_stream_sse_injection` |
| **F16** | E2E Integration Test Suite | Full multi-tier test suite execution | All Tiers | All 25+ test cases |

---

## 3. Tiered Coverage Plan

```
┌────────────────────────────────────────────────────────────────────────┐
│                   TIER 4: Real-World Chat Integration                 │
│  FastAPI /api/chat, /api/chat/stream, SSE events, UI Cards, Fallbacks │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│              TIER 3: Cross-Feature Execution Pipeline                  │
│  Selection + Async HTTP Execution + Payload Truncation + Card Gen     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│              TIER 2: Boundary, Resilience & Zero-Crash                 │
│  404, 429, 500, Timeouts, SSL, HTML Error Pages, Empty/Special Chars  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│              TIER 1: Public API Registry & Indexing                     │
│  1,079 Dataset, Inverted Index, Multilingual Aliases, Curated Schemas │
└────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Tier 1: Registry & Catalog Indexing
Validates the data layer and search engine powering the 1,079 tools:
1. **Dataset Integrity**: Confirms loading of exactly 1,079 no-auth APIs from `parsed_apis.json`. Verifies that no API requires an API key or OAuth.
2. **Schema & Model Validation**: Pydantic models `ToolDefinition`, `ToolParameter`, `ToolExecutionResult` enforce type safety and defaults.
3. **Inverted Index Performance**: Verifies sub-millisecond retrieval by keyword across name, category, and description.
4. **Multilingual Aliasing**:
   - French: `"météo"`, `"cours"`, `"blague"`, `"nourriture"` -> maps to `Weather`, `Finance/Crypto`, `Jokes`, `Food`.
   - Darija: `"flous"`, `"chhal"`, `"sarf"` -> maps to `Finance`, `Currency Exchange`.
   - Spanish: `"tiempo"`, `"precio"`, `"noticias"` -> maps to `Weather`, `Finance`, `News`.
5. **Curated Tool Schemas**: Ensures high-utility tools (Open-Meteo, CoinGecko, ExchangeRate, CatFacts, JokeAPI) feature valid REST endpoints and parameters.
6. **Registry Metadata**: Inspects `get_categories()` and `get_stats()`.

### 3.2 Tier 2: Boundary & Corner Cases (Resilience Matrix)
Validates zero-crash resilience against hostile or malformed inputs:
1. **Empty / Blank Queries**: Empty string, pure whitespace, or query exceeding 2,000 chars. Must return empty candidate list without throwing.
2. **Special Characters & Encoding**: Emojis, accents (`PokéAPI`, `Grönstrom`), null bytes, quotes, HTML tags (`<script>`), SQL syntax. Must sanitize and return cleanly.
3. **Unknown Tool ID**: Requesting execution of non-existent ID returns `ToolExecutionResult(success=False, error_code="TOOL_NOT_FOUND")`.
4. **HTTP 404 (Resource Missing)**: Upstream returns 404 -> handled cleanly, `error_code="UPSTREAM_NOT_FOUND"`.
5. **HTTP 429 (Rate Limit)**: Upstream throttles -> handled cleanly, `error_code="RATE_LIMITED"`.
6. **HTTP 500 / 503 (Server Error)**: Upstream crashes -> handled cleanly, `error_code="UPSTREAM_ERROR"`.
7. **Timeout (> 5s)**: Upstream hangs -> handled cleanly, `error_code="TIMEOUT"`.
8. **Non-JSON HTML Response**: Upstream returns Cloudflare HTML error or 502 Bad Gateway page -> caught safely, `error_code="PARSE_ERROR"`.

### 3.3 Tier 3: Cross-Feature Combinations
Validates end-to-end tool execution pipeline:
1. **Top-K Matching -> Async Execution**: User query triggers top-K matching; top candidate is dispatched through `httpx.AsyncClient`.
2. **Payload Truncation & Sanitization**: If upstream returns an oversized JSON array (e.g. 100 items, 150KB), the engine truncates it to top 5 items and caps output text at 2,500 characters.
3. **Interactive Cockpit UI Card Generation**: Execution automatically produces a structured card:
   ```json
   {
     "type": "public_api_data",
     "data": {
       "tool_id": "weather_open_meteo",
       "title": "Open-Meteo Weather Forecast",
       "payload": { ... }
     }
   }
   ```
4. **Concurrency & Thread Safety**: 10 concurrent requests to different tools resolve asynchronously without race conditions.

### 3.4 Tier 4: Real-World Chat Integration
Validates end-user chat endpoints in `src/api/server.py`:
1. **Standard Chat (`POST /api/chat`) with Weather Query**:
   - Request: `{"message": "Quel temps fait-il à Paris ?"}`.
   - Assertions: Status code 200, response contains live weather data, cards array contains `public_api_data`.
2. **Standard Chat (`POST /api/chat`) with Crypto Query**:
   - Request: `{"message": "Quel est le cours de Bitcoin en EUR ?"}`.
   - Assertions: Status code 200, response contains CoinGecko live price, card generated.
3. **Streaming Chat (`POST /api/chat/stream`)**:
   - Assertions: `text/event-stream` headers, emission of `status` events (`{"type": "status", "text": "...", "step": "tool_calling"}`), final `complete` event containing reply and cards.
4. **Graceful Fallback on Upstream Failure**:
   - Mock upstream failing with 500 or timeout during chat turn.
   - Assertions: Chat turn succeeds (HTTP 200), response informs user politely or answers with baseline knowledge, zero crash.
5. **REST API Management Endpoints**:
   - `GET /api/tools/public-apis`: Returns list of 1,079 tools with category and description.
   - `GET /api/tools/public-apis/stats`: Returns count (1,079) and category counts.
   - `POST /api/tools/public-apis/execute`: Programmatic execution endpoint returns execution result and card.

---

## 4. Test Architecture & Environment

### 4.1 Test Runner & Tools
- **Test Framework**: `pytest` 9.1.1 with `pytest-asyncio` 1.4.0.
- **Python Runtime**: Python 3.10.7.
- **HTTP Mocking Engine**: `httpx.MockTransport` (native, deterministic, zero-network).
- **FastAPI Client**: `starlette.testclient.TestClient` / `httpx.AsyncClient` with `ASGITransport(app=app)`.
- **Config**: `services/core-engine/pytest.ini`.

### 4.2 Mock Router Architecture
The test suite implements a centralized deterministic mock transport router:
```python
def make_mock_public_api_transport():
    def handler(request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        # Weather
        if "api.open-meteo.com" in url_str:
            return httpx.Response(200, json={"current_weather": {"temperature": 18.5, "windspeed": 12.0}})
        # Crypto
        if "api.coingecko.com" in url_str:
            return httpx.Response(200, json={"bitcoin": {"eur": 62500, "usd": 68000}})
        # Forex
        if "open.er-api.com" in url_str:
            return httpx.Response(200, json={"rates": {"USD": 1.08, "MAD": 10.85}})
        # Jokes
        if "jokeapi.dev" in url_str:
            return httpx.Response(200, json={"joke": "Why do programmers prefer dark mode? Because light attracts bugs."})
        # Cat facts
        if "catfact.ninja" in url_str:
            return httpx.Response(200, json={"fact": "Cats sleep 70% of their lives."})
        # Failure simulations
        if "status/404" in url_str:
            return httpx.Response(404, json={"error": "Not Found"})
        if "status/429" in url_str:
            return httpx.Response(429, json={"error": "Too Many Requests"})
        if "status/500" in url_str:
            return httpx.Response(500, json={"error": "Internal Server Error"})
        if "html-error" in url_str:
            return httpx.Response(502, text="<html><body>502 Bad Gateway</body></html>", headers={"content-type": "text/html"})
        if "huge-payload" in url_str:
            return httpx.Response(200, json={"items": [{"id": i, "data": "x" * 200} for i in range(100)]})
        # Default
        return httpx.Response(200, json={"status": "ok", "url": url_str})
    return httpx.MockTransport(handler)
```

---

## 5. Execution & Verification

### 5.1 Test Execution Command
To run the complete public API tool-calling test suite:
```powershell
cd C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine
pytest tests/test_public_api_tool_calling.py -v
```

To run a specific tier:
```powershell
pytest tests/test_public_api_tool_calling.py -k "TestTier1" -v
pytest tests/test_public_api_tool_calling.py -k "TestTier2" -v
pytest tests/test_public_api_tool_calling.py -k "TestTier3" -v
pytest tests/test_public_api_tool_calling.py -k "TestTier4" -v
```

### 5.2 Pass/Fail Criteria
- **Pass**: 100% of tests exit with code 0.
- **Fail**: Any unhandled exception, broken interface contract, missing card generation, or timeout.
