# Project: HoL AI — Production Refonte & Multi-Agents Upgrade

## Architecture
HoL AI undergoes a production-ready overhaul featuring advanced capabilities from leader chatbots (ChatGPT, Claude, Gemini, Perplexity), an Apple iOS 27 Liquid Glass design system, and specialized autonomous modules:
1. **Core Backend & Engine (`services/core-engine`)**:
   - FastAPI server with SSE streaming (`/api/chat/stream`), JSON chat (`/api/chat`), and REST APIs.
   - Cognitive Engine (Gemini SDK with Thinking Budget) integrating 45+ tools and 1,079 public APIs.
   - SQLite persistent conversation storage (`data/conversations.db` with WAL mode).
   - Dynamic model switcher and persona selector (Big Sis, Executive, Tutor).
   - Autonomous Morning Briefing Service (Google News RSS + Open-Meteo live weather + 5-persona/4-structure anti-repetition engine).
   - Visual Search Engine (entity extraction + Wikipedia REST API 4K/5K native photos).
   - E-Commerce Arbitration Service (single reference merchant per query + 3-4 same-merchant alternatives).
2. **Frontend Apple Liquid Glass SPA (`services/core-engine/src/api/static/index.html`)**:
   - Native Apple Liquid Glass styling (`backdrop-filter: blur(24px) saturate(180%) contrast(105%)`, 1px specular border, inset shadow reflections, spring physics animations).
   - Luxury monochrome neutral palette: titanium, anthracite, obsidian, off-white, transparent glass (zero emojis, vector icons only).
   - Floating Pill Input Dock centered at bottom.
   - Persistent History Sidebar with chronological sections (*Aujourd'hui*, *7 derniers jours*, *30 jours*), auto-title, pin, archive, delete, Markdown & JSON export, and instant context restoration.
   - Perplexity-style interactive clickable citation badges `[1]`, `[2]`.
   - Liquid Glass visual media cards with full-screen interactive lightbox zoom modal (`#liquid-image-lightbox`).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | SQLite Conversation Store | Local database storage for discussions, messages, metadata | M1 (Agent 1) | survey_backend |
| 2 | Conversation Management REST APIs | Endpoints for list, get, patch, delete, export, auto-title | M1 (Agent 1) | survey_backend |
| 3 | Frontend Persistent History Sidebar | Chronological grouping (Aujourd'hui, 7 jours, 30 jours), auto-title, pin, archive, delete | M1 (Agent 1) | survey_frontend |
| 4 | Conversation Export & Context Restore | Export to Markdown & JSON; instant context restore on click | M1 (Agent 1) | survey_frontend |
| 5 | Leader Chatbot AI Benchmark | Benchmark matrix of ChatGPT, Claude, Gemini, Perplexity features | M2 (Agent 2) | ORIGINAL_REQUEST |
| 6 | Dynamic Model Selection | Configurable model switching in backend and UI | M2 (Agent 2) | survey_backend |
| 7 | Multi-Persona & Tone Selector | Adaptable system prompt (Big Sis, Executive, Tutor) | M2 (Agent 2) | survey_backend |
| 8 | Perplexity-Style Citation Badges | Standardized citation objects and clickable badges [1], [2] | M2 (Agent 2) | survey_backend |
| 9 | Apple Liquid Glass Design System | Calibrated blur(24px) saturate(180%), 1px specular borders, spring physics | M3 (Agent 3) | survey_frontend |
| 10 | Luxury Monochrome Neutral Palette | Titanium, anthracite, obsidian, transparent glass; zero emoji clutter | M3 (Agent 3) | survey_frontend |
| 11 | Floating Pill Input Dock | Centered bottom pill dock with fluid micro-interactions | M3 (Agent 3) | survey_frontend |
| 12 | Advanced Markdown & Code Display | Enhanced typography, syntax highlighting, copy button | M3 (Agent 3) | survey_frontend |
| 13 | Live News & Weather Ingestion | Google News RSS + Open-Meteo Geocoding/Forecast (0-auth) | M4 (Agent 4) | survey_modules |
| 14 | Anti-Repetition Briefing Engine | 5-persona / 4-structure permutation engine with ring buffer | M4 (Agent 4) | survey_modules |
| 15 | Visual Entity Extraction & 4K Sourcing | Wikipedia REST API 4K/5K native photos without rate limits | M5 (Agent 5) | survey_modules |
| 16 | Liquid Glass Visual Card & Lightbox | High-res media card with modal zoom overlay on click | M5 (Agent 5) | survey_modules |
| 17 | Single Merchant E-Commerce Arbitration | Strict single reference merchant per query (Amazon/Cdiscount/Fnac) | M6 (Agent 6) | survey_modules |
| 18 | Same-Merchant Alternative Sourcing | 3-4 distinct alternatives strictly from chosen merchant | M6 (Agent 6) | survey_modules |
| 19 | Comprehensive Integration Test Suite | Automated test suite verifying all endpoints, persistence, modules | M7 (Integration) | survey_backend |
| 20 | Server Startup & SPA Serving Verification | Validate port 8000 launch and zero console errors | M7 (Integration) | ORIGINAL_REQUEST |
| 21 | Final Detailed Execution Report | Comprehensive report with all 5 mandatory sections | M8 (Report) | ORIGINAL_REQUEST |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M0 | Survey & Architecture Blueprint | 3 Explorers codebase mapping and technical blueprints | none | DONE |
| M1 | Agent 1: Persistence & History (R2) | SQLite backend store, REST APIs, frontend sidebar, auto-title, pin/archive/export | M0 | DONE |
| M2 | Agent 2: AI Benchmark & Features (R3) | Leader chatbot benchmark, dynamic models, personas, Perplexity-style citations | M1 | DONE |
| M3 | Agent 3: UI/UX Apple Liquid Glass (R4) | Apple Liquid Glass calibration, luxury palette, floating pill dock, emoji cleanup | M2 | DONE |
| M4 | Agent 4: Morning Briefing & Live News (R5) | Live RSS news, Open-Meteo weather, anti-repetition permutation engine | M3 | DONE |
| M5 | Agent 5: Visual Search & Image Card (R6) | Visual entity extraction, Wikipedia 4K photos, Liquid Glass card & Lightbox modal | M4 | DONE |
| M6 | Agent 6: E-Commerce Decision Optimizer (R7) | Single-merchant arbitration, same-merchant alternative recommendations | M5 | DONE |
| M7 | System Integration & Automated Testing | Full test execution, regression verification, port 8000 launch check | M1-M6 | DONE |
| M8 | Forensic Audit & Final Execution Report (R1) | Forensic integrity audit + Final Detailed Execution Report (5 sections) | M7 | DONE |

## Code Layout & File Boundaries
- `services/core-engine/src/services/conversation_store.py` (Owned by Agent 1)
- `services/core-engine/tests/test_conversation_persistence.py` (Owned by Agent 1)
- `services/core-engine/src/services/cognitive_engine.py` (Owned by Agent 2, with hooks for M4, M5, M6)
- `services/core-engine/tests/test_autonomous_ai_features.py` (Owned by Agent 2)
- `services/core-engine/src/api/static/index.html` (Owned sequentially: Agent 1 for history sidebar, Agent 3 for design system & dock, Agent 5 for lightbox)
- `services/core-engine/src/services/morning_briefing.py` (Owned by Agent 4)
- `services/core-engine/tests/test_morning_briefing_live.py` (Owned by Agent 4)
- `services/core-engine/src/services/visual_search.py` (Owned by Agent 5)
- `services/core-engine/tests/test_visual_search_enrichment.py` (Owned by Agent 5)
- `services/core-engine/src/services/ecommerce_arbitration.py` (Owned by Agent 6)
- `services/core-engine/tests/test_ecommerce_arbitration.py` (Owned by Agent 6)
- `services/core-engine/src/api/server.py` (Shared router, modified sequentially by specific agents)
