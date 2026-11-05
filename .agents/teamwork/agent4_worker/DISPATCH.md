# DISPATCH — Agent 4: Automatisation Matinale et Live News (R5)

## Identity
- Role: Agent 4 (Morning Briefing & Live News Specialist)
- Type: `teamwork_worker`
- Working Directory: `C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\.agents\teamwork\agent4_worker`

## Inputs & Blueprints to Read
1. `C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\.agents\teamwork\ORIGINAL_REQUEST.md` (R5 requirements)
2. `C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\.agents\teamwork\orchestrator\PROJECT.md`
3. `C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\.agents\teamwork\survey_modules\survey_modules_report.md` (§3, §4, §5)

## Mandatory Scope & Deliverables (R5)
1. **Module `services/core-engine/src/services/morning_briefing.py`**:
   - Live Weather: Open-Meteo Geocoding and Forecast API (0-auth, dynamic city support, resilient async httpx client).
   - Live Real News: Google News RSS (`https://news.google.com/rss?hl=fr&gl=FR&ceid=FR:fr`) and Le Monde RSS, XML parsing, real headlines with source links.
   - Anti-Repetition Permutation Engine:
     - 5 Personas (`executive`, `tech_pioneer`, `dynamic_coach`, `telegraphic`, `storyteller`).
     - 4 Structural Permutations (`weather_first`, `news_first`, `trends_first`, `dashboard_split`).
     - Ring buffer tracking last runs guaranteeing zero adjacent structural or persona repetition.
     - Dynamic prompt generator for LLM synthesis ensuring unique editorial angle and phrasing on every run.
2. **FastAPI Server Integration**:
   - Wire `MorningBriefingService` into `services/core-engine/src/api/server.py` at `GET /api/jarvis/briefing` (supporting optional query params `city`, `force_refresh`, `persona`).
   - Wire pre-LLM grounding or tool in `cognitive_engine.py` for queries asking for the morning briefing.
3. **Automated Integration Test Suite**:
   - Create `services/core-engine/tests/test_morning_briefing_live.py`.
   - Test live weather, live RSS news parsing, anti-repetition permutation verification (assert two consecutive runs have different personas, structures, and text), and endpoint `GET /api/jarvis/briefing`.
   - Run pytest and confirm 100% pass rate.
4. **Handoff**:
   - Deliver `handoff.md` with complete evidence and test results.

## 2026-11-03T21:25:50Z
You are Agent 4 (Morning Briefing & Live News Specialist) for HoL AI.
Working directory: C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\.agents\teamwork\agent4_worker
Mission: Implement Requirement R5 completely.
