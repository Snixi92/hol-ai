# DISPATCH — Agent 2: Benchmark Autonome et Intégration des Fonctionnalités IA (R3)

## Identity
- Role: Agent 2 (AI Features & Benchmark Specialist)
- Type: `teamwork_worker`
- Working Directory: `C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\.agents\teamwork\agent2_worker`

## Inputs & Blueprints to Read
1. `C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\.agents\teamwork\ORIGINAL_REQUEST.md` (R3 requirements)
2. `C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\.agents\teamwork\orchestrator\PROJECT.md`
3. `C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\.agents\teamwork\survey_backend\survey_backend_report.md` (§6, §9.2)

## Mandatory Scope & Deliverables (R3)
1. **Benchmark Documentation Matrix**:
   - Produce a structured benchmark table documenting features across ChatGPT, Claude, Gemini, and Perplexity, identifying key features integrated into HoL AI (Dynamic models, Personas, Perplexity citations, Thinking budget, Artifacts).
2. **Backend Engine Upgrades (`services/core-engine/src/services/cognitive_engine.py`)**:
   - Add dynamic model selection (`gemini-3.5-flash-lite`, `gemini-flash-latest`, `gemini-2.5-flash`, etc.).
   - Implement dynamic Personas (`big_sis`, `architect`, `executive`, `tutor`) in `_build_system_prompt`.
   - Implement Perplexity-Style Citation Engine: extract and standardize web search sources into structured citations (`index`, `title`, `domain`, `url`, `snippet`) and map `[1]`, `[2]` markers into response text and stream events.
3. **API Endpoints in `services/core-engine/src/api/server.py`**:
   - `GET /api/models`: Return available model IDs, names, provider, context limits, and capabilities.
   - `GET /api/personas`: Return available personas (id, name, tone, description).
   - Update `ChatMessageRequest` and endpoints (`/api/chat`, `/api/chat/stream`) to accept `model` and `persona`.
4. **Automated Test Suite**:
   - Create `services/core-engine/tests/test_autonomous_ai_features.py` testing model listing, persona prompt injection, citation formatting, and chat endpoints with model/persona parameters.
   - Run pytest and confirm 100% pass rate.
5. **Handoff**:
   - Deliver `handoff.md` with complete evidence and test results.

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.


## 2026-11-03T20:27:46Z
From: 64736e38-361b-4111-896d-8c7e6ac79637
You are Agent 2 (AI Features & Benchmark Specialist) for HoL AI.
Your working directory is: C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\.agents\teamwork\agent2_worker
Read ORIGINAL_REQUEST.md at: C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\.agents\teamwork\ORIGINAL_REQUEST.md
Read PROJECT.md at: C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\.agents\teamwork\orchestrator\PROJECT.md
Read DISPATCH.md at: C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\.agents\teamwork\agent2_worker\DISPATCH.md
Read Backend Survey Blueprint at: C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\.agents\teamwork\survey_backend\survey_backend_report.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your mission:
Implement Requirement R3 completely:
1. Conduct and document the AI Benchmark comparing ChatGPT, Claude, Gemini, and Perplexity in `ai_benchmark_matrix.md` in your working directory.
2. Upgrade `services/core-engine/src/services/cognitive_engine.py`:
   - Implement dynamic model selection supporting requested model IDs.
   - Implement dynamic Personas (`big_sis`, `architect`, `executive`, `tutor`) adapting tone and system prompt.
   - Implement Perplexity-Style Citation Engine standardizing web search results into structured citations (`index`, `title`, `domain`, `url`, `snippet`) and clickable `[1]`, `[2]` citation markers.
3. Expose REST endpoints in `services/core-engine/src/api/server.py`:
   - `GET /api/models` (available models list with descriptions).
   - `GET /api/personas` (available personas list with descriptions).
   - Support `model` and `persona` parameters in `ChatMessageRequest`, `/api/chat`, and `/api/chat/stream`.
4. Create comprehensive automated test suite `services/core-engine/tests/test_autonomous_ai_features.py` testing models, personas, citations, and endpoints.
5. Run pytest verification and confirm 100% pass rate with zero regression on existing suites.
6. Write handoff.md following the Handoff Protocol and notify orchestrator.


## 2026-11-03T20:38:15Z
From: 64736e38-361b-4111-896d-8c7e6ac79637
**Context**: Agent 2 (AI Benchmark & Features R3) Status Check
**Content**: Checking in on your implementation progress. We noted that `ai_benchmark_matrix.md` has been successfully produced. How is the implementation in `cognitive_engine.py` (models, personas, citations), `server.py`, and `test_autonomous_ai_features.py` progressing?
**Action**: Please report your current step, any hurdles, and your ETA for test execution and handoff.

## 2026-11-03T20:48:49Z
From: 64736e38-361b-4111-896d-8c7e6ac79637
**Context**: Agent 2 (AI Benchmark & Features R3) Progress Check
**Content**: We see `test_autonomous_ai_features.py` has been created. Are the test executions complete?
**Action**: Please provide your test pass counts, any hurdles, and ETA for handoff.md.
