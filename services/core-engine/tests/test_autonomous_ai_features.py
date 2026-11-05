"""
Suite de tests automatisés pour les fonctionnalités IA autonomes de HoL AI (Requirement R3).
Couvre :
1. Découverte des modèles LLM (/api/models).
2. Découverte et sélection des personas (/api/personas).
3. Adaptation dynamique des instructions système et du ton selon le persona.
4. Moteur de citations standardisées type Perplexity AI (PerplexityCitationEngine).
5. Intégration dans /api/chat et /api/chat/stream avec paramètres 'model' et 'persona'.
6. Résilience, rétrocompatibilité et valeurs par défaut.
"""
import json
import pytest
from fastapi.testclient import TestClient
from src.api.server import app
from src.services.cognitive_engine import (
    CognitiveAgentEngine,
    PerplexityCitationEngine,
    AVAILABLE_MODELS,
    AVAILABLE_PERSONAS
)
from src.services.session_manager import SessionManager


@pytest.fixture(autouse=True)
def clean_sessions():
    SessionManager.clear_all()
    yield
    SessionManager.clear_all()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


# ============================================================================
# 1. TESTS DES ENDPOINTS DE DÉCOUVERTE (/api/models & /api/personas)
# ============================================================================

def test_get_models_endpoint(client):
    """Vérifie que GET /api/models retourne la liste des modèles avec leurs spécifications."""
    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()

    assert "available_models" in data
    assert "default" in data
    assert data["default"] == "gemini-3.5-flash-lite"

    models = data["available_models"]
    assert len(models) >= 4

    model_ids = [m["id"] for m in models]
    assert "gemini-3.5-flash-lite" in model_ids
    assert "gemini-flash-latest" in model_ids
    assert "gemini-2.5-flash" in model_ids
    assert "gemini-pro-latest" in model_ids

    # Vérification des métadonnées requises par modèle
    for m in models:
        assert "id" in m and len(m["id"]) > 0
        assert "name" in m and len(m["name"]) > 0
        assert "provider" in m and m["provider"] == "Google"
        assert "speed" in m and len(m["speed"]) > 0
        assert "context_window" in m and "tokens" in m["context_window"]
        assert "description" in m and len(m["description"]) > 0
        assert "capabilities" in m and isinstance(m["capabilities"], list)
        assert len(m["capabilities"]) >= 2


def test_get_personas_endpoint(client):
    """Vérifie que GET /api/personas retourne les 4 personas avec description et tonalités."""
    response = client.get("/api/personas")
    assert response.status_code == 200
    data = response.json()

    assert "available_personas" in data
    assert "default" in data
    assert data["default"] == "big_sis"

    personas = data["available_personas"]
    assert len(personas) == 4

    persona_ids = [p["id"] for p in personas]
    assert set(persona_ids) == {"big_sis", "architect", "executive", "tutor"}

    for p in personas:
        assert "id" in p and len(p["id"]) > 0
        assert "name" in p and len(p["name"]) > 0
        assert "tone" in p and len(p["tone"]) > 0
        assert "description" in p and len(p["description"]) > 0
        assert "tags" in p and isinstance(p["tags"], list)


# ============================================================================
# 2. TESTS DU SÉLECTEUR DE PERSONAS ET ADAPTATION DU SYSTEM PROMPT
# ============================================================================

def test_persona_system_prompt_adaptation():
    """Vérifie que _build_system_prompt adapte fidèlement l'identité et le ton pour chaque persona."""
    # 1. Persona Big Sis (par défaut)
    prompt_big_sis = CognitiveAgentEngine._build_system_prompt(detected_lang="fr", thinking_level="standard", persona="big_sis")
    assert "Big sis energy & best friend" in prompt_big_sis
    assert "Friendly and funny like a best friend" in prompt_big_sis

    # 2. Persona Architect (Tech Lead)
    prompt_architect = CognitiveAgentEngine._build_system_prompt(detected_lang="fr", thinking_level="standard", persona="architect")
    assert "Architecte Senior & Tech Lead" in prompt_architect
    assert "architecture logicielle" in prompt_architect.lower()
    assert "trade-offs" in prompt_architect.lower()
    assert "clean code" in prompt_architect.lower()

    # 3. Persona Executive (Stratège ROI)
    prompt_executive = CognitiveAgentEngine._build_system_prompt(detected_lang="fr", thinking_level="standard", persona="executive")
    assert "Analyste Exécutif & Stratège ROI" in prompt_executive
    assert "Bottom Line Up Front" in prompt_executive or "BLUF" in prompt_executive
    assert "KPIs" in prompt_executive
    assert "ROI" in prompt_executive

    # 4. Persona Tutor (Pédagogue)
    prompt_tutor = CognitiveAgentEngine._build_system_prompt(detected_lang="fr", thinking_level="standard", persona="tutor")
    assert "Pédagogue & Mentor Didactique" in prompt_tutor
    assert "transmission du savoir" in prompt_tutor or "pédagogue" in prompt_tutor.lower()
    assert "analogies" in prompt_tutor.lower()

    # 5. Fallback sur persona inconnu -> doit retomber proprement sur big_sis
    prompt_unknown = CognitiveAgentEngine._build_system_prompt(detected_lang="fr", thinking_level="standard", persona="unknown_random")
    assert "Big sis energy & best friend" in prompt_unknown


# ============================================================================
# 3. TESTS DU MOTEUR DE CITATIONS PERPLEXITY-STYLE
# ============================================================================

def test_perplexity_citation_engine_domain_extraction():
    """Vérifie l'extraction précise et propre du nom de domaine d'une URL."""
    assert PerplexityCitationEngine.extract_domain("https://www.rockstargames.com/newswire/article") == "rockstargames.com"
    assert PerplexityCitationEngine.extract_domain("http://cdiscount.com/informatique/pc") == "cdiscount.com"
    assert PerplexityCitationEngine.extract_domain("https://news.ycombinator.com/item?id=123") == "news.ycombinator.com"
    assert PerplexityCitationEngine.extract_domain("") == ""
    assert PerplexityCitationEngine.extract_domain(None) == ""


def test_perplexity_citation_engine_standardization():
    """Vérifie la normalisation rigoureuse de sources web en citations 1-based indexées."""
    raw_results = [
        {
            "title": "GTA 6 Confirmed Release Window",
            "url": "https://www.rockstargames.com/newswire/article/gta-6-announcement",
            "snippet": "Rockstar Games announces GTA VI arriving in Fall 2025 on next-gen consoles."
        },
        {
            "title": "PlayStation 5 Pro Technical Overview",
            "url": "https://blog.playstation.com/2024/09/10/ps5-pro-overview",
            "snippet": "Spectral Super Resolution and upgraded GPU provide 45% faster rendering."
        },
        # Doublon d'URL : doit être dédupliqué
        {
            "title": "GTA 6 Official Announcement Duplicate",
            "url": "https://www.rockstargames.com/newswire/article/gta-6-announcement",
            "snippet": "Duplicate item."
        }
    ]

    citations = PerplexityCitationEngine.standardize_search_results(raw_results)
    assert len(citations) == 2

    c1 = citations[0]
    assert c1["index"] == 1
    assert c1["title"] == "GTA 6 Confirmed Release Window"
    assert c1["domain"] == "rockstargames.com"
    assert c1["url"] == "https://www.rockstargames.com/newswire/article/gta-6-announcement"
    assert "rockstargames.com" in c1["favicon"]
    assert "Fall 2025" in c1["snippet"]

    c2 = citations[1]
    assert c2["index"] == 2
    assert c2["domain"] == "blog.playstation.com"
    assert c2["title"] == "PlayStation 5 Pro Technical Overview"


def test_perplexity_citation_engine_formatting_and_markers():
    """Vérifie le formatage du contexte prompt et l'assurance de présence des marqueurs [1], [2]."""
    raw_results = [
        {"title": "Source Alpha", "url": "https://alpha.org/doc", "snippet": "Alpha information"},
        {"title": "Source Beta", "url": "https://beta.com/page", "snippet": "Beta details"}
    ]
    citations = PerplexityCitationEngine.standardize_search_results(raw_results)

    prompt_context = PerplexityCitationEngine.format_citations_prompt_context(citations)
    assert "[1] Source Alpha (alpha.org)" in prompt_context
    assert "[2] Source Beta (beta.com)" in prompt_context

    # Cas 1 : Le texte contient déjà des marqueurs
    reply_with_markers = "Selon Rockstar, le jeu sort à l'automne [1], et la PS5 Pro offre 45% de perf en plus [2]."
    ensured1 = PerplexityCitationEngine.ensure_citation_markers(reply_with_markers, citations)
    assert ensured1 == reply_with_markers

    # Cas 2 : Le texte n'a aucun marqueur -> les marqueurs doivent être insérés
    reply_no_markers = "Voici la réponse sans citations spontanées."
    ensured2 = PerplexityCitationEngine.ensure_citation_markers(reply_no_markers, citations)
    assert "[1]" in ensured2
    assert "[2]" in ensured2
    assert "Sources :" in ensured2


def test_perplexity_citation_engine_card_builder():
    """Vérifie la génération de la carte interactive 'citations' pour le cockpit Liquid Glass."""
    raw_results = [
        {"title": "TechCrunch Review", "url": "https://techcrunch.com/article-1", "snippet": "Preview data"},
        {"title": "The Verge Insights", "url": "https://theverge.com/article-2", "snippet": "Review data"}
    ]
    citations = PerplexityCitationEngine.standardize_search_results(raw_results)
    card = PerplexityCitationEngine.build_citations_card(citations)

    assert card is not None
    assert card["type"] == "citations"
    assert card["data"]["total"] == 2
    assert len(card["data"]["citations"]) == 2
    assert "techcrunch.com" in card["data"]["domains"]
    assert "theverge.com" in card["data"]["domains"]


# ============================================================================
# 4. TESTS D'INTÉGRATION END-TO-END (/api/chat & /api/chat/stream)
# ============================================================================

def test_api_chat_with_custom_model_and_persona(client):
    """Vérifie que /api/chat prend en compte et restitue les paramètres model et persona."""
    payload = {
        "message": "Fais un audit de scalabilité pour un cluster multi-région",
        "user_id": "test_dev",
        "model": "gemini-flash-latest",
        "persona": "architect",
        "thinking_level": "deep"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["model"] == "gemini-flash-latest"
    assert data["persona"] == "architect"
    assert data["thinking_level"] == "deep"
    assert "reply" in data
    assert len(data["reply"]) > 0
    assert "citations" in data
    assert isinstance(data["citations"], list)


def test_api_chat_with_executive_and_tutor_personas(client):
    """Vérifie le fonctionnement pour les personas executive et tutor."""
    # Test Executive
    res_exec = client.post("/api/chat", json={
        "message": "Quel est le ROI attendu pour une migration cloud ?",
        "persona": "executive",
        "model": "gemini-pro-latest"
    })
    assert res_exec.status_code == 200
    d_exec = res_exec.json()
    assert d_exec["persona"] == "executive"
    assert d_exec["model"] == "gemini-pro-latest"

    # Test Tutor
    res_tutor = client.post("/api/chat", json={
        "message": "Explique-moi la différence entre TCP et UDP",
        "persona": "tutor",
        "model": "gemini-2.5-flash"
    })
    assert res_tutor.status_code == 200
    d_tutor = res_tutor.json()
    assert d_tutor["persona"] == "tutor"
    assert d_tutor["model"] == "gemini-2.5-flash"


def test_api_chat_stream_preserves_model_persona_citations(client):
    """Vérifie que /api/chat/stream transmet model, persona et citations dans l'événement complete."""
    payload = {
        "message": "Explique la récursion en 2 phrases simples",
        "user_id": "stream_client",
        "session_id": "sess_stream_ai_features",
        "model": "gemini-flash-latest",
        "persona": "tutor",
        "thinking_level": "fast"
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

    complete_events = [e for e in events if e.get("type") == "complete"]
    assert len(complete_events) == 1
    complete = complete_events[0]

    assert complete["model"] == "gemini-flash-latest"
    assert complete["persona"] == "tutor"
    assert complete["thinking_level"] == "fast"
    assert "citations" in complete
    assert isinstance(complete["citations"], list)
    assert len(complete.get("reply", "")) > 0


def test_api_chat_default_parameters_safety(client):
    """Vérifie que sans paramètres model et persona, les valeurs par défaut sont appliquées."""
    response = client.post("/api/chat", json={
        "message": "Bonjour Muse !"
    })
    assert response.status_code == 200
    data = response.json()

    assert data["model"] == "gemini-3.5-flash-lite"
    assert data["persona"] == "big_sis"
    assert data["thinking_level"] == "standard"
    assert "citations" in data
