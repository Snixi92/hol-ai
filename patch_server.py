import re

path = r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\server.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Briefing morning alias
briefing_snippet = """@app.get("/api/briefing/morning")
async def get_morning_briefing_alias_endpoint(
    city: str = "Paris",
    topic: str = "general",
    force_refresh: bool = False,
    persona: Optional[str] = None,
    include_deals: bool = False
):
    \"\"\"Alias officiel pour /api/briefing/morning.\"\"\"
    from src.services.morning_briefing import MorningBriefingService
    return await MorningBriefingService.generate_briefing(
        city=city,
        topic=topic,
        force_refresh=force_refresh,
        force_persona=persona,
        include_deals=include_deals
    )
"""

if "/api/briefing/morning" not in content:
    target = '@app.get("/api/briefing/live")'
    if target in content:
        content = content.replace(target, briefing_snippet + "\n\n" + target)
        print("Added /api/briefing/morning")

# 2. Ecommerce search / arbitrate GET alias
ecom_snippet = """@app.get("/api/ecommerce/search")
@app.get("/api/ecommerce/arbitrate")
async def ecommerce_search_alias_get_endpoint(
    query: Optional[str] = None,
    q: Optional[str] = None,
    merchant: Optional[str] = None
):
    \"\"\"Alias GET pour la recherche et l'arbitrage e-commerce décisionnel.\"\"\"
    target_q = query or q or ""
    from src.services.ecommerce_arbitration import EcommerceArbitrationService
    return await EcommerceArbitrationService.generate_decision_card(query=target_q, preferred_merchant=merchant)
"""

if "/api/ecommerce/search" not in content:
    target2 = '@app.post("/api/ecommerce/arbitrate")'
    if target2 in content:
        content = content.replace(target2, ecom_snippet + "\n\n" + target2)
        print("Added /api/ecommerce/search and GET /api/ecommerce/arbitrate")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("server.py updated successfully")
