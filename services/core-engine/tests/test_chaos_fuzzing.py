"""
Chaos Fuzzing & Destructive Security Testing Suite for Muse-X OS.
Tests robustness against corrupt payloads, path traversal, XSS injections,
out-of-bounds numbers, malformed JSON, and WebSocket flooding.
"""
import sys
import math
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.api.server import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


# ============================================================================
# 1. POST /api/canvas/upload FUZZING & SECURITY
# ============================================================================

def test_canvas_upload_path_traversal_unix(client):
    """Vérifie que les tentatives de traversée de répertoire (/etc/passwd) sont neutralisées."""
    files = {"file": ("../../../../etc/passwd", b"root:x:0:0:root:/root:/bin/bash", "text/plain")}
    response = client.post("/api/canvas/upload", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # Le nom de fichier doit être strictement nettoyé sans chemin relatif
    node = data["node"]
    assert "etc" not in node["title"]
    assert ".." not in node["title"]
    assert ".." not in node["data"]["filename"]
    assert node["data"]["filename"] == "passwd"


def test_canvas_upload_path_traversal_windows(client):
    """Vérifie que les chemins Windows absolus ou relatifs sont neutralisés."""
    files = {"file": ("..\\..\\..\\Windows\\System32\\calc.exe", b"MZ_FAKE_PE_HEADER", "application/octet-stream")}
    response = client.post("/api/canvas/upload", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "\\" not in data["node"]["data"]["filename"]
    assert ".." not in data["node"]["data"]["filename"]
    assert data["node"]["data"]["filename"] == "calc.exe"


def test_canvas_upload_5000_char_filename(client):
    """Vérifie qu'un nom de fichier astronomique de 5000 caractères ne provoque aucun crash 500."""
    long_name = ("a" * 4990) + ".txt"
    # Test via JSON
    response_json = client.post("/api/canvas/upload", json={"filename": long_name, "content": "Contenu test"})
    assert response_json.status_code in [200, 400, 422]
    if response_json.status_code == 200:
        data = response_json.json()
        assert data["success"] is True
        assert len(data["node"]["data"]["filename"]) <= 200

    # Test via multipart form-data (rejeté en 400 par le parser de headers ou nettoyé en 200)
    files = {"file": (long_name, b"Contenu test", "text/plain")}
    response = client.post("/api/canvas/upload", files=files)
    assert response.status_code in [200, 400, 422]


def test_canvas_upload_zero_byte_empty_file(client):
    """Vérifie qu'un fichier de 0 octet ne provoque aucune exception 500."""
    files = {"file": ("empty.txt", b"", "text/plain")}
    response = client.post("/api/canvas/upload", files=files)
    assert response.status_code in [200, 400]
    if response.status_code == 200:
        data = response.json()
        assert data["success"] is True


def test_canvas_upload_corrupt_binary(client):
    """Vérifie qu'un fichier binaire corrompu (octets nuls, headers invalides) est traité sans crash."""
    corrupt_bytes = b"\x00\xff\xfe\x00\x01\x88\x99\xaa\xbb\xcc\xdd\xee\xff" * 100
    files = {"file": ("corrupt.png", corrupt_bytes, "image/png")}
    response = client.post("/api/canvas/upload", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_canvas_upload_xss_script_tags(client):
    """Vérifie que les balises <script> et SVG malveillantes sont assainies dans les titres et contenus."""
    payload = {
        "filename": "innocent.txt",
        "title": "<script>alert('XSS_POC')</script>",
        "content": "<svg onload='alert(1)'>Contenu malveillant</svg>",
        "content_type": "text/html"
    }
    response = client.post("/api/canvas/upload", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # Le titre ne doit plus contenir de balise script non échappée
    assert "<script>" not in data["node"]["title"]


def test_canvas_upload_nan_coordinates(client):
    """Vérifie que l'envoi de coordonnées NaN ou corrompues ne lève pas d'exception 500."""
    payload = {
        "filename": "test.txt",
        "content": "test",
        "x": "not_a_number",
        "y": "NaN"
    }
    response = client.post("/api/canvas/upload", json=payload)
    # Doit rejeter proprement avec 422 ou 400, JAMAIS 500
    assert response.status_code in [400, 422]


# ============================================================================
# 2. POST /api/cfo/margin FUZZING & OUT-OF-BOUNDS
# ============================================================================

def test_cfo_margin_invalid_types_string(client):
    """Vérifie que des types chaînes non convertibles renvoient 422 au lieu de 500."""
    payload = {
        "selling_price_ttc": "GRATUIT",
        "cost_price": "CENT_EUROS"
    }
    response = client.post("/api/cfo/margin", json=payload)
    assert response.status_code == 422


def test_cfo_margin_none_values(client):
    """Vérifie que l'envoi de valeurs null/None renvoie 422 au lieu de 500."""
    payload = {
        "selling_price_ttc": None,
        "cost_price": 50.0
    }
    response = client.post("/api/cfo/margin", json=payload)
    assert response.status_code == 422


def test_cfo_margin_zero_division_vat(client):
    """Vérifie que vat_rate = -1.0 ne déclenche pas de ZeroDivisionError (500)."""
    payload = {
        "selling_price_ttc": 100.0,
        "cost_price": 50.0,
        "vat_rate": -1.0
    }
    response = client.post("/api/cfo/margin", json=payload)
    # Rejet 422 / 400 ou calcul sécurisé
    assert response.status_code in [200, 400, 422]
    if response.status_code == 200:
        data = response.json()
        assert "net_margin_eur" in data


def test_cfo_margin_astronomical_numbers(client):
    """Vérifie que des valeurs astronomiques ne causent aucun dépassement de capacité."""
    payload = {
        "selling_price_ttc": 1e12,
        "cost_price": 1e11,
        "vat_rate": 0.20
    }
    response = client.post("/api/cfo/margin", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert math.isfinite(data["net_margin_eur"])


# ============================================================================
# 3. POST /api/cfo/receipt FUZZING & SPAM
# ============================================================================

def test_cfo_receipt_empty_body(client):
    """Vérifie qu'un corps JSON vide ou tous champs None ne provoque pas de 500."""
    payload = {}
    response = client.post("/api/cfo/receipt", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "invoice_number" in data


def test_cfo_receipt_none_amount(client):
    """Vérifie que amount_ttc: None ne plante pas float(None)."""
    payload = {
        "vendor": "Test Corp",
        "amount_ttc": None,
        "raw_text": None
    }
    response = client.post("/api/cfo/receipt", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["amount_ttc"] >= 0


def test_cfo_receipt_100k_chars_spam(client):
    """Vérifie qu'un texte de 100 000 caractères avec caractères d'échappement ne cause pas de DoS."""
    spam_text = "FACTURE REÇU TVA 20% TOTAL 150.00 EUR \n\r\t\\\"\'" * 2500  # ~100k chars
    payload = {
        "raw_text": spam_text,
        "vendor": "Spammer & Co"
    }
    response = client.post("/api/cfo/receipt", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "amount_ttc" in data
    assert data["amount_ttc"] > 0


def test_cfo_receipt_special_escape_characters(client):
    """Vérifie la robustesse face aux null bytes, tabulations et quotes."""
    payload = {
        "vendor": "ACME \x00 Corporation \r\n\t -- DROP TABLE receipts;",
        "raw_text": "Montant total: 99.99 € \x00 \x1b[31mRed Alert\x1b[0m"
    }
    response = client.post("/api/cfo/receipt", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "\x00" not in data["vendor"]


# ============================================================================
# 4. POST /api/sourcing/compare FUZZING
# ============================================================================

def test_sourcing_compare_unexpected_nested_json(client):
    """Vérifie que l'envoi d'objets imbriqués inattendus est rejeté avec 422 au lieu de 500."""
    payload = {
        "query": {"sub_object": {"nested": "laptop"}},
        "target_selling_price_ttc": 800.0
    }
    response = client.post("/api/sourcing/compare", json=payload)
    assert response.status_code == 422


def test_sourcing_compare_nan_price(client):
    """Vérifie que target_selling_price_ttc: NaN ne produit pas de 500."""
    payload = {
        "query": "PS5 Slim",
        "target_selling_price_ttc": "NaN"
    }
    response = client.post("/api/sourcing/compare", json=payload)
    assert response.status_code in [400, 422]


def test_sourcing_compare_empty_query(client):
    """Vérifie qu'une query vide est rejetée proprement."""
    payload = {"query": ""}
    response = client.post("/api/sourcing/compare", json=payload)
    assert response.status_code in [400, 422]


# ============================================================================
# 5. WEBSOCKET /ws/canvas CHAOS & ATTACK FRAMES
# ============================================================================

def test_websocket_non_json_frames(client):
    """Envoie des trames textuelles brutes non-JSON sans déconnecter sauvagement le serveur."""
    with client.websocket_connect("/ws/canvas") as ws:
        init_msg = ws.receive_json()
        assert init_msg["event"] == "INITIAL_STATE"

        # Rafale de payloads malformés
        ws.send_text("CECI N'EST PAS DU JSON")
        resp = ws.receive_json()
        assert resp["event"] in ["ERROR", "WARNING"]

        ws.send_text("{payload_incomplet: ")
        resp = ws.receive_json()
        assert resp["event"] in ["ERROR", "WARNING"]


def test_websocket_non_dict_payloads(client):
    """Envoie des payloads valides JSON mais qui ne sont pas des dictionnaires (listes, nombres, strings)."""
    with client.websocket_connect("/ws/canvas") as ws:
        ws.receive_json()  # INITIAL_STATE

        ws.send_text(json.dumps([1, 2, 3]))
        resp = ws.receive_json()
        assert resp["event"] == "ERROR"

        ws.send_text(json.dumps("string_payload"))
        resp = ws.receive_json()
        assert resp["event"] == "ERROR"

        ws.send_text(json.dumps(42))
        resp = ws.receive_json()
        assert resp["event"] == "ERROR"


def test_websocket_unknown_action(client):
    """Envoie des actions inconnues ou aléatoires."""
    with client.websocket_connect("/ws/canvas") as ws:
        ws.receive_json()  # INITIAL_STATE

        ws.send_json({"action": "DESTROY_CLUSTER_EXPLODE"})
        resp = ws.receive_json()
        assert resp["event"] in ["WARNING", "ERROR"]


def test_websocket_move_node_chaos(client):
    """MOVE_NODE sans node_id, avec positions NaN, infinies, types corrompus ou négatives."""
    with client.websocket_connect("/ws/canvas") as ws:
        ws.receive_json()  # INITIAL_STATE

        # 1. Sans node_id
        ws.send_json({"action": "MOVE_NODE", "position": {"x": 100, "y": 100}})
        resp = ws.receive_json()
        assert resp["event"] in ["ERROR", "WARNING"]

        # 2. Avec position non-dict
        ws.send_json({"action": "MOVE_NODE", "node_id": "node_welcome", "position": "nowhere"})
        resp = ws.receive_json()
        assert resp["event"] in ["ERROR", "WARNING"]

        # 3. Avec coordonnées string non numériques
        ws.send_json({"action": "MOVE_NODE", "node_id": "node_welcome", "position": {"x": "inf", "y": "NaN"}})
        resp = ws.receive_json()
        assert resp["event"] in ["ERROR", "WARNING"]

        # 4. Avec coordonnées négatives (doit être clampé ou géré sans crash)
        ws.send_json({"action": "MOVE_NODE", "node_id": "node_welcome", "position": {"x": -500, "y": -200}})
        # Soit broadcast clippé, soit message d'erreur/warning
        resp = ws.receive_json()
        assert resp["event"] in ["NODE_MOVED", "ERROR", "WARNING"]


def test_websocket_delete_nonexistent_node(client):
    """DELETE_NODE sur un nœud inexistant sans provoquer d'exception."""
    with client.websocket_connect("/ws/canvas") as ws:
        ws.receive_json()  # INITIAL_STATE

        ws.send_json({"action": "DELETE_NODE", "node_id": "node_fantome_qui_n_existe_pas_99999"})
        resp = ws.receive_json()
        assert resp["event"] in ["WARNING", "ERROR", "CANVAS_SYNC"]


# ============================================================================
# 6. POST /api/vault/sandbox & /api/chat SAFETY
# ============================================================================

def test_vault_sandbox_system_exit_defense(client):
    """Vérifie qu'une tentative de raise SystemExit() dans le sandbox ne tue pas le serveur."""
    code_attack = "raise [c for c in ().__class__.__bases__[0].__subclasses__() if c.__name__ == 'SystemExit'][0](0)"
    response = client.post("/api/vault/sandbox", json={"code": code_attack})
    assert response.status_code == 200
    data = response.json()
    assert data["execution_status"] == "ERROR"


def test_chat_null_bytes_and_empty(client):
    """Vérifie que /api/chat rejette les messages vides et filtre les null bytes sans crasher."""
    # Message vide
    res_empty = client.post("/api/chat", json={"message": "   "})
    assert res_empty.status_code in [400, 422]

    # Message avec null bytes
    res_null = client.post("/api/chat", json={"message": "Bonjour \x00 Muse, trouve moi un produit"})
    assert res_null.status_code == 200
