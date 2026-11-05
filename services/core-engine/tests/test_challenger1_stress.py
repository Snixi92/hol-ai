"""
Challenger 1 Empirical Adversarial Stress-Test Suite.
Stress-tests PublicApiRegistry and dataset indexing across 4 dimensions:
1. Dataset & Catalog Volume & Integrity (1,079 verified no-auth APIs, models, uniqueness)
2. Hostile & Boundary Inputs (extreme lengths, XSS, SQLi, null bytes, regex, emojis, RTL)
3. Concurrency & Latency Stress (100+ threads, async tasks, singleton race condition, <1ms latency)
4. Multilingual Accuracy & Ranking (French, Moroccan Darija, Spanish, English queries)
"""

import asyncio
import concurrent.futures
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List
import pytest

# Ensure services/core-engine root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.tools.models import (
    ToolDefinition,
    ToolParameter,
    ToolAuthType,
    ToolExecutionType,
    ParameterLocation,
    ToolQueryResult,
    ToolExecutionResult,
)
from src.tools.public_registry import PublicApiRegistry, normalize_string, tokenize


# ============================================================================
# 1. DATASET VOLUME & CATALOG INTEGRITY
# ============================================================================

class TestDatasetAndCatalogIntegrity:
    """Stress tests on catalog volume, schema conformance, and dataset structure."""

    @pytest.fixture(autouse=True)
    def setup_registry(self):
        self.registry = PublicApiRegistry.get_instance()

    def test_volume_exactly_1079_no_auth_apis(self):
        """Verify exactly 1,079 no-auth APIs in raw JSON and registry stats."""
        data_path = BASE_DIR / "data" / "public_apis" / "parsed_apis.json"
        assert data_path.exists(), f"Dataset file missing at {data_path}"

        with open(data_path, "r", encoding="utf-8") as f:
            raw_entries = json.load(f)

        assert len(raw_entries) == 1079, f"Raw JSON contains {len(raw_entries)} items, expected 1079"

        # Verify no auth in any entry
        for i, item in enumerate(raw_entries):
            auth_val = str(item.get("auth", "")).strip().lower().replace("`", "")
            assert auth_val in ["", "no", "none"], f"Item #{i} ({item.get('name')}) has auth: {auth_val}"

        stats = self.registry.get_stats()
        assert stats["total_tools"] == 1079, f"Registry reports {stats['total_tools']} tools, expected 1079"
        assert stats["no_auth_count"] == 1079
        assert stats["categories_count"] == 49

    def test_pydantic_schema_validation_all_1079_tools(self):
        """Validate every single tool in registry conforms to ToolDefinition without errors."""
        all_tools = self.registry.list_tools(limit=2000)
        assert len(all_tools) == 1079, f"Expected 1079 listed tools, got {len(all_tools)}"

        for tool in all_tools:
            assert isinstance(tool, ToolDefinition)
            assert tool.id and isinstance(tool.id, str)
            assert tool.name and isinstance(tool.name, str)
            assert tool.category and isinstance(tool.category, str)
            assert tool.url and (tool.url.startswith("http://") or tool.url.startswith("https://"))
            assert tool.auth_type == ToolAuthType.NO_AUTH
            assert isinstance(tool.https_support, bool)
            assert tool.cors_support in ("Yes", "No", "Unknown")

            # Check Gemini schema conversion does not crash
            schema = tool.to_gemini_schema()
            assert schema["name"] == tool.id
            assert "parameters" in schema
            assert schema["parameters"]["type"] == "object"

    def test_unique_tool_ids_and_deterministic_slugs(self):
        """
        Verify all generated tool IDs in the catalog are unique and non-empty.
        Exposes Open-Meteo vs Open-Meteo Ensemble collision.
        """
        all_tools = self.registry.list_tools(limit=2000)
        ids = [t.id for t in all_tools]
        unique_ids = set(ids)
        assert len(ids) == len(unique_ids), (
            f"Duplicate tool IDs detected! Total: {len(ids)}, Unique: {len(unique_ids)}. "
            f"Duplicate: {[x for x in ids if ids.count(x) > 1]}"
        )

    def test_open_meteo_ensemble_not_overwritten(self):
        """
        Stress test: Verify 'Open-Meteo Ensemble' API in Weather category is preserved
        and not hijacked/overwritten by the curated 'Open-Meteo' forecast tool.
        """
        ensemble_tool = self.registry.get_tool_by_id("weather_open_meteo_ensemble")
        assert ensemble_tool is not None, "Open-Meteo Ensemble tool not found in registry"
        assert ensemble_tool.name == "Open-Meteo Ensemble", (
            f"Expected tool name 'Open-Meteo Ensemble', got '{ensemble_tool.name}'"
        )
        assert "ensemble" in ensemble_tool.url.lower(), (
            f"Expected ensemble URL, got '{ensemble_tool.url}'"
        )

    def test_all_49_categories_populated(self):
        """Verify each of the 49 categories contains at least 1 tool."""
        categories = self.registry.get_categories()
        assert len(categories) == 49, f"Expected 49 categories, got {len(categories)}"
        for cat in categories:
            assert cat["count"] > 0, f"Category '{cat['category']}' has 0 tools"

    def test_curated_tools_mappings(self):
        """Verify all curated tools are retrievable by canonical ID and alias."""
        curated_ids = [
            "weather_open_meteo",
            "crypto_coingecko",
            "finance_exchangerate_api",
            "entertainment_jokeapi",
            "animals_catfact",
            "geocoding_adresse_data_gouv",
            "geocoding_nominatim",
        ]
        for cid in curated_ids:
            tool = self.registry.get_tool_by_id(cid)
            assert tool is not None, f"Curated tool '{cid}' not found in registry"
            assert tool.is_curated is True
            assert tool.execution_type == ToolExecutionType.DIRECT_REST
            assert tool.endpoint_url is not None
            assert len(tool.parameters) > 0


# ============================================================================
# 2. HOSTILE & BOUNDARY INPUTS
# ============================================================================

class TestHostileAndBoundaryInputs:
    """Stress tests on adversarial strings, SQL injection, XSS, null bytes, regex, and limits."""

    @pytest.fixture(autouse=True)
    def setup_registry(self):
        self.registry = PublicApiRegistry.get_instance()

    def test_ultra_long_queries_no_catastrophic_backtracking(self):
        """Test queries of 10k, 50k, and 100k characters for ReDoS and timeout."""
        for length in [10_000, 50_000, 100_000]:
            hostile_long = "weather " + ("a" * length)
            t0 = time.perf_counter()
            results = self.registry.search(hostile_long)
            duration_ms = (time.perf_counter() - t0) * 1000

            assert duration_ms < 50.0, f"Query of length {length} took {duration_ms:.2f}ms (threshold: 50ms)"
            assert len(results) > 0
            assert results[0].tool_id == "weather_open_meteo"

    def test_sql_injection_payloads(self):
        """Test SQL injection payloads do not cause syntax or processing errors."""
        sqli_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE tools; --",
            "1' UNION SELECT username, password FROM users--",
            "admin'--",
            "1' OR '1' = '1' /*",
            "'; EXEC xp_cmdshell('dir');--",
        ]
        for payload in sqli_payloads:
            results = self.registry.search(payload)
            assert isinstance(results, list)
            # Should safely return 0 results or top fallback without raising
            for r in results:
                assert isinstance(r, ToolQueryResult)

    def test_xss_and_html_injection(self):
        """Test HTML and XSS payloads are handled safely."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert(1)>",
            "<svg/onload=alert`1`>",
            "javascript:/*--></title></style></textarea></script></xmp><svg/onload='+/\"/+/onmouseover=1/+/[*/[]/+alert(1)//'>",
            "<iframe src=\"javascript:alert(1)\"></iframe>",
        ]
        for payload in xss_payloads:
            results = self.registry.search(payload)
            assert isinstance(results, list)

    def test_null_bytes_and_control_characters(self):
        """Test null bytes, control characters, and unprintable ASCII."""
        control_payloads = [
            "weather\x00meteo",
            "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0e\x0f",
            "bitcoin\r\n\tprice\x1b[31m",
            "\x7f\x80\x90\xff",
            "\u200b\u200c\u200d\ufeffweather\u200b",
        ]
        for payload in control_payloads:
            results = self.registry.search(payload)
            assert isinstance(results, list)

    def test_regex_metacharacters_and_unclosed_delimiters(self):
        """Test unclosed regex patterns and brackets do not cause regex errors."""
        regex_payloads = [
            "((((((((([a-z]+",
            "[a-z0-9_-]{100,",
            "*+?{2,3}\\d+.*",
            "\\\\\\\\\\\\\\\\",
            "(?<=abc)(?<!def)[",
            "^$|()[]{}+*?",
        ]
        for payload in regex_payloads:
            results = self.registry.search(payload)
            assert isinstance(results, list)

    def test_unicode_emojis_and_rtl_scripts(self):
        """Test emojis, Arabic, Hebrew, and mathematical Unicode symbols."""
        unicode_payloads = [
            "🎉🚀🔥 weather 🌧️⚡",
            "الطقس في الدار البيضاء",
            "מזג אוויר בתל אביב",
            "𝒲ℯ𝒶𝓉𝒽ℯ𝓇 ℱℴ𝓇ℯ𝒸𝒶𝓈𝓉",
            "猫 猫の事実",
            "погода и биткоин",
        ]
        for payload in unicode_payloads:
            results = self.registry.search(payload)
            assert isinstance(results, list)

    def test_boundary_top_k_values(self):
        """Test top_k boundary values: 0, 1, 10000, and negative numbers."""
        # top_k = 0
        r0 = self.registry.search("weather", top_k=0)
        assert len(r0) == 0

        # top_k = 1
        r1 = self.registry.search("weather", top_k=1)
        assert len(r1) == 1

        # top_k = 10000
        r_all = self.registry.search("weather", top_k=10000)
        assert 0 < len(r_all) <= 1079

        # top_k negative: should safely return empty list or slice without crashing
        r_neg = self.registry.search("weather", top_k=-1)
        assert isinstance(r_neg, list)

    def test_nonexistent_and_empty_categories(self):
        """Test search with empty or non-existent category strings."""
        assert self.registry.search("weather", category="")
        assert isinstance(self.registry.search("weather", category="NonExistentCategory999"), list)
        assert self.registry.search("", category="NonExistentCategory999") == []


# ============================================================================
# 3. CONCURRENCY & LATENCY STRESS
# ============================================================================

class TestConcurrencyAndLatencyStress:
    """Stress tests on multi-threading, asyncio, singleton initialization, and latency."""

    @pytest.fixture(autouse=True)
    def setup_registry(self):
        self.registry = PublicApiRegistry.get_instance()

    def test_multi_threaded_concurrent_searches(self):
        """Execute 100 concurrent threads making simultaneous search requests."""
        queries = [
            "weather forecast",
            "bitcoin price",
            "euro dollar exchange",
            "cat facts",
            "joke programming",
            "meteo paris",
            "taqs casablanca",
            "flous btc",
            "tiempo madrid",
            "adresse nantes",
        ]

        def worker_search(query: str):
            res = self.registry.search(query, top_k=5)
            assert len(res) > 0
            assert res[0].tool_id
            return len(res)

        start_time = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(worker_search, queries[i % len(queries)]) for i in range(100)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        total_time = (time.perf_counter() - start_time) * 1000
        assert len(results) == 100
        assert total_time < 500.0, f"100 concurrent thread searches took {total_time:.2f}ms (>500ms)"

    @pytest.mark.asyncio
    async def test_asyncio_concurrent_searches(self):
        """Execute 100 concurrent asyncio tasks searching the registry."""
        queries = ["weather", "crypto", "forex", "joke", "facts", "meteo", "taqs", "chhal"]

        async def async_worker(query: str):
            loop = asyncio.get_running_loop()
            res = await loop.run_in_executor(None, self.registry.search_tools, query, None, 3)
            assert len(res) > 0
            return len(res)

        tasks = [async_worker(queries[i % len(queries)]) for i in range(100)]
        results = await asyncio.gather(*tasks)
        assert len(results) == 100

    def test_singleton_thread_safety_race_condition(self):
        """50 concurrent threads simultaneously requesting get_instance() on reset."""
        PublicApiRegistry.reset_instance()

        instances = []

        def worker():
            inst = PublicApiRegistry.get_instance()
            instances.append(id(inst))

        threads = [concurrent.futures.ThreadPoolExecutor(max_workers=50).submit(worker) for _ in range(50)]
        concurrent.futures.wait(threads)

        assert len(instances) == 50
        assert len(set(instances)) == 1, f"Multiple singleton instances created under race condition: {set(instances)}"

    def test_sub_millisecond_search_latency_benchmark(self):
        """Benchmark 1,000 queries to verify sub-millisecond retrieval (PROJECT.md spec)."""
        queries = [
            "weather", "meteo", "taqs", "climat",
            "crypto", "bitcoin", "flous", "cripto",
            "exchange", "forex", "devises", "sarf",
            "joke", "blague", "nokat", "chiste",
            "cat", "chat", "qitat", "gato"
        ]

        latencies_ms: List[float] = []

        # Warm-up (50 runs)
        for _ in range(50):
            self.registry.search("weather")

        # 1,000 measured benchmark runs
        for i in range(1000):
            q = queries[i % len(queries)]
            t0 = time.perf_counter()
            self.registry.search(q, top_k=5)
            dt = (time.perf_counter() - t0) * 1000
            latencies_ms.append(dt)

        latencies_ms.sort()
        mean_lat = sum(latencies_ms) / len(latencies_ms)
        median_lat = latencies_ms[len(latencies_ms) // 2]
        p95_lat = latencies_ms[int(len(latencies_ms) * 0.95)]
        p99_lat = latencies_ms[int(len(latencies_ms) * 0.99)]

        print(f"\n[LATENCY BENCHMARK] Mean: {mean_lat:.3f}ms | Median: {median_lat:.3f}ms | P95: {p95_lat:.3f}ms | P99: {p99_lat:.3f}ms")

        assert median_lat < 1.0, f"Median search latency {median_lat:.3f}ms exceeds 1.0ms contract!"
        assert p95_lat < 2.0, f"P95 latency {p95_lat:.3f}ms exceeds 2.0ms!"

    def test_concurrent_reload_and_search_race_condition(self):
        """
        Stress test: Verify thread safety between reload() and continuous search() queries.
        Demonstrates KeyError risk if reload() clears internal dicts without synchronization.
        """
        import threading
        errors = []
        stop_event = threading.Event()

        def search_worker():
            while not stop_event.is_set():
                try:
                    res = self.registry.search("weather", top_k=3)
                    for r in res:
                        _ = r.tool_id
                except Exception as e:
                    errors.append(e)

        t1 = threading.Thread(target=search_worker)
        t2 = threading.Thread(target=search_worker)
        t1.start()
        t2.start()

        for _ in range(5):
            time.sleep(0.005)
            try:
                self.registry.reload()
            except Exception as e:
                errors.append(e)

        stop_event.set()
        t1.join()
        t2.join()

        assert len(errors) == 0, f"Race condition detected during reload vs search: {len(errors)} errors (e.g. {errors[0] if errors else ''})"


# ============================================================================
# 4. MULTILINGUAL ACCURACY & RANKING
# ============================================================================

class TestMultilingualAccuracyAndRanking:
    """Stress tests on ranking accuracy across French, Moroccan Darija, Spanish, and English."""

    @pytest.fixture(autouse=True)
    def setup_registry(self):
        self.registry = PublicApiRegistry.get_instance()

    @pytest.mark.parametrize("query,expected_canonical_id", [
        # French
        ("donne moi la météo à paris", "weather_open_meteo"),
        ("quel est le cours de bitcoin", "crypto_coingecko"),
        ("taux de change euro dollar", "finance_exchangerate_api"),
        ("raconte moi une blague drole", "entertainment_jokeapi"),
        ("des faits amusants sur les chats", "animals_catfact"),
        ("geolocaliser une adresse en france", "geocoding_adresse_data_gouv"),

        # Moroccan Darija
        ("taqs f casablanca lyoma", "weather_open_meteo"),
        ("jaw bared w shta", "weather_open_meteo"),
        ("chhal flous bitcoin", "crypto_coingecko"),
        ("sarf dial euro b dirham", "finance_exchangerate_api"),
        ("nokat zwina dial dahk", "entertainment_jokeapi"),
        ("qitat makla w facts", "animals_catfact"),
        ("kharieta w blassa f rabat", "geocoding_nominatim"),

        # Spanish
        ("cual es el tiempo en madrid", "weather_open_meteo"),
        ("pronostico del clima hoy", "weather_open_meteo"),
        ("precio de las criptomonedas y bitcoin", "crypto_coingecko"),
        ("tipo de cambio de divisas y finanzas", "finance_exchangerate_api"),
        ("cuentame un chiste gracioso", "entertainment_jokeapi"),
        ("hechos curiosos sobre gatos", "animals_catfact"),
        ("mapa y direccion en sevilla", "geocoding_nominatim"),

        # English
        ("real-time weather forecast", "weather_open_meteo"),
        ("live btc and eth crypto prices", "crypto_coingecko"),
        ("currency exchange rate conversion", "finance_exchangerate_api"),
        ("tell me a clean programming joke", "entertainment_jokeapi"),
        ("curious domestic cat trivia facts", "animals_catfact"),
        ("global geocoding search for tokyo", "geocoding_nominatim"),
    ])
    def test_multilingual_semantic_accuracy(self, query: str, expected_canonical_id: str):
        """
        Verify that natural conversational queries across 4 languages resolve
        to the expected canonical tool definition in the top 2 ranked results.
        """
        results = self.registry.search(query, top_k=3)
        assert len(results) > 0, f"Query '{query}' returned no results"

        matched_definitions = []
        for r in results[:2]:
            tool = self.registry.get_tool_by_id(r.tool_id)
            if tool:
                matched_definitions.append(tool.id)

        assert expected_canonical_id in matched_definitions, (
            f"Query '{query}' expected canonical tool '{expected_canonical_id}' in top-2, "
            f"got resolved tool IDs: {matched_definitions} (raw result tool_ids: {[r.tool_id for r in results[:2]]})"
        )

    def test_search_result_canonical_tool_id_consistency(self):
        """
        Stress test: Verify that ToolQueryResult.tool_id directly matches ToolDefinition.id
        for curated tools returned by search(), preventing ID divergence between Tier 1 and Tier 2.
        """
        for query, canonical_id in [
            ("weather", "weather_open_meteo"),
            ("bitcoin", "crypto_coingecko"),
            ("euro exchange rate", "finance_exchangerate_api"),
            ("joke", "entertainment_jokeapi"),
            ("cat fact", "animals_catfact"),
            ("adresse", "geocoding_adresse_data_gouv"),
            ("nominatim", "geocoding_nominatim"),
        ]:
            results = self.registry.search(query, top_k=1)
            assert len(results) > 0, f"Query '{query}' returned no results"
            res = results[0]
            tool = self.registry.get_tool_by_id(res.tool_id)
            assert tool is not None
            # Challenge: ToolQueryResult.tool_id should match the canonical ToolDefinition.id
            assert res.tool_id == tool.id, (
                f"ID Divergence detected for '{query}': ToolQueryResult.tool_id='{res.tool_id}' "
                f"does not match ToolDefinition.id='{tool.id}'"
            )
