import sys
import time
import json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add core-engine to path
core_engine_path = Path(r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine")
if str(core_engine_path) not in sys.path:
    sys.path.insert(0, str(core_engine_path))

from src.services.ecommerce_arbitration import EcommerceArbitrationService
from src.services.second_hand_hunter import SecondHandHunterService
from src.services.stealth_product_scraper import StealthProductScraper
from src.services.omni_scraper import OmniScraperService

results = {
    "agent": "Agent-1-Ecommerce-Sourcing",
    "tests_run": 0,
    "tests_passed": 0,
    "tests_failed": 0,
    "failures": [],
    "details": []
}

def record_test(name: str, passed: bool, info: str = ""):
    results["tests_run"] += 1
    if passed:
        results["tests_passed"] += 1
        print(f"  [PASS] {name} {info}")
    else:
        results["tests_failed"] += 1
        results["failures"].append({"name": name, "info": info})
        print(f"  [FAIL] {name} {info}")

print("=== STARTING AGENT 1: E-COMMERCE, SOURCING & SCRAPERS AUDIT ===")

# Test 1: EcommerceArbitrationEngine - Standard product
print("\n--- 1. Ecommerce Arbitration Tests ---")
test_queries = [
    "iPhone 13 128Go",
    "AirPods Pro 2",
    "Sony WH-1000XM5",
    "souris bleuthooth sans fil < 30eur",
    "ecran iphon xr pas cher"
]

for q in test_queries:
    t0 = time.time()
    try:
        card = EcommerceArbitrationService.generate_decision_card_sync(q)
        lat = round((time.time() - t0) * 1000, 1)
        valid = (
            card is not None and 
            isinstance(card, dict) and 
            "merchant" in card and 
            "primary_recommendation" in card
        )
        p_rec = card.get("primary_recommendation", {}) if card else {}
        price = p_rec.get("price")
        m_name = card.get("merchant", {}).get("name", "N/A") if card else "N/A"
        record_test(
            f"Arbitration for '{q}'", 
            valid, 
            f"({lat}ms) -> Marchand: {m_name}, Prix: {price}€, Alts: {len(card.get('alternatives', [])) if card else 0}"
        )
    except Exception as e:
        record_test(f"Arbitration for '{q}'", False, f"Exception: {e}")

# Test 2: SecondHandHunterService - Market comparison across platforms
print("\n--- 2. Second-Hand & Reconditioned Market Tests ---")
second_hand_queries = ["iPhone 12", "PlayStation 5", "MacBook Air M1"]
for prod in second_hand_queries:
    t0 = time.time()
    try:
        sh_data = SecondHandHunterService.hunt_second_hand(prod)
        lat = round((time.time() - t0) * 1000, 1)
        valid = (
            isinstance(sh_data, dict) and 
            "best_deals" in sh_data and 
            len(sh_data["best_deals"]) > 0 and 
            "current_drop_price_eur" in sh_data
        )
        min_p = sh_data.get("current_drop_price_eur") if sh_data else 0
        deals_count = len(sh_data.get("best_deals", [])) if sh_data else 0
        record_test(
            f"Second-hand hunt for '{prod}'", 
            valid, 
            f"({lat}ms) -> Prix d'appel: {min_p}€, {deals_count} plateformes vérifiées"
        )
    except Exception as e:
        record_test(f"Second-hand hunt for '{prod}'", False, f"Exception: {e}")

# Test 3: StealthProductScraper resilience & real scraping
print("\n--- 3. Stealth Product Scraper Tests ---")
try:
    t0 = time.time()
    deal = StealthProductScraper.scrape_live_deal("clavier mécanique")
    lat = round((time.time() - t0) * 1000, 1)
    p_name = deal.get("product") or deal.get("title")
    valid = isinstance(deal, dict) and bool(p_name) and "product_url" in deal
    record_test("StealthProductScraper scrape_live_deal", valid, f"({lat}ms) -> Produit: {p_name[:35]}..., Hub/URL: {deal.get('platform')}")
except Exception as e:
    record_test("StealthProductScraper scrape_live_deal", False, f"Exception: {e}")

# Test 4: OmniScraper multi-source fallback
print("\n--- 4. OmniScraper Tests ---")
try:
    t0 = time.time()
    omni_res = OmniScraperService.hunt_omni_product("aspirateur sans fil")
    lat = round((time.time() - t0) * 1000, 1)
    valid = isinstance(omni_res, (list, dict))
    record_test("OmniScraper multi-source search", valid, f"({lat}ms)")
except Exception as e:
    record_test("OmniScraper multi-source search", False, f"Exception: {e}")

# Test 5: Budget & Contradiction handling
print("\n--- 5. Edge-Cases & Impossible Requests ---")
impossible_q = "MacBook Pro M3 Max neuf pour 50 euros"
try:
    card = EcommerceArbitrationService.generate_decision_card_sync(impossible_q)
    # The primary recommendation price should reflect reality (not 50€!)
    p_rec = card.get("primary_recommendation", {}) if card else {}
    real_price = p_rec.get("price", 0)
    # Realistic check: An M3 Max cannot be 50€
    valid = real_price is None or real_price > 1000
    record_test("Reality check on impossible budget", valid, f"Price: {real_price}€ (not hallucinated to 50€)")
except Exception as e:
    record_test("Reality check on impossible budget", False, f"Exception: {e}")

print("\n=== AGENT 1 AUDIT SUMMARY ===")
print(f"Total Tests: {results['tests_run']} | Passed: {results['tests_passed']} | Failed: {results['tests_failed']}")
if results['failures']:
    print("Failures:")
    for f in results['failures']:
        print(f" - {f['name']}: {f['info']}")

# Output json report
report_path = core_engine_path.parent.parent / "scratch" / "multi_agent_audit" / "agent1_report.json"
report_path.parent.mkdir(parents=True, exist_ok=True)
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"Report saved to {report_path}")
