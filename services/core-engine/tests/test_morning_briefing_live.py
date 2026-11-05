"""
Tests d'intégration automatisés pour le Morning Briefing & Live News Engine (Requirement R5).
Vérifie :
1. Récupération météo en direct Open-Meteo avec géocodage dynamique et résilience.
2. Ingestion et parsing RSS des actualités réelles (Google News & Le Monde).
3. Moteur de permutation anti-répétition : garantie zéro répétition adjacente, diversité textuelle.
4. Endpoints FastAPI GET /api/jarvis/briefing et GET /api/briefing/live.
5. Pont rétrocompatible JarvisBriefingService.
"""

import hashlib
import pytest
from fastapi.testclient import TestClient

from src.api.server import app
from src.services.morning_briefing import MorningBriefingService
from src.services.jarvis_briefing import JarvisBriefingService


@pytest.fixture
def client():
    """Client de test FastAPI."""
    return TestClient(app)


# --- 1. TESTS MÉTÉO EN DIRECT & GÉOCODAGE ---

@pytest.mark.asyncio
async def test_live_weather_geocoding_and_forecast_paris():
    """Vérifie la météo réelle à Paris avec géocodage et prévisions valides."""
    weather = await MorningBriefingService.get_live_weather(city="Paris", force_refresh=True)

    assert isinstance(weather, dict)
    assert weather["city"] == "Paris"
    assert "temperature_c" in weather
    assert isinstance(weather["temperature_c"], (int, float))
    assert -30.0 <= weather["temperature_c"] <= 55.0
    assert "condition" in weather and len(weather["condition"]) > 0
    assert "wind_kmh" in weather
    assert "latitude" in weather and 48.0 <= weather["latitude"] <= 49.5
    assert "longitude" in weather and 2.0 <= weather["longitude"] <= 2.7


@pytest.mark.asyncio
async def test_live_weather_dynamic_geocoding_lyon():
    """Vérifie le géocodage dynamique pour Lyon (lat ~45.75, lon ~4.85)."""
    weather = await MorningBriefingService.get_live_weather(city="Lyon", force_refresh=True)

    assert isinstance(weather, dict)
    assert "Lyon" in weather["city"]
    assert 45.0 <= weather["latitude"] <= 46.5
    assert 4.0 <= weather["longitude"] <= 5.5
    assert isinstance(weather["temperature_c"], (int, float))
    assert len(weather["emoji"]) > 0


@pytest.mark.asyncio
async def test_live_weather_unknown_city_graceful_fallback():
    """Vérifie la résilience et le repli gracieux sans crash pour une ville inconnue."""
    weather = await MorningBriefingService.get_live_weather(city="VilleInexistante999", force_refresh=True)

    assert isinstance(weather, dict)
    assert "temperature_c" in weather
    assert "condition" in weather
    assert weather["city"] == "VilleInexistante999"


# --- 2. TESTS ACTUALITÉS RÉELLES EN DIRECT (RSS) ---

@pytest.mark.asyncio
async def test_live_news_rss_ingestion_and_cleaning():
    """Vérifie l'ingestion de vraies actualités en direct depuis les flux RSS."""
    news = await MorningBriefingService.get_live_news(topic="general", max_items=5, force_refresh=True)

    assert isinstance(news, list)
    assert len(news) >= 3

    for item in news:
        assert "title" in item and len(item["title"]) > 5
        assert "source" in item and len(item["source"]) > 0
        assert "url" in item and (item["url"].startswith("http://") or item["url"].startswith("https://"))
        assert "published" in item
        assert "summary" in item
        # Vérifie l'absence de balises HTML non échappées
        assert "<html" not in item["title"].lower()
        assert "<div" not in item["title"].lower()
        assert "<p>" not in item["title"].lower()


@pytest.mark.asyncio
async def test_live_news_topic_tech():
    """Vérifie la récupération d'actualités thématiques Tech."""
    tech_news = await MorningBriefingService.get_live_news(topic="tech", max_items=4, force_refresh=True)

    assert isinstance(tech_news, list)
    assert len(tech_news) >= 3
    assert all("url" in item for item in tech_news)


# --- 3. TESTS MOTEUR ANTI-RÉPÉTITION & PERMUTATIONS ---

@pytest.mark.asyncio
async def test_anti_repetition_consecutive_runs_differ():
    """
    Exécute deux briefings consécutifs et vérifie formellement :
    1. Persona différent
    2. Structure différente
    3. Script oralisé différent
    4. Empreinte de hachage différente (zéro répétition textuelle)
    """
    run_1 = await MorningBriefingService.generate_briefing(city="Paris", force_refresh=False)
    run_2 = await MorningBriefingService.generate_briefing(city="Paris", force_refresh=False)

    assert run_1["persona"] != run_2["persona"], (
        f"Répétition de persona détectée : {run_1['persona']} vs {run_2['persona']}"
    )
    assert run_1["structure"] != run_2["structure"], (
        f"Répétition de structure détectée : {run_1['structure']} vs {run_2['structure']}"
    )

    script_1 = run_1["spoken_script"].strip()
    script_2 = run_2["spoken_script"].strip()
    assert script_1 != script_2, "Le script oralisé ne doit pas être identique d'une exécution à l'autre."

    hash_1 = hashlib.sha256(script_1.encode("utf-8")).hexdigest()
    hash_2 = hashlib.sha256(script_2.encode("utf-8")).hexdigest()
    assert hash_1 != hash_2, "Empreintes de hachage identiques détectées."


@pytest.mark.asyncio
async def test_anti_repetition_ring_buffer_zero_adjacent_duplicates():
    """
    Vérifie mathématiquement sur 10 exécutions consécutives
    que P(duplicata adjacent) = 0 pour le persona et la structure.
    """
    history_runs = []
    for _ in range(10):
        res = await MorningBriefingService.generate_briefing(city="Paris", force_refresh=False)
        history_runs.append(res)

    for i in range(1, len(history_runs)):
        prev_run = history_runs[i - 1]
        curr_run = history_runs[i]

        assert curr_run["persona"] != prev_run["persona"], (
            f"Duplicata adjacent persona à l'index {i} : {curr_run['persona']}"
        )
        assert curr_run["structure"] != prev_run["structure"], (
            f"Duplicata adjacent structure à l'index {i} : {curr_run['structure']}"
        )


@pytest.mark.asyncio
async def test_forced_persona_and_structure_parameters():
    """Vérifie que forcer un persona ou une structure est scrupuleusement respecté."""
    res_exec = await MorningBriefingService.generate_briefing(
        force_persona="executive",
        force_structure="news_first"
    )
    assert res_exec["persona"] == "executive"
    assert res_exec["structure"] == "news_first"
    assert "exécutif" in res_exec["spoken_script"].lower() or "stratégique" in res_exec["spoken_script"].lower()

    res_coach = await MorningBriefingService.generate_briefing(
        force_persona="dynamic_coach",
        force_structure="weather_first"
    )
    assert res_coach["persona"] == "dynamic_coach"
    assert res_coach["structure"] == "weather_first"


# --- 4. TESTS DES ENDPOINTS REST FASTAPI ---

def test_api_jarvis_briefing_endpoint(client):
    """Vérifie que GET /api/jarvis/briefing retourne un briefing complet enrichi."""
    response = client.get("/api/jarvis/briefing?city=Paris&topic=general")
    assert response.status_code == 200

    data = response.json()
    assert "date" in data
    assert "weather" in data
    assert "news" in data
    assert len(data["news"]) >= 3
    assert "spoken_script" in data and len(data["spoken_script"]) > 50
    assert "persona" in data
    assert "structure" in data
    assert data["persona"] in MorningBriefingService.PERSONAS
    assert data["structure"] in MorningBriefingService.STRUCTURES
    assert "anti_repetition_metadata" in data


def test_api_briefing_live_endpoint_with_params(client):
    """Vérifie l'endpoint blueprint GET /api/briefing/live avec paramètres."""
    response = client.get("/api/briefing/live?city=Lyon&persona=storyteller")
    assert response.status_code == 200

    data = response.json()
    assert data["city"] == "Lyon"
    assert data["persona"] == "storyteller"
    assert "spoken_script" in data
    assert len(data["news"]) >= 3


# --- 5. TEST DU PONT RÉTROCOMPATIBLE JARVIS ---

def test_jarvis_briefing_service_backward_compatibility():
    """Vérifie que JarvisBriefingService.generate_full_briefing retourne le briefing enrichi."""
    data = JarvisBriefingService.generate_full_briefing(include_deals=True)

    assert isinstance(data, dict)
    assert "weather" in data
    assert "news" in data
    assert "spoken_script" in data
    assert "deals" in data
    assert len(data["deals"]) == 2


# --- 6. TEST DE L'INTÉGRATION COGNITIVE ENGINE ---

def test_cognitive_engine_briefing_tool_wiring():
    """Vérifie que MorningBriefingService est correctement injecté dans le Cognitive Engine."""
    from src.services.cognitive_engine import CognitiveAgentEngine

    # Vérification que le module est bien importé dans cognitive_engine
    import src.services.cognitive_engine as cog_mod
    assert hasattr(cog_mod, "MorningBriefingService")

    # Vérification de l'exécution du service de briefing synchronisé utilisé par le tool
    briefing = MorningBriefingService.generate_briefing_sync(city="Nice", topic="tech")
    assert isinstance(briefing, dict)
    assert "Nice" in briefing["city"]
    assert len(briefing["news"]) >= 3
    assert len(briefing["spoken_script"]) > 80


def test_spoken_script_audio_suitability_across_all_personas():
    """Vérifie que tous les personas produisent un script oralisé riche et adapté au TTS."""
    for persona in MorningBriefingService.PERSONAS:
        briefing = MorningBriefingService.generate_briefing_sync(
            city="Bordeaux",
            force_persona=persona,
            user_name="Yassir"
        )
        script = briefing["spoken_script"]
        assert isinstance(script, str)
        assert len(script) >= 120, f"Script trop court pour persona {persona}"
        assert "Yassir" in script
        assert "Bordeaux" in script
        assert len(briefing["news"]) >= 1

