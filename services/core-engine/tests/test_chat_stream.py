"""
Tests du streaming de réflexion en direct (/api/chat/stream) type Gemini / Claude / ChatGPT.
Vérifie l'émission séquentielle des statuts dynamiques et la complétion.
"""
import json
import pytest
from fastapi.testclient import TestClient
from src.api.server import app
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


def test_chat_stream_status_events_and_completion(client):
    """Vérifie que /api/chat/stream émet des événements SSE 'status' puis 'complete'."""
    payload = {
        "message": "Fais un calcul de rentabilité avec prix de vente 100€ et coût 40€",
        "user_id": "stream_tester",
        "session_id": "test_stream_session"
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
                data = json.loads(raw_json)
                events.append(data)

    assert len(events) >= 2, f"Événements reçus insuffisants : {events}"
    
    # Doit avoir au moins un événement 'status'
    status_events = [e for e in events if e.get("type") == "status"]
    assert len(status_events) >= 1
    # Doit contenir du texte de statut dynamique
    assert any("text" in s or "status" in s for s in status_events)

    # Doit se terminer par un événement 'complete'
    complete_events = [e for e in events if e.get("type") == "complete"]
    assert len(complete_events) == 1
    complete = complete_events[0]
    assert "reply" in complete
    assert len(complete["reply"]) > 0
    assert complete["session_id"] == "test_stream_session"


def test_chat_stream_web_factual_status_events(client):
    """Vérifie que pour une question factuelle/web, le statut de recherche et lecture est émis."""
    payload = {
        "message": "C'est quand la date de sortie de GTA 6 ?",
        "user_id": "stream_tester",
        "session_id": "test_stream_gta"
    }
    response = client.post("/api/chat/stream", json=payload)
    assert response.status_code == 200

    events = []
    for line in response.text.split("\n"):
        line = line.strip()
        if line.startswith("data:"):
            raw_json = line[5:].strip()
            if raw_json:
                events.append(json.loads(raw_json))

    # Doit contenir le statut de recherche ou de réflexion
    status_texts = [e.get("text", "") for e in events if e.get("type") == "status"]
    assert any("Réfléchit" in t or "Recherche" in t or "Rédaction" in t for t in status_texts), f"Statuts reçus : {status_texts}"

    # Doit terminer par 'complete'
    assert any(e.get("type") == "complete" for e in events)


def test_standard_api_chat_backward_compatibility(client):
    """Vérifie que l'endpoint standard /api/chat continue de fonctionner à 100% en JSON."""
    payload = {
        "message": "Bonjour, comment vas-tu ?",
        "user_id": "standard_tester"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert len(data["reply"]) > 0
    assert "session_id" in data


def test_thinking_levels_streaming(client):
    """Vérifie que thinking_level est bien pris en compte et retourné dans l'événement 'complete'."""
    for level in ["fast", "deep", "ultra"]:
        payload = {
            "message": f"Test du mode de réflexion {level}",
            "user_id": f"tester_{level}",
            "session_id": f"sess_{level}",
            "thinking_level": level
        }
        response = client.post("/api/chat/stream", json=payload)
        assert response.status_code == 200

        events = []
        for line in response.text.split("\n"):
            line = line.strip()
            if line.startswith("data:"):
                raw_json = line[5:].strip()
                if raw_json:
                    events.append(json.loads(raw_json))

        complete = next((e for e in events if e.get("type") == "complete"), None)
        assert complete is not None, f"Pas d'événement complete pour le niveau {level}"
        assert complete.get("thinking_level") == level
        assert len(complete.get("reply", "")) > 0


def test_thinking_levels_standard_api(client):
    """Vérifie que /api/chat retourne thinking_level et le champ thoughts."""
    payload = {
        "message": "Résous 12 * 14 étape par étape",
        "user_id": "math_tester",
        "thinking_level": "deep"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data.get("thinking_level") == "deep"
    assert "reply" in data
    assert "thoughts" in data
