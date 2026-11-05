"""
E2E Integration Test Suite for HoL AI's 1,079 Public APIs Catalog and Autonomous Tool-Calling Engine.
Governed by TEST_INFRA.md, PROJECT.md, and ORIGINAL_REQUEST.md.

Tiers Covered:
- Tier 1: Public API Registry & Catalog Indexing (Dataset integrity, Pydantic models, inverted index, multilingual aliases, curated tools)
- Tier 2: Boundary & Corner Cases (Resilience Matrix: 404, 429, 500, timeouts, non-JSON HTML, empty/special queries)
- Tier 3: Cross-Feature Combinations (Selection + Async Execution + Truncation + Cockpit Card Generation)
- Tier 4: Real-World Application Scenarios (FastAPI /api/chat & /api/chat/stream integration, SSE events, UI cards, zero-crash)

Determinism:
All HTTP interactions with external public APIs are intercepted and fulfilled offline using httpx.MockTransport.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import pytest
import httpx
from starlette.testclient import TestClient

# Ensure services/core-engine root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Dynamic imports of Tool Registry & Tool Calling Engine modules
try:
    from src.tools.models import (
        ToolDefinition,
        ToolParameter,
        ToolAuthType,
        ToolExecutionType,
        ParameterLocation,
        ToolQueryResult,
        ToolExecutionResult,
    )
    HAVE_TOOL_MODELS = True
except ImportError:
    HAVE_TOOL_MODELS = False
    ToolDefinition = None
    ToolParameter = None
    ToolAuthType = None
    ToolExecutionType = None
    ParameterLocation = None
    ToolQueryResult = None
    ToolExecutionResult = None

try:
    from src.tools.public_registry import PublicApiRegistry
    HAVE_TOOL_REGISTRY = True
except ImportError:
    HAVE_TOOL_REGISTRY = False
    PublicApiRegistry = None

try:
    from src.tools.tool_calling_engine import AutonomousToolCallingEngine
    HAVE_TOOL_ENGINE = True
except ImportError:
    HAVE_TOOL_ENGINE = False
    AutonomousToolCallingEngine = None

from src.api.server import app
from src.services.session_manager import SessionManager


# ============================================================================
# DETERMINISTIC MOCK TRANSPORT ROUTER (Zero external network requests)
# ============================================================================

def make_mock_public_api_transport() -> httpx.MockTransport:
    """
    Centralized mock transport for offline, deterministic public API testing.
    Intercepts calls to Open-Meteo, CoinGecko, ExchangeRate, CatFacts, JokeAPI,
    and simulated error endpoints (404, 429, 500, delay/timeout, HTML).
    """
    def handler(request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)

        # 0. Error & Edge Case Simulations (checked first so simulation flags work across all domains)
        if "simulate_404" in url_str or "status/404" in url_str:
            return httpx.Response(404, json={"error": "Not Found", "message": "The requested public endpoint does not exist"})

        if "simulate_429" in url_str or "status/429" in url_str:
            return httpx.Response(429, json={"error": "Rate limit exceeded", "retry_after": 60})

        if "simulate_500" in url_str or "status/500" in url_str:
            return httpx.Response(500, json={"error": "Internal Server Error", "message": "Upstream service crashed"})

        if "simulate_timeout" in url_str or "delay" in url_str:
            raise httpx.ReadTimeout("Mock request timed out after 5.0s", request=request)

        if "simulate_html_error" in url_str:
            return httpx.Response(
                502,
                headers={"content-type": "text/html"},
                text="<!DOCTYPE html><html><head><title>Cloudflare 502</title></head><body>Bad Gateway</body></html>"
            )

        if "simulate_huge_payload" in url_str:
            return httpx.Response(
                200,
                json={
                    "total": 1000,
                    "items": [{"id": i, "name": f"Item_{i}", "payload": "x" * 200} for i in range(100)]
                }
            )

        # 1. Weather: Open-Meteo
        if "open-meteo.com" in url_str:
            return httpx.Response(
                200,
                json={
                    "latitude": 48.85,
                    "longitude": 2.35,
                    "current_weather": {
                        "temperature": 18.5,
                        "windspeed": 12.0,
                        "weathercode": 1,
                        "time": "2026-10-31T20:00"
                    }
                }
            )

        # 2. Cryptocurrency: CoinGecko
        if "coingecko.com" in url_str:
            return httpx.Response(
                200,
                json={
                    "bitcoin": {"eur": 62500, "usd": 68000, "change_24h": 2.4},
                    "ethereum": {"eur": 3100, "usd": 3400, "change_24h": -0.8}
                }
            )

        # 3. Currency / Forex: ExchangeRate-API
        if "er-api.com" in url_str or "exchangerate" in url_str:
            return httpx.Response(
                200,
                json={
                    "result": "success",
                    "base_code": "EUR",
                    "rates": {"USD": 1.085, "MAD": 10.85, "GBP": 0.855, "JPY": 165.2}
                }
            )

        # 4. Jokes: JokeAPI
        if "jokeapi.dev" in url_str:
            return httpx.Response(
                200,
                json={
                    "error": False,
                    "category": "Programming",
                    "type": "single",
                    "joke": "Why do programmers prefer dark mode? Because light attracts bugs.",
                    "id": 42
                }
            )

        # 5. Animal Facts: Cat Fact
        if "catfact.ninja" in url_str:
            return httpx.Response(
                200,
                json={
                    "fact": "Cats sleep 70% of their lives.",
                    "length": 31
                }
            )

        # 6. Geocoding: adresse.data.gouv.fr / Nominatim
        if "adresse.data.gouv.fr" in url_str or "nominatim" in url_str:
            return httpx.Response(
                200,
                json={
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {"coordinates": [2.3522, 48.8566]},
                            "properties": {"label": "Paris, France", "postcode": "75001"}
                        }
                    ]
                }
            )

        # Default fallback response for any unspecified GET
        return httpx.Response(200, json={"status": "ok", "url": url_str})

    return httpx.MockTransport(handler)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def clean_sessions():
    """Ensure clean session state for every test."""
    SessionManager.clear_all()
    yield
    SessionManager.clear_all()


@pytest.fixture
def mock_transport():
    """Provides the deterministic mock transport."""
    return make_mock_public_api_transport()


@pytest.fixture(autouse=True)
def intercept_httpx_async_client(monkeypatch, mock_transport):
    """
    Global monkeypatch ensuring any httpx.AsyncClient instantiated in services/core-engine
    uses the deterministic mock transport, preventing any real network outbound requests.
    """
    original_init = httpx.AsyncClient.__init__

    def patched_init(self, *args, **kwargs):
        # Override transport with our mock transport
        kwargs["transport"] = mock_transport
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)
    yield


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    with TestClient(app) as test_client:
        yield test_client


# ============================================================================
# TIER 1: PUBLIC API REGISTRY & CATALOG INDEXING
# ============================================================================

class TestTier1RegistryAndCatalog:
    """
    Tier 1 tests: Verifies data storage, Pydantic models, in-memory inverted index,
    multilingual aliases, and curated tool retrieval.
    """

    def test_f1_dataset_loading_and_count(self):
        """
        [F1] Verify the 1,079 no-auth APIs catalog dataset.
        Authoritative source: ORIGINAL_REQUEST.md & PROJECT.md Feature 1.
        """
        # 1. Verify JSON file exists in data directory or brain scratch
        data_path = BASE_DIR / "data" / "public_apis" / "parsed_apis.json"
        if not data_path.exists():
            # Fallback to brain scratch path if M1 is copying
            data_path = Path(r"C:\Users\Yassir\.gemini\antigravity\brain\e150d96d-341f-4124-86c7-4e4f474c8494\scratch\parsed_apis.json")

        assert data_path.exists(), f"Catalog dataset not found at {data_path}"

        with open(data_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        # Count verified no-auth APIs
        no_auth_apis = [
            a for a in raw_data
            if a.get("auth", "").strip().lower().replace("`", "") in ["no", "none", ""]
        ]
        assert len(no_auth_apis) == 1079, f"Expected exactly 1,079 no-auth APIs, found {len(no_auth_apis)}"

        # If PublicApiRegistry is implemented, verify registry loads exactly 1,079 tools
        assert HAVE_TOOL_REGISTRY, "src.tools.public_registry.PublicApiRegistry not available (M1 in progress)"
        registry = PublicApiRegistry.get_instance()
        stats = registry.get_stats()
        assert stats["total_tools"] == 1079, f"Registry reports {stats['total_tools']} tools, expected 1079"

    def test_f2_tool_data_models_validation(self):
        """
        [F2] Verify Pydantic validation of ToolDefinition, ToolParameter, and ToolExecutionResult.
        Authoritative source: PROJECT.md Feature 2.
        """
        assert HAVE_TOOL_MODELS, "src.tools.models not available (M1 in progress)"

        param = ToolParameter(
            name="latitude",
            type="number",
            location=ParameterLocation.QUERY,
            required=True,
            default=48.85,
            description="Geographic latitude"
        )
        assert param.name == "latitude"
        assert param.required is True
        assert param.default == 48.85

        tool = ToolDefinition(
            id="weather_open_meteo",
            name="Open-Meteo",
            category="Weather",
            description="Accurate global weather forecasts without API key",
            url="https://open-meteo.com/",
            endpoint_url="https://api.open-meteo.com/v1/forecast",
            http_method="GET",
            auth_type=ToolAuthType.NO_AUTH,
            execution_type=ToolExecutionType.DIRECT_REST,
            parameters=[param],
            tags=["meteo", "weather", "climat", "temperature", "forecast"],
            is_curated=True
        )
        assert tool.id == "weather_open_meteo"
        assert tool.auth_type == ToolAuthType.NO_AUTH
        assert tool.is_curated is True

        gemini_schema = tool.to_gemini_schema()
        assert gemini_schema["name"] == "weather_open_meteo"
        assert "parameters" in gemini_schema
        assert "latitude" in gemini_schema["parameters"]["properties"]

    def test_f3_inverted_keyword_search(self):
        """
        [F3] Verify sub-millisecond keyword search across 1,079 tools.
        Authoritative source: PROJECT.md Feature 3.
        """
        assert HAVE_TOOL_REGISTRY, "src.tools.public_registry.PublicApiRegistry not available"
        registry = PublicApiRegistry.get_instance()

        # Query for weather
        weather_results = registry.search_tools("weather", top_k=5)
        assert len(weather_results) >= 1
        assert any("weather" in t.name.lower() or "weather" in t.category.lower() or "weather" in t.description.lower() for t in weather_results)

        # Query for crypto
        crypto_results = registry.search_tools("crypto", top_k=5)
        assert len(crypto_results) >= 1
        assert any("crypto" in t.name.lower() or "cryptocurrency" in t.category.lower() for t in crypto_results)

        # Query for cat facts
        cat_results = registry.search_tools("cat facts", top_k=5)
        assert len(cat_results) >= 1
        assert any("cat" in t.name.lower() or "cat" in t.description.lower() for t in cat_results)

    def test_f4_multilingual_category_aliasing(self):
        """
        [F4] Verify query resolution across French, Darija, Spanish, and English.
        Authoritative source: PROJECT.md Feature 4.
        """
        assert HAVE_TOOL_REGISTRY, "src.tools.public_registry.PublicApiRegistry not available"
        registry = PublicApiRegistry.get_instance()

        # French queries
        fr_meteo = registry.search_tools("donne-moi la météo à Paris", top_k=5)
        assert len(fr_meteo) >= 1
        assert any(t.category == "Weather" or "meteo" in t.id for t in fr_meteo)

        fr_blague = registry.search_tools("raconte moi une blague", top_k=5)
        assert len(fr_blague) >= 1
        assert any("joke" in t.name.lower() or "entertainment" in t.category.lower() or "joke" in t.id for t in fr_blague)

        # Darija queries (flous = money/crypto/forex, taqs = weather, nokat = jokes)
        darija_flous = registry.search_tools("chhal flous bitcoin", top_k=5)
        assert len(darija_flous) >= 1

        darija_taqs = registry.search_tools("kidayr taqs lyouma", top_k=5)
        assert len(darija_taqs) >= 1
        assert any(t.category == "Weather" for t in darija_taqs)

        # Spanish queries (tiempo = weather, noticias = news)
        es_tiempo = registry.search_tools("pronostico del tiempo", top_k=5)
        assert len(es_tiempo) >= 1
        assert any(t.category == "Weather" for t in es_tiempo)

    def test_f5_curated_high_value_tools_retrieval(self):
        """
        [F5] Verify pre-configured curated tool schemas for Weather, Crypto, Forex, Jokes, Facts.
        Authoritative source: PROJECT.md Feature 5.
        """
        assert HAVE_TOOL_REGISTRY, "src.tools.public_registry.PublicApiRegistry not available"
        registry = PublicApiRegistry.get_instance()

        curated_ids = [
            "weather_open_meteo",
            "crypto_coingecko",
            "forex_exchangerate",
            "entertainment_jokeapi",
            "animals_catfact"
        ]

        for cid in curated_ids:
            tool = registry.get_tool_by_id(cid)
            assert tool is not None, f"Curated tool '{cid}' not found in registry"
            assert tool.is_curated is True
            assert tool.endpoint_url is not None
            assert tool.endpoint_url.startswith("http")
            assert len(tool.parameters) >= 0

    def test_f1_registry_categories_and_stats(self):
        """
        [F1] Verify category listing and global registry statistics.
        Authoritative source: PROJECT.md Interface Contracts.
        """
        assert HAVE_TOOL_REGISTRY, "src.tools.public_registry.PublicApiRegistry not available"
        registry = PublicApiRegistry.get_instance()

        categories = registry.get_categories()
        assert len(categories) >= 40, f"Expected at least 40 categories, got {len(categories)}"
        cat_names = [c["category"] if isinstance(c, dict) else c for c in categories]
        assert "Weather" in cat_names
        assert "Cryptocurrency" in cat_names
        assert "Development" in cat_names

        stats = registry.get_stats()
        assert "total_tools" in stats
        assert stats["total_tools"] == 1079
        assert "curated_count" in stats
        assert stats["curated_count"] >= 5


# ============================================================================
# TIER 2: BOUNDARY, CORNER CASES & RESILIENCE MATRIX
# ============================================================================

class TestTier2BoundaryAndResilience:
    """
    Tier 2 tests: Boundary conditions, hostile inputs, and zero-crash HTTP resilience.
    Verifies error codes and graceful degradation under 404, 429, 500, timeouts, and HTML errors.
    """

    def test_f3_empty_and_whitespace_query(self):
        """
        [F3/Edge] Verify empty, whitespace, and very long query strings do not crash.
        """
        assert HAVE_TOOL_REGISTRY, "PublicApiRegistry not available"
        registry = PublicApiRegistry.get_instance()

        assert registry.search_tools("") == []
        assert registry.search_tools("   \t  \n  ") == []
        assert isinstance(registry.search_tools("a" * 3000), list)

    def test_f3_special_characters_and_accents(self):
        """
        [F3/Edge] Verify unicode accents, emojis, and adversarial injection strings.
        """
        assert HAVE_TOOL_REGISTRY, "PublicApiRegistry not available"
        registry = PublicApiRegistry.get_instance()

        # Accented characters
        results_accents = registry.search_tools("PokéAPI Grönstrom", top_k=3)
        assert isinstance(results_accents, list)

        # Adversarial input (SQL injection, XSS)
        results_xss = registry.search_tools("<script>alert('xss')</script> ' OR '1'='1", top_k=3)
        assert isinstance(results_xss, list)

        # Emojis
        results_emoji = registry.search_tools("🌤️ 🐱 🪙", top_k=3)
        assert isinstance(results_emoji, list)

    @pytest.mark.asyncio
    async def test_f9_unknown_tool_execution(self):
        """
        [F9/Resilience] Executing non-existent tool ID returns graceful failure without throwing.
        """
        assert HAVE_TOOL_ENGINE, "AutonomousToolCallingEngine not available (M2 in progress)"
        engine = AutonomousToolCallingEngine.get_instance()

        res = await engine.execute_tool("non_existent_tool_xyz_999")
        assert res.success is False
        assert res.error_code in ["TOOL_NOT_FOUND", "NOT_FOUND"]
        assert "not found" in res.error_message.lower()

    @pytest.mark.asyncio
    async def test_f9_http_404_handling(self):
        """
        [F9/Resilience] Upstream HTTP 404 Not Found returns handled error, no exception.
        """
        assert HAVE_TOOL_ENGINE, "AutonomousToolCallingEngine not available"
        engine = AutonomousToolCallingEngine.get_instance()

        res = await engine.execute_tool(
            "weather_open_meteo",
            path_suffix="?simulate_404=1"
        )
        assert res.success is False
        assert res.error_code in ["UPSTREAM_NOT_FOUND", "HTTP_404", "UPSTREAM_ERROR"]
        assert res.card is None or res.card.get("error") is not None

    @pytest.mark.asyncio
    async def test_f9_http_429_rate_limiting(self):
        """
        [F9/Resilience] Upstream HTTP 429 Rate Limiting returns RATE_LIMITED code.
        """
        assert HAVE_TOOL_ENGINE, "AutonomousToolCallingEngine not available"
        engine = AutonomousToolCallingEngine.get_instance()

        res = await engine.execute_tool(
            "crypto_coingecko",
            path_suffix="?simulate_429=1"
        )
        assert res.success is False
        assert res.error_code in ["RATE_LIMITED", "HTTP_429", "UPSTREAM_ERROR"]
        assert "rate limit" in res.error_message.lower() or "429" in res.error_message

    @pytest.mark.asyncio
    async def test_f9_http_500_upstream_error(self):
        """
        [F9/Resilience] Upstream HTTP 500 Internal Server Error returns UPSTREAM_ERROR.
        """
        assert HAVE_TOOL_ENGINE, "AutonomousToolCallingEngine not available"
        engine = AutonomousToolCallingEngine.get_instance()

        res = await engine.execute_tool(
            "forex_exchangerate",
            path_suffix="?simulate_500=1"
        )
        assert res.success is False
        assert res.error_code in ["UPSTREAM_ERROR", "HTTP_500"]

    @pytest.mark.asyncio
    async def test_f8_f9_http_timeout_circuit_breaking(self):
        """
        [F8/F9/Resilience] Upstream read timeout triggers TIMEOUT error code safely.
        """
        assert HAVE_TOOL_ENGINE, "AutonomousToolCallingEngine not available"
        engine = AutonomousToolCallingEngine.get_instance()

        res = await engine.execute_tool(
            "animals_catfact",
            path_suffix="?simulate_timeout=1"
        )
        assert res.success is False
        assert res.error_code in ["TIMEOUT", "REQUEST_TIMEOUT", "UPSTREAM_TIMEOUT"]

    @pytest.mark.asyncio
    async def test_f9_non_json_html_response(self):
        """
        [F9/Resilience] Non-JSON HTML error page (Cloudflare 502) is caught safely without JSONDecodeError.
        """
        assert HAVE_TOOL_ENGINE, "AutonomousToolCallingEngine not available"
        engine = AutonomousToolCallingEngine.get_instance()

        res = await engine.execute_tool(
            "entertainment_jokeapi",
            path_suffix="?simulate_html_error=1"
        )
        assert res.success is False
        assert res.error_code in ["PARSE_ERROR", "NON_JSON_RESPONSE", "UPSTREAM_ERROR"]


# ============================================================================
# TIER 3: CROSS-FEATURE COMBINATIONS
# ============================================================================

class TestTier3CrossFeatureExecution:
    """
    Tier 3 tests: Full execution pipeline combining query matching,
    async HTTP execution, payload truncation, and interactive UI card generation.
    """

    @pytest.mark.asyncio
    async def test_f6_top_k_tool_selection_matching(self):
        """
        [F6] Query-to-tool selection returns top candidate tools (top 3 to 5).
        Authoritative source: PROJECT.md Feature 6.
        """
        assert HAVE_TOOL_ENGINE, "AutonomousToolCallingEngine not available"
        engine = AutonomousToolCallingEngine.get_instance()

        candidates = engine.select_candidate_tools("Quel est le cours de Bitcoin ?", top_k=3)
        assert 1 <= len(candidates) <= 3
        assert any("crypto" in c.id or "coingecko" in c.id or "bitcoin" in c.name.lower() for c in candidates)

    @pytest.mark.asyncio
    async def test_f7_async_http_tool_executor_success(self):
        """
        [F7] Non-blocking async HTTP tool execution using httpx.AsyncClient.
        Authoritative source: PROJECT.md Feature 7.
        """
        assert HAVE_TOOL_ENGINE, "AutonomousToolCallingEngine not available"
        engine = AutonomousToolCallingEngine.get_instance()

        res = await engine.execute_tool(
            "weather_open_meteo",
            query_params={"latitude": 48.85, "longitude": 2.35, "current_weather": True}
        )
        assert res.success is True
        assert res.tool_id == "weather_open_meteo"
        assert res.data is not None
        assert "current_weather" in res.data
        assert res.data["current_weather"]["temperature"] == 18.5

    @pytest.mark.asyncio
    async def test_f10_payload_truncation_and_sanitization(self):
        """
        [F10] Verify that huge responses (>100 items / >50KB) are truncated to top 5 items and <= 2,500 chars.
        Authoritative source: PROJECT.md Feature 10.
        """
        assert HAVE_TOOL_ENGINE, "AutonomousToolCallingEngine not available"
        engine = AutonomousToolCallingEngine.get_instance()

        res = await engine.execute_tool(
            "weather_open_meteo",
            path_suffix="?simulate_huge_payload=1"
        )
        assert res.success is True
        # Summary text must not exceed 2,500 characters
        assert len(res.summary_text) <= 2500
        # If payload contains items list, it must be capped to top 5
        if isinstance(res.data, dict) and "items" in res.data:
            assert len(res.data["items"]) <= 5

    @pytest.mark.asyncio
    async def test_f14_interactive_cockpit_card_generation(self):
        """
        [F14] Verify generation of 'public_api_data' interactive HUD card.
        Authoritative source: PROJECT.md Feature 14.
        """
        assert HAVE_TOOL_ENGINE, "AutonomousToolCallingEngine not available"
        engine = AutonomousToolCallingEngine.get_instance()

        res = await engine.execute_tool(
            "crypto_coingecko",
            query_params={"ids": "bitcoin", "vs_currencies": "eur,usd"}
        )
        assert res.success is True
        assert res.card is not None
        assert res.card["type"] == "public_api_data"
        assert "data" in res.card
        assert res.card["data"]["tool_id"] == "crypto_coingecko"
        assert "bitcoin" in str(res.card["data"]).lower()

    @pytest.mark.asyncio
    async def test_f7_concurrent_tool_execution(self):
        """
        [F7/Concurrency] Dispatch multiple asynchronous tool calls simultaneously.
        """
        assert HAVE_TOOL_ENGINE, "AutonomousToolCallingEngine not available"
        engine = AutonomousToolCallingEngine.get_instance()

        tasks = [
            engine.execute_tool("weather_open_meteo"),
            engine.execute_tool("crypto_coingecko"),
            engine.execute_tool("forex_exchangerate"),
            engine.execute_tool("animals_catfact"),
            engine.execute_tool("entertainment_jokeapi"),
        ]
        results = await asyncio.gather(*tasks)
        assert len(results) == 5
        for r in results:
            assert r.success is True
            assert r.execution_time_ms >= 0


# ============================================================================
# TIER 4: REAL-WORLD CHAT INTEGRATION
# ============================================================================

class TestTier4ChatIntegration:
    """
    Tier 4 tests: FastAPI server endpoints, native tool declaration,
    live data injection in /api/chat and /api/chat/stream, and chat zero-crash resilience.
    """

    def test_f11_rest_api_tool_inspection_endpoints(self, client):
        """
        [F11] Verify REST endpoints in server.py:
        - GET /api/tools/public-apis
        - GET /api/tools/public-apis/stats
        - POST /api/tools/public-apis/execute
        Authoritative source: PROJECT.md Feature 11.
        """
        # 1. Stats endpoint
        res_stats = client.get("/api/tools/public-apis/stats")
        assert res_stats.status_code == 200, f"Stats endpoint failed: {res_stats.text}"
        data_stats = res_stats.json()
        assert data_stats.get("total_tools") == 1079

        # 2. List tools endpoint
        res_list = client.get("/api/tools/public-apis?limit=10")
        assert res_list.status_code == 200
        tools = res_list.json()
        assert isinstance(tools, list) or "tools" in tools
        tool_items = tools if isinstance(tools, list) else tools["tools"]
        assert len(tool_items) <= 10

        # 3. Direct execute endpoint
        res_exec = client.post(
            "/api/tools/public-apis/execute",
            json={"tool_id": "weather_open_meteo", "query_params": {"latitude": 48.85, "longitude": 2.35}}
        )
        assert res_exec.status_code == 200
        data_exec = res_exec.json()
        assert data_exec.get("success") is True
        assert "current_weather" in str(data_exec)

    def test_f12_native_gemini_tool_declaration(self):
        """
        [F12] Verify declaration of fetch_public_api_data native tool in CognitiveAgentEngine.
        Authoritative source: PROJECT.md Feature 12.
        """
        from src.services.cognitive_engine import CognitiveAgentEngine

        # Function fetch_public_api_data must be defined or present in tools_list
        tools = getattr(CognitiveAgentEngine, "get_registered_tools", lambda: [])()
        tool_names = [getattr(t, "__name__", str(t)) for t in tools]

        # Alternatively check module-level tool function
        import src.services.cognitive_engine as cog_mod
        has_tool = hasattr(cog_mod, "fetch_public_api_data") or "fetch_public_api_data" in tool_names
        assert has_tool, "Native tool function 'fetch_public_api_data' not declared in cognitive_engine"

    def test_f13_pre_llm_dynamic_grounding_weather(self):
        """
        [F13] Verify pre-LLM grounding hooks intercept weather query and inject live data.
        Authoritative source: PROJECT.md Feature 13.
        """
        assert HAVE_TOOL_ENGINE, "AutonomousToolCallingEngine not available"
        engine = AutonomousToolCallingEngine.get_instance()

        grounding = engine.match_and_fetch_live_data("Quel temps fait-il à Paris ?")
        assert grounding is not None
        assert grounding.get("success") is True
        assert "weather" in grounding.get("tool_id", "").lower()
        assert "card" in grounding
        assert grounding["card"]["type"] == "public_api_data"

    def test_f15_chat_endpoint_json_injection(self, client):
        """
        [F15] POST /api/chat with live data query injects public API data and card into response.
        Authoritative source: PROJECT.md Feature 15 & Acceptance Criteria.
        """
        payload = {
            "message": "Donne-moi la météo en direct pour Paris s'il te plaît",
            "user_id": "test_e2e_user",
            "session_id": "session_e2e_weather"
        }
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 200, f"Chat failed with status {response.status_code}: {response.text}"

        data = response.json()
        assert "reply" in data
        assert len(data["reply"]) > 0

        # Cards array must contain a 'public_api_data' card
        cards = data.get("cards", [])
        has_api_card = any(c.get("type") == "public_api_data" for c in cards)
        assert has_api_card, f"Expected 'public_api_data' card in response cards: {cards}"

    def test_f15_chat_stream_sse_injection(self, client):
        """
        [F15] POST /api/chat/stream emits tool_calling status and complete event with card.
        Authoritative source: PROJECT.md Feature 15.
        """
        payload = {
            "message": "Quel est le cours de Bitcoin aujourd'hui ?",
            "user_id": "test_stream_user",
            "session_id": "session_e2e_crypto"
        }
        response = client.post("/api/chat/stream", json=payload)
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

        events = []
        for line in response.text.split("\n"):
            line = line.strip()
            if line.startswith("data:"):
                raw_json = line[5:].strip()
                if raw_json:
                    events.append(json.loads(raw_json))

        assert len(events) >= 2, f"Expected multiple SSE events, got: {events}"

        # Check for tool_calling status event
        status_events = [e for e in events if e.get("type") == "status"]
        assert len(status_events) >= 1

        # Check for complete event with cards
        complete_events = [e for e in events if e.get("type") == "complete"]
        assert len(complete_events) == 1
        complete = complete_events[0]
        assert "cards" in complete
        assert any(c.get("type") == "public_api_data" for c in complete["cards"])

    def test_f9_chat_zero_crash_on_upstream_failure(self, client):
        """
        [F9/Resilience] When public API fails (e.g. timeout or 500), chat still returns 200.
        Authoritative source: ORIGINAL_REQUEST.md Acceptance Criteria:
        "En cas d'indisponibilité ou d'erreur sur une API tierce, le moteur gère l'incident
        gracieusement sans bloquer ni faire planter la requête de chat."
        """
        payload = {
            "message": "Donne-moi la météo simulate_timeout à Paris",
            "user_id": "test_resilience_user",
            "session_id": "session_resilience_fail"
        }
        # Server must NEVER return HTTP 500 even if upstream tool fails
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 200, f"Server crashed with code {response.status_code}"
        data = response.json()
        assert "reply" in data
        assert len(data["reply"]) > 0
