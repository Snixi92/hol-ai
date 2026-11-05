# DISPATCH — Agent 6 Worker

## 2026-11-03T22:08:00Z
**Mission**: Milestone 6 / Requirement R7 (Optimiseur E-Commerce & Sourcing Décisionnel)

### Scope & Responsibilities
1. **Single Reference Merchant Arbitration & Same-Merchant Alternatives**:
   - Create `services/core-engine/src/services/ecommerce_arbitration.py`.
   - Implement `EcommerceArbitrationService`:
     - Shopping intent & category extraction (audio, high-tech, consoles, électroménager, informatique, maison/bricolage, etc.).
     - Single Reference Merchant arbitration algorithm:
       - Strictly selects ONE merchant per query: `Amazon`, `Cdiscount`, or `Fnac`.
       - Rationale & scoring based on query affinity (e.g. Fnac for high-tech audio/photo/culture/gaming; Cdiscount for électroménager/home/discount; Amazon for computing/accessories/universal).
       - Enforces ZERO multi-merchant mixing (no confusion).
     - Same-Merchant Alternatives Generator:
       - For the chosen merchant, produces:
         1. Primary recommendation (Best Overall Choice) with title, price, specs, rating, pros/cons, verified merchant URL.
         2. Exactly 3 to 4 distinct alternatives from that SAME chosen merchant (e.g. Budget Choice, Best Value / Mid-tier, Flagship / Pro Choice, Compact / Alternative model) with differentiated specs and prices.
     - Returns standardized payload:
       ```python
       {
           "type": "ecommerce_arbitration_card",
           "merchant": {
               "name": "Fnac",  # or "Amazon" or "Cdiscount"
               "badge": "Marchand de Référence Sélectionné",
               "arbitration_reason": "Spécialiste audio haute-fidélité et garantie SAV certifiée"
           },
           "query": "casque bluetooth antibruit",
           "primary_recommendation": {
               "title": "Sony WH-1000XM5",
               "price": 329.99,
               "currency": "EUR",
               "rating": 4.8,
               "verdict": "Meilleure réduction de bruit active et autonomie 30h",
               "specs": ["ANC HD QN1", "Autonomie 30h", "Multipoint Bluetooth 5.2", "LDAC Hi-Res"],
               "url": "https://www.fnac.com/..."
           },
           "alternatives": [
               {
                   "tier": "Alternative Économique",
                   "title": "Sony WH-CH720N",
                   "price": 99.99,
                   "specs": ["ANC V1", "Autonomie 35h", "Poids plume 192g"],
                   "url": "https://www.fnac.com/..."
               },
               {
                   "tier": "Rapport Qualité/Prix",
                   "title": "Bose QuietComfort SE",
                   "price": 199.99,
                   "specs": ["Confort légendaire", "Autonomie 24h", "Mode Aware"],
                   "url": "https://www.fnac.com/..."
               },
               {
                   "tier": "Alternative Premium Audiophile",
                   "title": "Sennheiser Momentum 4 Wireless",
                   "price": 279.99,
                   "specs": ["Autonomie colossale 60h", "Transducteurs 42mm", "Son audiophile"],
                   "url": "https://www.fnac.com/..."
               }
           ]
       }
       ```

2. **REST Endpoints & Cognitive Engine Hook**:
   - In `services/core-engine/src/api/server.py`:
     - Expose `GET /api/sourcing/arbitrate` (params: `q: str`, `merchant: Optional[str] = None`).
     - Expose `POST /api/sourcing/arbitrate` with JSON body.
   - In `services/core-engine/src/services/cognitive_engine.py`:
     - Register `ecommerce_sourcing_arbitration` tool in `CognitiveAgentEngine.get_registered_tools()`.
     - In chat processing, when shopping / buying / product recommendation intent is detected, attach `ecommerce_arbitration_card` into `cards` list in the response.

3. **Frontend Apple Liquid Glass Rendering**:
   - In `services/core-engine/src/api/static/index.html`:
     - In `renderChatCard`, render `ecommerce_arbitration_card`:
       - Apple Liquid Glass card with merchant badge header (`Marchand de Référence : Fnac`), arbitration rationale pill.
       - Primary product spotlight with large price tag, verdict badge, specs tags, and direct buy link.
       - Grid / list of 3-4 same-merchant alternatives showing tier chip (e.g. "Alternative Économique", "Rapport Qualité/Prix", "Premium"), price, specs, and external link.
       - Vector icons only (Lucide icons `<i data-lucide="...">`).

4. **Tests & Regression Suite**:
   - Create `services/core-engine/tests/test_ecommerce_arbitration.py`:
     - Test merchant arbitration logic: verify that high-tech/audio picks Fnac, appliance picks Cdiscount, computing picks Amazon.
     - Test same-merchant integrity: verify that all alternatives strictly match the primary merchant (no cross-merchant mixing).
     - Test 3-4 alternatives count and pricing tier differentiation.
     - Test REST API endpoint `/api/sourcing/arbitrate`.
     - Test frontend HTML contains `ecommerce_arbitration_card` rendering and classes.
   - Run full regression suite:
     `python -m pytest tests/test_conversation_persistence.py tests/test_autonomous_ai_features.py tests/test_morning_briefing_live.py tests/test_visual_search_enrichment.py tests/test_ecommerce_arbitration.py -v`.
     Ensure 100% pass!

5. **Mandatory Integrity Warning**:
   DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
