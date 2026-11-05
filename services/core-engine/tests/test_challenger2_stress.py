"""
Challenger 2 Empirical Adversarial Stress Test Suite for HoL AI AutonomousToolCallingEngine & Chat.
Empirically challenges upstream failure resilience:
1. Slowloris timeout > 5s
2. Sudden connection reset (ECONNRESET / RemoteProtocolError)
3. HTTP 503 Gateway Crash (HTML and raw payload)
4. Corrupted non-UTF8 binary data (b'\\x80\\xff\\xfe\\xfd...')
5. Huge 10MB payload stress / memory bounds
6. Concurrency stress under heavy load (30 concurrent async executions)
7. Zero-crash chat guarantee on /api/chat and /api/chat/stream under all failure modes.
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List
import pytest
import httpx
from starlette.testclient import TestClient

# Ensure services/core-engine root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.tools.models import ToolExecutionResult
from src.tools.public_registry import PublicApiRegistry
from src.tools.tool_calling_engine import AutonomousToolCallingEngine
from src.api.server import app
from src.services.session_manager import SessionManager


# ============================================================================
# ADVERSARIAL MOCK TRANSPORT SIMULATOR
# ============================================================================

class AdversarialMode:
    NORMAL = "normal"
    SLOWLORIS = "slowloris"
    CONNECTION_RESET = "connection_reset"
    GATEWAY_503_HTML = "gateway_503_html"
    GATEWAY_503_TEXT = "gateway_503_text"
    CORRUPTED_NON_UTF8 = "corrupted_non_utf8"
    HUGE_10MB_PAYLOAD = "huge_10mb_payload"


CURRENT_ADVERSARIAL_MODE = AdversarialMode.NORMAL


def adversarial_handler(request: httpx.Request) -> httpx.Response:
    url_str = str(request.url)

    # 1. Slowloris timeout > 5s
    if CURRENT_ADVERSARIAL_MODE == AdversarialMode.SLOWLORIS or "simulate_slowloris" in url_str:
        raise httpx.ReadTimeout("Adversarial upstream: Slowloris read timeout exceeded 5.0s", request=request)

    # 2. Connection reset
    if CURRENT_ADVERSARIAL_MODE == AdversarialMode.CONNECTION_RESET or "simulate_reset" in url_str:
        raise httpx.RemoteProtocolError("Adversarial upstream: Connection reset by peer (ECONNRESET)", request=request)

    # 3. HTTP 503 Gateway Crash HTML
    if CURRENT_ADVERSARIAL_MODE == AdversarialMode.GATEWAY_503_HTML or "simulate_503_html" in url_str:
        return httpx.Response(
            503,
            headers={"content-type": "text/html; charset=utf-8"},
            text="<!DOCTYPE html><html><head><title>503 Service Unavailable</title></head><body><h1>Upstream Gateway Crashed</h1></body></html>"
        )

    # 4. HTTP 503 Gateway Crash Plain Text
    if CURRENT_ADVERSARIAL_MODE == AdversarialMode.GATEWAY_503_TEXT or "simulate_503_text" in url_str:
        return httpx.Response(
            503,
            headers={"content-type": "text/plain"},
            text="503 Service Unavailable: Backing microservice died."
        )

    # 5. Corrupted Non-UTF8 Binary Payload
    if CURRENT_ADVERSARIAL_MODE == AdversarialMode.CORRUPTED_NON_UTF8 or "simulate_non_utf8" in url_str:
        # Invalid UTF-8 bytes that trigger UnicodeDecodeError if decoded directly as UTF-8
        corrupted_bytes = b"\x80\xFF\xFE\xFD\x90\xAA\xBB\xCC\xDD\xEE\x00\xFF\xC0\xC1\xF5\xF6\xF7"
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            content=corrupted_bytes
        )

    # 6. Huge 10MB Payload
    if CURRENT_ADVERSARIAL_MODE == AdversarialMode.HUGE_10MB_PAYLOAD or "simulate_10mb" in url_str:
        # Generate approximately 10MB of JSON
        large_padding = "X" * (10 * 1024 * 1024)
        huge_obj = {
            "status": "success",
            "size_marker": "10MB_PAYLOAD",
            "blob": large_padding,
            "items": [{"idx": i, "content": f"Entry_{i}_{'Y' * 50}"} for i in range(1000)]
        }
        json_bytes = json.dumps(huge_obj).encode("utf-8")
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            content=json_bytes
        )

    # Default normal response for Open-Meteo
    if "open-meteo.com" in url_str:
        return httpx.Response(
            200,
            json={
                "latitude": 48.85,
                "longitude": 2.35,
                "current_weather": {
                    "temperature": 21.0,
                    "windspeed": 10.5,
                    "weathercode": 0
                }
            }
        )

    # Default normal response for CoinGecko
    if "coingecko.com" in url_str:
        return httpx.Response(
            200,
            json={
                "bitcoin": {
                    "eur": 85000,
                    "usd": 92000,
                    "change_24h": 3.4
                }
            }
        )

    # Default fallback
    return httpx.Response(200, json={"status": "ok", "url": url_str})


@pytest.fixture(autouse=True)
def clean_sessions_and_reset_mode():
    global CURRENT_ADVERSARIAL_MODE
    CURRENT_ADVERSARIAL_MODE = AdversarialMode.NORMAL
    SessionManager.clear_all()
    yield
    CURRENT_ADVERSARIAL_MODE = AdversarialMode.NORMAL
    SessionManager.clear_all()


@pytest.fixture(autouse=True)
def intercept_adversarial_httpx(monkeypatch):
    """Intercept all httpx.AsyncClient instances with adversarial mock transport."""
    mock_transport = httpx.MockTransport(adversarial_handler)
    original_init = httpx.AsyncClient.__init__

    def patched_init(self, *args, **kwargs):
        kwargs["transport"] = mock_transport
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


# ============================================================================
# EMPIRICAL ADVERSARIAL CHALLENGES
# ============================================================================

class TestChallenger2EmpiricalStress:
    """
    Adversarial challenge test suite executed by Challenger 2.
    Validates failure resilience, memory bounds, zero unhandled exceptions, and chat guarantees.
    """

    @pytest.mark.asyncio
    async def test_challenge_1_slowloris_timeout_resilience(self):
        """
        Challenge 1: Slowloris Upstream Delay (>5.0s).
        Must cleanly return TIMEOUT without unhandled exceptions or thread hang.
        """
        global CURRENT_ADVERSARIAL_MODE
        CURRENT_ADVERSARIAL_MODE = AdversarialMode.SLOWLORIS

        engine = AutonomousToolCallingEngine.get_instance()
        start = time.perf_counter()
        result = await engine.execute_tool("weather_open_meteo")
        duration = time.perf_counter() - start

        assert not result.success, "Tool execution must fail under slowloris timeout"
        assert result.error_code == "TIMEOUT", f"Expected error_code 'TIMEOUT', got '{result.error_code}'"
        assert "timed out" in result.error_message.lower()
        assert result.card is None
        # Must return in bounded time without hanging
        assert duration < 5.0, f"Slowloris interception took too long: {duration}s"

    @pytest.mark.asyncio
    async def test_challenge_2_abrupt_connection_reset_resilience(self):
        """
        Challenge 2: Sudden Connection Reset (ECONNRESET / RemoteProtocolError).
        Must cleanly catch network disconnection and return UPSTREAM_ERROR.
        """
        global CURRENT_ADVERSARIAL_MODE
        CURRENT_ADVERSARIAL_MODE = AdversarialMode.CONNECTION_RESET

        engine = AutonomousToolCallingEngine.get_instance()
        result = await engine.execute_tool("crypto_coingecko")

        assert not result.success
        assert result.error_code == "UPSTREAM_ERROR"
        assert "connection" in result.error_message.lower() or "reset" in result.error_message.lower()
        assert result.card is None

    @pytest.mark.asyncio
    async def test_challenge_3a_gateway_503_html_crash_resilience(self):
        """
        Challenge 3a: Upstream 503 Gateway Crash with HTML Error Page (Cloudflare / Nginx 503).
        Must detect non-JSON HTML, return NON_JSON_RESPONSE or UPSTREAM_ERROR without JSONDecodeError.
        """
        global CURRENT_ADVERSARIAL_MODE
        CURRENT_ADVERSARIAL_MODE = AdversarialMode.GATEWAY_503_HTML

        engine = AutonomousToolCallingEngine.get_instance()
        result = await engine.execute_tool("weather_open_meteo")

        assert not result.success
        assert result.error_code in ["NON_JSON_RESPONSE", "UPSTREAM_ERROR"], (
            f"Expected NON_JSON_RESPONSE or UPSTREAM_ERROR, got {result.error_code}"
        )
        assert result.card is None

    @pytest.mark.asyncio
    async def test_challenge_3b_gateway_503_text_crash_resilience(self):
        """
        Challenge 3b: Upstream 503 Gateway Crash with Plain Text Body.
        Must return UPSTREAM_ERROR without unhandled exception.
        """
        global CURRENT_ADVERSARIAL_MODE
        CURRENT_ADVERSARIAL_MODE = AdversarialMode.GATEWAY_503_TEXT

        engine = AutonomousToolCallingEngine.get_instance()
        result = await engine.execute_tool("weather_open_meteo")

        assert not result.success
        assert result.error_code == "UPSTREAM_ERROR"
        assert result.card is None

    @pytest.mark.asyncio
    async def test_challenge_4_corrupted_non_utf8_binary_resilience(self):
        """
        Challenge 4: Corrupted Non-UTF8 Binary Payload (raw bytes b'\\x80\\xff\\xfe\\xfd...').
        Must handle corrupted binary stream safely without crashing the process or raising uncaught UnicodeDecodeError.
        """
        global CURRENT_ADVERSARIAL_MODE
        CURRENT_ADVERSARIAL_MODE = AdversarialMode.CORRUPTED_NON_UTF8

        engine = AutonomousToolCallingEngine.get_instance()
        result = await engine.execute_tool("weather_open_meteo")

        assert not result.success
        # Must return clean error result without unhandled crash
        assert result.error_code in ["UPSTREAM_ERROR", "PARSE_ERROR"]
        assert result.card is None

    @pytest.mark.asyncio
    async def test_challenge_5_huge_10mb_payload_bounds(self):
        """
        Challenge 5: Huge 10MB Payload Stress & Truncation Bounds.
        Must handle 10MB upstream response, truncate lists to <= 5 items,
        and bound summary text strictly <= 2,500 characters.
        """
        global CURRENT_ADVERSARIAL_MODE
        CURRENT_ADVERSARIAL_MODE = AdversarialMode.HUGE_10MB_PAYLOAD

        engine = AutonomousToolCallingEngine.get_instance()
        result = await engine.execute_tool("weather_open_meteo")

        assert result.success, "Engine should successfully parse valid JSON even if 10MB"
        # Truncation verification
        items = result.data.get("items", [])
        assert len(items) <= 5, f"Items list must be truncated to <= 5 items, found {len(items)}"
        # Summary verification: strictly <= 2,500 characters
        assert len(result.summary_text) <= 2500, (
            f"Summary exceeded 2,500 characters: {len(result.summary_text)}"
        )
        assert result.card is not None
        assert result.card["type"] == "public_api_data"

    @pytest.mark.asyncio
    async def test_challenge_6_concurrency_stress_under_load(self):
        """
        Challenge 6: Concurrency stress with 30 simultaneous asynchronous tool executions
        with mixed conditions (normal, timeout, 503, 10MB payload).
        Verifies thread safety, connection pool stability, and zero race conditions.
        """
        engine = AutonomousToolCallingEngine.get_instance()

        async def worker(idx: int):
            if idx % 4 == 0:
                # Normal weather
                return await engine.execute_tool("weather_open_meteo")
            elif idx % 4 == 1:
                # Connection reset simulation
                return await engine.execute_tool("crypto_coingecko", path_suffix="?simulate_reset=1")
            elif idx % 4 == 2:
                # 503 HTML simulation
                return await engine.execute_tool("weather_open_meteo", path_suffix="?simulate_503_html=1")
            else:
                # Huge 10MB simulation
                return await engine.execute_tool("weather_open_meteo", path_suffix="?simulate_10mb=1")

        start = time.perf_counter()
        tasks = [worker(i) for i in range(32)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.perf_counter() - start

        # Verify all 32 completed without any unhandled Python exceptions
        for i, res in enumerate(results):
            assert not isinstance(res, Exception), f"Task {i} raised unhandled exception: {res}"
            assert isinstance(res, ToolExecutionResult)

        # Confirm expected distribution
        successes = [r for r in results if r.success]
        failures = [r for r in results if not r.success]
        assert len(successes) == 16  # idx % 4 == 0 and idx % 4 == 3
        assert len(failures) == 16   # idx % 4 == 1 and idx % 4 == 2
        assert total_time < 5.0, f"32 concurrent tasks took too long: {total_time}s"

    def test_challenge_7a_chat_zero_crash_on_slowloris(self, client):
        """
        Challenge 7a: POST /api/chat under upstream slowloris timeout.
        Endpoint MUST return HTTP 200 with polite conversational reply.
        """
        global CURRENT_ADVERSARIAL_MODE
        CURRENT_ADVERSARIAL_MODE = AdversarialMode.SLOWLORIS

        resp = client.post(
            "/api/chat",
            json={
                "message": "Quelle est la météo en direct à Paris ?",
                "user_id": "challenger2_user",
                "session_id": "session_stress_slowloris"
            }
        )
        assert resp.status_code == 200, f"Server crashed with status {resp.status_code}"
        data = resp.json()
        assert "reply" in data
        assert len(data["reply"]) > 0
        # No corrupted card injected
        assert not any(c.get("type") == "public_api_data" and not c.get("data") for c in data.get("cards", []))

    def test_challenge_7b_chat_zero_crash_on_connection_reset(self, client):
        """
        Challenge 7b: POST /api/chat under upstream connection reset.
        Endpoint MUST return HTTP 200.
        """
        global CURRENT_ADVERSARIAL_MODE
        CURRENT_ADVERSARIAL_MODE = AdversarialMode.CONNECTION_RESET

        resp = client.post(
            "/api/chat",
            json={
                "message": "Donne-moi le cours de Bitcoin",
                "user_id": "challenger2_user",
                "session_id": "session_stress_reset"
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "reply" in data
        assert len(data["reply"]) > 0

    def test_challenge_7c_chat_zero_crash_on_503_gateway_crash(self, client):
        """
        Challenge 7c: POST /api/chat under upstream 503 HTML gateway crash.
        Endpoint MUST return HTTP 200 with polite fallback.
        """
        global CURRENT_ADVERSARIAL_MODE
        CURRENT_ADVERSARIAL_MODE = AdversarialMode.GATEWAY_503_HTML

        resp = client.post(
            "/api/chat",
            json={
                "message": "Quel temps fait-il aujourd'hui ?",
                "user_id": "challenger2_user",
                "session_id": "session_stress_503"
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "reply" in data

    def test_challenge_7d_chat_zero_crash_on_corrupted_non_utf8(self, client):
        """
        Challenge 7d: POST /api/chat under corrupted non-UTF8 binary response.
        Endpoint MUST return HTTP 200 without UnicodeDecodeError crash.
        """
        global CURRENT_ADVERSARIAL_MODE
        CURRENT_ADVERSARIAL_MODE = AdversarialMode.CORRUPTED_NON_UTF8

        resp = client.post(
            "/api/chat",
            json={
                "message": "Météo à Paris s'il te plaît",
                "user_id": "challenger2_user",
                "session_id": "session_stress_non_utf8"
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "reply" in data

    def test_challenge_7e_chat_stream_zero_crash_under_adversarial_conditions(self, client):
        """
        Challenge 7e: POST /api/chat/stream under upstream connection reset and 503.
        SSE stream MUST return HTTP 200, emit events, and terminate with 'complete' event.
        """
        global CURRENT_ADVERSARIAL_MODE
        CURRENT_ADVERSARIAL_MODE = AdversarialMode.CONNECTION_RESET

        resp = client.post(
            "/api/chat/stream",
            json={
                "message": "Météo en direct à Paris",
                "user_id": "challenger2_stream_user",
                "session_id": "session_stress_stream_reset"
            }
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")

        events = []
        for line in resp.text.split("\n"):
            line = line.strip()
            if line.startswith("data:"):
                raw_json = line[5:].strip()
                if raw_json:
                    events.append(json.loads(raw_json))

        assert len(events) >= 1, f"Expected at least one event, got {events}"
        # Last event must be complete
        complete_events = [e for e in events if e.get("type") == "complete"]
        assert len(complete_events) == 1, f"Expected complete event, got {events}"
        complete = complete_events[0]
        assert "reply" in complete
        assert len(complete["reply"]) > 0

    def test_challenge_7f_chat_huge_10mb_payload_handling(self, client):
        """
        Challenge 7f: POST /api/chat when upstream returns 10MB JSON payload.
        Verifies JSON payload response size does not crash or corrupt the HTTP chat response.
        """
        global CURRENT_ADVERSARIAL_MODE
        CURRENT_ADVERSARIAL_MODE = AdversarialMode.HUGE_10MB_PAYLOAD

        resp = client.post(
            "/api/chat",
            json={
                "message": "Donne-moi la météo à Paris",
                "user_id": "challenger2_user",
                "session_id": "session_stress_10mb"
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "reply" in data
        cards = data.get("cards", [])
        api_cards = [c for c in cards if c.get("type") == "public_api_data"]
        assert len(api_cards) == 1
        card_data = api_cards[0].get("data", {})
        # Summary in card must be bounded to <= 2,500 chars
        summary = card_data.get("summary", "")
        assert len(summary) <= 2500
