"""
Tests unitaires et d'intégration pour la Phase 2 complète de Muse-X :
1. Sourcing multi-fournisseurs (Alibaba, DHgate, Hacoo, Cdiscount, Amazon) avec calcul des marges brutes/nettes
2. Suivi transporteurs multi-points (Colissimo, Mondial Relay, UPS, DHL) avec points relais et lockers temps réel
3. Moteur CFO Agent 4 (Calcul marge nette Stripe + TVA 20%, Rapprochement Affiliation vs OPEX, Audit Factures/Reçus)
4. Endpoints API REST dédiés
"""
import sys
from pathlib import Path
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
import fakeredis.aioredis as fake_aioredis

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

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
from src.broker.stream_bus import StreamBus
from src.services.product_hunter import ProductHunterService
from src.agents.agent_3_logistics.service import LogisticsAgent
from src.agents.agent_4_finance.service import FinanceAgent
from src.api.server import app


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def fake_bus():
    client = fake_aioredis.FakeRedis(decode_responses=True)
    return StreamBus(redis_client=client)


@pytest.fixture
def logistics_agent(fake_bus):
    return LogisticsAgent(fake_bus)


@pytest.fixture
def finance_agent(fake_bus):
    return FinanceAgent(fake_bus)


@pytest.fixture
def api_client():
    with TestClient(app) as client:
        yield client


# ============================================================================
# 1. TESTS SOURCING & PRODUCT HUNTER (5 PLATEFORMES & MARGES)
# ============================================================================

def test_product_hunter_compare_five_platforms():
    """Valide la comparaison multi-fournisseurs sur Alibaba, DHgate, Hacoo, Cdiscount et Amazon."""
    res = ProductHunterService.compare_multi_suppliers(
        query="Bague Connectée Smart Ring Titane",
        target_selling_price_ttc=89.90
    )

    assert res["platforms_compared_count"] == 5
    suppliers = res["suppliers"]
    platforms = [s["platform"] for s in suppliers]

    # Vérification explicite des 5 plateformes demandées
    assert "Alibaba" in platforms
    assert "DHgate" in platforms
    assert "Hacoo" in platforms
    assert "Cdiscount" in platforms
    assert "Amazon" in platforms

    # Vérification des marges brutes et nettes
    for s in suppliers:
        assert s["unit_cost_eur"] > 0
        assert s["shipping_cost_eur"] >= 0
        assert s["gross_margin_eur"] > 0
        assert s["gross_margin_percent"] > 0
        assert s["net_margin_eur"] is not None
        assert s["stripe_fee_eur"] > 0
        assert "direct_url" in s
        assert s["direct_url"].startswith("http")

    # Alibaba doit offrir le coût unitaire le plus bas et la meilleure marge sur volume
    alibaba = next(s for s in suppliers if s["platform"] == "Alibaba")
    assert alibaba["moq"] == 50
    assert alibaba["profitability_tier"] == "EXCELLENT"

    # Amazon doit offrir les délais les plus courts
    amazon = next(s for s in suppliers if s["platform"] == "Amazon")
    assert amazon["delivery_days"] <= 2

    # Vérification des gagnants
    winners = res["winners"]
    assert "max_net_margin" in winners
    assert "cheapest_unit_cost" in winners
    assert "fastest_delivery" in winners
    assert winners["cheapest_unit_cost"]["platform"] == "Alibaba"
    assert winners["fastest_delivery"]["platform"] in ["Amazon", "Cdiscount"]


def test_product_hunter_direct_platform_sourcing():
    """Vérifie la détection de sourcing direct pour Alibaba, DHgate, Hacoo, Cdiscount et Amazon."""
    # Alibaba direct
    res_ali = ProductHunterService.hunt_best_offer("trouve moi une smart ring sur alibaba")
    assert res_ali["platform"] == "Alibaba"
    assert "alibaba.com" in res_ali["product_url"]

    # DHgate direct
    res_dh = ProductHunterService.hunt_best_offer("ecouteurs bluetooth pas cher", platform_hint="DHgate")
    assert res_dh["platform"] == "DHgate"
    assert "dhgate.com" in res_dh["product_url"]

    # Hacoo direct
    res_hacoo = ProductHunterService.hunt_best_offer("sweat streetwear tendance", platform_hint="Hacoo")
    assert res_hacoo["platform"] == "Hacoo"
    assert "hacoo.app" in res_hacoo["product_url"]

    # Cdiscount laptop gaming vérifié
    res_cdiscount = ProductHunterService.hunt_best_offer("pc portable gamer 4060 cdiscount")
    assert res_cdiscount["platform"] == "Cdiscount"
    assert "cdiscount.com" in res_cdiscount["product_url"]

    # Amazon PS5 vérifiée
    res_amazon = ProductHunterService.hunt_best_offer("ps5 slim amazon")
    assert res_amazon["platform"] == "Amazon.fr"
    assert "amazon.fr" in res_amazon["product_url"]


# ============================================================================
# 2. TESTS SUIVI MULTI-TRANSPORTEURS & POINTS RELAIS (COLISSIMO, MONDIAL RELAY, DHL, UPS)
# ============================================================================

def test_logistics_colissimo_tracking_with_relay(logistics_agent):
    """Vérifie le suivi Colissimo avec checkpoints français et point de retrait."""
    tracking = logistics_agent._simulate_tracking("6A98127391823", carrier="Colissimo")

    assert tracking["carrier"] == "Colissimo"
    assert tracking["status"] == "EN_TRANSIT"
    assert tracking["progress_percent"] == 85
    assert len(tracking["checkpoints"]) >= 4

    # Checkpoints spécifiques La Poste / Colissimo
    locations = [cp["location"] for cp in tracking["checkpoints"]]
    assert any("La Poste" in loc or "Belleville" in loc for loc in locations)
    assert any("Briarde" in loc or "Moissy-Cramayel" in loc for loc in locations)

    # Point de retrait bureau de poste
    relay = tracking["relay_point"]
    assert relay is not None
    assert "Bureau de Poste" in relay["name"]
    assert "pickup_code" in relay
    assert "retention_deadline" in relay


def test_logistics_mondial_relay_tracking_with_locker_pin(logistics_agent):
    """Vérifie le suivi Mondial Relay avec casier Locker 24/7, code PIN et QR code."""
    tracking = logistics_agent._simulate_tracking("MR88921039", carrier="Mondial Relay")

    assert tracking["carrier"] == "Mondial Relay"
    assert tracking["status"] == "DISPONIBLE_AU_POINT_RELAIS"
    assert tracking["progress_percent"] == 100

    # Checkpoints spécifiques Mondial Relay
    locations = [cp["location"] for cp in tracking["checkpoints"]]
    assert any("Ensisheim" in loc for loc in locations)
    assert any("Locker" in loc or "Paris" in loc for loc in locations)

    # Détails du Locker 24/7
    relay = tracking["relay_point"]
    assert relay is not None
    assert "24/7" in relay["network"]
    assert "PIN:" in relay["pickup_code"]
    assert "qr_code_token" in relay
    assert "retention_deadline" in relay


def test_logistics_dhl_express_tracking(logistics_agent):
    """Vérifie le suivi DHL Express avec hubs internationaux (Leipzig, Roissy CDG)."""
    tracking = logistics_agent._simulate_tracking("DHL88291029", carrier="DHL Express")

    assert tracking["carrier"] == "DHL Express"
    assert tracking["status"] == "EN_TRANSIT"
    assert any("Leipzig" in cp["location"] for cp in tracking["checkpoints"])
    assert any("CDG" in cp["location"] or "Roissy" in cp["location"] for cp in tracking["checkpoints"])
    assert tracking["relay_point"] is not None


def test_logistics_ups_tracking(logistics_agent):
    """Vérifie le suivi UPS standard et hub Chilly-Mazarin."""
    tracking = logistics_agent._simulate_tracking("1Z99283749281", carrier="UPS")

    assert tracking["carrier"] == "UPS"
    assert tracking["status"] == "EN_TRANSIT"
    assert "Chilly-Mazarin" in tracking["last_location"]
    assert tracking["relay_point"] is not None


@pytest.mark.asyncio
async def test_logistics_agent_handle_message_find_suppliers(logistics_agent):
    """Vérifie la délégation A2A de FIND_SUPPLIERS avec sourcing complet 5 plateformes."""
    msg = A2AMessage(
        source=SourceDescriptor(agent_id=AgentID.MANAGER),
        target=TargetDescriptor(agent_id=AgentID.AGENT_3_LOGISTICS, action=ActionType.FIND_SUPPLIERS),
        context=ContextModel(user_id="cfo_user", session_id="ses_1"),
        payload={"product": "Smart Ring Gen 3", "target_price": 79.90}
    )

    response = await logistics_agent.handle_message(msg)
    assert response.status == StatusEnum.SUCCESS
    res = response.result
    assert "multi_supplier_comparison" in res
    assert len(res["suppliers"]) == 5
    assert res["best_supplier"] is not None
    assert res["unit_price_eur"] > 0


# ============================================================================
# 3. TESTS MOTEUR CFO (MARGE NETTE STRIPE + TVA 20%, AFFILIATION, FACTURES)
# ============================================================================

def test_cfo_realtime_margin_exact_formula(finance_agent):
    """
    Vérifie la formule exacte :
    Prix TTC (100€) - TVA 20% (16.67€) - Coût achat (40€) - Stripe 1.5% + 0.25€ (1.75€)
    = Marge Nette en € et en %.
    """
    selling_ttc = 100.00
    cost_price = 40.00

    margin = finance_agent.calculate_cfo_realtime_margin(
        selling_price_ttc=selling_ttc,
        cost_price=cost_price
    )

    # 1. Vérification TVA 20%
    # 100 * (0.20 / 1.20) = 16.67€
    assert margin["vat_amount"] == 16.67
    assert margin["revenue_ht"] == 83.33

    # 2. Vérification Frais Stripe
    # (100 * 0.015) + 0.25 = 1.75€
    assert margin["stripe_fee_eur"] == 1.75

    # 3. Vérification Marge Nette en €
    # 83.33 (HT) - 40.00 (COGS) - 1.75 (Stripe) = 41.58€
    assert margin["net_margin_eur"] == 41.58

    # 4. Vérification Marge Nette en % du CA HT
    # (41.58 / 83.33) * 100 = 49.9%
    assert margin["net_margin_percent"] == 49.9
    assert margin["margin_rate_percent"] == 49.9
    assert margin["rating"] == "EXCELLENT"
    assert margin["profitability_rating"] == "HEALTHY"


def test_cfo_margin_deficit_scenario(finance_agent):
    """Vérifie la détection d'une vente déficitaire (coût fournisseur supérieur au HT)."""
    margin = finance_agent.calculate_cfo_realtime_margin(
        selling_price_ttc=50.00,
        cost_price=45.00
    )
    # HT = 41.67€, Cost = 45€ -> Marge Nette négative
    assert margin["net_margin_eur"] < 0
    assert margin["net_margin_percent"] < 0
    assert margin["rating"] == "DÉFICITAIRE"
    assert margin["profitability_rating"] == "LOW"


def test_cfo_affiliate_vs_opex_reconciliation(finance_agent):
    """
    Vérifie le rapprochement des commissions d'affiliation entrantes
    (Hacoo, DHgate, Amazon Partners) vis-à-vis des dépenses opérationnelles.
    """
    reconciliation = finance_agent.reconcile_affiliate_and_expenses()

    # Commissions d'affiliation
    assert reconciliation["total_affiliate_revenue_eur"] > 4000.00
    breakdown = reconciliation["affiliate_breakdown"]
    assert "Hacoo" in breakdown
    assert "DHgate" in breakdown
    assert "Amazon_Partners" in breakdown

    # Vérification des taux de conversion et commissions
    assert breakdown["Hacoo"]["commission_rate_percent"] == 10.0
    assert breakdown["Hacoo"]["earned_commission_eur"] == 1560.00
    assert breakdown["DHgate"]["commission_rate_percent"] == 7.0
    assert breakdown["Amazon_Partners"]["commission_rate_percent"] == 5.5

    # Dépenses opérationnelles
    assert reconciliation["total_operational_expenses_eur"] > 2000.00
    assert "saas_cloud_and_infrastructure" in reconciliation["opex_breakdown"]
    assert "marketing_acquisition" in reconciliation["opex_breakdown"]

    # Cash-flow net & couverture
    assert reconciliation["net_cash_flow_eur"] > 0
    assert reconciliation["coverage_ratio"] >= 1.5
    assert reconciliation["status"] == "CASH_FLOW_POSITIF"
    assert len(reconciliation["strategic_recommendations"]) >= 3


def test_cfo_receipt_and_invoice_analysis(finance_agent):
    """
    Vérifie l'audit instantané d'une facture téléversée :
    - Catégorisation automatique
    - Extraction TVA
    - Rapprochement avec le budget mensuel
    """
    # Test 1 : Facture Logistique Colissimo
    invoice_colissimo = finance_agent.analyze_receipt_or_invoice(
        receipt_data={"vendor": "La Poste Colissimo", "amount_ttc": 120.00}
    )
    assert invoice_colissimo["category"] == "LOGISTIQUE_TRANSPORT"
    assert invoice_colissimo["vat_rate_percent"] == 20.0
    assert invoice_colissimo["vat_amount"] == 20.00  # 120 * (0.2 / 1.2)
    assert invoice_colissimo["vat_deductible"] is True
    rec_budget = invoice_colissimo["monthly_budget_reconciliation"]
    assert rec_budget["status"] == "DANS_LE_BUDGET"
    assert rec_budget["remaining_budget_eur"] > 0

    # Test 2 : Facture SaaS AWS Cloud
    invoice_aws = finance_agent.analyze_receipt_or_invoice(
        raw_text="Facture mensuelle AWS Cloud EMEA SARL montant total 85.50€"
    )
    assert invoice_aws["category"] == "SAAS_ET_OUTILS_CLOUD"
    assert "Amazon Web Services" in invoice_aws["vendor"]
    assert invoice_aws["amount_ttc"] == 85.50

    # Test 3 : Reçu Restaurant Frais Pro
    invoice_resto = finance_agent.analyze_receipt_or_invoice(
        raw_text="Addition restaurant déjeuner d'affaires client 44.00€ TTC"
    )
    assert invoice_resto["category"] == "FRAIS_DE_DEPLACEMENT_RESTAURATION"
    assert invoice_resto["vat_rate_percent"] == 10.0  # Restauration 10%


@pytest.mark.asyncio
async def test_finance_agent_handle_message_actions(finance_agent):
    """Vérifie la gestion des messages A2A pour AUDIT_MARGINS, RECONCILE_TRANSACTIONS et EXTRACT_INVOICE_DATA."""
    # Action 1: AUDIT_MARGINS
    msg_margin = A2AMessage(
        source=SourceDescriptor(agent_id=AgentID.MANAGER),
        target=TargetDescriptor(agent_id=AgentID.AGENT_4_FINANCE, action=ActionType.AUDIT_MARGINS),
        context=ContextModel(user_id="usr_1", session_id="ses_1"),
        payload={"selling_price": 150.0, "cost_price": 60.0}
    )
    resp_margin = await finance_agent.handle_message(msg_margin)
    assert resp_margin.status == StatusEnum.SUCCESS
    assert resp_margin.result["net_margin_eur"] > 0
    assert "formula_applied" in resp_margin.result

    # Action 2: RECONCILE_TRANSACTIONS
    msg_rec = A2AMessage(
        source=SourceDescriptor(agent_id=AgentID.MANAGER),
        target=TargetDescriptor(agent_id=AgentID.AGENT_4_FINANCE, action=ActionType.RECONCILE_TRANSACTIONS),
        context=ContextModel(user_id="usr_1", session_id="ses_1"),
        payload={}
    )
    resp_rec = await finance_agent.handle_message(msg_rec)
    assert resp_rec.status == StatusEnum.SUCCESS
    assert "total_affiliate_revenue_eur" in resp_rec.result
    assert resp_rec.result["net_cash_flow_eur"] > 0

    # Action 3: EXTRACT_INVOICE_DATA
    msg_inv = A2AMessage(
        source=SourceDescriptor(agent_id=AgentID.MANAGER),
        target=TargetDescriptor(agent_id=AgentID.AGENT_4_FINANCE, action=ActionType.EXTRACT_INVOICE_DATA),
        context=ContextModel(user_id="usr_1", session_id="ses_1"),
        payload={"vendor": "Shopify Commerce Europe", "amount_ttc": 129.0}
    )
    resp_inv = await finance_agent.handle_message(msg_inv)
    assert resp_inv.status == StatusEnum.SUCCESS
    assert resp_inv.result["category"] == "SAAS_ET_OUTILS_CLOUD"


# ============================================================================
# 4. TESTS ENDPOINTS REST PHASE 2
# ============================================================================

def test_rest_api_sourcing_compare_endpoint(api_client):
    """Vérifie l'endpoint POST /api/sourcing/compare."""
    payload = {
        "query": "Smart Watch Amoled",
        "target_selling_price_ttc": 99.00
    }
    response = api_client.post("/api/sourcing/compare", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["platforms_compared_count"] == 5
    assert len(data["suppliers"]) == 5
    assert "winners" in data


def test_rest_api_logistics_track_endpoint(api_client):
    """Vérifie l'endpoint POST /api/logistics/track avec Colissimo et Mondial Relay."""
    # Colissimo
    res_colis = api_client.post("/api/logistics/track", json={"tracking_number": "6A123456789", "carrier": "Colissimo"})
    assert res_colis.status_code == 200
    assert res_colis.json()["carrier"] == "Colissimo"
    assert "relay_point" in res_colis.json()

    # Mondial Relay
    res_mr = api_client.post("/api/logistics/track", json={"tracking_number": "MR987654321", "carrier": "Mondial Relay"})
    assert res_mr.status_code == 200
    assert res_mr.json()["carrier"] == "Mondial Relay"
    assert "Locker" in res_mr.json()["relay_point"]["name"]


def test_rest_api_cfo_margin_endpoint(api_client):
    """Vérifie l'endpoint POST /api/cfo/margin."""
    payload = {
        "selling_price_ttc": 120.00,
        "cost_price": 45.00,
        "vat_rate": 0.20
    }
    response = api_client.post("/api/cfo/margin", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["selling_price_ttc"] == 120.00
    assert data["net_margin_eur"] > 0
    assert "stripe_fee_eur" in data


def test_rest_api_cfo_affiliate_reconciliation_endpoint(api_client):
    """Vérifie l'endpoint GET /api/cfo/affiliate-reconciliation."""
    response = api_client.get("/api/cfo/affiliate-reconciliation")
    assert response.status_code == 200
    data = response.json()
    assert data["total_affiliate_revenue_eur"] > 0
    assert "Hacoo" in data["affiliate_breakdown"]
    assert "Amazon_Partners" in data["affiliate_breakdown"]


def test_rest_api_cfo_receipt_endpoint(api_client):
    """Vérifie l'endpoint POST /api/cfo/receipt."""
    payload = {
        "vendor": "Mondial Relay SA",
        "amount_ttc": 65.40,
        "raw_text": "Bordereaux d'expédition lockers Mondial Relay"
    }
    response = api_client.post("/api/cfo/receipt", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "LOGISTIQUE_TRANSPORT"
    assert data["vat_deductible"] is True
    assert "monthly_budget_reconciliation" in data
