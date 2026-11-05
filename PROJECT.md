# Project: HoL AI - 1,079 Public APIs Catalog & Autonomous Tool-Calling Engine

## Architecture
HoL AI integrates a catalog of 1,079 no-auth public APIs across 49 categories and an Autonomous Tool-Calling Engine in its FastAPI backend (`services/core-engine`). The architecture resolves the LLM context window bottleneck via a **Two-Tier Dynamic Retrieval & Execution Pipeline**:
- **Tier 1 (In-Memory Tool Registry & Search Index)**: Sub-millisecond inverted index with multilingual aliasing (French, Darija, Spanish, English) indexing all 1,079 APIs, plus pre-configured curated schemas for high-utility domains (weather, crypto, finance, jokes, etc.).
- **Tier 2 (Autonomous Tool Execution & Resilience Engine)**: Async HTTP client (`httpx.AsyncClient`) with connection pooling, strict timeouts (5.0s), circuit-breaking error handling (404, 429, 500, SSL, timeouts), payload truncation (max 2,500 chars), interactive cockpit UI cards generation (`public_api_data`), and prompt context injection.
- **FastAPI Core Engine Integration**: Registered as a native tool (`fetch_public_api_data`) and dynamic pre-LLM interceptor in `CognitiveAgentEngine.process_chat()`, dual-channel injection in `/api/chat` and `/api/chat/stream`, plus REST management endpoints (`/api/tools/public-apis/...`).

```
User Query (Chat/Stream)
          │
          ▼
┌────────────────────────────────────────────────────────┐
│  FastAPI server.py (/api/chat & /api/chat/stream)       │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│  CognitiveAgentEngine (services/core-engine)           │
│  - Pre-LLM Grounding & Intent Interception             │
│  - Native Gemini Tool: fetch_public_api_data           │
└─────────────────────────┬──────────────────────────────┘
                          │
          ┌───────────────┴──────────────┐
          ▼                              ▼
┌───────────────────────────┐  ┌─────────────────────────┐
│ Tier 1: PublicApiRegistry │  │ Tier 2: Execution Engine│
│ - 1,079 No-Auth APIs      │  │ - Async httpx client    │
│ - Inverted Search Index   │  │ - 5s strict timeout     │
│ - Multilingual Aliasing   │  │ - Error Resilience Matrix│
│ - Curated Tool Schemas    │  │ - Payload Truncation    │
└───────────────────────────┘  └─────────────┬───────────┘
                                             │
                                             ▼
                               ┌─────────────────────────┐
                               │ Context Data + UI Cards │
                               │ injected into Chat / SSE│
                               └─────────────────────────┘
```

## Code Layout
- `services/core-engine/data/public_apis/parsed_apis.json`: The 1,079 verified no-auth APIs dataset.
- `services/core-engine/src/tools/models.py`: Pydantic models for tools, parameters, categories, and execution results.
- `services/core-engine/src/tools/public_registry.py`: `PublicApiRegistry` class with in-memory inverted index, search, and curated schemas.
- `services/core-engine/src/tools/tool_calling_engine.py`: `AutonomousToolCallingEngine` with async HTTP execution, error handling, and card formatting.
- `services/core-engine/src/api/server.py`: FastAPI endpoints for public tools and chat endpoints injection.
- `services/core-engine/src/services/cognitive_engine.py`: Gemini native tool declaration and pre-query grounding.
- `services/core-engine/tests/test_public_api_tool_calling.py`: E2E integration test suite for public APIs and tool-calling.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | No-Auth API Dataset Storage | Store and load verified 1,079 no-auth APIs dataset locally | M1 | Survey 1 |
| 2 | Tool Data Models | Pydantic models for tool definition, parameters, and query results | M1 | Survey 1 |
| 3 | Inverted Keyword Index | Sub-millisecond token & category index for 1,079 APIs | M1 | Survey 1 |
| 4 | Multilingual Category Aliases | Map French/Darija/Spanish queries to API categories & keywords | M1 | Survey 1 |
| 5 | Curated High-Value Tools | Pre-configured executable REST schemas for Weather, Crypto, Finance, etc. | M1 | Survey 1 |
| 6 | Top-K Candidate Tool Selection | Dynamic Tier 1 tool selection matching user query to top 3-5 tools | M2 | Survey 3 |
| 7 | Async HTTP Tool Executor | Non-blocking `httpx.AsyncClient` executor with connection pooling | M2 | Survey 2, 3 |
| 8 | Strict Timeouts & Circuit Breaking | 5s timeout and domain rate limit protection | M2 | Survey 3 |
| 9 | Zero-Crash Error Handling Matrix | Graceful fallback on 404, 429, 500, SSL, timeouts, malformed HTML | M2 | Survey 3 |
| 10 | Payload Truncation & Sanitization | Limit responses to 2,500 chars and top 5 items | M2 | Survey 3 |
| 11 | REST Tool Inspection Endpoints | Endpoints `/api/tools/public-apis/...` in FastAPI server | M2 | Survey 2 |
| 12 | Native Gemini Tool Declaration | Register `fetch_public_api_data` in `CognitiveAgentEngine.process_chat` | M3 | Survey 2 |
| 13 | Pre-LLM Dynamic Grounding | Intercept factual queries and inject live API data pre-flight | M3 | Survey 2 |
| 14 | Interactive Cockpit Card Generation | Emit `public_api_data` UI cards for frontend HUD | M3 | Survey 2 |
| 15 | Chat Endpoint Data Injection | Dual-channel injection into `/api/chat` (JSON) and `/api/chat/stream` (SSE) | M3 | Survey 2 |
| 16 | E2E Integration Test Suite | Comprehensive tests covering Tiers 1-4 with deterministic mocks | E2E-Track | Survey 3 |
| 17 | Final System Report | Detailed architecture, test results, and system state report | M4 | ORIGINAL_REQUEST |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| E2E | E2E Testing Track | Design & implement comprehensive E2E test suite (Tiers 1-4) | none | DONE |
| 1 | M1: Tool Registry & Catalog Indexing | Dataset setup, Pydantic models, in-memory inverted index, multilingual aliases, curated schemas | none | DONE |
| 2 | M2: Autonomous Tool-Calling Engine | Async HTTP client, dynamic top-K selection, resilience matrix, REST endpoints | M1 | DONE |
| 3 | M3: Chat Integration & Live Data Injection | Wire into `CognitiveAgentEngine`, `/api/chat`, and `/api/chat/stream` | M2 | DONE |
| 4 | M4: End-to-End Validation & Final Project Report | Pass 100% E2E tests, zero regressions, forensic audit, final report | M3, E2E | IN_PROGRESS |

## Interface Contracts

### PublicApiRegistry ↔ AutonomousToolCallingEngine
- `PublicApiRegistry.get_instance() -> PublicApiRegistry`
- `PublicApiRegistry.search_tools(query: str, category: Optional[str] = None, top_k: int = 5) -> List[ToolDefinition]`
- `PublicApiRegistry.get_tool_by_id(tool_id: str) -> Optional[ToolDefinition]`
- `PublicApiRegistry.get_categories() -> List[Dict[str, Any]]`
- `PublicApiRegistry.get_stats() -> Dict[str, Any]`

### AutonomousToolCallingEngine ↔ CognitiveAgentEngine & server.py
- `AutonomousToolCallingEngine.execute_tool(tool_id: str, query_params: Optional[Dict[str, Any]] = None, path_suffix: str = "") -> ToolExecutionResult`
- `AutonomousToolCallingEngine.match_and_fetch_live_data(user_message: str) -> Optional[Dict[str, Any]]`
- Return payload:
  ```json
  {
    "success": true,
    "tool_id": "weather_open_meteo",
    "name": "Open-Meteo",
    "data": { ... },
    "summary_text": "...",
    "card": {
      "type": "public_api_data",
      "data": { "tool_id": "...", "title": "...", "payload": { ... } }
    }
  }
  ```
- Error payload (zero-crash):
  ```json
  {
    "success": false,
    "tool_id": "...",
    "error_code": "UPSTREAM_UNAVAILABLE",
    "error_message": "...",
    "card": null
  }
  ```
