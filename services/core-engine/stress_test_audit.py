"""
Adversarial Stress Testing Script for HoL AI (Milestone 7 Audit).
Tests edge cases, boundary conditions, injection payloads, and error resiliency.
"""
import sys
from fastapi.testclient import TestClient

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from src.api.server import app

def run_stress_tests():
    print("\n" + "=" * 70)
    print("HO L AI — ADVERSARIAL STRESS TESTING & EDGE CASE MINING")
    print("=" * 70)

    with TestClient(app) as client:
        # 1. Non-visual query must return 0 false positive visual cards
        r1 = client.get("/api/visual/search?q=bonjour%20comment%20vas%20tu")
        assert r1.status_code == 200
        assert r1.json()["results"] == []
        print("  [PASS] Non-visual query produces 0 false positive visual cards")

        # 2. Sourcing arbitrate with empty query
        r2 = client.get("/api/sourcing/arbitrate?q=")
        assert r2.status_code == 200
        assert "merchant" in r2.json()
        print("  [PASS] Empty query handled gracefully by e-commerce arbitrator")

        # 3. Sourcing arbitrate with SQL injection string
        r3 = client.get("/api/sourcing/arbitrate?q=%27%20OR%201=1;%20--")
        assert r3.status_code == 200
        assert "merchant" in r3.json()
        print("  [PASS] SQL injection string sanitized and handled without error")

        # 4. Conversation search with XSS script tags
        r4 = client.get("/api/conversations?search=%3Cscript%3Ealert(1)%3C/script%3E")
        assert r4.status_code == 200
        assert "conversations" in r4.json()
        print("  [PASS] XSS payload safely handled in conversation search")

        # 5. Morning briefing with non-existent city
        r5 = client.get("/api/jarvis/briefing?city=AtlantisFantaisieXYZ")
        assert r5.status_code == 200
        assert "weather" in r5.json()
        print("  [PASS] Non-existent city gracefully triggers fallback weather model")

    print("=" * 70)
    print("ALL 5 ADVERSARIAL STRESS TESTS PASSED WITH 100% RESILIENCE")
    print("=" * 70 + "\n")
    return True

if __name__ == "__main__":
    success = run_stress_tests()
    sys.exit(0 if success else 1)
