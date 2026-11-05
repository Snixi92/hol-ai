"""
Suite de tests pour la Recherche Universelle Web & Plateformes d'Occasion (OmniSearch).
Vérifie :
1. Recherche illimitée sur tout le web (Sephora, Leboncoin, Vinted, Back Market, etc.).
2. Prise en charge des catégories diverses : Beauté/Maquillage/Crèmes, Tech, Mode, Général.
3. Détection des requêtes ouvertes et génération de cartes interactives de clarification avec questions et chips.
4. Intégration E2E via /api/chat.
"""
import pytest
from fastapi.testclient import TestClient
from src.api.server import app
from src.services.omni_scraper import OmniScraperService
from src.services.product_hunter import ProductHunterService
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


def test_omni_category_detection():
    """Vérifie la détection multi-univers (Beauté, Tech, Mode, etc.)."""
    assert OmniScraperService.detect_category("palette de maquillage") == "BEAUTY"
    assert OmniScraperService.detect_category("crème hydratante cerave") == "BEAUTY"
    assert OmniScraperService.detect_category("rouge à lèvres mat") == "BEAUTY"
    assert OmniScraperService.detect_category("pc portable gamer rtx") == "TECH"
    assert OmniScraperService.detect_category("téléphone samsung galaxy") == "TECH"
    assert OmniScraperService.detect_category("sweat à capuche oversize") == "FASHION"


def test_ambiguity_and_interactive_chips_generation():
    """Vérifie que les requêtes ouvertes génèrent des questions pertinentes et des chips de réponse rapide."""
    # Requête ouverte maquillage
    assert OmniScraperService.is_ambiguous_or_open("trouve moi une palette de maquillage") is True
    res_palette = OmniScraperService.hunt_omni_product("trouve moi une palette de maquillage")
    assert res_palette["is_clarification_needed"] is True
    assert res_palette["interactive_clarification"] is not None
    assert len(res_palette["interactive_clarification"]["questions"]) >= 2
    assert len(res_palette["interactive_clarification"]["quick_chips"]) >= 4

    # Requête ouverte crème
    assert OmniScraperService.is_ambiguous_or_open("cherche une bonne crème hydratante") is True
    res_creme = OmniScraperService.hunt_omni_product("cherche une bonne crème hydratante")
    assert res_creme["is_clarification_needed"] is True
    assert "type de peau" in str(res_creme["interactive_clarification"]["questions"]).lower()

    # Requête ultra-spécifique (ne doit PAS bloquer avec une clarification inutile)
    assert OmniScraperService.is_ambiguous_or_open("crème cerave peau sèche") is False
    assert OmniScraperService.is_ambiguous_or_open("pc portable lenovo rtx 4060") is False


def test_all_platforms_links_contain_second_hand_and_specialty_stores():
    """Vérifie que les liens générés couvrent à la fois les sites d'occasion et les boutiques spécialisées."""
    # Test Beauté / Maquillage
    beauty_links = OmniScraperService.generate_all_platform_links("palette fards", "BEAUTY")
    occ_names = [p["platform"] for p in beauty_links["occasion"]]
    ret_names = [p["platform"] for p in beauty_links["retail"]]

    # Sites d'occasion inclus
    assert "Leboncoin" in occ_names
    assert "Vinted" in occ_names
    assert "Back Market" in occ_names

    # Boutiques spécialisées beauté incluses
    assert "Sephora" in ret_names
    assert "Nocibé" in ret_names

    # Test Tech
    tech_links = OmniScraperService.generate_all_platform_links("ordinateur portable", "TECH")
    tech_ret_names = [p["platform"] for p in tech_links["retail"]]
    assert "Fnac.com" in tech_ret_names
    assert "Amazon.fr" in tech_ret_names


def test_product_hunter_delegates_to_omni_for_non_catalog_items():
    """Vérifie que ProductHunterService fait appel à OmniScraperService pour n'importe quel produit du web."""
    res = ProductHunterService.hunt_best_offer("trouve moi une palette de maquillage")
    assert res.get("is_omni_search") is True
    assert res.get("category") == "BEAUTY"
    assert len(res.get("occasion_platforms", [])) >= 3
    assert len(res.get("retail_platforms", [])) >= 3


def test_api_chat_open_query_returns_interactive_clarification_cards(client):
    """
    Test E2E :
    Quand l'utilisateur demande 'trouve moi une palette de maquillage',
    l'API /api/chat doit renvoyer :
    1. Une carte interactive_clarification avec questions et chips cliquables.
    2. Une carte omni_deal avec les plateformes d'occasion (Leboncoin, Vinted) et retail (Sephora, Nocibé).
    """
    resp = client.post("/api/chat", json={
        "message": "trouve moi une palette de maquillage",
        "session_id": "test_palette_sess_01",
        "user_id": "user_beauty"
    })
    assert resp.status_code == 200
    data = resp.json()

    card_types = [c.get("type") for c in data.get("cards", [])]
    assert "interactive_clarification" in card_types
    assert "omni_deal" in card_types

    # Vérification des détails de la carte clarification
    clarif_card = next(c for c in data["cards"] if c["type"] == "interactive_clarification")
    assert len(clarif_card["data"]["questions"]) >= 2
    assert len(clarif_card["data"]["quick_chips"]) >= 4

    # Vérification de la carte omni
    omni_card = next(c for c in data["cards"] if c["type"] == "omni_deal")
    occ_plats = [p["platform"] for p in omni_card["data"]["occasion_platforms"]]
    assert "Leboncoin" in occ_plats
    assert "Vinted" in occ_plats


def test_api_chat_creme_hydratante_omni_search(client):
    """
    Test E2E :
    Demande de crème hydratante -> scan omni-web et questions de type de peau.
    """
    resp = client.post("/api/chat", json={
        "message": "cherche une bonne crème hydratante",
        "session_id": "test_creme_sess_02",
        "user_id": "user_skincare"
    })
    assert resp.status_code == 200
    data = resp.json()

    card_types = [c.get("type") for c in data.get("cards", [])]
    assert "interactive_clarification" in card_types
    assert "omni_deal" in card_types

    clarif_card = next(c for c in data["cards"] if c["type"] == "interactive_clarification")
    questions_text = " ".join(clarif_card["data"]["questions"]).lower()
    assert "peau" in questions_text


def test_second_hand_hunter_service_returns_accurate_benchmarks():
    """Vérifie que SecondHandHunterService extrait des prix réels et cohérents (Leboncoin, Back Market, etc.)."""
    from src.services.second_hand_hunter import SecondHandHunterService

    res = SecondHandHunterService.hunt_second_hand("iphone xr d'occasion")
    assert res["is_second_hand_deal"] is True
    assert res["product"] == "iPhone XR 64 Go"
    assert res["min_peer_price_eur"] == 65.0
    assert res["pro_reconditioned_price_eur"] == 135.0
    assert len(res["offers"]) >= 3

    platforms = [o["platform"] for o in res["offers"]]
    assert "Leboncoin" in platforms
    assert "Back Market" in platforms
    assert "Vinted" in platforms


def test_product_hunter_routes_to_second_hand():
    """Vérifie que ProductHunterService délègue à SecondHandHunterService quand l'utilisateur demande de l'occasion."""
    res = ProductHunterService.hunt_best_offer("cherche moi un iphone xr d'occasion")
    assert res.get("is_second_hand_deal") is True
    assert res.get("current_drop_price_eur") == 65.0
    assert res.get("pro_reconditioned_price_eur") == 135.0


def test_api_chat_second_hand_iphone_xr_e2e(client):
    """
    Test E2E :
    Requête : 'cherche moi un iphone xr d'occasion le moin chère'
    L'API /api/chat doit renvoyer la carte interactive second_hand_deals
    avec comparaison réelle Leboncoin vs Back Market et conseil de grande sœur.
    """
    resp = client.post("/api/chat", json={
        "message": "cherche moi un iphone xr d'occasion le moin chère",
        "session_id": "test_xr_second_hand_01",
        "user_id": "user_deal_hunter"
    })
    assert resp.status_code == 200
    data = resp.json()

    card_types = [c.get("type") for c in data.get("cards", [])]
    assert "second_hand_deals" in card_types

    card = next(c for c in data["cards"] if c["type"] == "second_hand_deals")
    card_data = card["data"]
    assert card_data["product"] == "iPhone XR 64 Go"
    assert card_data["min_peer_price_eur"] == 65.0
    assert card_data["pro_reconditioned_price_eur"] == 135.0
    assert len(card_data["offers"]) >= 3

    # Vérifie que la réponse conversationnelle contient les conseils sans rediriger vers Amazon inutilement
    msg = data.get("reply", "") or data.get("message", "")
    assert "Leboncoin" in msg or "Back Market" in msg or "65" in msg or "135" in msg

