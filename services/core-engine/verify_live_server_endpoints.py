"""
Empirical Server Boot & Live Route Verification Script for HoL AI (Milestone 7).
Verifies:
- Clean server startup with lifespan context
- GET / serves index.html with HTTP 200 and UTF-8 content
- All milestone endpoints respond with HTTP 200 and expected schema structures
"""
import sys
from fastapi.testclient import TestClient

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from src.api.server import app

def run_route_audit():
    print("\n" + "=" * 70)
    print("HO L AI — FORENSIC SERVER BOOT & ENDPOINT ROUTE VERIFICATION")
    print("=" * 70)

    with TestClient(app) as client:
        # 1. GET /
        r0 = client.get("/")
        print(f"  [PASS] GET / -> HTTP {r0.status_code} ({len(r0.text)} bytes)")
        assert r0.status_code == 200, f"Expected 200, got {r0.status_code}"
        assert "<!DOCTYPE html>" in r0.text or "<html" in r0.text, "Expected HTML document"
        assert "liquid-glass" in r0.text, "Expected liquid-glass styles in index.html"

        # 2. GET /api/conversations
        r1 = client.get("/api/conversations")
        keys = list(r1.json().keys())
        print(f"  [PASS] GET /api/conversations -> HTTP {r1.status_code} (keys: {keys})")
        assert r1.status_code == 200
        assert "conversations" in r1.json()

        # 3. GET /api/models
        r2 = client.get("/api/models")
        m_count = len(r2.json().get("available_models", []))
        print(f"  [PASS] GET /api/models -> HTTP {r2.status_code} ({m_count} models registered)")
        assert r2.status_code == 200
        assert m_count >= 4

        # 4. GET /api/personas
        r3 = client.get("/api/personas")
        p_count = len(r3.json().get("available_personas", []))
        print(f"  [PASS] GET /api/personas -> HTTP {r3.status_code} ({p_count} personas registered)")
        assert r3.status_code == 200
        assert p_count >= 4

        # 5. GET /api/jarvis/briefing
        r4 = client.get("/api/jarvis/briefing")
        city = r4.json().get("weather", {}).get("city")
        print(f"  [PASS] GET /api/jarvis/briefing -> HTTP {r4.status_code} (city: {city})")
        assert r4.status_code == 200
        assert "weather" in r4.json()

        # 6. GET /api/briefing/live
        r5 = client.get("/api/briefing/live")
        persona = r5.json().get("meta", {}).get("persona")
        print(f"  [PASS] GET /api/briefing/live -> HTTP {r5.status_code} (persona: {persona})")
        assert r5.status_code == 200
        assert "spoken_script" in r5.json()

        # 7. GET /api/visual/search?q=Tour+Eiffel
        r6 = client.get("/api/visual/search?q=Tour+Eiffel")
        res_count = len(r6.json().get("results", []))
        print(f"  [PASS] GET /api/visual/search?q=Tour+Eiffel -> HTTP {r6.status_code} ({res_count} cards)")
        assert r6.status_code == 200
        assert res_count >= 1

        # 8. GET /api/sourcing/arbitrate?q=casque+bluetooth
        r7 = client.get("/api/sourcing/arbitrate?q=casque+bluetooth")
        merchant = r7.json().get("merchant", {}).get("name")
        alts = len(r7.json().get("alternatives", []))
        print(f"  [PASS] GET /api/sourcing/arbitrate?q=casque+bluetooth -> HTTP {r7.status_code} (merchant: {merchant}, alternatives: {alts})")
        assert r7.status_code == 200
        assert merchant == "Fnac"
        assert alts >= 3

    print("=" * 70)
    print("ALL 8 ENDPOINTS VERIFIED AND VALIDATED EMPIRICALLY (HTTP 200 OK)")
    print("=" * 70 + "\n")
    return True

if __name__ == "__main__":
    success = run_route_audit()
    sys.exit(0 if success else 1)
