"""
Comprehensive Integration Test Suite for HoL AI Conversation Persistence (Requirement R2).
Tests SQLite WAL store, CRUD, chronological bucketing, auto-titling,
Markdown/JSON exports, REST endpoints, real-time chat hooks, and context restoration.
"""
import os
import time
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from src.api.server import app
from src.services.conversation_store import ConversationStore
from src.services.session_manager import SessionManager


@pytest.fixture
def temp_store(tmp_path):
    """Fournit une instance isolée de ConversationStore dans un répertoire temporaire."""
    db_file = tmp_path / "test_conversations.db"
    store = ConversationStore(str(db_file))
    return store


@pytest.fixture
def test_client():
    """Client de test FastAPI avec exécution du cycle de vie lifespan."""
    with TestClient(app) as client:
        yield client


# ============================================================================
# 1. Tests Unitaires du ConversationStore & Mode WAL
# ============================================================================

@pytest.mark.asyncio
async def test_conversation_store_initialization_and_wal(temp_store):
    """Vérifie l'initialisation du schéma SQLite et l'activation du mode WAL."""
    await temp_store.init_db()
    assert os.path.exists(temp_store.db_path)

    # Vérification du mode journal WAL
    with temp_store._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode;")
        mode = cursor.fetchone()[0]
        assert mode.lower() == "wal"

        # Vérification de l'existence des tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        assert "conversations" in tables
        assert "messages" in tables


@pytest.mark.asyncio
async def test_conversation_crud_lifecycle(temp_store):
    """Vérifie le cycle de vie complet d'une conversation (Create, Read, Update, Delete)."""
    await temp_store.init_db()

    # 1. Create
    conv = await temp_store.create_conversation(
        id="conv_lifecycle_001",
        user_id="user_test",
        title="Discussion initiale",
        is_pinned=False,
        is_archived=False,
        metadata={"tags": ["tech", "ai"]}
    )
    assert conv["id"] == "conv_lifecycle_001"
    assert conv["title"] == "Discussion initiale"
    assert conv["is_pinned"] is False
    assert conv["is_archived"] is False
    assert conv["metadata"]["tags"] == ["tech", "ai"]

    # 2. Read
    fetched = await temp_store.get_conversation("conv_lifecycle_001")
    assert fetched is not None
    assert fetched["id"] == "conv_lifecycle_001"
    assert fetched["title"] == "Discussion initiale"

    # 3. Update
    updated = await temp_store.update_conversation(
        "conv_lifecycle_001",
        title="Discussion renommée",
        is_pinned=True,
        is_archived=False
    )
    assert updated["title"] == "Discussion renommée"
    assert updated["is_pinned"] is True

    # 4. Delete
    deleted = await temp_store.delete_conversation("conv_lifecycle_001")
    assert deleted is True

    # Vérification post-suppression
    post_get = await temp_store.get_conversation("conv_lifecycle_001")
    assert post_get is None


@pytest.mark.asyncio
async def test_messages_persistence_and_cascading(temp_store):
    """Vérifie l'ajout de messages, la sérialisation des cartes et pensées, et la suppression en cascade."""
    await temp_store.init_db()

    conv_id = "conv_cascade_002"
    await temp_store.create_conversation(id=conv_id, title="Chat avec cartes")

    # Ajout d'un message utilisateur
    m1 = await temp_store.add_message(
        conversation_id=conv_id,
        role="user",
        content="Trouve-moi une RTX 4070"
    )
    assert m1["role"] == "user"
    assert m1["content"] == "Trouve-moi une RTX 4070"

    # Ajout d'une réponse assistant avec cartes et trace de réflexion
    cards = [
        {
            "type": "deal",
            "data": {
                "product": "Asus Dual GeForce RTX 4070",
                "current_drop_price_eur": 589.99,
                "platform": "Cdiscount"
            }
        }
    ]
    m2 = await temp_store.add_message(
        conversation_id=conv_id,
        role="assistant",
        content="Voici la meilleure offre RTX 4070 trouvée !",
        cards=cards,
        thoughts="Recherche e-commerce effectuée sur Cdiscount et Amazon...",
        thinking_level="deep"
    )
    assert m2["role"] == "assistant"
    assert len(m2["cards"]) == 1
    assert m2["cards"][0]["data"]["platform"] == "Cdiscount"
    assert m2["thoughts"] == "Recherche e-commerce effectuée sur Cdiscount et Amazon..."

    # Vérification de la récupération complète
    full_conv = await temp_store.get_conversation(conv_id, include_messages=True)
    assert len(full_conv["messages"]) == 2
    assert full_conv["turns_count"] == 2
    assert full_conv["messages"][1]["cards"][0]["data"]["current_drop_price_eur"] == 589.99

    # Suppression de la conversation et vérification de la cascade SQLite
    await temp_store.delete_conversation(conv_id)
    with temp_store._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM messages WHERE conversation_id = ?", (conv_id,))
        count = cursor.fetchone()[0]
        assert count == 0


@pytest.mark.asyncio
async def test_chronological_bucketing(temp_store):
    """Vérifie le classement chronologique exact (today, last_7_days, last_30_days, older, pinned)."""
    await temp_store.init_db()
    now = time.time()

    # 1. Discussion d'aujourd'hui
    c_today = await temp_store.create_conversation(id="conv_today", title="Chat Aujourd'hui")
    await temp_store.add_message("conv_today", "user", "Message du jour", timestamp=now)

    # 2. Discussion d'il y a 3 jours (7 derniers jours)
    t_7d = now - (3 * 86400)
    await temp_store.create_conversation(id="conv_7d", title="Chat 3 jours")
    await temp_store.add_message("conv_7d", "user", "Message 3 jours", timestamp=t_7d)
    with temp_store._get_connection() as conn:
        conn.execute("UPDATE conversations SET updated_at = ? WHERE id = 'conv_7d'", (t_7d,))
        conn.commit()

    # 3. Discussion d'il y a 15 jours (30 jours)
    t_30d = now - (15 * 86400)
    await temp_store.create_conversation(id="conv_30d", title="Chat 15 jours")
    await temp_store.add_message("conv_30d", "user", "Message 15 jours", timestamp=t_30d)
    with temp_store._get_connection() as conn:
        conn.execute("UPDATE conversations SET updated_at = ? WHERE id = 'conv_30d'", (t_30d,))
        conn.commit()

    # 4. Discussion d'il y a 45 jours (older)
    t_older = now - (45 * 86400)
    await temp_store.create_conversation(id="conv_older", title="Chat Ancien")
    await temp_store.add_message("conv_older", "user", "Message ancien", timestamp=t_older)
    with temp_store._get_connection() as conn:
        conn.execute("UPDATE conversations SET updated_at = ? WHERE id = 'conv_older'", (t_older,))
        conn.commit()

    # 5. Discussion épinglée
    await temp_store.create_conversation(id="conv_pinned", title="Chat Épinglé", is_pinned=True)

    result = await temp_store.list_conversations()
    convs = {c["id"]: c for c in result["conversations"]}

    assert convs["conv_today"]["time_bucket"] == "today"
    assert convs["conv_7d"]["time_bucket"] == "last_7_days"
    assert convs["conv_30d"]["time_bucket"] == "last_30_days"
    assert convs["conv_older"]["time_bucket"] == "older"
    assert convs["conv_pinned"]["is_pinned"] is True

    # Vérification des compteurs de buckets
    buckets = result["buckets"]
    assert buckets["today"] >= 1
    assert buckets["last_7_days"] >= 1
    assert buckets["last_30_days"] >= 1
    assert buckets["older"] >= 1


@pytest.mark.asyncio
async def test_auto_title_nlp_generation(temp_store):
    """Vérifie la génération automatique de titre concise et pertinente sans mots vides."""
    await temp_store.init_db()

    conv_id = "conv_titling_test"
    await temp_store.create_conversation(id=conv_id, title="Nouvelle discussion")

    # Simulation d'une requête utilisateur avec formules de politesse
    msg = "Salut, peux-tu me trouver un PC portable gamer Lenovo LOQ avec RTX 4060 pas cher stp ?"
    await temp_store.add_message(conv_id, role="user", content=msg)

    generated_title = await temp_store.generate_title_from_first_message(conv_id)
    assert generated_title != "Nouvelle discussion"
    assert len(generated_title) <= 40
    assert not any(w in generated_title.lower().split() for w in ["salut", "peux-tu", "stp", "me"])

    # Vérification que le titre a bien été persisté en base
    fetched = await temp_store.get_conversation(conv_id)
    assert fetched["title"] == generated_title


@pytest.mark.asyncio
async def test_exports_markdown_and_json(temp_store):
    """Vérifie l'exportation structurée en Markdown et en JSON."""
    await temp_store.init_db()

    conv_id = "conv_export_test"
    await temp_store.create_conversation(id=conv_id, title="Comparatif Smartphone")

    await temp_store.add_message(conv_id, "user", "iPhone 15 vs Galaxy S24 ?")
    await temp_store.add_message(
        conv_id,
        "assistant",
        "L'iPhone 15 excelle en vidéo et le Galaxy S24 offre un écran 120Hz adaptatif.",
        cards=[{"type": "deal", "data": {"product": "Galaxy S24", "current_drop_price_eur": 699.0, "platform": "Amazon"}}],
        thoughts="Comparaison d'écrans et d'autonomie..."
    )

    # 1. Export Markdown
    md = await temp_store.export_conversation_markdown(conv_id)
    assert "# Comparatif Smartphone" in md
    assert "### 👤 Utilisateur" in md
    assert "### 🤖 HoL AI" in md
    assert "iPhone 15 vs Galaxy S24 ?" in md
    assert "> **Raisonnement interne :**" in md
    assert "Galaxy S24" in md

    # 2. Export JSON
    js = await temp_store.export_conversation_json(conv_id)
    assert js["version"] == "1.0"
    assert js["conversation"]["id"] == conv_id
    assert len(js["conversation"]["messages"]) == 2
    assert js["conversation"]["messages"][1]["cards"][0]["data"]["platform"] == "Amazon"


# ============================================================================
# 2. Tests d'Intégration des Endpoints REST FastAPI
# ============================================================================

def test_api_conversations_rest_endpoints(test_client):
    """Vérifie tous les endpoints REST /api/conversations (GET list, POST, GET id, PATCH, DELETE, export)."""
    # 1. Création d'une conversation via POST
    create_payload = {
        "title": "Test REST API Persistence",
        "user_id": "api_tester",
        "is_pinned": False,
        "is_archived": False
    }
    res_post = test_client.post("/api/conversations", json=create_payload)
    assert res_post.status_code == 200
    conv_data = res_post.json()
    conv_id = conv_data["id"]
    assert conv_data["title"] == "Test REST API Persistence"

    # 2. Récupération dans la liste
    res_list = test_client.get("/api/conversations?user_id=api_tester")
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert any(c["id"] == conv_id for c in list_data["conversations"])
    assert "buckets" in list_data

    # 3. Récupération unitaire par ID
    res_get = test_client.get(f"/api/conversations/{conv_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == conv_id

    # 4. Mise à jour via PATCH (Renommer et Épingler)
    patch_payload = {
        "title": "Titre mis à jour",
        "is_pinned": True,
        "is_archived": False
    }
    res_patch = test_client.patch(f"/api/conversations/{conv_id}", json=patch_payload)
    assert res_patch.status_code == 200
    assert res_patch.json()["title"] == "Titre mis à jour"
    assert res_patch.json()["is_pinned"] is True

    # 5. Export Markdown
    res_export_md = test_client.get(f"/api/conversations/{conv_id}/export?format=markdown")
    assert res_export_md.status_code == 200
    assert "text/markdown" in res_export_md.headers.get("content-type", "")
    assert "# Titre mis à jour" in res_export_md.text

    # 6. Export JSON
    res_export_json = test_client.get(f"/api/conversations/{conv_id}/export?format=json")
    assert res_export_json.status_code == 200
    assert res_export_json.json()["conversation"]["id"] == conv_id

    # 7. Suppression via DELETE
    res_del = test_client.delete(f"/api/conversations/{conv_id}")
    assert res_del.status_code == 200
    assert res_del.json()["success"] is True

    # 8. Vérification 404
    res_get_404 = test_client.get(f"/api/conversations/{conv_id}")
    assert res_get_404.status_code == 404


def test_realtime_chat_persistence_hook(test_client):
    """Vérifie que les échanges conversationnels via /api/chat sont persistés en temps réel."""
    session_id = f"test_session_hook_{int(time.time() * 1000):x}"

    chat_payload = {
        "message": "Bonjour HoL AI, retiens que mon sport préféré est le padel",
        "session_id": session_id,
        "user_id": "test_sports_user",
        "thinking_level": "fast"
    }

    res = test_client.post("/api/chat", json=chat_payload)
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data

    # Vérification que la conversation a été persistée dans le store
    res_conv = test_client.get(f"/api/conversations/{session_id}")
    assert res_conv.status_code == 200
    conv_data = res_conv.json()

    # Doit contenir au moins 2 messages (l'utilisateur et l'assistant)
    messages = conv_data["messages"]
    assert len(messages) >= 2
    assert messages[0]["role"] == "user"
    assert "padel" in messages[0]["content"].lower()
    assert messages[1]["role"] == "assistant"
    assert len(messages[1]["content"]) > 0

    # Nettoyage
    test_client.delete(f"/api/conversations/{session_id}")


def test_realtime_chat_stream_persistence_hook(test_client):
    """Vérifie que les requêtes SSE en streaming via /api/chat/stream sont également persistées."""
    session_id = f"test_stream_hook_{int(time.time() * 1000):x}"

    stream_payload = {
        "message": "Donne-moi un mot d'encouragement rapide",
        "session_id": session_id,
        "user_id": "stream_user",
        "thinking_level": "fast"
    }

    res = test_client.post("/api/chat/stream", json=stream_payload)
    assert res.status_code == 200
    body_text = res.text
    assert "data:" in body_text

    # Vérification que les messages du flux ont été enregistrés dans la base
    res_conv = test_client.get(f"/api/conversations/{session_id}")
    assert res_conv.status_code == 200
    conv_data = res_conv.json()
    messages = conv_data["messages"]
    assert len(messages) >= 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"

    # Nettoyage
    test_client.delete(f"/api/conversations/{session_id}")


def test_context_restoration_syncs_session_manager(test_client):
    """Vérifie que GET /api/conversations/{id} recharge fidèlement l'état dans SessionManager."""
    session_id = f"test_restore_sync_{int(time.time() * 1000):x}"

    # Envoi d'un premier message
    test_client.post("/api/chat", json={
        "message": "Trouve-moi un iPhone 14 Pro sur Amazon",
        "session_id": session_id,
        "user_id": "sync_tester"
    })

    # Effacer l'état en mémoire vive pour simuler un redémarrage ou changement de page
    SessionManager._sessions.pop(session_id, None)
    assert session_id not in SessionManager._sessions

    # Appel de reprise de contexte GET /api/conversations/{id}
    res_restore = test_client.get(f"/api/conversations/{session_id}")
    assert res_restore.status_code == 200

    # Vérifier que SessionManager a été immédiatement réhydraté
    assert session_id in SessionManager._sessions
    restored_session = SessionManager._sessions[session_id]
    assert len(restored_session.history) >= 2
    assert restored_session.history[0].role == "user"
    assert "iPhone 14 Pro" in restored_session.history[0].content

    # Nettoyage
    test_client.delete(f"/api/conversations/{session_id}")
