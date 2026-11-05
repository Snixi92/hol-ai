"""
Tests de robustesse métier et validation des cas limites mathématiques pour Muse-X OS.
Couvre :
1. Finance & Marge CFO (Agent 4) :
   - Vente TTC = 0€ (division par zéro évitée, marge % = 0.0)
   - Vente TTC négative (-50€)
   - Coût d'achat fournisseur astronomique (1 000 000€)
   - Taux de TVA aberrants (négatifs, > 1.0, 0%)
   - Frais Stripe (micro-montants 0.10€ et 0.01€, montants négatifs)
   - Rapprochement d'affiliation : Total commissions = 0€ vs OPEX = 2000€, et Commissions = 5000€ vs OPEX = 0€
   - Audit de factures/reçus : Reçu sans date, sans devise, montants négatifs, caractères de contrôle, budget = 0€
2. Sourcing Multi-Plateformes (ProductHunterService) :
   - Requête vide, espaces seuls, symboles seuls, 50 000 caractères, produit introuvable
3. Suivi Transporteurs (LogisticsAgent - Agent 3) :
   - Transporteur inconnu (TRANSPORTEUR_INEXISTANT, TRANSPORTEUR_FANTOME)
   - Numéro de colis vide ou < 4 caractères
4. Cœur Neuronal Polyglotte & Content Engine (LLMBrain & Agent 5) :
   - Détection multilingue extrême (FR + Darija + ES + EN), texte arabe sans voyelles, emojis massifs
   - Prompt vide et emojis pour la génération conversationnelle
   - Hooks viraux avec thématique vide ou injection de code (HTML, JS, SQL, Python)
   - Drop d'affiliation avec promo_price >= original_price ou valeurs négatives
5. Gardien d'Arrière-Plan (BackgroundGuardian) :
   - Déclenchements en rafale consécutifs des 3 Cron Jobs (8h, 13h, 22h)
   - Plafonnement strict de execution_history et cron_history sans fuite mémoire
"""
import pytest
import fakeredis.aioredis as fake_aioredis
from datetime import datetime, timezone

from src.broker.stream_bus import StreamBus
from src.agents.agent_4_finance.service import FinanceAgent
from src.agents.agent_3_logistics.service import LogisticsAgent
from src.agents.agent_5_content.service import ContentSocialAgent
from src.services.product_hunter import ProductHunterService
from src.services.llm_engine import LLMBrain
from src.services.background_watcher import BackgroundGuardian


@pytest.fixture
def fake_bus():
    client = fake_aioredis.FakeRedis(decode_responses=True)
    return StreamBus(redis_client=client)


@pytest.fixture
def finance_agent(fake_bus):
    return FinanceAgent(fake_bus)


@pytest.fixture
def logistics_agent(fake_bus):
    return LogisticsAgent(fake_bus)


@pytest.fixture
def content_agent(fake_bus):
    return ContentSocialAgent(fake_bus)


# ============================================================================
# 1. FINANCE & MARGE CFO (AGENT 4)
# ============================================================================

def test_cfo_margin_zero_selling_price(finance_agent):
    """Vérifie que vente TTC = 0€ gère la division par zéro et renvoie 0.0% de marge."""
    res = finance_agent.calculate_cfo_realtime_margin(
        selling_price_ttc=0.0,
        cost_price=25.0
    )
    assert res["selling_price_ttc"] == 0.0
    assert res["revenue_ht"] == 0.0
    assert res["vat_amount"] == 0.0
    assert res["stripe_fee_eur"] == 0.0
    assert res["gross_margin_percent"] == 0.0
    assert res["net_margin_percent"] == 0.0
    assert res["margin_rate_percent"] == 0.0
    assert res["net_margin_eur"] == -25.0
    assert res["rating"] == "DÉFICITAIRE"
    assert res["profitability_rating"] == "LOW"


def test_cfo_margin_negative_selling_price(finance_agent):
    """Vérifie que vente TTC négative (-50€) ne plante pas et retourne une marge déficitaire."""
    res = finance_agent.calculate_cfo_realtime_margin(
        selling_price_ttc=-50.0,
        cost_price=10.0
    )
    assert res["selling_price_ttc"] == -50.0
    assert res["revenue_ht"] == -50.0
    assert res["vat_amount"] == 0.0
    assert res["stripe_fee_eur"] == 0.0  # Aucun frais Stripe crédité
    assert res["net_margin_eur"] <= -50.0
    assert res["net_margin_percent"] == 0.0
    assert res["rating"] == "DÉFICITAIRE"


def test_cfo_margin_astronomical_cost_price(finance_agent):
    """Vérifie qu'un coût d'achat astronomique (1 000 000€) est géré proprement en perte nette."""
    res = finance_agent.calculate_cfo_realtime_margin(
        selling_price_ttc=100.0,
        cost_price=1_000_000.0
    )
    assert res["cost_price"] == 1_000_000.0
    assert res["net_margin_eur"] < -900_000.0
    assert res["rating"] == "DÉFICITAIRE"
    assert res["profitability_rating"] == "LOW"


def test_cfo_margin_aberrant_vat_rates(finance_agent):
    """Vérifie que les taux de TVA négatifs, supérieurs à 1.0 ou nuls sont sécurisés."""
    # TVA négative (-0.20 ou -1.0 qui causerait 1 + (-1) = 0)
    res_neg = finance_agent.calculate_cfo_realtime_margin(
        selling_price_ttc=100.0,
        cost_price=30.0,
        vat_rate=-1.0
    )
    assert res_neg["vat_rate_percent"] == 0.0
    assert res_neg["vat_amount"] == 0.0
    assert res_neg["revenue_ht"] == 100.0

    # TVA supérieure à 1.0 (ex: 1.5 ou 150%)
    res_high = finance_agent.calculate_cfo_realtime_margin(
        selling_price_ttc=100.0,
        cost_price=30.0,
        vat_rate=1.5
    )
    assert res_high["vat_rate_percent"] <= 100.0
    assert res_high["revenue_ht"] > 0

    # TVA nulle (0%)
    res_zero = finance_agent.calculate_cfo_realtime_margin(
        selling_price_ttc=100.0,
        cost_price=30.0,
        vat_rate=0.0
    )
    assert res_zero["vat_rate_percent"] == 0.0
    assert res_zero["vat_amount"] == 0.0
    assert res_zero["revenue_ht"] == 100.0


def test_stripe_fees_micro_and_negative_amounts():
    """Vérifie le calcul des frais Stripe sur micro-montants et montants négatifs."""
    # Micro-montant 0.10€ : frais de (0.10 * 0.015) + 0.25 = 0.2515 -> 0.25€
    fee_10 = FinanceAgent.calculate_stripe_fee(0.10)
    assert fee_10 == 0.25

    # Micro-montant 0.01€ : frais fixes de 0.25€
    fee_01 = FinanceAgent.calculate_stripe_fee(0.01)
    assert fee_01 == 0.25

    # Montant négatif : aucun frais
    fee_neg = FinanceAgent.calculate_stripe_fee(-20.0)
    assert fee_neg == 0.0

    # Montant nul : aucun frais
    fee_zero = FinanceAgent.calculate_stripe_fee(0.0)
    assert fee_zero == 0.0


def test_affiliate_reconciliation_zero_commissions_vs_opex(finance_agent):
    """Vérifie le rapprochement lorsque Commissions = 0€ vs OPEX = 2000€ (ratio = 0.0x sans ZeroDivisionError)."""
    rec = finance_agent.reconcile_affiliate_and_expenses(
        affiliate_data={"total_commissions": 0.0},
        expense_data={"total_opex": 2000.0}
    )
    assert rec["total_affiliate_revenue_eur"] == 0.0
    assert rec["total_operational_expenses_eur"] == 2000.0
    assert rec["coverage_ratio"] == 0.0
    assert rec["net_cash_flow_eur"] == -2000.0
    assert rec["profit_margin_percent"] == 0.0
    assert rec["status"] == "DEFICIT_ALERTE"


def test_affiliate_reconciliation_zero_opex_vs_commissions(finance_agent):
    """Vérifie le rapprochement lorsque Commissions = 5000€ vs OPEX = 0€ (ratio capé sans ZeroDivisionError)."""
    rec = finance_agent.reconcile_affiliate_and_expenses(
        affiliate_data={"total_commissions": 5000.0},
        expense_data={"total_opex": 0.0}
    )
    assert rec["total_affiliate_revenue_eur"] == 5000.0
    assert rec["total_operational_expenses_eur"] == 0.0
    assert rec["coverage_ratio"] == 999.99  # Capé proprement pour compatibilité JSON
    assert rec["net_cash_flow_eur"] == 5000.0
    assert rec["profit_margin_percent"] == 100.0
    assert rec["status"] == "CASH_FLOW_POSITIF"


def test_receipt_analysis_corrupted_inputs_and_edge_cases(finance_agent):
    """Vérifie l'audit de factures avec données manquantes, montants négatifs, et texte corrompu."""
    # Reçu sans date et sans devise
    inv_no_date = finance_agent.analyze_receipt_or_invoice(
        receipt_data={"vendor": "Colissimo", "amount_ttc": 45.0}
    )
    assert inv_no_date["currency"] == "EUR"
    assert inv_no_date["date"] == datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Reçu avec devise inconnue -> repli "EUR"
    inv_bad_curr = finance_agent.analyze_receipt_or_invoice(
        receipt_data={"vendor": "Shopify", "amount_ttc": 80.0, "currency": "BITCOIN_FAKE"}
    )
    assert inv_bad_curr["currency"] == "EUR"

    # Reçu avec montant négatif (avoir / remboursement fournisseur)
    inv_neg = finance_agent.analyze_receipt_or_invoice(
        receipt_data={"vendor": "AWS", "amount_ttc": -50.0}
    )
    assert inv_neg["amount_ttc"] == -50.0
    assert inv_neg["amount_ht"] < 0

    # Reçu avec caractères de contrôle corrompus
    corrupt_text = "Facture\x00\x08 Colissimo\x1b livraison\x0c 35.50€ TTC"
    inv_corrupt = finance_agent.analyze_receipt_or_invoice(raw_text=corrupt_text)
    assert inv_corrupt["category"] == "LOGISTIQUE_TRANSPORT"
    assert inv_corrupt["amount_ttc"] == 35.50

    # Reçu avec TVA corrompue (string ou aberrant)
    inv_bad_vat = finance_agent.analyze_receipt_or_invoice(
        receipt_data={"vendor": "Mondial Relay", "amount_ttc": 60.0, "vat_rate": "CORRUPTED_RATE"}
    )
    assert inv_bad_vat["vat_rate_percent"] == 20.0  # Repli sûr sur le taux de catégorie


# ============================================================================
# 2. SOURCING MULTI-FOURNISSEURS (PRODUCT HUNTER)
# ============================================================================

def test_sourcing_empty_and_whitespace_query():
    """Vérifie la comparaison multi-fournisseurs avec requête vide ou espaces seuls."""
    # Chaîne vide
    res_empty = ProductHunterService.compare_multi_suppliers(query="")
    assert res_empty["platforms_compared_count"] == 5
    assert len(res_empty["suppliers"]) == 5
    assert res_empty["cleaned_product"] != ""

    # Espaces seuls
    res_spaces = ProductHunterService.compare_multi_suppliers(query="     ")
    assert res_spaces["platforms_compared_count"] == 5
    assert len(res_spaces["suppliers"]) == 5


def test_sourcing_symbols_only_query():
    """Vérifie la recherche avec symboles uniquement ($#%@! ou !@#$%^&*()_+)."""
    res_symbols = ProductHunterService.compare_multi_suppliers(query="!@#$%^&*()_+")
    assert res_symbols["platforms_compared_count"] == 5
    assert "Article" in res_symbols["cleaned_product"]
    for s in res_symbols["suppliers"]:
        assert s["direct_url"].startswith("http")


def test_sourcing_massive_character_query():
    """Vérifie la recherche avec 10 000 ou 50 000 caractères sans dépassement de buffer."""
    huge_query = "laptop gamer rtx " + ("x" * 50_000)
    res_huge = ProductHunterService.compare_multi_suppliers(query=huge_query)
    assert res_huge["platforms_compared_count"] == 5
    # Doit être tronqué sans crash
    assert len(res_huge["cleaned_product"]) <= 350


def test_sourcing_unknown_unfindable_product():
    """Vérifie la gestion d'un produit inexistant sans fiche cataloguée : search_hub sans faux prix."""
    res_unknown = ProductHunterService.hunt_best_offer("produit_inexistant_xyz_998844")
    assert res_unknown["in_stock"] is True
    assert "product_url" in res_unknown
    assert res_unknown["is_search_hub"] is True
    assert res_unknown["current_drop_price_eur"] is None
    assert res_unknown["requires_user_approval"] is False


# ============================================================================
# 3. SUIVI TRANSPORTEURS (LOGISTICS AGENT)
# ============================================================================

def test_carrier_tracking_unknown_ghost_carrier(logistics_agent):
    """Vérifie qu'un transporteur inexistant (TRANSPORTEUR_INEXISTANT) n'est pas silencieusement attribué à UPS."""
    res = logistics_agent._simulate_tracking(
        tracking_number="99283719283",
        carrier="TRANSPORTEUR_INEXISTANT"
    )
    assert res["status"] == "TRANSPORTEUR_INCONNU"
    assert res["carrier"] == "TRANSPORTEUR_INEXISTANT"
    assert res["progress_percent"] == 0
    assert res["badge_color"] == "#6b7280"
    assert res["relay_point"] is None
    assert "error" in res


def test_carrier_tracking_invalid_short_tracking_number(logistics_agent):
    """Vérifie qu'un numéro de suivi vide ou de moins de 4 caractères est signalé comme invalide."""
    # Numéro vide
    res_empty = logistics_agent._simulate_tracking(tracking_number="", carrier="Colissimo")
    assert res_empty["status"] == "NUMERO_DE_SUIVI_INVALIDE"
    assert res_empty["progress_percent"] == 0
    assert "error" in res_empty

    # Numéro de 2 caractères
    res_short = logistics_agent._simulate_tracking(tracking_number="12", carrier="UPS")
    assert res_short["status"] == "NUMERO_DE_SUIVI_INVALIDE"
    assert res_short["progress_percent"] == 0
    assert res_short["badge_color"] == "#ef4444"


# ============================================================================
# 4. CODE-SWITCHING & CONTENT ENGINE (LLMBRAIN & AGENT 5)
# ============================================================================

def test_llm_extreme_multilingual_code_switching():
    """Vérifie la détection multilingue avec mélange extrême FR + Darija + ES + EN."""
    extreme_text = "Salam khouya, hola amigo, how are you avec la commande de ce produit ?"
    lang = LLMBrain.detect_language(extreme_text)
    # Contient du Darija et du Français
    assert lang in ["darija_fr", "darija"]


def test_llm_arabic_script_without_vowels():
    """Vérifie la détection de texte arabe sans voyelles / harakat."""
    arabic_unvocalized = "شكرا خويا بزاف على هاد لافير"
    lang = LLMBrain.detect_language(arabic_unvocalized)
    assert lang in ["darija", "darija_fr"]


def test_llm_empty_and_emojis_prompt():
    """Vérifie la détection avec prompt vide ou uniquement des emojis."""
    # Emojis uniquement
    lang_emoji = LLMBrain.detect_language("🔥🔥🔥💯")
    assert lang_emoji == "fr"

    # Prompt vide
    lang_empty = LLMBrain.detect_language("")
    assert lang_empty == "fr"


def test_content_viral_hooks_code_injection_and_empty(content_agent):
    """Vérifie que la génération de hooks neutralise les injections de code et les thématiques vides."""
    # Injection de balises script
    hook_xss = content_agent.generate_viral_hooks("<script>alert('xss')</script>")
    assert "<script>" not in hook_xss["topic"]
    assert "alert" not in hook_xss["topic"]
    assert len(hook_xss["primary_hook"]) > 10

    # Injection SQL
    hook_sql = content_agent.generate_viral_hooks("SELECT * FROM users WHERE admin = 1;")
    assert "SELECT *" not in hook_sql["topic"]

    # Injection Python exec
    hook_py = content_agent.generate_viral_hooks("exec('import os; os.system(\"rm -rf /\")')")
    assert "exec(" not in hook_py["topic"]

    # Thématique vide
    hook_empty = content_agent.generate_viral_hooks("")
    assert hook_empty["topic"] == "E-Commerce & Rentabilité"


def test_affiliate_drop_edge_case_prices(content_agent):
    """Vérifie la génération de drop d'affiliation avec prix promotionnel supérieur au prix de base ou négatif."""
    # Prix promo supérieur au prix initial (pas de réduction)
    drop_high = content_agent.generate_affiliate_drop(
        product_name="Sneakers Retro",
        original_price=50.0,
        promo_price=70.0
    )
    assert drop_high["discount_percent"] == 0
    assert drop_high["savings_eur"] == 0.0

    # Prix promotionnel négatif
    drop_neg = content_agent.generate_affiliate_drop(
        product_name="Casque Bluetooth",
        original_price=100.0,
        promo_price=-10.0
    )
    assert drop_neg["promo_price_eur"] == 0.0
    assert drop_neg["discount_percent"] == 100


# ============================================================================
# 5. BACKGROUND WATCHER (CRON JOBS EN RAFALE & ANTI-FUITE MEMOIRE)
# ============================================================================

def test_background_guardian_burst_cron_execution():
    """Vérifie que 100 déclenchements consécutifs en rafale ne provoquent aucune fuite mémoire."""
    guardian = BackgroundGuardian()

    # Déclenchements en rafale des 3 cron jobs
    job_ids = [
        "cron_08h00_morning_summary",
        "cron_13h00_midday_checkpoint",
        "cron_22h00_nightly_finance"
    ]

    for i in range(100):
        target_job = job_ids[i % len(job_ids)]
        res = guardian.execute_cron_job(target_job)
        assert res["status"] == "COMPLETED"

    # Vérification anti-fuite mémoire : l'historique doit être strictement plafonné à 30 entrées
    assert len(guardian.cron_history) <= 30
    assert len(guardian.execution_history) <= 30
    assert len(guardian.activity_log) <= 50

    # Vérification de l'état
    status = guardian.get_status()
    assert "execution_history" in status
    assert len(status["execution_history"]) <= 10
