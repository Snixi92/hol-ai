# Système Jarvis Thomas Berton - Plan d'Implémentation Complet

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construire l'intégralité du système Jarvis démontré par Thomas Berton dans sa vidéo YouTube (pilotage d'applications Windows, génération de code et applications locales avec aperçu direct dans Chrome, graphiques dynamiques de données, veille IA, posts LinkedIn avec génération d'images, et protocole de test complet).

**Architecture:** Moteur cognitif ReAct (`CognitiveAgentEngine`) étendu avec 4 nouveaux modules spécialisés (`AppLauncherService`, `CodeAppGeneratorService`, `ChartGeneratorService`, `SocialMediaAgentService`). Intégration dans l'interface Cockpit HUD de `src/api/static/index.html` avec rendu dynamique des cartes applicatives, aperçu direct des jeux/apps HTML générés, et graphiques HUD animés.

**Tech Stack:** Python 3.10+, FastAPI, Google GenAI SDK (Gemini 3.5 Flash Lite), Windows OS APIs (`subprocess`, `os.startfile`, `webbrowser`), Vanilla JS / HTML5 Canvas & SVG pour le cockpit HUD sans dépendance externe lourde.

**Spec:** Vidéo YouTube `https://www.youtube.com/watch?v=L0Xf2CyZur0` (Thomas Berton - "J'ai Créé mon Propre JARVIS avec Claude Code").

## Global Constraints

- 100% Gratuit : Aucune dépendance payante (ni abonnement Claude Pro 20€/m, ni OpenAI Realtime payant à la seconde).
- Sécurité OS : Les commandes Windows sont sanitisées et isolées pour éviter toute injection arbitraire.
- Tolérance aux pannes : Fallback gracieux si une application n'est pas installée sur le PC (avec proposition d'alternative web).
- Zéro régression : Les 129 tests existants doivent rester verts à 100%.

## Review Focus

1. Tentative d'ouverture d'une application non installée sur Windows (ex: "ouvre Photoshop" quand il n'existe pas) -> Retourne un message explicite et propose la version web sans crasher.
2. Génération de code HTML malicieux ou corrompu -> Validation et assainissement du code avant écriture sur le disque.
3. Conflit de chemin de fichier pour les applications locales -> Isolation dans `scratch/apps/<app_name>/`.
4. Rendu de graphiques avec des valeurs nulles ou négatives -> Rendu graphique robuste sans division par zéro.
5. Latence de synthèse vocale lors d'actions longues -> Accusé de réception vocal immédiat avant l'exécution lourde.

---

### Task 1: Windows App Launcher & Multi-screen Controller

**Files:**
- Create: `src/services/app_launcher.py`
- Test: `tests/test_app_launcher.py`

**Interfaces:**
- Produces: `AppLauncherService.launch_application(app_name: str, target_screen: str = "principal") -> Dict[str, Any]`

- [ ] **Step 1: Write the failing test in `tests/test_app_launcher.py`**
- [ ] **Step 2: Run test to verify it fails (`pytest tests/test_app_launcher.py`)**
- [ ] **Step 3: Implement `AppLauncherService` in `src/services/app_launcher.py`**
- [ ] **Step 4: Run test to verify it passes**

---

### Task 2: Autonomous Local Code & App Generator with Live Browser Preview

**Files:**
- Create: `src/services/code_app_generator.py`
- Modify: `src/api/server.py` (servir les fichiers générés dans `/apps/{app_name}/...`)
- Test: `tests/test_code_app_generator.py`

**Interfaces:**
- Produces: `CodeAppGeneratorService.create_and_preview_app(app_name: str, description: str, html_content: str, css_content: str = "", js_content: str = "") -> Dict[str, Any]`

- [ ] **Step 1: Write the failing test in `tests/test_code_app_generator.py`**
- [ ] **Step 2: Run test to verify it fails (`pytest tests/test_code_app_generator.py`)**
- [ ] **Step 3: Implement `CodeAppGeneratorService` in `src/services/code_app_generator.py`**
- [ ] **Step 4: Mount static app preview directory in `src/api/server.py`**
- [ ] **Step 5: Run test to verify it passes**

---

### Task 3: Interactive Data Chart & Visual Infographic Generator

**Files:**
- Create: `src/services/chart_generator.py`
- Test: `tests/test_chart_generator.py`

**Interfaces:**
- Produces: `ChartGeneratorService.create_chart(title: str, chart_type: str, labels: List[str], values: List[float], unit: str = "%") -> Dict[str, Any]`

- [ ] **Step 1: Write the failing test in `tests/test_chart_generator.py`**
- [ ] **Step 2: Run test to verify it fails (`pytest tests/test_chart_generator.py`)**
- [ ] **Step 3: Implement `ChartGeneratorService` in `src/services/chart_generator.py`**
- [ ] **Step 4: Run test to verify it passes**

---

### Task 4: Social Media Post Creator & Media Asset Manager

**Files:**
- Create: `src/services/social_media_agent.py`
- Test: `tests/test_social_media_agent.py`

**Interfaces:**
- Produces: `SocialMediaAgentService.create_post(platform: str, topic: str, tone_style: str = "expert", scheduled_time: str = "") -> Dict[str, Any]`

- [ ] **Step 1: Write the failing test in `tests/test_social_media_agent.py`**
- [ ] **Step 2: Run test to verify it fails (`pytest tests/test_social_media_agent.py`)**
- [ ] **Step 3: Implement `SocialMediaAgentService` in `src/services/social_media_agent.py`**
- [ ] **Step 4: Run test to verify it passes**

---

### Task 5: Wire All Tools into Cognitive ReAct Engine

**Files:**
- Modify: `src/services/cognitive_engine.py`
- Test: `tests/test_cognitive_engine_tools.py`

**Interfaces:**
- Consumes: All 4 services from Tasks 1-4.
- Produces: Tool-call hooks: `launch_application`, `create_local_web_app`, `generate_data_chart`, `create_social_post`.

- [ ] **Step 1: Write integration test for new cognitive tools**
- [ ] **Step 2: Register tools in `CognitiveAgentEngine.process_chat`**
- [ ] **Step 3: Run full integration tests**

---

### Task 6: Frontend Cockpit HUD Components (HTML/CSS/JS)

**Files:**
- Modify: `src/api/static/index.html`

- [ ] **Step 1: Add App Launcher card renderer (badge, status, direct launch button)**
- [ ] **Step 2: Add Code App Preview card with interactive iframe modal & 'Ouvrir dans Chrome' button**
- [ ] **Step 3: Add HUD Neon Chart renderer (animated bar chart & SVG line chart)**
- [ ] **Step 4: Add Social Post preview card with LinkedIn styling and Schedule status**

---

### Task 7: End-to-end Verification & Test Protocol Generation

**Files:**
- Run: Full test suite (`pytest`)
- Verify: Live server endpoints on `http://localhost:8000`
- Deliver: Detailed test protocol for the user to try every command live!
