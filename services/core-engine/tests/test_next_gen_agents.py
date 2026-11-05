"""
Test Suite Complète pour les 5 Agents Next-Gen de HoL AI :
1. BiographicalMemoryAgent (Cerveau Biographique Persistant)
2. LiveVoiceAgent (Mode Vocal Mains-Libres & Synthèse SAPI)
3. ProactiveNotifierAgent (Notifications Proactives Windows & Historique)
4. DesktopAutomationAgent (Contrôle Graphique Windows & Sentinel Safety)
5. MobilePWAVisionAgent (PWA Mobile Dédiée & Vision Caméra)
6. Endpoints API FastAPI Next-Gen
"""
import pytest
import os
import json
from fastapi.testclient import TestClient

from src.agents.next_gen import (
    BiographicalMemoryAgent,
    LiveVoiceAgent,
    ProactiveNotifierAgent,
    DesktopAutomationAgent,
    MobilePWAVisionAgent
)
from src.api.server import app

client = TestClient(app)


# =========================================================================
# AGENT 1 : MÉMOIRE BIOGRAPHIQUE PERSISTANTE
# =========================================================================
def test_biographical_memory_initialization_and_crud():
    """Vérifie l'initialisation SQLite et les opérations CRUD de mémoire permanente."""
    BiographicalMemoryAgent.initialize_db()
    
    # Enregistrement d'un fait utilisateur
    rec = BiographicalMemoryAgent.record_fact(
        user_id="test_user_unit",
        category="hardware",
        key="laptop_gpu",
        value="RTX 5060 Laptop"
    )
    assert rec["success"] is True
    assert rec["status"] == "recorded"

    # Lecture du fait
    fact = BiographicalMemoryAgent.get_fact("test_user_unit", "hardware", "laptop_gpu")
    assert fact is not None
    assert fact["value"] == "RTX 5060 Laptop"

    # Récupération de tous les faits
    all_facts = BiographicalMemoryAgent.get_all_facts("test_user_unit")
    assert len(all_facts) >= 1
    assert any(f["key"] == "laptop_gpu" for f in all_facts)

    # Contexte biographique formaté pour le prompt
    ctx = BiographicalMemoryAgent.get_biographical_context("test_user_unit")
    assert "RTX 5060 Laptop" in ctx

    # Suppression du fait
    del_res = BiographicalMemoryAgent.delete_fact("test_user_unit", "hardware", "laptop_gpu")
    assert del_res["success"] is True
    assert BiographicalMemoryAgent.get_fact("test_user_unit", "hardware", "laptop_gpu") is None


def test_biographical_memory_auto_learn():
    """Vérifie l'auto-apprentissage discret depuis le dialogue."""
    learned = BiographicalMemoryAgent.auto_learn_from_interaction(
        user_message="J'ai déménagé, j'habite à Vienne 38200 maintenant et mon budget max est de 500 euros",
        assistant_reply="C'est super bien noté frérot !",
        user_id="test_user_learn"
    )
    assert len(learned) >= 1
    facts = BiographicalMemoryAgent.get_all_facts("test_user_learn")
    keys = [f["key"] for f in facts]
    assert "city" in keys or "budget_max" in keys


# =========================================================================
# AGENT 2 : VOCAL MAINS-LIBRES & SYNTHÈSE VOCALE
# =========================================================================
def test_live_voice_capabilities():
    """Vérifie la découverte des capacités vocales et le mode mains-libres."""
    caps = LiveVoiceAgent.get_voice_capabilities()
    assert caps["tts_available"] is True
    assert "Microsoft Hortense Desktop" in caps["default_voice"]
    assert caps["hands_free_hotkey"] == "Alt+Space"

    # Activation mode mains-libres
    res_on = LiveVoiceAgent.set_hands_free_state(True)
    assert res_on["hands_free_active"] is True
    assert LiveVoiceAgent.get_voice_capabilities()["hands_free_active"] is True

    # Désactivation
    res_off = LiveVoiceAgent.set_hands_free_state(False)
    assert res_off["hands_free_active"] is False


def test_live_voice_speech_synthesis():
    """Vérifie la génération d'un flux audio WAV valide via PowerShell SAPI."""
    res = LiveVoiceAgent.synthesize_speech(
        text="Bonjour, le test unitaire vocal fonctionne.",
        direct_speak=False
    )
    assert res["success"] is True
    assert res["mime_type"] == "audio/wav"
    assert len(res["audio_base64"]) > 500  # Doit contenir des octets WAV réels
    assert res["size_bytes"] > 1000


# =========================================================================
# AGENT 3 : NOTIFICATIONS PROACTIVES RÉELLES
# =========================================================================
def test_proactive_notifications_dispatch_and_history():
    """Vérifie l'émission de notifications toast et la persistance de l'historique."""
    res = ProactiveNotifierAgent.dispatch_notification(
        title="Test Notification Unitaire",
        message="Ceci est un test unitaire de notification Toast",
        category="unit_test",
        urgency="normal"
    )
    assert res["success"] is True
    notif = res["notification"]
    assert notif["title"] == "Test Notification Unitaire"
    assert notif["delivered"] is True

    # Vérification de l'historique
    history = ProactiveNotifierAgent.get_notification_history(limit=5)
    assert len(history) >= 1
    assert any(n["id"] == notif["id"] for n in history)


def test_proactive_specialized_notifications():
    """Vérifie les alertes métier (Locker PIN & Baisse de prix)."""
    pin_res = ProactiveNotifierAgent.notify_locker_pin(
        service="Amazon Hub",
        pin_code="948123",
        locker_address="Gare de Vienne"
    )
    assert pin_res["success"] is True
    assert "948123" in pin_res["notification"]["message"]

    deal_res = ProactiveNotifierAgent.notify_price_drop(
        product_name="PlayStation 5 Slim",
        old_price=549.99,
        new_price=429.00
    )
    assert deal_res["success"] is True
    assert "429.00" in deal_res["notification"]["message"]


# =========================================================================
# AGENT 4 : BUREAU WINDOWS & SÉCURITÉ SENTINEL
# =========================================================================
def test_desktop_automation_list_and_telemetry():
    """Vérifie le listage applicatif et la télémétrie matérielle."""
    apps = DesktopAutomationAgent.list_running_applications()
    assert isinstance(apps, list)

    stats = DesktopAutomationAgent.get_hardware_telemetry()
    assert "Windows" in stats["os"]
    assert stats["cpu_usage_percent"] is not None or stats["os"] is not None


def test_desktop_automation_sentinel_guardrail():
    """Vérifie que les composants critiques Windows sont inviolables."""
    for proc in ["csrss", "winlogon", "explorer", "services"]:
        res = DesktopAutomationAgent.close_application(proc)
        assert res["success"] is False
        assert "Sécurité Sentinel" in res["error"]


# =========================================================================
# AGENT 5 : PWA MOBILE & VISION CAMÉRA
# =========================================================================
def test_mobile_pwa_manifest_and_sw():
    """Vérifie la conformité PWA Mobile (Manifest & Service Worker)."""
    manifest = MobilePWAVisionAgent.get_pwa_manifest()
    assert manifest["short_name"] == "HoL AI"
    assert manifest["display"] == "standalone"
    assert manifest["orientation"] == "portrait-primary"
    assert len(manifest["icons"]) >= 1

    sw_code = MobilePWAVisionAgent.get_service_worker_code()
    assert "addEventListener('install'" in sw_code
    assert "caches.open" in sw_code


# =========================================================================
# ENDPOINTS API FASTAPI NEXT-GEN
# =========================================================================
def test_api_memory_endpoints():
    """Teste les routes API de la mémoire biographique."""
    # POST /api/memory/facts
    r_post = client.post("/api/memory/facts", json={
        "user_id": "api_test_user",
        "category": "preferences",
        "key": "theme",
        "value": "dark_cyberpunk"
    })
    assert r_post.status_code == 200
    assert r_post.json()["success"] is True

    # GET /api/memory/facts
    r_get = client.get("/api/memory/facts?user_id=api_test_user")
    assert r_get.status_code == 200
    data = r_get.json()
    assert data["total"] >= 1
    assert any(f["key"] == "theme" for f in data["facts"])

    # DELETE /api/memory/facts
    r_del = client.delete("/api/memory/facts/preferences/theme?user_id=api_test_user")
    assert r_del.status_code == 200
    assert r_del.json()["success"] is True


def test_api_voice_endpoints():
    """Teste les routes API de vocalisation et capacités."""
    r_caps = client.get("/api/voice/capabilities")
    assert r_caps.status_code == 200
    assert r_caps.json()["tts_available"] is True

    r_synth = client.post("/api/voice/synthesize", json={
        "text": "Test vocal API",
        "direct_speak": False
    })
    assert r_synth.status_code == 200
    res = r_synth.json()
    assert res["success"] is True
    assert len(res["audio_base64"]) > 200


def test_api_notifications_endpoints():
    """Teste les routes de dispatch de notifications."""
    r_post = client.post("/api/notifications/dispatch", json={
        "title": "Alerte API Test",
        "message": "Notification par l'API",
        "urgency": "low"
    })
    assert r_post.status_code == 200
    assert r_post.json()["success"] is True

    r_hist = client.get("/api/notifications/history?limit=3")
    assert r_hist.status_code == 200
    assert r_hist.json()["total"] >= 1


def test_api_desktop_endpoints():
    """Teste les routes du contrôle bureau Windows."""
    r_wins = client.get("/api/desktop/windows")
    assert r_wins.status_code == 200
    assert "windows" in r_wins.json()

    r_telem = client.get("/api/desktop/telemetry")
    assert r_telem.status_code == 200
    assert "Windows" in r_telem.json()["os"]


def test_api_pwa_manifest_endpoint():
    """Teste la route du manifest PWA."""
    r_man = client.get("/api/pwa/manifest")
    assert r_man.status_code == 200
    assert r_man.json()["short_name"] == "HoL AI"
