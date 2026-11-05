"""
Tests unitaires pour l'Agent 5 : Content Engine, Shot-Lists Virales & Drops d'Affiliation (Phase 4).
"""
import pytest
from uuid import uuid4
from src.core.contracts import (
    AgentID,
    ActionType,
    A2AMessage,
    SourceDescriptor,
    TargetDescriptor,
    ContextModel,
    PriorityEnum,
    StatusEnum
)
from src.agents.agent_5_content.service import ContentSocialAgent
from src.broker.stream_bus import StreamBus
import fakeredis.aioredis as fake_aioredis


@pytest.fixture
def content_agent():
    bus = StreamBus(redis_client=fake_aioredis.FakeRedis(decode_responses=True))
    return ContentSocialAgent(bus)


def test_analyze_trending_audios(content_agent):
    """Vérifie l'analyse d'audios tendances avec BPM, mood, virality score et cues de synchro."""
    audios = content_agent.analyze_trending_audios("ecommerce_tech")
    assert len(audios) >= 3
    for audio in audios:
        assert "title" in audio
        assert "bpm" in audio
        assert audio["bpm"] > 60
        assert "virality_score" in audio
        assert audio["virality_score"] >= 90
        assert "sync_cue" in audio
        assert "platforms" in audio
        assert any(p in ["TikTok", "Instagram Reels", "YouTube Shorts"] for p in audio["platforms"])


def test_generate_viral_hooks_multilingual(content_agent):
    """Vérifie la génération de hooks percutants multi-angles et polyglottes."""
    hooks_data = content_agent.generate_viral_hooks("Automatisation E-commerce")
    assert "primary_hook" in hooks_data
    assert "primary_hook_darija" in hooks_data
    assert "primary_hook_en" in hooks_data
    assert "primary_hook_es" in hooks_data

    # Vérification des variations psychologiques
    variations = hooks_data["hook_variations"]
    assert len(variations) >= 3
    types = [v["type"] for v in variations]
    assert any("Pattern Interrupt" in t for t in types)
    assert any("Aversion" in t for t in types)
    assert any("Secret" in t for t in types)

    # Vérification des versions Darija dans chaque variation
    for v in variations:
        assert "darija" in v and len(v["darija"]) > 5
        assert "fr" in v and len(v["fr"]) > 5


def test_generate_shot_list_four_plans(content_agent):
    """
    Vérifie le découpage précis en shot list (plan par plan) :
    - Plan 1 Hook (0-3s)
    - Plan 2 Problème (3-10s)
    - Plan 3 Démo (10-25s)
    - Plan 4 Call-to-action (25-30s)
    """
    shots = content_agent.generate_shot_list("Audit Marge & TVA")
    assert len(shots) == 4

    p1, p2, p3, p4 = shots[0], shots[1], shots[2], shots[3]

    # Plan 1 : Hook (0-3s)
    assert p1["plan_number"] == 1
    assert p1["timing"] == "0-3s"
    assert "Hook" in p1["phase"]
    assert "voiceover_fr" in p1 and "voiceover_darija" in p1
    assert "audio_cue" in p1

    # Plan 2 : Problème (3-10s)
    assert p2["plan_number"] == 2
    assert p2["timing"] == "3-10s"
    assert "Problème" in p2["phase"]

    # Plan 3 : Démo (10-25s)
    assert p3["plan_number"] == 3
    assert p3["timing"] == "10-25s"
    assert "Démo" in p3["phase"]

    # Plan 4 : CTA (25-30s)
    assert p4["plan_number"] == 4
    assert p4["timing"] == "25-30s"
    assert "Call-to-Action" in p4["phase"] or "CTA" in p4["phase"]


def test_generate_affiliate_drops_hacoo_dhgate_amazon(content_agent):
    """
    Vérifie la génération de drops d'affiliation pour canaux Telegram :
    - Formatage emojis soigné
    - Prix barré, prix flash, % réduction
    - Code promo
    - Liens affiliés Hacoo, DHgate, Amazon
    """
    # Test 1 : Hacoo
    drop_hacoo = content_agent.generate_affiliate_drop(
        product_name="Bape Sta Low White Camo",
        platform="Hacoo",
        original_price=95.00,
        promo_price=29.90,
        promo_code="MUSE20"
    )
    assert drop_hacoo["is_affiliate_drop"] is True
    assert "hacoo.app" in drop_hacoo["affiliate_url"]
    assert drop_hacoo["discount_percent"] >= 65
    assert drop_hacoo["promo_code"] == "MUSE20"
    caption_hacoo = drop_hacoo["telegram_caption"]
    assert "🔥 *DROP EXCLUSIF DU JOUR* 🔥" in caption_hacoo
    assert "Bape Sta Low White Camo" in caption_hacoo
    assert "`MUSE20`" in caption_hacoo
    assert "29.90€" in caption_hacoo

    # Test 2 : DHgate
    drop_dhgate = content_agent.generate_affiliate_drop(
        product_name="Montre Chronographe Céramique",
        platform="DHgate",
        original_price=150.00,
        promo_price=45.00,
        promo_code="DHGATE15"
    )
    assert "dhgate.com" in drop_dhgate["affiliate_url"]
    assert drop_dhgate["discount_percent"] == 70
    assert "DHgate Direct Factory" in drop_dhgate["platform"]

    # Test 3 : Amazon
    drop_amazon = content_agent.generate_affiliate_drop(
        product_name="Sony WH-1000XM5 Casque Réduction Bruit",
        platform="Amazon",
        original_price=399.00,
        promo_price=279.00,
        promo_code="AMZFLASH"
    )
    assert "amazon.fr" in drop_amazon["affiliate_url"]
    assert drop_amazon["discount_percent"] >= 30
    assert "tag=musex-21" in drop_amazon["affiliate_url"]


@pytest.mark.asyncio
async def test_agent_5_handle_message_viral_script_and_affiliate_drop(content_agent):
    """Vérifie l'envoi de messages A2A standardisés vers l'Agent 5."""
    context = ContextModel(user_id="user_affiliate_01", session_id="ses_01")

    # 1. Action GENERATE_SCRIPT
    msg_script = A2AMessage(
        source=SourceDescriptor(agent_id=AgentID.MANAGER),
        target=TargetDescriptor(agent_id=AgentID.AGENT_5_CONTENT, action=ActionType.GENERATE_SCRIPT),
        priority=PriorityEnum.HIGH,
        context=context,
        payload={"topic": "Erreurs Marge Stripe"}
    )
    resp_script = await content_agent.handle_message(msg_script)
    assert resp_script.status == StatusEnum.SUCCESS
    assert "shot_list" in resp_script.result
    assert len(resp_script.result["shot_list"]) == 4
    assert "trending_audios" in resp_script.result

    # 2. Action GENERATE_AFFILIATE_DROP
    msg_drop = A2AMessage(
        source=SourceDescriptor(agent_id=AgentID.MANAGER),
        target=TargetDescriptor(agent_id=AgentID.AGENT_5_CONTENT, action=ActionType.GENERATE_AFFILIATE_DROP),
        priority=PriorityEnum.HIGH,
        context=context,
        payload={
            "product_name": "Nike Dunk Low Retro Panda",
            "platform": "Hacoo",
            "original_price": 110.0,
            "promo_price": 32.0,
            "promo_code": "PANDA70"
        }
    )
    resp_drop = await content_agent.handle_message(msg_drop)
    assert resp_drop.status == StatusEnum.SUCCESS
    assert resp_drop.result["is_affiliate_drop"] is True
    assert resp_drop.result["discount_percent"] == 71
    assert "PANDA70" in resp_drop.result["telegram_caption"]
