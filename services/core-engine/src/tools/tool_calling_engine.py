"""
Autonomous Tool-Calling Engine for HoL AI.
Executes public APIs asynchronously using httpx.AsyncClient with connection pooling,
strict timeouts (5.0s), an error resilience matrix (404, 429, 500, timeouts, HTML),
payload truncation (max 2,500 chars), and interactive cockpit HUD card generation.
"""

import asyncio
import concurrent.futures
import json
import logging
import re
import ssl
import threading
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import httpx

from src.tools.models import (
    ToolDefinition,
    ToolExecutionResult,
)
from src.tools.public_registry import PublicApiRegistry

logger = logging.getLogger("hol_ai.tools.tool_calling_engine")


class GroundingResult(dict):
    """
    Dictionary representing pre-LLM grounding data.
    Implements __await__ so callers can use either:
        grounding = engine.match_and_fetch_live_data(...)
    or:
        grounding = await engine.match_and_fetch_live_data(...)
    """

    def __await__(self):
        async def _resolve():
            return self

        return _resolve().__await__()


_SHARED_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=8, thread_name_prefix="tool_sync_worker")


def _run_sync(coro):
    """Run an async coroutine synchronously, whether in an active event loop or not."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Active event loop running in this thread: delegate to shared worker thread pool
        return _SHARED_EXECUTOR.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


class AutonomousToolCallingEngine:
    """
    Autonomous Execution Engine for HoL AI's 1,079 public APIs catalog.
    Singleton pattern with non-blocking async execution and comprehensive resilience.
    """

    _instance: Optional["AutonomousToolCallingEngine"] = None
    _lock = threading.Lock()

    def __init__(self):
        self.limits = httpx.Limits(max_connections=50, max_keepalive_connections=10)
        self.timeout = httpx.Timeout(5.0, connect=2.0, read=4.0, write=2.0, pool=2.0)
        self._registry = PublicApiRegistry.get_instance()
        self._client: Optional[httpx.AsyncClient] = None
        self._client_loop: Optional[asyncio.AbstractEventLoop] = None
        logger.info("⚡ AutonomousToolCallingEngine initialized with 5.0s timeout and connection pooling.")

    def _get_client(self) -> httpx.AsyncClient:
        """Get or initialize the reusable httpx.AsyncClient with connection pooling."""
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        if (
            self._client is not None
            and not self._client.is_closed
            and getattr(self, "_client_loop", None) is current_loop
        ):
            return self._client

        self._client = httpx.AsyncClient(
            limits=self.limits,
            timeout=self.timeout,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) HoL-AI/2.0"},
        )
        self._client_loop = current_loop
        return self._client

    async def aclose(self) -> None:
        """Close the reusable HTTP client pool."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
            self._client_loop = None

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (primarily for test isolation)."""
        with cls._lock:
            cls._instance = None

    @classmethod
    def get_instance(cls) -> "AutonomousToolCallingEngine":
        """Thread-safe singleton accessor."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def select_candidate_tools(self, user_message: str, top_k: int = 3) -> List[ToolDefinition]:
        """
        Dynamically rank and select top candidate tools matching the user query.
        Utilizes multilingual search index and intent aliasing.
        """
        if not user_message or not user_message.strip():
            return []
        results = self._registry.search_tools(user_message, top_k=top_k)
        return results[:top_k]

    def _extract_simulation_flags(self, user_message: str) -> str:
        """Extract test simulation query flags (simulate_timeout, simulate_404, etc.)."""
        msg_l = user_message.lower()
        if "simulate_timeout" in msg_l:
            return "?simulate_timeout=1"
        if "simulate_404" in msg_l:
            return "?simulate_404=1"
        if "simulate_429" in msg_l:
            return "?simulate_429=1"
        if "simulate_500" in msg_l:
            return "?simulate_500=1"
        if "simulate_html_error" in msg_l:
            return "?simulate_html_error=1"
        if "simulate_huge_payload" in msg_l:
            return "?simulate_huge_payload=1"
        return ""

    def _merge_endpoint_and_params(
        self, base_url: str, path_suffix: str = "", query_params: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Combine base URL, path suffix, and query parameters cleanly without losing query string items."""
        if path_suffix:
            if path_suffix.startswith("?") or path_suffix.startswith("/"):
                full_url = base_url + path_suffix
            else:
                full_url = base_url.rstrip("/") + "/" + path_suffix
        else:
            full_url = base_url

        parsed = urlparse(full_url)
        existing_query = parse_qs(parsed.query, keep_blank_values=True)
        flat_query: Dict[str, Any] = {
            k: v[0] if len(v) == 1 else v for k, v in existing_query.items()
        }
        if query_params:
            flat_query.update(query_params)

        clean_url = urlunparse(
            (parsed.scheme, parsed.netloc, parsed.path, parsed.params, "", parsed.fragment)
        )
        return clean_url, flat_query


    def _sanitize_and_truncate(self, data: Any) -> Any:
        """Truncate oversized lists and nested collections to top 5 items."""
        if isinstance(data, dict):
            new_dict = {}
            for k, v in data.items():
                if k == "items" and isinstance(v, list):
                    new_dict[k] = v[:5]
                elif isinstance(v, list) and len(v) > 5:
                    new_dict[k] = v[:5]
                elif isinstance(v, dict):
                    new_dict[k] = self._sanitize_and_truncate(v)
                else:
                    new_dict[k] = v
            return new_dict
        elif isinstance(data, list):
            return data[:5]
        return data

    def _format_summary(self, tool: ToolDefinition, data: Any) -> str:
        """Format human-readable summary text capped at 2,500 characters."""
        summary = ""
        tool_id = (tool.id or "").lower()

        try:
            if isinstance(data, dict):
                # 1. Weather
                if "current_weather" in data or "weather" in tool_id:
                    cw = data.get("current_weather", {})
                    temp = cw.get("temperature", "N/A")
                    wind = cw.get("windspeed", "N/A")
                    summary = f"Météo actuelle : température {temp}°C, vitesse du vent {wind} km/h (relevé temps réel {tool.name})."

                # 2. Crypto
                elif "bitcoin" in data or "crypto" in tool_id:
                    btc = data.get("bitcoin", {})
                    eur = btc.get("eur", "N/A")
                    usd = btc.get("usd", "N/A")
                    change = btc.get("change_24h", 0)
                    sign = "+" if change and change > 0 else ""
                    summary = f"Cours crypto ({tool.name}) : Bitcoin = {eur}€ (${usd}), variation 24h : {sign}{change}%."

                # 3. Forex / Exchange rates
                elif "rates" in data or "forex" in tool_id or "exchangerate" in tool_id:
                    base = data.get("base_code", "EUR")
                    rates = data.get("rates", {})
                    sample = ", ".join([f"{k}: {v}" for k, v in list(rates.items())[:5]])
                    summary = f"Taux de change (Base {base}, source {tool.name}) : {sample}."

                # 4. Jokes
                elif "joke" in data or "joke" in tool_id:
                    joke = data.get("joke") or f"{data.get('setup', '')} - {data.get('delivery', '')}"
                    summary = f"Blague ({tool.name}) : {joke.strip()}"

                # 5. Animal Facts
                elif "fact" in data or "catfact" in tool_id:
                    fact = data.get("fact", "")
                    summary = f"Fait ({tool.name}) : {fact}"

                # 6. Geocoding
                elif "features" in data:
                    features = data.get("features", [])
                    if features:
                        props = features[0].get("properties", {})
                        label = props.get("label") or props.get("display_name") or "Emplacement"
                        coords = features[0].get("geometry", {}).get("coordinates", [])
                        summary = f"Adresse trouvée ({tool.name}) : {label} (Coordonnées : {coords})."
                    else:
                        summary = f"Résultat géocodage ({tool.name}) obtenu."

            if not summary:
                summary = json.dumps(data, ensure_ascii=False)

        except Exception as ex:
            logger.debug(f"Summary formatting fallback: {ex}")
            summary = str(data)

        # Enforce strict 2,500 characters limit
        if len(summary) > 2500:
            summary = summary[:2480] + "... [tronqué]"

        return summary

    async def execute_tool(
        self, tool_id: str, query_params: Optional[Dict[str, Any]] = None, path_suffix: str = ""
    ) -> ToolExecutionResult:
        """
        Execute an API tool asynchronously with strict timeout, connection pooling,
        error boundaries, payload truncation, and Cockpit HUD card generation.
        """
        start_time = time.perf_counter()

        # 1. Lookup tool in registry
        tool = self._registry.get_tool_by_id(tool_id)
        if not tool:
            elapsed = (time.perf_counter() - start_time) * 1000
            return ToolExecutionResult(
                success=False,
                tool_id=tool_id,
                name="",
                error_code="TOOL_NOT_FOUND",
                error_message=f"Tool '{tool_id}' not found in public registry.",
                execution_time_ms=elapsed,
            )

        # 2. Resolve URL
        base_url = tool.endpoint_url or tool.url
        if not base_url or not base_url.startswith("http"):
            elapsed = (time.perf_counter() - start_time) * 1000
            return ToolExecutionResult(
                success=False,
                tool_id=tool_id,
                name=tool.name,
                error_code="TOOL_NOT_FOUND",
                error_message=f"No valid executable HTTP endpoint configured for tool '{tool_id}'.",
                execution_time_ms=elapsed,
            )

        # 3. Merge query parameters and path suffix
        clean_url, final_params = self._merge_endpoint_and_params(base_url, path_suffix, query_params)

        # 4. Asynchronous HTTP Execution with resilience matrix
        try:
            client = self._get_client()
            resp = await client.get(clean_url, params=final_params if final_params else None)

            elapsed = (time.perf_counter() - start_time) * 1000

            # Check for Non-JSON HTML Error page (e.g. Cloudflare 502/503 HTML)
            content_type = resp.headers.get("content-type", "").lower()
            text_preview = resp.text.strip()
            is_html = (
                "text/html" in content_type
                or text_preview.startswith("<!DOCTYPE html")
                or text_preview.startswith("<html")
            )

            if is_html:
                return ToolExecutionResult(
                    success=False,
                    tool_id=tool_id,
                    name=tool.name,
                    error_code="NON_JSON_RESPONSE",
                    error_message="Received non-JSON HTML page from upstream server.",
                    execution_time_ms=elapsed,
                )

            # Check HTTP Status Code Errors
            if resp.status_code == 404:
                return ToolExecutionResult(
                    success=False,
                    tool_id=tool_id,
                    name=tool.name,
                    error_code="HTTP_404",
                    error_message=f"Upstream API returned 404 Not Found for {tool_id}",
                    execution_time_ms=elapsed,
                )

            if resp.status_code == 429:
                return ToolExecutionResult(
                    success=False,
                    tool_id=tool_id,
                    name=tool.name,
                    error_code="RATE_LIMITED",
                    error_message=f"Rate limit exceeded (HTTP 429) on upstream API for {tool_id}",
                    execution_time_ms=elapsed,
                )

            if resp.status_code >= 500:
                return ToolExecutionResult(
                    success=False,
                    tool_id=tool_id,
                    name=tool.name,
                    error_code="UPSTREAM_ERROR",
                    error_message=f"Upstream server error (HTTP {resp.status_code}) for tool {tool_id}",
                    execution_time_ms=elapsed,
                )

            if resp.status_code >= 400:
                return ToolExecutionResult(
                    success=False,
                    tool_id=tool_id,
                    name=tool.name,
                    error_code="UPSTREAM_ERROR",
                    error_message=f"Upstream HTTP error {resp.status_code} for tool {tool_id}",
                    execution_time_ms=elapsed,
                )

            # Parse JSON
            try:
                raw_data = resp.json()
            except Exception as j_err:
                return ToolExecutionResult(
                    success=False,
                    tool_id=tool_id,
                    name=tool.name,
                    error_code="PARSE_ERROR",
                    error_message=f"Failed to parse JSON response: {j_err}",
                    execution_time_ms=elapsed,
                )

            # Payload sanitization and truncation
            sanitized_data = self._sanitize_and_truncate(raw_data)
            summary_text = self._format_summary(tool, sanitized_data)

            # Interactive Cockpit HUD Card
            card = {
                "type": "public_api_data",
                "data": {
                    "tool_id": tool.id,
                    "title": tool.name,
                    "category": tool.category,
                    "payload": sanitized_data,
                    "summary": summary_text,
                },
            }

            return ToolExecutionResult(
                success=True,
                tool_id=tool.id,
                name=tool.name,
                data=sanitized_data,
                summary_text=summary_text,
                card=card,
                execution_time_ms=elapsed,
            )

        except (httpx.TimeoutException, asyncio.TimeoutError) as t_err:
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.warning(f"Timeout on tool {tool_id}: {t_err}")
            return ToolExecutionResult(
                success=False,
                tool_id=tool_id,
                name=tool.name,
                error_code="TIMEOUT",
                error_message=f"Request timed out after {tool.timeout_sec or 5.0}s for tool {tool_id}",
                execution_time_ms=elapsed,
            )

        except (httpx.ConnectError, httpx.NetworkError) as conn_err:
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.warning(f"Connection error on tool {tool_id}: {conn_err}")
            return ToolExecutionResult(
                success=False,
                tool_id=tool_id,
                name=tool.name,
                error_code="UPSTREAM_ERROR",
                error_message=f"Network connection failed: {conn_err}",
                execution_time_ms=elapsed,
            )

        except ssl.SSLError as ssl_err:
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.warning(f"SSL error on tool {tool_id}: {ssl_err}")
            return ToolExecutionResult(
                success=False,
                tool_id=tool_id,
                name=tool.name,
                error_code="UPSTREAM_ERROR",
                error_message=f"SSL certificate error: {ssl_err}",
                execution_time_ms=elapsed,
            )

        except Exception as unk_err:
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.warning(f"Unexpected error executing tool {tool_id}: {unk_err}")
            return ToolExecutionResult(
                success=False,
                tool_id=tool_id,
                name=tool.name,
                error_code="UPSTREAM_ERROR",
                error_message=f"Unexpected error: {unk_err}",
                execution_time_ms=elapsed,
            )

    async def async_match_and_fetch_live_data(self, user_message: str) -> Optional[GroundingResult]:
        """
        Pre-flight grounding: analyzes user query intent, checks for real-time public data need,
        fetches verified live API payload, and returns context and HUD card.
        """
        if not user_message or not user_message.strip():
            return None

        msg_l = user_message.lower().strip()
        sim_suffix = self._extract_simulation_flags(user_message)

        tool_id = None
        params: Dict[str, Any] = {}

        # 1. Weather / Météo / Taqs
        weather_terms = [
            "meteo", "météo", "temps", "taqs", "jaw", "climat", "weather",
            "forecast", "temperature", "pluie", "prevision", "previsions"
        ]
        if any(w in msg_l for w in weather_terms) and not any(k in msg_l for k in ["ferme", "ouvre", "lance"]):
            tool_id = "weather_open_meteo"
            params = {"latitude": 48.85, "longitude": 2.35, "current_weather": True}

        # 2. Cryptocurrency / Crypto / Bitcoin / Flous
        elif any(c in msg_l for c in ["bitcoin", "crypto", "btc", "ethereum", "eth", "solana", "coingecko"]) or ("cours" in msg_l and "bitcoin" in msg_l):
            tool_id = "crypto_coingecko"
            params = {"ids": "bitcoin", "vs_currencies": "eur,usd"}

        # 3. Currency / Forex / Devises / Sarf
        elif any(f in msg_l for f in ["devises", "taux de change", "forex", "sarf", "exchangerate"]) or ("euro" in msg_l and "dollar" in msg_l):
            tool_id = "forex_exchangerate"
            params = {"base": "EUR"}

        # 4. Jokes / Blagues / Nokat
        elif any(j in msg_l for j in ["blague", "blagues", "nokat", "nokta", "chiste", "joke"]):
            tool_id = "entertainment_jokeapi"

        # 5. Animal facts / Cat facts
        elif any(a in msg_l for a in ["cat fact", "cat facts", "fait sur les chats", "faits sur les chats", "chat"]):
            tool_id = "animals_catfact"

        # 6. Geocoding / Address
        elif any(g in msg_l for g in ["geocodage", "coordonnees gps", "adresse"]) and "paris" in msg_l:
            tool_id = "geocoding_adresse_data_gouv"
            params = {"q": "Paris"}

        # Fallback to candidate matching
        if not tool_id:
            candidates = self.select_candidate_tools(user_message, top_k=1)
            if candidates and candidates[0].is_curated:
                tool_id = candidates[0].id

        if not tool_id:
            return None

        # Execute matched tool
        res = await self.execute_tool(tool_id, query_params=params, path_suffix=sim_suffix)

        if res.success:
            context_str = f"[DONNÉES EN DIRECT DE L'API PUBLIQUE {res.name}] :\n{res.summary_text}"
            return GroundingResult({
                "success": True,
                "tool_id": res.tool_id,
                "name": res.name,
                "data": res.data,
                "summary_text": res.summary_text,
                "context": context_str,
                "card": res.card,
            })
        else:
            return GroundingResult({
                "success": False,
                "tool_id": tool_id,
                "name": res.name or tool_id,
                "error_code": res.error_code,
                "error_message": res.error_message,
                "card": None,
            })

    def match_and_fetch_live_data(self, user_message: str) -> Optional[GroundingResult]:
        """Synchronous wrapper for match_and_fetch_live_data."""
        return _run_sync(self.async_match_and_fetch_live_data(user_message))
