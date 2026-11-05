"""
Tests d'intégration de l'API FastAPI et du serveur WebSocket HoL AI.
"""
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

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


def test_api_system_state(client):
    """Vérifie l'état initial du cluster et des nœuds du canevas."""
    response = client.get("/api/state")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ONLINE"
    assert "nodes" in data
    assert len(data["nodes"]) >= 1


def test_api_agents_status(client):
    """Vérifie que les 6 agents et le manager sont en ligne."""
    response = client.get("/api/agents/status")
    assert response.status_code == 200
    agents = response.json()
    assert len(agents) == 7
    for ag in agents:
        assert ag["status"] == "ONLINE"


def test_api_orchestrate_and_canvas_node_creation(client):
    """Vérifie l'orchestration complète via l'API REST et la génération des blocs sur le canevas."""
    payload = {
        "intent": "Suis mon colis UPS 1Z99283749281, calcule ma marge sur le produit vendu à 140€ (coût 48€) et ajoute la synthèse sur le canevas",
        "user_id": "tester_1",
        "canvas_id": "workspace_test"
    }
    response = client.post("/api/orchestrate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "orchestration" in data
    assert data["orchestration"]["success"] is True
    assert len(data["canvas_nodes"]) >= 3  # Initial + Colis + Marge
    assert len(data["new_node_ids"]) >= 2


def test_muse_chat_ps5_deal_watch(client):
    """Pilier 1 & 3 : Surveillance Amazon PS5 en arrière-plan et achat 1-clic."""
    payload = {
        "message": "Surveille Amazon pour me choper une PS5 pas chère",
        "user_id": "mobile_tester"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert any(c["type"] == "deal" for c in data["cards"])


def test_muse_chat_recipe_to_grocery(client):
    """Pilier 2 : Vidéo recette Instagram vers liste de courses ordonnée par rayons."""
    payload = {
        "message": "Transforme cette recette Instagram de pâtes crémeuses en liste de courses",
        "user_id": "mobile_tester"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert any(c["type"] == "grocery" for c in data["cards"])


def test_muse_chat_restaurant_booking(client):
    """Pilier 1 & 5 : Réservation avec validation Human-in-the-Loop."""
    payload = {
        "message": "Réserve une table pour 2 samedi soir chez un bon italien à Paris",
        "user_id": "mobile_tester"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert any(c["type"] == "reservation" for c in data["cards"])


def test_muse_chat_inbox_cleaner(client):
    """Pilier 2 : Tri intelligent de la boîte mail et brouillons prêts."""
    payload = {
        "message": "Trie mes emails et prépare les réponses urgentes",
        "user_id": "mobile_tester"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert any(c["type"] == "inbox" for c in data["cards"])


def test_muse_chat_cdiscount_laptop(client):
    """Vérifie que la requête Cdiscount ne déclenche JAMAIS une fausse réservation de restaurant."""
    payload = {
        "message": "vas sur cdiscount et trouve moi le pc portable le moin chère avec une 5060",
        "user_id": "mobile_tester"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    # Ne doit jamais avoir de carte reservation !
    assert not any(c["type"] == "reservation" for c in data["cards"])
    # Doit avoir une carte deal avec Cdiscount
    deal_cards = [c for c in data["cards"] if c["type"] == "deal"]
    assert len(deal_cards) == 1
    assert "Cdiscount" in deal_cards[0]["data"]["platform"]
    assert "5060" in deal_cards[0]["data"]["product"] or "4060" in deal_cards[0]["data"]["product"]


def test_muse_chat_calendar_management(client):
    """Pilier 2 : Détection de conflits et optimisation d'agenda."""
    payload = {
        "message": "Optimise mon calendrier et règle les conflits de réunions",
        "user_id": "mobile_tester"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert any(c["type"] == "calendar" for c in data["cards"])


def test_muse_action_execution(client):
    """Pilier 5 : Validation Human-in-the-Loop et signature cryptographique."""
    payload = {
        "action_id": "act_test_checkout_01",
        "action_type": "ONE_CLICK_PURCHASE",
        "payload": {"product": "PS5 Slim", "price": 429.0}
    }
    response = client.post("/api/actions/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["tx_hash"].startswith("0x")


def test_muse_background_status(client):
    """Pilier 3 : Surveillance 24/7 en arrière-plan."""
    response = client.get("/api/background/status")
    assert response.status_code == 200
    data = response.json()
    assert data["active_missions_count"] >= 1


def test_muse_vault_sandbox_and_ledger(client):
    """Pilier 4 : Sandbox de code et registre d'audit de l'Enclave."""
    sandbox_res = client.post("/api/vault/sandbox", json={"code": "print(40 + 2)"})
    assert sandbox_res.status_code == 200
    assert sandbox_res.json()["stdout"] == "42"

    ledger_res = client.get("/api/vault/ledger")
    assert ledger_res.status_code == 200
    assert len(ledger_res.json()["ledger"]) >= 1


def test_pwa_static_routes(client):
    """Pilier 6 : Fichiers PWA installables pour mobile."""
    res_manifest = client.get("/manifest.json")
    assert res_manifest.status_code == 200
    assert "HoL AI" in res_manifest.json()["short_name"]

    res_sw = client.get("/sw.js")
    assert res_sw.status_code == 200
    assert "hol-ai" in res_sw.text


def test_canvas_upload_multipart_image(client):
    """Phase 1 Muse-X : Ingestion multimodale d'image et création de nœud spatial."""
    fake_image_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    files = {"file": ("mockup_design.png", fake_image_bytes, "image/png")}
    data = {"x": "250.0", "y": "180.0", "title": "Maquette Spatial OS"}

    response = client.post("/api/canvas/upload", files=files, data=data)
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    node = result["node"]
    assert node["type"] == "image"
    assert node["title"] == "Maquette Spatial OS"
    assert node["position"]["x"] == 250.0
    assert node["position"]["y"] == 180.0
    assert "data" in node
    assert "thumbnail" in node["data"]


def test_canvas_upload_invoice_pdf(client):
    """Phase 1 Muse-X : Ingestion de facture PDF, OCR Agent 2 et création de nœud spatial."""
    fake_pdf = b"%PDF-1.4 Fake Invoice Shenzhen Tech 2400 EUR"
    files = {"file": ("facture_shenzhen_2026.pdf", fake_pdf, "application/pdf")}

    response = client.post("/api/canvas/upload", files=files)
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    node = result["node"]
    assert node["type"] == "invoice"
    assert "Shenzhen" in node["data"]["parsed_data"]["supplier"]
    assert node["data"]["parsed_data"]["total_ht"] == 2400.0


def test_canvas_upload_json_note(client):
    """Phase 1 Muse-X : Création d'un nœud spatial textuel / note via JSON."""
    payload = {
        "filename": "note_strategie.md",
        "title": "Stratégie Lancement Muse-X",
        "content": "Feuille de route Phase 1 : Canevas 2D infini 60 FPS opérationnel.",
        "content_type": "text/markdown",
        "x": 300.0,
        "y": 450.0
    }
    response = client.post("/api/canvas/upload", json=payload)
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    node = result["node"]
    assert node["type"] == "note"
    assert node["title"] == "Stratégie Lancement Muse-X"
    assert node["position"]["x"] == 300.0
    assert node["position"]["y"] == 450.0


def test_canvas_websocket_move_and_connect(client):
    """Phase 1 Muse-X : WebSocket temps réel pour MOVE_NODE, CONNECT_NODES et DELETE_NODE."""
    with client.websocket_connect("/ws/canvas") as websocket:
        # 1. Réception initiale
        init_data = websocket.receive_json()
        assert init_data["event"] == "INITIAL_STATE"
        nodes = init_data["data"]["nodes"]
        assert len(nodes) >= 1
        target_node = nodes[0]
        node_id = target_node["id"]

        # 2. Test MOVE_NODE
        websocket.send_json({
            "action": "MOVE_NODE",
            "node_id": node_id,
            "position": {"x": 777.0, "y": 888.0}
        })
        moved_event = websocket.receive_json()
        assert moved_event["event"] == "NODE_MOVED"
        assert moved_event["data"]["node_id"] == node_id
        assert moved_event["data"]["position"]["x"] == 777.0

        # 3. Test CONNECT_NODES
        if len(nodes) >= 2:
            source_id = nodes[0]["id"]
            dest_id = nodes[1]["id"]
            websocket.send_json({
                "action": "CONNECT_NODES",
                "source_id": source_id,
                "target_id": dest_id
            })
            connect_event = websocket.receive_json()
            assert connect_event["event"] == "NODES_CONNECTED"




