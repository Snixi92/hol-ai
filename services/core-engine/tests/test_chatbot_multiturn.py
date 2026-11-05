"""
Suite de Tests de Validation Multi-Tours & Anaphores pour le Chatbot Muse-X / HoL AI.
Vérifie la conservation de contexte, la résolution des ellipses ('et sur cdiscount??'),
l'absence de cartes hallucinées ('Et ??' 89.90€), et la cohérence multilingue.
"""
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.api.server import app
from src.services.product_hunter import ProductHunterService
from src.services.session_manager import SessionManager, ConversationSession


@pytest.fixture(autouse=True)
def clean_sessions():
    """Nettoie toutes les sessions avant chaque test."""
    SessionManager.clear_all()
    yield
    SessionManager.clear_all()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_stop_words_and_substantive_extraction():
    """Vérifie que les stop-words purs ne sont JAMAIS considérés comme des noms de produits."""
    # Requêtes elliptiques ou stop-words purs -> None
    assert ProductHunterService.extract_substantive_product("et sur cdiscount??") is None
    assert ProductHunterService.extract_substantive_product("et ??") is None
    assert ProductHunterService.extract_substantive_product("sur amazon") is None
    assert ProductHunterService.extract_substantive_product("trouve le moins cher") is None
    assert ProductHunterService.extract_substantive_product("combien ça coûte ?") is None
    assert ProductHunterService.extract_substantive_product("et chez fnac ?") is None

    # Requêtes substantielles -> extraction correcte
    assert "ps5" in ProductHunterService.extract_substantive_product("trouve moi une ps5 sur amazon").lower()
    assert "pc portable" in ProductHunterService.extract_substantive_product("pc portable gamer lenovo").lower()
    assert "smart ring" in ProductHunterService.extract_substantive_product("smart ring titanium").lower()


def test_isolated_query_requires_clarification():
    """Une requête elliptique sans contexte préalable doit demander une clarification et NE PAS fabriquer de deal factice."""
    res = ProductHunterService.hunt_best_offer("et sur cdiscount??", context_product=None)
    assert res.get("is_clarification_needed") is True
    assert res.get("platform") == "Cdiscount"
    assert res.get("product") is None
    assert res.get("current_drop_price_eur") is None
    assert res.get("in_stock") is False
    assert res.get("deal_urgency") is None


def test_anaphora_with_context_product_hunting():
    """Avec un produit en contexte, la recherche elliptique cible le bon produit sur la nouvelle plateforme."""
    # Contexte précédent : PS5
    res = ProductHunterService.hunt_best_offer("et sur cdiscount??", context_product="ps5")
    assert res.get("is_clarification_needed") is not True
    assert res.get("platform") == "Cdiscount"
    assert "PlayStation 5" in res.get("product")
    assert res.get("current_drop_price_eur") == 439.99
    assert "cdiscount.com" in res.get("product_url")
    assert "et+%3F%3F" not in res.get("product_url")


def test_laptop_cross_platform_hunting():
    """Vérifie la comparaison PC gamer entre Cdiscount et Amazon."""
    # Cdiscount
    res_cd = ProductHunterService.hunt_best_offer("vas sur cdiscount et trouve moi le pc portable le moins cher avec une 5060")
    assert res_cd.get("platform") == "Cdiscount"
    assert "Lenovo LOQ" in res_cd.get("product")
    assert res_cd.get("current_drop_price_eur") == 799.99

    # Amazon avec contexte
    res_amz = ProductHunterService.hunt_best_offer("et sur amazon ?", context_product=res_cd.get("product"))
    assert res_amz.get("platform") == "Amazon.fr"
    assert "Lenovo LOQ" in res_amz.get("product")
    assert res_amz.get("current_drop_price_eur") == 829.99


def test_session_manager_resolution():
    """Vérifie la résolution des anaphores dans la session conversationnelle."""
    session = SessionManager.get_or_create(session_id="test_sess_01")
    
    # 1. Requête initiale
    eff_msg, prod, plat = SessionManager.resolve_anaphora_and_context(session, "trouve moi une ps5 sur amazon")
    assert "ps5" in prod.lower()
    assert plat == "Amazon.fr"

    # Simuler l'enregistrement de la réponse avec carte deal
    session.add_assistant_message("Voici la PS5 sur Amazon", cards=[{
        "type": "deal",
        "data": {
            "product": "Sony PlayStation 5 Édition Standard (Modèle Slim avec lecteur disque)",
            "platform": "Amazon.fr",
            "current_drop_price_eur": 429.00
        }
    }])

    # 2. Requête de suivi elliptique
    eff_msg2, prod2, plat2 = SessionManager.resolve_anaphora_and_context(session, "et sur cdiscount??")
    assert "PlayStation 5" in prod2
    assert plat2 == "Cdiscount"
    assert "Cdiscount" in eff_msg2


def test_api_chat_multiturn_dialogue(client):
    """
    Test d'intégration E2E du scénario exact de l'utilisateur :
    Tour 1 : L'utilisateur demande une PS5 sur Amazon.
    Tour 2 : L'utilisateur enchaîne avec 'et sur cdiscount??'.
    Vérifie qu'aucune fausse carte 'Et ??' à 89.90€ n'apparaît et que la vraie PS5 Cdiscount est trouvée.
    """
    session_id = "test_e2e_session_ps5"

    # Tour 1
    resp1 = client.post("/api/chat", json={
        "message": "trouve moi une ps5 sur amazon",
        "session_id": session_id,
        "user_id": "user_ps5_hunter"
    })
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["session_id"] == session_id
    assert len(data1["cards"]) >= 1
    deal1 = data1["cards"][0]["data"]
    assert "PlayStation 5" in deal1["product"]
    assert deal1["platform"] == "Amazon.fr"
    assert deal1["current_drop_price_eur"] == 429.00

    # Tour 2 : Requête elliptique
    resp2 = client.post("/api/chat", json={
        "message": "et sur cdiscount??",
        "session_id": session_id,
        "user_id": "user_ps5_hunter"
    })
    assert resp2.status_code == 200
    data2 = resp2.json()

    # Vérification stricte : AUCUNE carte 'Et ??' ou 89.90€
    for card in data2["cards"]:
        if card.get("type") == "deal":
            prod_title = card["data"].get("product", "")
            assert prod_title != "Et ??"
            assert prod_title != "Et"
            assert "89.9" not in str(card["data"].get("current_drop_price_eur"))
            # Doit être la PS5 sur Cdiscount
            assert "PlayStation 5" in prod_title
            assert card["data"].get("platform") == "Cdiscount"
            assert card["data"].get("current_drop_price_eur") == 439.99
            assert "et+%3F%3F" not in card["data"].get("product_url")


def test_api_chat_isolated_elliptical_query_no_hallucination(client):
    """
    Test d'intégration : Une requête 'et sur cdiscount??' envoyée isolément
    dans une session vierge NE DOIT JAMAIS générer de carte promotionnelle bidon.
    """
    session_id = "fresh_isolated_session"

    resp = client.post("/api/chat", json={
        "message": "et sur cdiscount??",
        "session_id": session_id,
        "user_id": "fresh_user"
    })
    assert resp.status_code == 200
    data = resp.json()

    # Zéro carte deal fantôme
    deal_cards = [c for c in data.get("cards", []) if c.get("type") == "deal"]
    assert len(deal_cards) == 0

    # La réponse ne doit pas inventer de fausse promo pour 'Et ??'
    reply_lower = data.get("reply", "").lower()
    assert "89,90" not in reply_lower
    assert "89.90" not in reply_lower


def test_macbook_neo_clarification_and_real_macbook_offer(client):
    """
    Test d'intégration du cas réel de l'utilisateur :
    L'utilisateur demande 'trouve le macbook neo le moins chère'.
    Le système doit comprendre que 'MacBook Neo' n'existe pas, proposer la vraie référence
    MacBook Air M2 à 999,00 € et ne JAMAIS inventer un faux prix à 89,90 €.
    """
    session_id = "test_macbook_neo_session"

    resp = client.post("/api/chat", json={
        "message": "trouve le macbook neo le moins chère",
        "session_id": session_id,
        "user_id": "apple_hunter"
    })
    assert resp.status_code == 200
    data = resp.json()

    # Vérification des cartes
    assert len(data.get("cards", [])) >= 1
    deal = data["cards"][0]["data"]
    assert "MacBook" in deal["product"]
    assert deal["current_drop_price_eur"] == 999.00
    assert "89.9" not in str(deal.get("current_drop_price_eur"))
    assert "MacBook Neo" in deal.get("market_insight", "") or "MacBook Neo" in deal.get("specs", []) or "MacBook Neo" in str(deal)

    # Vérification de la réponse
    reply_lower = data.get("reply", "").lower()
    assert "89,90" not in reply_lower
    assert "89.90" not in reply_lower


def test_unknown_product_returns_search_hub_no_fake_price(client):
    """
    Test d'intégration pour un produit inconnu / non référencé :
    Le système doit renvoyer une carte de type 'search_hub', SANS faux prix inventé ni faux stock.
    """
    session_id = "test_search_hub_session"

    resp = client.post("/api/chat", json={
        "message": "trouve moi un aspirateur robot cyberbot 9000",
        "session_id": session_id,
        "user_id": "robot_hunter"
    })
    assert resp.status_code == 200
    data = resp.json()

    cards = data.get("cards", [])
    assert len(cards) >= 1
    card_types = [c["type"] for c in cards]
    assert "omni_deal" in card_types or "search_hub" in card_types
    omni_card = next(c for c in cards if c["type"] in ["omni_deal", "search_hub"])
    card_data = omni_card["data"]
    assert card_data.get("current_drop_price_eur") is None
    assert card_data.get("savings_percent") is None
    assert card_data.get("requires_user_approval") is False
    assert "amazon.fr/s?k=" in card_data["product_url"]

    reply_lower = data.get("reply", "").lower()
    assert "89,90" not in reply_lower
    assert "89.90" not in reply_lower


def test_iphone_xr_hunter_returns_xr_not_iphone_15():
    """Vérifie que la recherche d'un iPhone XR renvoie bien l'iPhone XR reconditionné (~189€) et NON l'iPhone 15 à 799€."""
    res_amz = ProductHunterService.hunt_best_offer("trouve moi un iphone xr le moin chère")
    assert "iPhone XR" in res_amz["product"]
    assert res_amz["current_drop_price_eur"] == 189.00
    assert res_amz["platform"] == "Amazon.fr"
    assert "iphone+xr" in res_amz["product_url"]
    assert "B0CHWV4J8Z" not in res_amz["product_url"]
    assert res_amz["in_stock"] is True

    res_cd = ProductHunterService.hunt_best_offer("iphone xr reconditionné sur cdiscount")
    assert "iPhone XR" in res_cd["product"]
    assert res_cd["current_drop_price_eur"] == 179.00
    assert res_cd["platform"] == "Cdiscount"
    assert "cdiscount.com" in res_cd["product_url"]


def test_iphone_other_models_return_specific_search_hub():
    """Vérifie que les autres modèles d'iPhone (11, 12, 13, etc.) ciblent leur propre modèle et pas l'iPhone 15."""
    res_13 = ProductHunterService.hunt_best_offer("trouve un iphone 13 sur amazon")
    assert "iPhone 13" in res_13["product"]
    assert res_13["is_search_hub"] is True
    assert "iphone+13" in res_13["product_url"].lower()


def test_api_chat_iphone_xr_e2e_no_iphone_15_hijack(client):
    """
    Test E2E de la requête exacte de l'utilisateur :
    'trouve moi un iphone xr le moin chère'
    Vérifie qu'on renvoie l'iPhone XR reconditionné (~189€), aucun détournement vers l'iPhone 15 à 799€,
    et que le suivi 'et sur cdiscount??' conserve bien l'iPhone XR.
    """
    session_id = "test_e2e_iphone_xr_session"

    # Tour 1 : Recherche iPhone XR sur Amazon
    resp1 = client.post("/api/chat", json={
        "message": "trouve moi un iphone xr le moin chère",
        "session_id": session_id,
        "user_id": "user_iphone_tester"
    })
    assert resp1.status_code == 200
    data1 = resp1.json()

    assert len(data1["cards"]) >= 1
    deal1 = data1["cards"][0]["data"]
    assert "iPhone XR" in deal1["product"]
    assert deal1["current_drop_price_eur"] == 189.00
    assert "799" not in str(deal1["current_drop_price_eur"])
    assert "B0CHWV4J8Z" not in deal1["product_url"]
    assert "iphone+xr" in deal1["product_url"]

    # La réponse ne doit pas forcer l'iPhone 15 ni prétendre que l'iPhone XR est indisponible
    reply_lower = data1.get("reply", "").lower()
    assert "iphone 15" not in reply_lower or "xr" in reply_lower
    assert "799" not in reply_lower

    # Tour 2 : Suivi elliptique sur Cdiscount
    resp2 = client.post("/api/chat", json={
        "message": "et sur cdiscount??",
        "session_id": session_id,
        "user_id": "user_iphone_tester"
    })
    assert resp2.status_code == 200
    data2 = resp2.json()

    assert len(data2["cards"]) >= 1
    deal2 = data2["cards"][0]["data"]
    assert "iPhone XR" in deal2["product"]
    assert deal2["platform"] == "Cdiscount"
    assert deal2["current_drop_price_eur"] == 179.00

