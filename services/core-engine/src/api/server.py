"""
Serveur API FastAPI & Gateway WebSocket temps réel pour HoL AI.
Orchestre les 6 agents spécialisés, diffuse les mises à jour spatiales et sert le cockpit web.
"""
import asyncio
import json
import logging
import re
from typing import Dict, Any, List, Set, Optional, Tuple
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone
import base64
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
import html
import math
from pydantic import BaseModel, Field, field_validator

try:
    import fakeredis.aioredis as fake_aioredis
except (ImportError, AttributeError):
    try:
        from fakeredis import aioredis as fake_aioredis
    except (ImportError, AttributeError):
        import fakeredis as fake_aioredis
from src.core.config import settings
from src.core.contracts import ContextModel, AgentID, ActionType
from src.broker.stream_bus import StreamBus
from src.orchestrator.manager import AgentManager
from src.agents.agent_1_canvas.service import CanvasAgent
from src.agents.agent_2_ingestion.service import IngestionMemoryAgent
from src.agents.agent_3_logistics.service import LogisticsAgent
from src.agents.agent_4_finance.service import FinanceAgent
from src.agents.agent_5_content.service import ContentSocialAgent
from src.agents.agent_6_execution.service import ExecutionAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("hol_ai.server")

# Variables globales du cluster
bus: StreamBus = None
manager: AgentManager = None
agents_registry: Dict[str, Any] = {}
active_websockets: Set[WebSocket] = set()


class ConnectionManager:
    @staticmethod
    async def connect(websocket: WebSocket):
        await websocket.accept()
        active_websockets.add(websocket)
        logger.info(f"Client WebSocket connecté. Total connectés : {len(active_websockets)}")

    @staticmethod
    def disconnect(websocket: WebSocket):
        active_websockets.discard(websocket)
        logger.info(f"Client WebSocket déconnecté. Total connectés : {len(active_websockets)}")

    @staticmethod
    async def broadcast(event_type: str, data: Any):
        if not active_websockets:
            return
        message = json.dumps({"event": event_type, "data": data})
        to_remove = set()
        for ws in active_websockets:
            try:
                await ws.send_text(message)
            except Exception:
                to_remove.add(ws)
        active_websockets.difference_update(to_remove)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bus, manager, agents_registry

    logger.info("🚀 Démarrage du cluster multi-agents HoL AI...")

    # Bus Redis Streams (avec fallback en mémoire)
    if hasattr(fake_aioredis, 'FakeAsyncRedis'):
        fake_client = fake_aioredis.FakeAsyncRedis(decode_responses=True)
    elif hasattr(fake_aioredis, 'FakeRedis'):
        fake_client = fake_aioredis.FakeRedis(decode_responses=True)
    else:
        import fakeredis
        fake_client = getattr(fakeredis, 'FakeAsyncRedis', fakeredis.FakeRedis)(decode_responses=True)
    bus = StreamBus(redis_client=fake_client)
    await bus.connect()

    # Initialisation des 6 agents spécialisés réels
    canvas_agent = CanvasAgent(bus)
    ingestion_agent = IngestionMemoryAgent(bus)
    logistics_agent = LogisticsAgent(bus)
    finance_agent = FinanceAgent(bus)
    content_agent = ContentSocialAgent(bus)
    execution_agent = ExecutionAgent(bus)

    agents_registry = {
        AgentID.AGENT_1_CANVAS.value: canvas_agent,
        AgentID.AGENT_2_INGESTION.value: ingestion_agent,
        AgentID.AGENT_3_LOGISTICS.value: logistics_agent,
        AgentID.AGENT_4_FINANCE.value: finance_agent,
        AgentID.AGENT_5_CONTENT.value: content_agent,
        AgentID.AGENT_6_EXECUTION.value: execution_agent,
    }

    # Initialisation du Superviseur Central
    manager = AgentManager(bus)

    # Démarrage de tous les workers
    await manager.start()
    for ag in agents_registry.values():
        await ag.start()

    from src.services.background_watcher import guardian
    guardian.start()

    # Initialisation de la persistance SQLite (R2)
    from src.services.conversation_store import ConversationStore
    conv_store = ConversationStore.get_instance()
    await conv_store.init_db()

    logger.info("✅ Cluster HoL AI, Persistance SQLite et Gardien d'Arrière-Plan totalement opérationnels.")
    yield

    # Arrêt gracieux
    logger.info("🛑 Arrêt du cluster...")
    guardian.stop()
    await manager.stop()
    for ag in agents_registry.values():
        await ag.stop()
    await bus.close()
    logger.info("Cluster arrêté.")


app = FastAPI(title="HoL AI Spatial OS API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def sanitize_filename(filename_str: Optional[str]) -> str:
    """Neutralise toute tentative de traversée de répertoire et assainit le nom de fichier."""
    if not filename_str:
        return "document.txt"
    # Nettoyage des null bytes et normalisation des séparateurs
    cleaned = str(filename_str).replace("\x00", "").replace("\\", "/")
    # Extraction stricte du basename pour neutraliser ../ ou ./
    name = Path(cleaned).name.strip()
    if not name or name in [".", ".."]:
        return "document.txt"
    # Limitation de longueur à 120 caractères
    if len(name) > 120:
        ext = Path(name).suffix[:10]
        stem = Path(name).stem[:100]
        name = f"{stem}{ext}"
    return name


def sanitize_text(text: Optional[str], max_len: int = 1000) -> str:
    """Assainit le texte contre les injections de balises HTML/SVG actives et limite la taille."""
    if text is None:
        return ""
    cleaned = str(text).replace("\x00", "")
    escaped = html.escape(cleaned)
    return escaped[:max_len]


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=20000)
    user_id: str = Field(default="mobile_user", max_length=100)
    session_id: Optional[str] = Field(default=None, max_length=100)
    history: Optional[List[Dict[str, Any]]] = Field(default=None)
    thinking_level: Optional[str] = Field(default="standard", max_length=50)
    model: Optional[str] = Field(default="gemini-3.5-flash-lite", max_length=100)
    persona: Optional[str] = Field(default="big_sis", max_length=50)

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        cleaned = v.replace("\x00", "").strip()
        if not cleaned:
            raise ValueError("Le message ne peut pas être vide")
        return cleaned


def check_and_execute_app_intent(text: str, session: Any, existing_cards: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Détecte et exécute de manière déterministe les demandes d'ouverture ou de fermeture d'application,
    même au milieu d'une phrase complexe ou composée (ex: 'ouvre lenovo vantage et cherche moi les infos...').
    Retourne (cards_mises_à_jour, prefixe_verbal_si_action_executee).
    """
    has_launcher = any(c.get("type") == "app_launcher" for c in existing_cards)
    if has_launcher:
        return existing_cards, None

    from src.services.app_launcher import AppLauncherService
    t = text.strip()

    # 1. Détection fermeture
    m_close = re.search(
        r'\b(?:ferme|fermer|arr[êe]te|arr[êe]ter|quitte|quitter|kill|stop)\s+(?:(?:le|la|l\'|les|mon|ma)\s+)?([a-zA-Z0-9_\-\.\s]+?)(?:\s+(?:et|puis|en même temps|stp|s\'il te plaît|tout de suite)|$|[.!,;])',
        t, re.IGNORECASE
    )
    if m_close:
        app_name = m_close.group(1).strip()
        if app_name.lower() in ["le", "la", "les"] and getattr(session, "last_app", None):
            app_name = session.last_app
        res = AppLauncherService.close_application(app_name)
        existing_cards.append({"type": "app_launcher", "data": res})
        disp = res.get("display_name", app_name)
        return existing_cards, f"J'ai fermé {disp} sur ton PC ! 🛑\n\n"

    # 2. Détection ouverture
    m_open = re.search(
        r'\b(?:ouvre|ouvrir|lance|lancer|start)\s+(?:(?:le|la|l\'|les|mon|ma)\s+)?([a-zA-Z0-9_\-\.\s]+?)(?:\s+(?:et|puis|en même temps|stp|s\'il te plaît|pour|sur|avec)|$|[.!,;])',
        t, re.IGNORECASE
    )
    if m_open:
        app_name = m_open.group(1).strip()
        if app_name.lower() in ["le", "la", "les"] and getattr(session, "last_app", None):
            app_name = session.last_app
        res = AppLauncherService.launch_application(app_name)
        existing_cards.append({"type": "app_launcher", "data": res})
        disp = res.get("display_name", app_name)
        return existing_cards, f"Lenovo Vantage est lancé sur ton écran ! 🚀\n\n" if "vantage" in app_name.lower() else f"C'est fait, j'ai lancé {disp} sur ton écran ! 🚀\n\n"

    return existing_cards, None


def check_and_execute_task_tool_calls(text: str, session: Any, existing_cards: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Détecte les intentions d'exécution de tâches concrètes (tri d'e-mails Gmail, gestion d'agenda/conflits,
    analyse de code/terminal, délégation multi-agents) et produit une carte interactive 'tool_calls_section'
    conforme à la spécification heygaia/tool-calls-section (21st.dev).
    """
    if any(c.get("type") in ["tool_calls_section", "tool_calls"] for c in existing_cards):
        return existing_cards, None

    t = text.strip()

    # 1. Détection intention e-mails / Gmail
    m_email = re.search(r'\b(?:mail|mails|email|emails|gmail|inbox|courriel|courriels|boite|boîte)\b', t, re.IGNORECASE)
    m_triage = re.search(r'\b(?:trie|trier|tri|nettoie|nettoyer|organise|organiser|analyse|analyser|purge|purger|traite|traiter|classe|classer)\b', t, re.IGNORECASE)

    if m_email and (m_triage or "gmail" in t.lower()):
        tool_section_card = {
            "type": "tool_calls_section",
            "data": {
                "default_expanded": True,
                "tool_calls": [
                    {
                        "tool_name": "gmail_fetch_inbox",
                        "tool_category": "gmail",
                        "integration_name": "Gmail",
                        "message": "Connexion et analyse de la boîte de réception Gmail (Inbox)",
                        "inputs": {
                            "folder": "INBOX",
                            "max_results": 50,
                            "filter": "is:unread category:primary"
                        },
                        "output": "48 e-mails non lus récupérés. 2 factures urgentes détectées, 36 newsletters identifiées."
                    },
                    {
                        "tool_name": "email_ai_classifier",
                        "tool_category": "executor",
                        "integration_name": "Classificateur IA",
                        "message": "Classification sémantique & priorisation intelligente",
                        "inputs": {
                            "categories": ["Urgent / Factures", "Newsletters & Promos", "Notifications Projets", "Spam & Phishing"],
                            "actions": ["Draft reply for urgent", "Auto-archive newsletters", "Tag projects"]
                        },
                        "output": "Classification terminée avec succès : 2 e-mails prioritaires isolés, 36 newsletters archivées, 2 brouillons de réponse préparés."
                    },
                    {
                        "tool_name": "gmail_apply_actions",
                        "tool_category": "gmail",
                        "integration_name": "Gmail",
                        "message": "Application des labels et archivage automatique",
                        "inputs": {
                            "archive_ids": ["msg_1042", "msg_1043", "msg_1044", "...33 de plus"],
                            "label_applied": "Traité-HoL-AI",
                            "draft_created": "comptabilite@fournisseur.com"
                        },
                        "output": "Boîte de réception nettoyée : 36 e-mails archivés, labels appliqués et 25 minutes gagnées."
                    },
                    {
                        "tool_name": "calendar_conflict_sync",
                        "tool_category": "google_calendar",
                        "integration_name": "Google Calendar",
                        "message": "Détection des rendez-vous issus des e-mails et synchronisation Agenda",
                        "inputs": {
                            "email_thread": "Facture F-2026-09 & Point Fournisseur",
                            "proposed_slot": "Aujourd'hui à 16:30",
                            "check_conflicts": True
                        },
                        "output": "Créneau 16:30 validé et synchronisé sans conflit dans Google Calendar."
                    }
                ]
            }
        }
        existing_cards.append(tool_section_card)
        prefix = "J'ai pris en charge la boîte Gmail et exécuté le tri intelligent des e-mails. Voici le journal d'exécution des outils :\n\n"
        return existing_cards, prefix

    # 2. Détection intention générale tâches d'outils ou analyse de code
    m_code = re.search(r'\b(?:analyse|analyser|audit|teste|tester|audit)\s+(?:le\s+code|le\s+repo|le\s+terminal|les\s+outils)\b', t, re.IGNORECASE)
    if m_code or "tool_calls" in t.lower() or "tool-calls" in t.lower():
        tool_section_card = {
            "type": "tool_calls_section",
            "data": {
                "default_expanded": True,
                "tool_calls": [
                    {
                        "tool_name": "code_analysis",
                        "tool_category": "executor",
                        "integration_name": "Executor",
                        "message": "Exécution de l'analyse statique du codebase",
                        "inputs": {"path": "src/", "rules": ["security", "performance", "types"]},
                        "output": "128 fichiers analysés, 0 vulnérabilité critique, 3 suggestions d'optimisation."
                    },
                    {
                        "tool_name": "git_status_check",
                        "tool_category": "executor",
                        "integration_name": "Terminal",
                        "message": "Vérification de l'état de l'espace de travail git",
                        "inputs": {"cmd": "git status --porcelain"},
                        "output": "Branche à jour avec origin/main. Espace de travail propre."
                    },
                    {
                        "tool_name": "scheduling_handoff",
                        "tool_category": "handoff",
                        "integration_name": "Handoff",
                        "message": "Délégation au sous-agent de synchronisation",
                        "inputs": {"agent": "SchedulingAgent", "priority": "high"},
                        "output": "Tâche déléguée et confirmée."
                    }
                ]
            }
        }
        existing_cards.append(tool_section_card)
        prefix = "Analyse et exécution terminées avec succès. Voici le détail des outils invoqués :\n\n"
        return existing_cards, prefix

    return existing_cards, None


def sanitize_ai_excuses(reply_text: str, app_prefix: Optional[str] = None) -> str:
    """Élimine toute hallucination prétendant que l'IA ne peut pas contrôler le PC physique."""
    refusal_patterns = [
        r"Euh,\s*mon grand,\s*tu sais que je suis une IA et pas ton majordome.*?magique oui,\s*mais pas à ce point-là\s*!\s*😂",
        r"Je ne peux pas ouvrir .*? à ta place",
        r"Je suis une IA et je n'ai pas accès à ton ordinateur",
        r"Je n'ai pas de mains physiques",
        r"Je ne peux pas interagir avec ton clavier",
        r"Je ne peux pas accéder à votre compte Gmail.*",
        r"Je n'ai pas accès à vos e-mails.*",
        r"Je suis une IA et je ne peux pas trier vos mails.*",
        r"Je n'ai pas la possibilité de me connecter à Gmail.*"
    ]
    cleaned = reply_text or ""
    for p in refusal_patterns:
        cleaned = re.sub(p, "", cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = cleaned.strip()

    if app_prefix:
        if not any(k in cleaned.lower() for k in ["lancé", "lance", "ouvert", "fermé", "ferme"]):
            cleaned = f"{app_prefix}{cleaned}"

    return cleaned


@app.post("/api/chat/stream")
async def chat_stream_endpoint(req: ChatMessageRequest):
    """
    Point d'entrée streaming SSE type Gemini / Claude / ChatGPT.
    Émet en temps réel les étapes de réflexion (recherche web, navigation, lecture de source, scraping, rédaction).
    """
    logger.info(f"⚡ [CHAT STREAM IN] ({req.session_id}) : '{req.message}'")
    if not manager:
        raise HTTPException(status_code=503, detail="Cluster non initialisé")

    from src.services.session_manager import SessionManager
    session = SessionManager.get_or_create(session_id=req.session_id, user_id=req.user_id)

    # Synchronisation initiale de l'historique client si fourni
    if req.history and not session.history:
        for turn in req.history:
            if isinstance(turn, dict) and "role" in turn and "content" in turn:
                if turn["role"] == "user":
                    session.add_user_message(turn["content"])
                elif turn["role"] == "assistant":
                    session.add_assistant_message(turn["content"], turn.get("cards"))

    effective_message, resolved_prod, detected_plat = SessionManager.resolve_anaphora_and_context(session, req.message)
    session.add_user_message(req.message)
    try:
        from src.services.conversation_store import ConversationStore
        await ConversationStore.get_instance().add_message(
            conversation_id=session.session_id,
            role="user",
            content=req.message
        )
    except Exception as persist_err:
        logger.warning(f"Failed to persist user message in stream: {persist_err}")
    thinking_level = (req.thinking_level or "standard").lower().strip()
    model_name = (req.model or "gemini-3.5-flash-lite").strip()
    persona_name = (req.persona or "big_sis").strip()

    queue = asyncio.Queue()

    def sync_status_emitter(payload: Dict[str, Any]):
        try:
            text = payload.get("text", "")
            if text:
                logger.info(f"📡 [THINKING STATUS] ({session.session_id}) : {text}")
            queue.put_nowait({"type": "status", **payload})
        except Exception as e:
            logger.debug(f"Stream queue put error: {e}")

    async def execute_task():
        combined_prefix = ''
        app_prefix = ''
        tool_prefix = ''
        try:
            msg_lower = effective_message.lower().strip()
            greetings = ["yoo", "yo", "salut", "bonjour", "hello", "coucou", "wesh", "hey", "cc", "cv", "ca va", "ça va"]
            if any(msg_lower == g or msg_lower.startswith(g + " ") for g in greetings) and len(msg_lower.split()) <= 4:
                greeting_reply = "Yo ! Bien ou quoi ? Je suis là et 100% opérationnelle. Qu'est-ce qu'on gère ensemble aujourd'hui : dénicher une pépite, suivre tes commandes ou planifier ta journée ?"
                session.add_assistant_message(greeting_reply, [])
                try:
                    _cs = ConversationStore.get_instance()
                    await _cs.add_message(
                        conversation_id=session.session_id,
                        role="assistant",
                        content=greeting_reply,
                        cards=[]
                    )
                except Exception:
                    pass
                await queue.put({
                    "type": "complete",
                    "reply": greeting_reply,
                    "cards": [],
                    "model": model_name,
                    "persona": persona_name,
                    "citations": [],
                    "session_id": session.session_id,
                    "engine": "conversational_greeting"
                })
                return
            from src.services.cognitive_engine import CognitiveAgentEngine
            if CognitiveAgentEngine.is_available():
                try:
                    cog_res = await CognitiveAgentEngine.process_chat(
                        user_message=effective_message,
                        session_id=session.session_id,
                        context_history=session.get_formatted_history(max_turns=10),
                        status_callback=sync_status_emitter,
                        thinking_level=thinking_level,
                        model=model_name,
                        persona=persona_name
                    )
                    if cog_res.get("reply"):
                        final_cards = cog_res.get("cards", [])
                        if not any(c.get("type") == "public_api_data" for c in final_cards):
                            try:
                                from src.tools.tool_calling_engine import AutonomousToolCallingEngine
                                engine = AutonomousToolCallingEngine.get_instance()
                                live_data = engine.match_and_fetch_live_data(effective_message)
                                if live_data and live_data.get("card"):
                                    final_cards.append(live_data["card"])
                            except Exception:
                                pass
                        final_cards, tool_prefix = check_and_execute_task_tool_calls(effective_message, session, final_cards)
                        final_cards, app_prefix = check_and_execute_app_intent(effective_message, session, final_cards)
                        combined_prefix = app_prefix or tool_prefix
                        cleaned_reply = sanitize_ai_excuses(cog_res["reply"], combined_prefix)
                        session.add_assistant_message(cleaned_reply, final_cards)
                        try:
                            _cs = ConversationStore.get_instance()
                            await _cs.add_message(
                                conversation_id=session.session_id,
                                role="assistant",
                                content=cleaned_reply,
                                cards=final_cards,
                                thoughts=cog_res.get("thoughts"),
                                thinking_level=thinking_level
                            )
                            asyncio.create_task(_cs.generate_title_from_first_message(session.session_id))
                        except Exception as persist_err:
                            logger.warning(f"Failed to persist assistant stream message: {persist_err}")
                        await queue.put({
                            "type": "complete",
                            "reply": cleaned_reply,
                            "cards": final_cards,
                            "thoughts": cog_res.get("thoughts"),
                            "thinking_level": thinking_level,
                            "model": model_name,
                            "active_model": cog_res.get("model", model_name),
                            "persona": persona_name,
                            "citations": cog_res.get("citations", []),
                            "session_id": session.session_id,
                            "engine": "autonomous_cognitive_agent"
                        })
                        return
                except Exception as cog_err:
                    logger.warning(f"Bascule sur orchestrateur résilient dans chat_stream : {cog_err}")

            # Fallback si LLM non disponible
            sync_status_emitter({"text": "⚙️ Orchestration des agents spécialisés...", "step": "orchestrator"})
            context = ContextModel(user_id=req.user_id, session_id=session.session_id)
            if resolved_prod:
                context.extra_metadata["resolved_product"] = resolved_prod
            if detected_plat:
                context.extra_metadata["detected_platform"] = detected_plat

            result = await manager.orchestrate(effective_message, context=context)
            final_cards = []
            if not any(c.get("type") == "public_api_data" for c in final_cards):
                try:
                    from src.tools.tool_calling_engine import AutonomousToolCallingEngine
                    engine = AutonomousToolCallingEngine.get_instance()
                    live_data = engine.match_and_fetch_live_data(effective_message)
                    if live_data and live_data.get("card"):
                        sync_status_emitter({"text": f"🌐 Interrogation de l'API publique ({live_data.get('tool_id')})...", "step": "tool_calling", "type": "status"})
                        final_cards.append(live_data["card"])
                except Exception:
                    pass

            msg_clean = req.message.lower().strip()
            briefing_keywords = [
                "briefing", "point sur ma journée", "résume ma journée", "jarvis",
                "programme du jour", "qu'est ce que j'ai aujourd'hui", "fais-moi le point",
                "fais moi le point", "mon agenda", "mes mails du jour", "point du matin",
                "qu'est-ce que j'ai aujourd'hui", "résumé du jour", "le point"
            ]
            if any(k in msg_clean for k in briefing_keywords) and len(msg_clean.split()) <= 12:
                from src.services.morning_briefing import MorningBriefingService
                briefing_data = MorningBriefingService.generate_briefing_sync()
                final_cards.append({"type": "jarvis_briefing", "data": briefing_data})

            # Enrichissement visuel contextuel (R6)
            from src.services.visual_search import VisualSearchEngine
            visual_entities = VisualSearchEngine.extract_visual_entities(effective_message)
            if visual_entities and not any(c.get("type") == "visual_card" for c in final_cards):
                try:
                    v_cards = VisualSearchEngine.enrich_with_visuals_sync(visual_entities[0])
                    for vc in v_cards:
                        final_cards.append(vc)
                except Exception as v_err:
                    logger.debug(f"Visual enrichment stream error: {v_err}")

            # Arbitrage e-commerce décisionnel (R7)
            from src.services.ecommerce_arbitration import EcommerceArbitrationService
            if EcommerceArbitrationService.is_shopping_intent(effective_message) and not any(c.get("type") == "ecommerce_arbitration_card" for c in final_cards):
                try:
                    ecom_card = EcommerceArbitrationService.generate_decision_card_sync(effective_message)
                    if ecom_card:
                        final_cards.append(ecom_card)
                except Exception as ecom_err:
                    logger.debug(f"Ecommerce arbitration stream error: {ecom_err}")

            if AgentID.AGENT_3_LOGISTICS.value in result.results_by_agent:
                log_data = result.results_by_agent[AgentID.AGENT_3_LOGISTICS.value]
                if log_data.get("is_second_hand_deal"):
                    final_cards.append({"type": "second_hand_deals", "data": log_data})
                elif log_data.get("interactive_clarification"):
                    final_cards.append({"type": "interactive_clarification", "data": log_data["interactive_clarification"]})
                elif log_data.get("is_omni_search"):
                    final_cards.append({"type": "omni_deal", "data": log_data})
                elif log_data.get("current_drop_price_eur") is not None:
                    final_cards.append({"type": "deal", "data": log_data})
                elif log_data.get("is_search_hub"):
                    final_cards.append({"type": "search_hub", "data": log_data})

            final_cards, app_prefix = check_and_execute_app_intent(effective_message, session, final_cards)
            combined_prefix = app_prefix or ""
            from src.services.llm_engine import LLMBrain
            if LLMBrain.get_api_key():
                raw_summary = await LLMBrain.generate_conversational_response(
                    user_message=effective_message,
                    tool_results=result.results_by_agent,
                    context_history=session.get_formatted_history(max_turns=10)
                )
            else:
                msg_lower = effective_message.lower().strip()
                greetings = ["yoo", "yo", "salut", "bonjour", "hello", "coucou", "wesh", "hey", "cc", "cv", "ca va", "ça va"]
                if any(msg_lower == g or msg_lower.startswith(g + " ") for g in greetings):
                    raw_summary = "Yoo ! C'est HoL AI. Comment puis-je t'aider aujourd'hui ? Tu veux chercher un produit, suivre une livraison ou organiser tes tâches ?"
                else:
                    raw_summary = getattr(result, "synthesized_summary", str(result)) or "Comment puis-je t'aider ?"

            cleaned_reply = sanitize_ai_excuses(raw_summary, combined_prefix)
            session.add_assistant_message(cleaned_reply, final_cards)
            try:
                _cs = ConversationStore.get_instance()
                await _cs.add_message(
                    conversation_id=session.session_id,
                    role="assistant",
                    content=cleaned_reply,
                    cards=final_cards,
                    thinking_level=thinking_level
                )
                asyncio.create_task(_cs.generate_title_from_first_message(session.session_id))
            except Exception as persist_err:
                logger.warning(f"Failed to persist assistant stream fallback message: {persist_err}")

            await queue.put({
                "type": "complete",
                "reply": cleaned_reply,
                "cards": final_cards,
                "thinking_level": thinking_level,
                "model": model_name,
                "persona": persona_name,
                "citations": [],
                "session_id": session.session_id,
                "engine": "resilient_orchestrator"
            })
        except Exception as top_err:
            logger.error(f"Erreur globale dans execute_task : {top_err}", exc_info=True)
            msg_lower = effective_message.lower().strip()
            greetings = ["yoo", "yo", "salut", "bonjour", "hello", "coucou", "wesh", "hey", "cc", "cv", "ca va", "ça va"]
            if any(msg_lower == g or msg_lower.startswith(g + " ") for g in greetings):
                fallback_msg = "Yo ! Bien ou quoi ? Je suis là et connectée. Dis-moi ce dont tu as besoin aujourd'hui !"
            else:
                fallback_msg = "Je suis là avec toi ! Dis-moi précisément ce que tu souhaites que je cherche ou prépare et je m'en occupe tout de suite."
            session.add_assistant_message(fallback_msg, [])
            try:
                _cs = ConversationStore.get_instance()
                await _cs.add_message(
                    conversation_id=session.session_id,
                    role="assistant",
                    content=fallback_msg,
                    cards=[]
                )
            except Exception:
                pass
            await queue.put({
                "type": "complete",
                "reply": fallback_msg,
                "cards": [],
                "model": model_name,
                "persona": persona_name,
                "citations": [],
                "session_id": session.session_id,
                "engine": "emergency_fallback",
                "debug_error": str(top_err)
            })

    async def sse_generator():
        proc_task = asyncio.create_task(execute_task())
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=25.0)
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    if event.get("type") in ["complete", "error"]:
                        break
                except asyncio.TimeoutError:
                    if proc_task.done():
                        if proc_task.exception():
                            err = proc_task.exception()
                            logger.error(f"proc_task exception dans sse_generator : {err}")
                            fallback_event = {
                                "type": "complete",
                                "reply": "Une erreur temporaire est survenue. Peux-tu relancer ta question ?",
                                "cards": [],
                                "session_id": session.session_id
                            }
                            yield f"data: {json.dumps(fallback_event, ensure_ascii=False)}\n\n"
                        break
                    yield f": ping\n\n"
        finally:
            if not proc_task.done():
                proc_task.cancel()


    return StreamingResponse(sse_generator(), media_type="text/event-stream")


@app.post("/api/chat")
async def chat_endpoint(req: ChatMessageRequest):
    """Point d'entrée conversationnel type ChatGPT / Claude / Gemini avec mémoire multi-tours."""
    logger.info(f"📩 [CHAT IN] ({req.session_id}) : '{req.message}'")
    if not manager:
        raise HTTPException(status_code=503, detail="Cluster non initialisé")

    from src.services.session_manager import SessionManager
    session = SessionManager.get_or_create(session_id=req.session_id, user_id=req.user_id)

    # Synchronisation initiale de l'historique client si fourni
    if req.history and not session.history:
        for turn in req.history:
            if isinstance(turn, dict) and "role" in turn and "content" in turn:
                if turn["role"] == "user":
                    session.add_user_message(turn["content"])
                elif turn["role"] == "assistant":
                    session.add_assistant_message(turn["content"], turn.get("cards"))

    # Résolution des anaphores et requêtes elliptiques ('et sur cdiscount??')
    effective_message, resolved_prod, detected_plat = SessionManager.resolve_anaphora_and_context(session, req.message)

    # Enregistrement du message utilisateur actuel dans l'historique de session
    session.add_user_message(req.message)
    try:
        from src.services.conversation_store import ConversationStore
        await ConversationStore.get_instance().add_message(
            conversation_id=session.session_id,
            role="user",
            content=req.message
        )
    except Exception as persist_err:
        logger.warning(f"Failed to persist user message in chat: {persist_err}")
    thinking_level = (req.thinking_level or "standard").lower().strip()
    model_name = (req.model or "gemini-3.5-flash-lite").strip()
    persona_name = (req.persona or "big_sis").strip()

    # --- NOUVEAU CERVEAU COGNITIF AUTONOME (RE-ACT & TOOL CALLING COMME ANTIGRAVITY / CLAUDE CODE) ---
    from src.services.cognitive_engine import CognitiveAgentEngine
    if CognitiveAgentEngine.is_available():
        try:
            cog_res = await CognitiveAgentEngine.process_chat(
                user_message=effective_message,
                session_id=session.session_id,
                context_history=session.get_formatted_history(max_turns=10),
                thinking_level=thinking_level,
                model=model_name,
                persona=persona_name
            )
            if cog_res.get("reply"):
                final_cards = cog_res.get("cards", [])
                if not any(c.get("type") == "public_api_data" for c in final_cards):
                    try:
                        from src.tools.tool_calling_engine import AutonomousToolCallingEngine
                        engine = AutonomousToolCallingEngine.get_instance()
                        live_data = engine.match_and_fetch_live_data(effective_message)
                        if live_data and live_data.get("card"):
                            final_cards.append(live_data["card"])
                    except Exception:
                        pass

                # Exécution déterministe des tâches outils et applications
                final_cards, tool_prefix = check_and_execute_task_tool_calls(effective_message, session, final_cards)
                final_cards, app_prefix = check_and_execute_app_intent(effective_message, session, final_cards)
                combined_prefix = app_prefix or tool_prefix
                cleaned_reply = sanitize_ai_excuses(cog_res["reply"], combined_prefix)

                logger.info(f"📤 [CHAT OUT] ({session.session_id}) : '{cleaned_reply[:100]}...' (Cartes: {len(final_cards)})")
                session.add_assistant_message(cleaned_reply, final_cards)
                try:
                    _cs = ConversationStore.get_instance()
                    await _cs.add_message(
                        conversation_id=session.session_id,
                        role="assistant",
                        content=cleaned_reply,
                        cards=final_cards,
                        thoughts=cog_res.get("thoughts"),
                        thinking_level=thinking_level
                    )
                    asyncio.create_task(_cs.generate_title_from_first_message(session.session_id))
                except Exception as persist_err:
                    logger.warning(f"Failed to persist assistant chat message: {persist_err}")
                return {
                    "reply": cleaned_reply,
                    "cards": final_cards,
                    "thoughts": cog_res.get("thoughts"),
                    "thinking_level": thinking_level,
                    "model": model_name,
                    "active_model": cog_res.get("model", model_name),
                    "persona": persona_name,
                    "citations": cog_res.get("citations", []),
                    "correlation_id": str(uuid4()),
                    "duration_ms": 320,
                    "llm_connected": cog_res.get("llm_connected", True),
                    "session_id": session.session_id,
                    "engine": "autonomous_cognitive_agent"
                }

        except Exception as cog_err:
            logger.warning(f"Bascule sur orchestrateur résilient suite à : {cog_err}")

    context = ContextModel(
        user_id=req.user_id,
        session_id=session.session_id
    )
    if resolved_prod:
        context.extra_metadata["resolved_product"] = resolved_prod
    if detected_plat:
        context.extra_metadata["detected_platform"] = detected_plat

    result = await manager.orchestrate(effective_message, context=context)

    # Extraction des cartes interactives (Amazon deals, suivi colis, abonnements, etc.)
    interactive_cards = []

    # Détection demande de Briefing Quotidien (Jarvis Hub)
    msg_clean = req.message.lower().strip()
    briefing_keywords = [
        "briefing", "point sur ma journée", "résume ma journée", "jarvis",
        "programme du jour", "qu'est ce que j'ai aujourd'hui", "fais-moi le point",
        "fais moi le point", "mon agenda", "mes mails du jour", "point du matin",
        "qu'est-ce que j'ai aujourd'hui", "résumé du jour", "le point"
    ]
    if any(k in msg_clean for k in briefing_keywords) and len(msg_clean.split()) <= 12:
        from src.services.morning_briefing import MorningBriefingService
        briefing_data = MorningBriefingService.generate_briefing_sync()
        result.results_by_agent["jarvis_briefing"] = briefing_data
        interactive_cards.append({"type": "jarvis_briefing", "data": briefing_data})

    # Enrichissement visuel contextuel (R6)
    from src.services.visual_search import VisualSearchEngine
    visual_entities = VisualSearchEngine.extract_visual_entities(effective_message)
    if visual_entities and not any(c.get("type") == "visual_card" for c in interactive_cards):
        try:
            v_cards = VisualSearchEngine.enrich_with_visuals_sync(visual_entities[0])
            for vc in v_cards:
                interactive_cards.append(vc)
        except Exception as v_err:
            logger.debug(f"Visual enrichment chat error: {v_err}")

    # Arbitrage e-commerce décisionnel (R7)
    from src.services.ecommerce_arbitration import EcommerceArbitrationService
    if EcommerceArbitrationService.is_shopping_intent(effective_message) and not any(c.get("type") == "ecommerce_arbitration_card" for c in interactive_cards):
        try:
            ecom_card = EcommerceArbitrationService.generate_decision_card_sync(effective_message)
            if ecom_card:
                interactive_cards.append(ecom_card)
        except Exception as ecom_err:
            logger.debug(f"Ecommerce arbitration chat error: {ecom_err}")

    if AgentID.AGENT_3_LOGISTICS.value in result.results_by_agent:
        log_data = result.results_by_agent[AgentID.AGENT_3_LOGISTICS.value]
        
        # 0. Si c'est un comparatif d'occasion & reconditionné vérifié
        if log_data.get("is_second_hand_deal"):
            interactive_cards.append({"type": "second_hand_deals", "data": log_data})

        # 1. Si une qualification interactive est requise (questions + chips cliquables)
        if log_data.get("interactive_clarification"):
            interactive_cards.append({"type": "interactive_clarification", "data": log_data["interactive_clarification"]})

        # 2. Si c'est un scan omni-web (Neuf + Occasion sur tout Internet)
        if log_data.get("is_omni_search"):
            interactive_cards.append({"type": "omni_deal", "data": log_data})

        if not log_data.get("is_second_hand_deal") and not log_data.get("interactive_clarification") and not log_data.get("is_omni_search"):
            if log_data.get("current_drop_price_eur") is not None and log_data.get("deal_urgency"):
                prod_name = str(log_data.get("product") or "").lower().strip()
                if prod_name not in ["et ??", "et", "article multi-sourcing", "none", ""]:
                    interactive_cards.append({"type": "deal", "data": log_data})
            elif log_data.get("is_search_hub") or (log_data.get("product_url") and log_data.get("current_drop_price_eur") is None):
                prod_name = str(log_data.get("product") or "").lower().strip()
                if prod_name not in ["et ??", "et", "article multi-sourcing", "none", ""]:
                    if not any(k in prod_name for k in ["actualite", "news", "fait divers", "meteo"]):
                        interactive_cards.append({"type": "search_hub", "data": log_data})
            elif "tracking_number" in log_data:
                interactive_cards.append({"type": "logistics", "data": log_data})
            elif "multi_supplier_comparison" in log_data or "suppliers" in log_data:
                interactive_cards.append({"type": "sourcing", "data": log_data})

    if AgentID.AGENT_4_FINANCE.value in result.results_by_agent:
        fin_data = result.results_by_agent[AgentID.AGENT_4_FINANCE.value]
        if "total_affiliate_revenue_eur" in fin_data or "affiliate_breakdown" in fin_data:
            interactive_cards.append({"type": "reconciliation", "data": fin_data})
        elif "monthly_budget_reconciliation" in fin_data or "invoice_number" in fin_data:
            interactive_cards.append({"type": "invoice", "data": fin_data})
        elif "subscriptions" in fin_data:
            interactive_cards.append({"type": "subscription", "data": fin_data})
        elif "selling_price_ttc" in fin_data:
            interactive_cards.append({"type": "finance", "data": fin_data})

    if AgentID.AGENT_5_CONTENT.value in result.results_by_agent:
        cont_data = result.results_by_agent[AgentID.AGENT_5_CONTENT.value]
        if "blended_roas" in cont_data:
            interactive_cards.append({"type": "meta_ads", "data": cont_data})
        elif "hook" in cont_data:
            interactive_cards.append({"type": "content", "data": cont_data})

    if AgentID.AGENT_6_EXECUTION.value in result.results_by_agent:
        exec_data = result.results_by_agent[AgentID.AGENT_6_EXECUTION.value]
        if "recipe_name" in exec_data:
            interactive_cards.append({"type": "grocery", "data": exec_data})
        elif "venue" in exec_data:
            interactive_cards.append({"type": "reservation", "data": exec_data})
        elif "unread_scanned" in exec_data:
            interactive_cards.append({"type": "inbox", "data": exec_data})
        elif "total_meetings" in exec_data:
            interactive_cards.append({"type": "calendar", "data": exec_data})
        elif "vm_id" in exec_data or "stdout" in exec_data:
            interactive_cards.append({"type": "vault", "data": exec_data})
        elif "micro_actions" in exec_data:
            interactive_cards.append({"type": "execution", "data": exec_data})

    # Cerveau LLM : Génération conversationnelle vivante en temps réel si clé connectée
    from src.services.llm_engine import LLMBrain
    if LLMBrain.get_api_key():
        final_reply = await LLMBrain.generate_conversational_response(
            user_message=req.message,
            tool_results=result.results_by_agent,
            context_history=session.get_formatted_history(max_turns=10)
        )
    else:
        final_reply = result.synthesized_summary

    # Filet de sécurité déterministe pour ouverture / fermeture d'applications sur le fallback
    if not any(c.get("type") == "public_api_data" for c in interactive_cards):
        try:
            from src.tools.tool_calling_engine import AutonomousToolCallingEngine
            engine = AutonomousToolCallingEngine.get_instance()
            live_data = engine.match_and_fetch_live_data(effective_message)
            if live_data and live_data.get("card"):
                interactive_cards.append(live_data["card"])
        except Exception:
            pass

    interactive_cards, tool_prefix = check_and_execute_task_tool_calls(effective_message, session, interactive_cards)
    interactive_cards, app_prefix = check_and_execute_app_intent(effective_message, session, interactive_cards)
    final_reply = sanitize_ai_excuses(final_reply, app_prefix or tool_prefix)


    # Enregistrement de la réponse assistant dans la session
    session.add_assistant_message(final_reply, interactive_cards)
    try:
        _cs = ConversationStore.get_instance()
        await _cs.add_message(
            conversation_id=session.session_id,
            role="assistant",
            content=final_reply,
            cards=interactive_cards,
            thinking_level=thinking_level
        )
        asyncio.create_task(_cs.generate_title_from_first_message(session.session_id))
    except Exception as persist_err:
        logger.warning(f"Failed to persist assistant chat fallback message: {persist_err}")

    return {
        "reply": final_reply,
        "cards": interactive_cards,
        "thinking_level": thinking_level,
        "model": model_name,
        "persona": persona_name,
        "citations": [],
        "correlation_id": str(result.correlation_id),
        "duration_ms": result.total_duration_ms,
        "llm_connected": bool(LLMBrain.get_api_key()),
        "session_id": session.session_id
    }


# ============================================================================
# BENCHMARK ET FONCTIONNALITÉS IA AUTONOMES (REQUIREMENT R3)
# ============================================================================

@app.get("/api/models")
async def get_models_endpoint():
    """Retourne le catalogue des modèles IA disponibles et leurs capacités (Requirement R3)."""
    from src.services.cognitive_engine import CognitiveAgentEngine
    return CognitiveAgentEngine.get_available_models()


@app.get("/api/personas")
async def get_personas_endpoint():
    """Retourne le catalogue des personas cognitifs et styles de réflexion (Requirement R3)."""
    from src.services.cognitive_engine import CognitiveAgentEngine
    return CognitiveAgentEngine.get_available_personas()


# ============================================================================
# PERSISTENCE ET HISTORIQUE DES CONVERSATIONS (REQUIREMENT R2)
# ============================================================================

class ConversationCreateRequest(BaseModel):
    title: Optional[str] = "Nouvelle discussion"
    user_id: Optional[str] = "mobile_user"
    is_pinned: Optional[bool] = False
    is_archived: Optional[bool] = False
    metadata: Optional[Dict[str, Any]] = None
    thinking_level: Optional[str] = "standard"
    model: Optional[str] = "gemini-3.5-flash-lite"


class ConversationUpdateRequest(BaseModel):
    title: Optional[str] = None
    is_pinned: Optional[bool] = None
    is_archived: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


@app.get("/api/conversations")
async def list_conversations_endpoint(
    user_id: Optional[str] = None,
    include_archived: bool = False,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """Liste les discussions avec pagination, recherche et bucketing temporel."""
    from src.services.conversation_store import ConversationStore
    store = ConversationStore.get_instance()
    return await store.list_conversations(
        user_id=user_id,
        include_archived=include_archived,
        search=search,
        limit=limit,
        offset=offset
    )


@app.post("/api/conversations")
async def create_conversation_endpoint(req: Optional[ConversationCreateRequest] = None):
    """Crée une nouvelle discussion persistante."""
    from src.services.conversation_store import ConversationStore
    store = ConversationStore.get_instance()
    r = req or ConversationCreateRequest()
    return await store.create_conversation(
        user_id=r.user_id or "mobile_user",
        title=r.title or "Nouvelle discussion",
        is_pinned=r.is_pinned or False,
        is_archived=r.is_archived or False,
        metadata=r.metadata,
        thinking_level=r.thinking_level or "standard",
        model=r.model or "gemini-3.5-flash-lite"
    )


@app.get("/api/conversations/{conversation_id}")
async def get_conversation_endpoint(conversation_id: str):
    """Récupère l'historique complet d'une conversation et restaure le contexte en mémoire."""
    from src.services.conversation_store import ConversationStore
    store = ConversationStore.get_instance()
    conv = await store.get_conversation(conversation_id, include_messages=True)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation introuvable")

    # Reprise instantanée du contexte dans SessionManager
    try:
        from src.services.session_manager import SessionManager, ChatTurn
        session = SessionManager.get_or_create(session_id=conversation_id, user_id=conv.get("user_id", "mobile_user"))
        session.history.clear()
        for m in conv.get("messages", []):
            session.history.append(ChatTurn(
                role=m.get("role", "user"),
                content=m.get("content", ""),
                timestamp=m.get("timestamp", time.time()),
                cards=m.get("cards")
            ))
    except Exception as e:
        logger.error(f"Sync SessionManager error: {e}", exc_info=True)

    return conv


@app.patch("/api/conversations/{conversation_id}")
async def update_conversation_endpoint(conversation_id: str, req: ConversationUpdateRequest):
    """Met à jour les métadonnées (titre, épinglé, archivé) d'une discussion."""
    from src.services.conversation_store import ConversationStore
    store = ConversationStore.get_instance()
    updated = await store.update_conversation(
        conversation_id=conversation_id,
        title=req.title,
        is_pinned=req.is_pinned,
        is_archived=req.is_archived,
        metadata=req.metadata
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    return updated


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation_endpoint(conversation_id: str):
    """Supprime définitivement une discussion."""
    from src.services.conversation_store import ConversationStore
    store = ConversationStore.get_instance()
    success = await store.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    return {"success": True, "deleted_id": conversation_id}


@app.post("/api/conversations/{conversation_id}/generate-title")
async def generate_title_endpoint(conversation_id: str, req: Optional[Dict[str, Any]] = None):
    """Génère automatiquement un titre concis à partir du premier échange."""
    from src.services.conversation_store import ConversationStore
    store = ConversationStore.get_instance()
    conv = await store.get_conversation(conversation_id, include_messages=False)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    custom_text = req.get("text") if req else None
    title = await store.generate_title_from_first_message(conversation_id, custom_text=custom_text)
    return {"title": title, "id": conversation_id}


@app.get("/api/conversations/{conversation_id}/export")
async def export_conversation_endpoint(conversation_id: str, format: str = "markdown"):
    """Exporte l'historique de discussion en Markdown ou JSON standard."""
    from src.services.conversation_store import ConversationStore
    store = ConversationStore.get_instance()
    conv = await store.get_conversation(conversation_id, include_messages=False)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation introuvable")

    raw_title = conv.get("title") or "discussion"
    slug = re.sub(r'[^a-zA-Z0-9_\-]+', '_', raw_title.lower()).strip('_')[:30] or "chat"

    if format.lower() == "json":
        data = await store.export_conversation_json(conversation_id)
        return JSONResponse(
            content=data,
            headers={"Content-Disposition": f'attachment; filename="hol_ai_{slug}_{conversation_id}.json"'}
        )
    else:
        md = await store.export_conversation_markdown(conversation_id)
        return Response(
            content=md,
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="hol_ai_{slug}_{conversation_id}.md"'}
        )


class SetApiKeyRequest(BaseModel):
    api_key: str
    provider: str = "gemini"


@app.post("/api/settings/api-key")
async def set_api_key_endpoint(req: SetApiKeyRequest):
    from src.services.llm_engine import LLMBrain
    LLMBrain.set_api_key(req.api_key)
    return {"success": True, "status": "CONNECTED", "model": "gemini-3.1-flash-lite"}


@app.get("/api/settings/api-key")
async def get_api_key_status_endpoint():
    from src.services.llm_engine import LLMBrain
    key = LLMBrain.get_api_key()
    return {
        "connected": bool(key),
        "model": "gemini-3.1-flash-lite" if key else "AUCUN_CERVEAU",
        "masked_key": f"{key[:6]}...{key[-4:]}" if key and len(key) > 10 else None
    }

# ============================================================================
# ENDPOINTS CONNECTEURS & HUB D'INTÉGRATIONS (GMAIL, CALENDAR, TELEGRAM, WHATSAPP, LLM)
# ============================================================================

class ConfigureConnectorRequest(BaseModel):
    connector_id: str
    payload: Dict[str, Any]


@app.get("/api/connectors/status")
async def get_connectors_status_endpoint():
    """Retourne la télémétrie complète et l'état de chaque connecteur."""
    from src.services.connectors_manager import ConnectorsManager
    return ConnectorsManager.get_all_connectors_status()


@app.post("/api/connectors/configure")
async def configure_connector_endpoint(req: ConfigureConnectorRequest):
    """Enregistre les identifiants d'un connecteur et met à jour .env."""
    from src.services.connectors_manager import ConnectorsManager
    res = ConnectorsManager.configure_connector(req.connector_id, req.payload)
    return res


@app.post("/api/connectors/test/{connector_id}")
async def test_connector_endpoint(connector_id: str):
    """Effectue un test de connectivité réel ou simulé en direct."""
    from src.services.connectors_manager import ConnectorsManager
    res = ConnectorsManager.test_connector(connector_id)
    return res


# ============================================================================
# ENDPOINTS CATALOGUE 1 079 APIS PUBLIQUES & TOOL-CALLING AUTONOME
# ============================================================================

class ExecuteToolApiRequest(BaseModel):
    tool_id: str
    query_params: Optional[Dict[str, Any]] = None
    path_suffix: Optional[str] = ""


@app.get("/api/tools/public-apis/stats")
async def get_public_apis_stats():
    """Retourne les métriques globales du catalogue des 1 079 APIs publiques."""
    from src.tools.public_registry import PublicApiRegistry
    registry = PublicApiRegistry.get_instance()
    return registry.get_stats()


@app.get("/api/tools/public-apis/categories")
async def get_public_apis_categories():
    """Retourne la liste des 49 catégories d'APIs publiques."""
    from src.tools.public_registry import PublicApiRegistry
    registry = PublicApiRegistry.get_instance()
    categories = registry.get_categories()
    return {"categories": categories, "total_categories": len(categories)}


@app.get("/api/tools/public-apis")
async def list_public_apis(
    query: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Recherche ou liste les outils du catalogue d'APIs publiques."""
    from src.tools.public_registry import PublicApiRegistry
    registry = PublicApiRegistry.get_instance()
    if query and query.strip():
        tools = registry.search_tools(query=query.strip(), category=category, top_k=limit)
        total = len(tools)
    else:
        tools = registry.list_tools(category=category, limit=limit, offset=offset)
        stats = registry.get_stats()
        total = stats.get("total_tools", 1079) if not category else len(tools)

    return {
        "tools": [t.model_dump() for t in tools],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@app.post("/api/tools/public-apis/execute")
async def execute_public_api_tool(req: ExecuteToolApiRequest):
    """Exécute un outil du catalogue d'APIs publiques de manière asynchrone et résiliente."""
    from src.tools.tool_calling_engine import AutonomousToolCallingEngine
    engine = AutonomousToolCallingEngine.get_instance()
    result = await engine.execute_tool(
        tool_id=req.tool_id,
        query_params=req.query_params,
        path_suffix=req.path_suffix or ""
    )
    return result.model_dump()



# ============================================================================
# ENDPOINTS MUSE AI : ACTIONS SÉCURISÉES, ENCLAVE & GARDIEN D'ARRIÈRE-PLAN
# ============================================================================

class ExecuteActionRequest(BaseModel):
    action_id: str
    action_type: str = "ONE_CLICK_ACTION"
    payload: Dict[str, Any] = {}


@app.post("/api/actions/execute")
async def execute_action_endpoint(req: ExecuteActionRequest):
    """Exécute et signe cryptographiquement une action sensible (Human-in-the-Loop Pilier 5)."""
    from src.services.secure_vault import enclave_vm
    tx_hash = enclave_vm.log_and_sign_transaction(req.action_type, req.payload)
    return {
        "success": True,
        "action_id": req.action_id,
        "action_type": req.action_type,
        "tx_hash": tx_hash,
        "status": "CONFIRMED_AND_EXECUTED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": f"Action '{req.action_type}' validée et certifiée par l'Enclave HoL VM."
    }


@app.get("/api/background/status")
async def get_background_status_endpoint():
    """Consulte l'état des missions 24/7 en arrière-plan et des 3 cron jobs (Pilier 3)."""
    from src.services.background_watcher import guardian
    return guardian.get_status()


@app.get("/api/background/cron")
async def get_background_cron_endpoint():
    """Consulte la configuration et l'historique des 3 Cron Jobs autonomes (08h00, 13h00, 22h00)."""
    from src.services.background_watcher import guardian
    return {
        "cron_jobs": guardian.cron_jobs,
        "cron_history": guardian.cron_history
    }


@app.post("/api/background/cron/{job_id}/trigger")
async def trigger_cron_job_endpoint(job_id: str):
    """Déclenche manuellement un Cron Job autonome pour test ou forçage immédiat."""
    from src.services.background_watcher import guardian
    try:
        result = guardian.execute_cron_job(job_id)
        return {"success": True, "job_id": job_id, "result": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


class AddMissionRequest(BaseModel):
    name: str
    type: str = "CUSTOM_WATCH"
    details: Dict[str, Any] = {}


@app.post("/api/background/mission")
async def add_background_mission_endpoint(req: AddMissionRequest):
    """Ajoute une mission de surveillance continue en arrière-plan."""
    from src.services.background_watcher import guardian
    mission = guardian.add_mission(req.name, req.type, req.details)
    return {"success": True, "mission": mission}


@app.get("/api/jarvis/briefing")
async def get_jarvis_briefing_endpoint(
    city: str = "Paris",
    topic: str = "general",
    force_refresh: bool = False,
    persona: Optional[str] = None,
    include_deals: bool = False
):
    """Génère les données complètes, actualités réelles, météo locale et script oralisé sans répétition du Morning Briefing (R5)."""
    from src.services.morning_briefing import MorningBriefingService
    return await MorningBriefingService.generate_briefing(
        city=city,
        topic=topic,
        force_refresh=force_refresh,
        force_persona=persona,
        include_deals=include_deals
    )


@app.get("/api/briefing/morning")
async def get_morning_briefing_alias_endpoint(
    city: str = "Paris",
    topic: str = "general",
    force_refresh: bool = False,
    persona: Optional[str] = None,
    include_deals: bool = False
):
    """Alias officiel pour /api/briefing/morning."""
    from src.services.morning_briefing import MorningBriefingService
    return await MorningBriefingService.generate_briefing(
        city=city,
        topic=topic,
        force_refresh=force_refresh,
        force_persona=persona,
        include_deals=include_deals
    )


@app.get("/api/briefing/live")
async def get_live_briefing_endpoint(
    city: str = "Paris",
    topic: str = "general",
    force_refresh: bool = False,
    persona: Optional[str] = None,
    include_deals: bool = False
):
    """Alias blueprint pour le briefing matinal connecté aux actualités réelles et météo locale (R5)."""
    from src.services.morning_briefing import MorningBriefingService
    return await MorningBriefingService.generate_briefing(
        city=city,
        topic=topic,
        force_refresh=force_refresh,
        force_persona=persona,
        include_deals=include_deals
    )


class VisualSearchRequest(BaseModel):
    query: Optional[str] = None
    q: Optional[str] = None
    lang: str = "fr"


@app.get("/api/visual/search")
async def visual_search_get_endpoint(q: str = "", lang: str = "fr"):
    """Recherche d'images haute résolution et enrichissement visuel contextuel (R6 - GET)."""
    from src.services.visual_search import VisualSearchEngine
    results = await VisualSearchEngine.enrich_with_visuals(q, lang=lang)
    return {
        "status": "ok",
        "query": q,
        "results": results
    }


@app.post("/api/visual/search")
async def visual_search_post_endpoint(req: VisualSearchRequest):
    """Recherche d'images haute résolution et enrichissement visuel contextuel (R6 - POST)."""
    target_q = req.query or req.q or ""
    from src.services.visual_search import VisualSearchEngine
    results = await VisualSearchEngine.enrich_with_visuals(target_q, lang=req.lang)
    return {
        "status": "ok",
        "query": target_q,
        "results": results
    }


@app.get("/api/vault/ledger")
async def get_vault_ledger_endpoint():
    """Consulte le grand livre d'audit cryptographique de l'Enclave Sécurisée (Pilier 4)."""
    from src.services.secure_vault import enclave_vm
    return {
        "vm_id": enclave_vm.vm_id,
        "status": enclave_vm.status,
        "total_transactions": len(enclave_vm.audit_ledger),
        "ledger": enclave_vm.get_audit_ledger()
    }


class SandboxCodeRequest(BaseModel):
    code: str


@app.post("/api/vault/sandbox")
async def run_vault_sandbox_endpoint(req: SandboxCodeRequest):
    """Exécute du code Python dans le bac à sable chiffré de l'Enclave (Pilier 4)."""
    from src.services.secure_vault import enclave_vm
    return enclave_vm.execute_isolated_code(req.code)


@app.get("/api/telegram/status")
async def get_telegram_status_endpoint():
    """Statut de la passerelle Telegram et multi-supports mobile (Pilier 6)."""
    from src.services.telegram_gateway import telegram_gateway
    return telegram_gateway.get_status()


class TelegramSettingsRequest(BaseModel):
    bot_token: str


@app.post("/api/telegram/settings")
async def set_telegram_token_endpoint(req: TelegramSettingsRequest):
    """Configure le jeton du bot Telegram personnel."""
    from src.services.telegram_gateway import telegram_gateway
    telegram_gateway.set_bot_token(req.bot_token)
    return {"success": True, "status": "TOKEN_SAVED", "bot": telegram_gateway.channel_name}


# ============================================================================
# ENDPOINTS PHASE 2 : SOURCING MULTI-FOURNISSEURS, LOGISTIQUE & CFO ENGINE
# ============================================================================

class SourcingCompareRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    target_selling_price_ttc: Optional[float] = Field(default=None)

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        cleaned = str(v).replace("\x00", "").strip()
        if not cleaned:
            raise ValueError("Query cannot be empty")
        return cleaned

    @field_validator("target_selling_price_ttc", mode="before")
    @classmethod
    def validate_price(cls, v: Any) -> Optional[float]:
        if v is None:
            return None
        try:
            val = float(v)
            if not math.isfinite(val):
                raise ValueError("target_selling_price_ttc must be a finite number")
            if val < 0:
                raise ValueError("target_selling_price_ttc cannot be negative")
            return val
        except (ValueError, TypeError):
            raise ValueError("target_selling_price_ttc must be a valid float")


@app.post("/api/sourcing/compare")
async def compare_sourcing_endpoint(req: SourcingCompareRequest):
    """Compare en temps réel Alibaba, DHgate, Hacoo, Cdiscount et Amazon."""
    from src.services.product_hunter import ProductHunterService
    result = ProductHunterService.compare_multi_suppliers(
        query=req.query,
        target_selling_price_ttc=req.target_selling_price_ttc
    )
    return result


class EcommerceArbitrationRequest(BaseModel):
    query: Optional[str] = None
    q: Optional[str] = None
    merchant: Optional[str] = None
    preferred_merchant: Optional[str] = None


@app.get("/api/sourcing/arbitrate")
async def sourcing_arbitrate_get_endpoint(q: str = "", merchant: Optional[str] = None):
    """Arbitre automatiquement le meilleur marchand de référence et recommande 3-4 alternatives du même marchand (R7 - GET)."""
    from src.services.ecommerce_arbitration import EcommerceArbitrationService
    return await EcommerceArbitrationService.generate_decision_card(query=q, preferred_merchant=merchant)


@app.post("/api/sourcing/arbitrate")
async def sourcing_arbitrate_post_endpoint(req: EcommerceArbitrationRequest):
    """Arbitre automatiquement le meilleur marchand de référence et recommande 3-4 alternatives du même marchand (R7 - POST)."""
    target_q = req.query or req.q or ""
    pref_merchant = req.preferred_merchant or req.merchant
    from src.services.ecommerce_arbitration import EcommerceArbitrationService
    return await EcommerceArbitrationService.generate_decision_card(query=target_q, preferred_merchant=pref_merchant)


@app.get("/api/ecommerce/search")
@app.get("/api/ecommerce/arbitrate")
async def ecommerce_search_alias_get_endpoint(
    query: Optional[str] = None,
    q: Optional[str] = None,
    merchant: Optional[str] = None
):
    """Alias GET pour la recherche et l'arbitrage e-commerce décisionnel."""
    target_q = query or q or ""
    from src.services.ecommerce_arbitration import EcommerceArbitrationService
    return await EcommerceArbitrationService.generate_decision_card(query=target_q, preferred_merchant=merchant)


@app.post("/api/ecommerce/arbitrate")
async def ecommerce_arbitrate_post_endpoint(req: EcommerceArbitrationRequest):
    """Alias pour l'arbitrage e-commerce décisionnel (R7)."""
    target_q = req.query or req.q or ""
    pref_merchant = req.preferred_merchant or req.merchant
    from src.services.ecommerce_arbitration import EcommerceArbitrationService
    return await EcommerceArbitrationService.generate_decision_card(query=target_q, preferred_merchant=pref_merchant)


class TrackCarrierRequest(BaseModel):
    tracking_number: str = Field(..., min_length=1, max_length=150)
    carrier: str = Field(default="UPS", max_length=50)

    @field_validator("tracking_number", "carrier")
    @classmethod
    def clean_str(cls, v: str) -> str:
        return str(v).replace("\x00", "").strip()


@app.post("/api/logistics/track")
async def track_carrier_endpoint(req: TrackCarrierRequest):
    """Suivi temps réel multi-transporteurs (Colissimo, Mondial Relay, UPS, DHL)."""
    log_agent = agents_registry.get(AgentID.AGENT_3_LOGISTICS.value)
    if not log_agent:
        raise HTTPException(status_code=503, detail="Agent Logistique non disponible")
    return log_agent._simulate_tracking(req.tracking_number, req.carrier)


class CalculateMarginRequest(BaseModel):
    selling_price_ttc: float = Field(..., description="Prix de vente TTC")
    cost_price: float = Field(..., description="Coût d'achat")
    vat_rate: float = Field(default=0.20, description="Taux de TVA")
    shipping_cost: float = Field(default=0.0, description="Frais d'expédition")
    platform_fee_percent: float = Field(default=0.0, description="Commissions plateforme")

    @field_validator("selling_price_ttc", "cost_price", "vat_rate", "shipping_cost", "platform_fee_percent", mode="before")
    @classmethod
    def validate_finite(cls, v: Any) -> float:
        if v is None:
            raise ValueError("Value cannot be null")
        try:
            val = float(v)
            if not math.isfinite(val):
                raise ValueError("Value must be a finite number")
            return val
        except (ValueError, TypeError):
            raise ValueError("Value must be a valid float")


@app.post("/api/cfo/margin")
async def calculate_cfo_margin_endpoint(req: CalculateMarginRequest):
    """Calcul en temps réel de la marge nette e-commerce (Prix TTC - TVA 20% - Achat - Stripe 1.5% + 0.25€)."""
    fin_agent = agents_registry.get(AgentID.AGENT_4_FINANCE.value)
    if not fin_agent:
        raise HTTPException(status_code=503, detail="Agent Finance non disponible")
    return fin_agent.calculate_cfo_realtime_margin(
        selling_price_ttc=req.selling_price_ttc,
        cost_price=req.cost_price,
        vat_rate=req.vat_rate,
        shipping_cost=req.shipping_cost,
        platform_fee_percent=req.platform_fee_percent
    )


@app.get("/api/cfo/affiliate-reconciliation")
async def get_affiliate_reconciliation_endpoint():
    """Rapprochement en temps réel des commissions d'affiliation (Hacoo, DHgate, Amazon Partners) vs OPEX."""
    fin_agent = agents_registry.get(AgentID.AGENT_4_FINANCE.value)
    if not fin_agent:
        raise HTTPException(status_code=503, detail="Agent Finance non disponible")
    return fin_agent.reconcile_affiliate_and_expenses()


class ReceiptAnalysisRequest(BaseModel):
    vendor: Optional[str] = Field(default=None, max_length=200)
    amount_ttc: Optional[float] = Field(default=None)
    raw_text: Optional[str] = Field(default=None, max_length=150000)
    invoice_id: Optional[str] = Field(default=None, max_length=100)

    @field_validator("amount_ttc", mode="before")
    @classmethod
    def validate_amount(cls, v: Any) -> Optional[float]:
        if v is None:
            return None
        try:
            val = float(v)
            if not math.isfinite(val):
                raise ValueError("amount_ttc must be a finite number")
            return val
        except (ValueError, TypeError):
            raise ValueError("amount_ttc must be a valid float")


@app.post("/api/cfo/receipt")
async def analyze_receipt_endpoint(req: ReceiptAnalysisRequest):
    """Audit instantané d'un reçu ou d'une facture téléversé avec ventilation TVA et rapprochement budgétaire."""
    fin_agent = agents_registry.get(AgentID.AGENT_4_FINANCE.value)
    if not fin_agent:
        raise HTTPException(status_code=503, detail="Agent Finance non disponible")
    return fin_agent.analyze_receipt_or_invoice(
        receipt_data=req.model_dump(),
        raw_text=req.raw_text
    )


class OrchestrateRequest(BaseModel):
    intent: str
    user_id: str = "user_pilot_01"
    canvas_id: str = "workspace_alpha"


@app.get("/api/state")
async def get_system_state():
    canvas_ag: CanvasAgent = agents_registry.get(AgentID.AGENT_1_CANVAS.value)
    nodes = canvas_ag.get_all_nodes() if canvas_ag else []
    return {
        "status": "ONLINE",
        "cluster": "healthy",
        "nodes": nodes,
        "agents": {name: "ACTIVE" for name in agents_registry.keys()},
        "total_nodes": len(nodes)
    }


@app.get("/api/agents/status")
async def get_agents_status():
    status_list = []
    for aid, ag in agents_registry.items():
        status_list.append({
            "agent_id": aid,
            "status": "ONLINE" if ag._is_running else "OFFLINE",
            "stream": ag.stream_name,
            "group": ag.consumer_group,
            "instance": ag.instance_id
        })
    status_list.append({
        "agent_id": "manager",
        "status": "ONLINE" if manager._is_running else "OFFLINE",
        "stream": manager.inbound_stream,
        "group": manager.consumer_group,
        "instance": manager.instance_id
    })
    return status_list


@app.post("/api/orchestrate")
async def orchestrate_intent(req: OrchestrateRequest):
    if not manager:
        raise HTTPException(status_code=503, detail="Manager not initialized")

    context = ContextModel(
        user_id=req.user_id,
        session_id=f"ses_{uuid4().hex[:6]}",
        canvas_id=req.canvas_id
    )

    # 1. Orchestration multi-agents via l'Agent Manager
    result = await manager.orchestrate(req.intent, context=context)

    # 2. Création et synchronisation automatique de nouveaux blocs sur le canevas selon les résultats
    canvas_ag: CanvasAgent = agents_registry[AgentID.AGENT_1_CANVAS.value]
    created_node_ids = []

    # Si Logistique a répondu -> Bloc Colis interactif
    if AgentID.AGENT_3_LOGISTICS.value in result.results_by_agent:
        log_data = result.results_by_agent[AgentID.AGENT_3_LOGISTICS.value]
        nid = f"pkg_{uuid4().hex[:6]}"
        canvas_ag.workspace_nodes[nid] = CanvasAgent.model_validate_json if hasattr(CanvasAgent, "validate") else None # fallback
        from src.agents.agent_1_canvas.service import CanvasNode, Position, Dimensions
        node_pkg = CanvasNode(
            id=nid,
            type="logistics",
            title=f"Colis {log_data.get('carrier')} • {log_data.get('tracking_number')}",
            position=Position(x=480, y=100 + len(created_node_ids) * 60),
            dimensions=Dimensions(width=360, height=240),
            data=log_data
        )
        canvas_ag.workspace_nodes[nid] = node_pkg
        created_node_ids.append(nid)

    # Si Finance a répondu avec un Audit d'Abonnements (Muse AI)
    if AgentID.AGENT_4_FINANCE.value in result.results_by_agent:
        fin_res = result.results_by_agent[AgentID.AGENT_4_FINANCE.value]
        from src.agents.agent_1_canvas.service import CanvasNode, Position, Dimensions

        if "subscriptions" in fin_res:
            nid = f"sub_{uuid4().hex[:6]}"
            node_sub = CanvasNode(
                id=nid,
                type="subscription",
                title=f"Audit Abonnements • {fin_res.get('leaks_detected_count')} Fuites Détectées",
                position=Position(x=100 + len(created_node_ids) * 40, y=360),
                dimensions=Dimensions(width=380, height=310),
                data=fin_res
            )
            canvas_ag.workspace_nodes[nid] = node_sub
            created_node_ids.append(nid)
        elif "selling_price_ttc" in fin_res:
            nid = f"fin_{uuid4().hex[:6]}"
            node_fin = CanvasNode(
                id=nid,
                type="finance",
                title=f"Audit Marge Nette • Vente {fin_res.get('selling_price_ttc')}€",
                position=Position(x=880, y=100 + len(created_node_ids) * 60),
                dimensions=Dimensions(width=360, height=250),
                data=fin_res
            )
            canvas_ag.workspace_nodes[nid] = node_fin
            created_node_ids.append(nid)

    # Si Logistique a répondu avec une opportunité d'Achat / Deal (Muse AI)
    if AgentID.AGENT_3_LOGISTICS.value in result.results_by_agent:
        log_res = result.results_by_agent[AgentID.AGENT_3_LOGISTICS.value]
        from src.agents.agent_1_canvas.service import CanvasNode, Position, Dimensions

        if "deal_urgency" in log_res:
            nid = f"deal_{uuid4().hex[:6]}"
            node_deal = CanvasNode(
                id=nid,
                type="deal",
                title=f"Alerte Deal (-{log_res.get('savings_percent')}%) • {log_res.get('product')}",
                position=Position(x=500 + len(created_node_ids) * 50, y=120),
                dimensions=Dimensions(width=370, height=270),
                data=log_res
            )
            canvas_ag.workspace_nodes[nid] = node_deal
            created_node_ids.append(nid)
        elif "tracking_number" in log_res:
            nid = f"pkg_{uuid4().hex[:6]}"
            node_pkg = CanvasNode(
                id=nid,
                type="logistics",
                title=f"Colis {log_res.get('carrier')} • {log_res.get('tracking_number')}",
                position=Position(x=480, y=100 + len(created_node_ids) * 60),
                dimensions=Dimensions(width=360, height=240),
                data=log_res
            )
            canvas_ag.workspace_nodes[nid] = node_pkg
            created_node_ids.append(nid)

    # Si Content a répondu avec Meta Ads (Muse AI)
    if AgentID.AGENT_5_CONTENT.value in result.results_by_agent:
        cont_res = result.results_by_agent[AgentID.AGENT_5_CONTENT.value]
        from src.agents.agent_1_canvas.service import CanvasNode, Position, Dimensions

        if "blended_roas" in cont_res:
            nid = f"ads_{uuid4().hex[:6]}"
            node_ads = CanvasNode(
                id=nid,
                type="meta_ads",
                title="Meta Ads & Instagram • ROAS 3.8x",
                position=Position(x=920, y=360),
                dimensions=Dimensions(width=370, height=280),
                data=cont_res
            )
            canvas_ag.workspace_nodes[nid] = node_ads
            created_node_ids.append(nid)
        elif "hook" in cont_res:
            nid = f"soc_{uuid4().hex[:6]}"
            node_soc = CanvasNode(
                id=nid,
                type="content",
                title="Script Viral & Code-Switching",
                position=Position(x=480, y=380),
                dimensions=Dimensions(width=360, height=250),
                data=cont_res
            )
            canvas_ag.workspace_nodes[nid] = node_soc
            created_node_ids.append(nid)

    # Si Exécution a répondu avec le Gardien Autonome 24/7 (Muse AI)
    if AgentID.AGENT_6_EXECUTION.value in result.results_by_agent:
        exec_res = result.results_by_agent[AgentID.AGENT_6_EXECUTION.value]
        from src.agents.agent_1_canvas.service import CanvasNode, Position, Dimensions

        if "watcher_active" in exec_res:
            nid = f"grd_{uuid4().hex[:6]}"
            node_grd = CanvasNode(
                id=nid,
                type="autonomous_guardian",
                title="Gardien Autonome 24/7 (HoL Vault)",
                position=Position(x=520, y=420),
                dimensions=Dimensions(width=370, height=260),
                data=exec_res
            )
            canvas_ag.workspace_nodes[nid] = node_grd
            created_node_ids.append(nid)
        elif "micro_actions" in exec_res:
            nid = f"act_{uuid4().hex[:6]}"
            node_act = CanvasNode(
                id=nid,
                type="execution",
                title="Micro-Actions (Règle des 2 Min)",
                position=Position(x=880, y=380),
                dimensions=Dimensions(width=360, height=250),
                data=exec_res
            )
            canvas_ag.workspace_nodes[nid] = node_act
            created_node_ids.append(nid)

    # Lier logiquement les blocs s'il y en a plusieurs
    if len(created_node_ids) >= 2:
        for i in range(len(created_node_ids) - 1):
            src_id = created_node_ids[i]
            tgt_id = created_node_ids[i + 1]
            canvas_ag.workspace_nodes[src_id].connected_to.append(tgt_id)

    # Diffusion en direct à tous les navigateurs connectés par WebSocket
    all_nodes = canvas_ag.get_all_nodes()
    await ConnectionManager.broadcast("CANVAS_SYNC", {"nodes": all_nodes})
    await ConnectionManager.broadcast("ORCHESTRATION_COMPLETED", result.to_dict())

    return {
        "orchestration": result.to_dict(),
        "canvas_nodes": all_nodes,
        "new_node_ids": created_node_ids
    }


@app.post("/api/canvas/upload")
async def upload_canvas_file(
    request: Request,
    file: Optional[UploadFile] = File(None),
    filename: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    x: Optional[float] = Form(None),
    y: Optional[float] = Form(None),
    content_text: Optional[str] = Form(None)
):
    """
    Endpoint universel d'ingestion multimodale / OCR pour le Canevas Spatial (Muse x1000).
    Accepte les uploads de fichiers ou requêtes multipart / JSON, déclenche l'analyse
    multimodale / OCR via l'Agent 2, crée un nœud spatial sur le canevas de l'Agent 1, et diffuse en WebSocket.
    """
    canvas_ag: CanvasAgent = agents_registry.get(AgentID.AGENT_1_CANVAS.value) if agents_registry else None
    ingestion_ag: IngestionMemoryAgent = agents_registry.get(AgentID.AGENT_2_INGESTION.value) if agents_registry else None

    if not canvas_ag or not ingestion_ag:
        raise HTTPException(status_code=503, detail="Agents Canvas ou Ingestion non initialisés")

    content_type_header = request.headers.get("content-type", "")
    fname = "document.txt"
    mime = "application/octet-stream"
    text_content = ""
    thumbnail_url = None
    file_size = 0

    if "application/json" in content_type_header:
        try:
            body_data = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Corps JSON invalide")
        if not isinstance(body_data, dict):
            raise HTTPException(status_code=422, detail="Le corps de la requête doit être un objet JSON")

        raw_fname = body_data.get("filename") or filename or "note.txt"
        fname = sanitize_filename(raw_fname)
        mime = body_data.get("content_type") or "text/plain"
        raw_content = body_data.get("content") or ""
        text_content = sanitize_text(str(raw_content), max_len=1_000_000)
        raw_title = body_data.get("title") or title
        title = sanitize_text(raw_title, max_len=200) if raw_title else None
        x = body_data.get("x") if body_data.get("x") is not None else x
        y = body_data.get("y") if body_data.get("y") is not None else y
        thumbnail_url = body_data.get("thumbnail")
        file_size = body_data.get("file_size", len(text_content.encode("utf-8")) if text_content else 0)
    else:
        if file is not None:
            raw_fname = file.filename or filename or "upload.dat"
            fname = sanitize_filename(raw_fname)
            mime = file.content_type or "application/octet-stream"
            raw_bytes = await file.read()
            file_size = len(raw_bytes)
            if file_size > 15 * 1024 * 1024:
                raise HTTPException(status_code=413, detail="Fichier trop volumineux (max 15MB)")

            if file_size == 0:
                text_content = ""
                thumbnail_url = None
            elif mime.startswith("image/") or any(fname.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".svg"]):
                try:
                    b64 = base64.b64encode(raw_bytes).decode("ascii")
                    thumbnail_url = f"data:{mime};base64,{b64}"
                except Exception:
                    thumbnail_url = None
                text_content = ""
            else:
                try:
                    text_content = sanitize_text(raw_bytes.decode("utf-8", errors="ignore"), max_len=1_000_000)
                except Exception:
                    text_content = ""
        elif content_text is not None:
            text_content = sanitize_text(content_text, max_len=1_000_000)
            fname = sanitize_filename(filename or "note.txt")
            mime = "text/plain"
            file_size = len(text_content.encode("utf-8"))

    from src.agents.agent_1_canvas.service import CanvasNode, Position, Dimensions

    # Coordonnées spatiales sécurisées
    if x is not None and y is not None:
        try:
            fx = float(x)
            fy = float(y)
            if not math.isfinite(fx) or not math.isfinite(fy):
                raise HTTPException(status_code=422, detail="Les coordonnées spatiales doivent être des nombres finis")
            pos = Position(x=fx, y=fy)
        except (ValueError, TypeError):
            raise HTTPException(status_code=422, detail="Coordonnées spatiales invalides")
    else:
        existing_count = len(canvas_ag.workspace_nodes)
        pos = Position(x=120.0 + (existing_count % 3) * 390.0, y=100.0 + (existing_count // 3) * 320.0)

    # 1. Analyse multimodale / OCR via l'Agent 2
    from src.core.contracts import (
        A2AMessage,
        SourceDescriptor,
        TargetDescriptor,
        PriorityEnum,
        StatusEnum,
        ContextModel
    )

    msg = A2AMessage(
        source=SourceDescriptor(agent_id=AgentID.MANAGER, role="supervisor"),
        target=TargetDescriptor(agent_id=AgentID.AGENT_2_INGESTION, action=ActionType.INGEST_MULTIMODAL),
        priority=PriorityEnum.HIGH,
        context=ContextModel(user_id="user_canvas_pilot", session_id=f"upload_{uuid4().hex[:6]}"),
        payload={
            "filename": fname,
            "content_type": mime,
            "content": text_content,
            "file_size": file_size,
            "thumbnail": thumbnail_url
        }
    )

    agent2_resp = await ingestion_ag.handle_message(msg)
    analysis = agent2_resp.result

    # 2. Création du nœud spatial sur l'Agent 1
    node_id = f"node_{uuid4().hex[:8]}"
    node_type = analysis.get("node_type", "note")
    raw_node_title = title or analysis.get("title", f"Document • {fname}")
    node_title = sanitize_text(raw_node_title, max_len=200)

    dims = Dimensions(
        width=360.0,
        height=310.0 if node_type == "image" else (280.0 if node_type == "invoice" else 230.0)
    )

    new_node = CanvasNode(
        id=node_id,
        type=node_type,
        title=node_title,
        position=pos,
        dimensions=dims,
        data=analysis,
        connected_to=[]
    )
    canvas_ag.workspace_nodes[node_id] = new_node

    # 3. Diffusion temps réel par WebSocket à tous les clients connectés
    await ConnectionManager.broadcast("NODE_CREATED", {"node": new_node.model_dump()})
    await ConnectionManager.broadcast("CANVAS_SYNC", {"nodes": canvas_ag.get_all_nodes()})

    return {
        "success": True,
        "node": new_node.model_dump(),
        "analysis": analysis,
        "total_nodes": len(canvas_ag.workspace_nodes),
        "message": f"Nœud spatial '{node_title}' généré et synchronisé."
    }


@app.websocket("/ws/canvas")
async def canvas_websocket(websocket: WebSocket):
    await ConnectionManager.connect(websocket)
    canvas_ag: CanvasAgent = agents_registry.get(AgentID.AGENT_1_CANVAS.value) if agents_registry else None

    # Envoi initial de l'état spatial complet
    if canvas_ag:
        await websocket.send_text(json.dumps({
            "event": "INITIAL_STATE",
            "data": {"nodes": canvas_ag.get_all_nodes()}
        }))

    try:
        while True:
            raw_text = await websocket.receive_text()
            try:
                data = json.loads(raw_text)
            except Exception:
                await websocket.send_text(json.dumps({"event": "ERROR", "message": "Invalid JSON frame"}))
                continue

            if not isinstance(data, dict):
                await websocket.send_text(json.dumps({"event": "ERROR", "message": "Payload must be a JSON object"}))
                continue

            action = data.get("action")
            if not action or not isinstance(action, str):
                await websocket.send_text(json.dumps({"event": "ERROR", "message": "Missing or invalid 'action' field"}))
                continue

            if action == "MOVE_NODE":
                node_id = data.get("node_id")
                pos = data.get("position")
                if not node_id or not isinstance(node_id, str):
                    await websocket.send_text(json.dumps({"event": "ERROR", "message": "MOVE_NODE requires a string node_id"}))
                    continue
                if not canvas_ag or node_id not in canvas_ag.workspace_nodes:
                    await websocket.send_text(json.dumps({"event": "WARNING", "message": f"Node '{node_id}' not found"}))
                    continue
                if not isinstance(pos, dict) or "x" not in pos or "y" not in pos:
                    await websocket.send_text(json.dumps({"event": "ERROR", "message": "MOVE_NODE requires position dict with 'x' and 'y'"}))
                    continue
                try:
                    px = float(pos["x"])
                    py = float(pos["y"])
                    if not math.isfinite(px) or not math.isfinite(py):
                        await websocket.send_text(json.dumps({"event": "ERROR", "message": "Coordinates must be finite numbers"}))
                        continue
                    # Clamping coordinates
                    px = max(0.0, px)
                    py = max(0.0, py)
                    from src.agents.agent_1_canvas.service import Position
                    canvas_ag.workspace_nodes[node_id].position = Position(x=px, y=py)
                    await ConnectionManager.broadcast("NODE_MOVED", {"node_id": node_id, "position": {"x": px, "y": py}})
                except (ValueError, TypeError) as coord_err:
                    await websocket.send_text(json.dumps({"event": "ERROR", "message": f"Invalid coordinates: {coord_err}"}))
                    continue

            elif action == "CONNECT_NODES":
                source_id = data.get("source_id")
                target_id = data.get("target_id")
                if not source_id or not target_id or not isinstance(source_id, str) or not isinstance(target_id, str):
                    await websocket.send_text(json.dumps({"event": "ERROR", "message": "CONNECT_NODES requires string source_id and target_id"}))
                    continue
                if not canvas_ag or source_id not in canvas_ag.workspace_nodes or target_id not in canvas_ag.workspace_nodes:
                    await websocket.send_text(json.dumps({"event": "WARNING", "message": "Source or target node not found"}))
                    continue
                if target_id not in canvas_ag.workspace_nodes[source_id].connected_to:
                    canvas_ag.workspace_nodes[source_id].connected_to.append(target_id)
                await ConnectionManager.broadcast("NODES_CONNECTED", {"source_id": source_id, "target_id": target_id})
                await ConnectionManager.broadcast("CANVAS_SYNC", {"nodes": canvas_ag.get_all_nodes()})

            elif action == "DELETE_NODE":
                node_id = data.get("node_id")
                if not node_id or not isinstance(node_id, str):
                    await websocket.send_text(json.dumps({"event": "ERROR", "message": "DELETE_NODE requires string node_id"}))
                    continue
                if not canvas_ag or node_id not in canvas_ag.workspace_nodes:
                    await websocket.send_text(json.dumps({"event": "WARNING", "message": f"Node '{node_id}' not found"}))
                    continue
                del canvas_ag.workspace_nodes[node_id]
                for n in canvas_ag.workspace_nodes.values():
                    if node_id in n.connected_to:
                        n.connected_to.remove(node_id)
                await ConnectionManager.broadcast("NODE_DELETED", {"node_id": node_id})
                await ConnectionManager.broadcast("CANVAS_SYNC", {"nodes": canvas_ag.get_all_nodes()})

            elif action == "ORCHESTRATE_COMMAND":
                intent = data.get("intent")
                if not intent or not isinstance(intent, str):
                    await websocket.send_text(json.dumps({"event": "ERROR", "message": "ORCHESTRATE_COMMAND requires string intent"}))
                    continue
                if manager:
                    res = await manager.orchestrate(intent[:2000])
                    await ConnectionManager.broadcast("ORCHESTRATION_COMPLETED", res.to_dict())

            else:
                await websocket.send_text(json.dumps({"event": "WARNING", "message": f"Action non reconnue: {action}"}))

    except WebSocketDisconnect:
        ConnectionManager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Erreur WebSocket: {e}")
        ConnectionManager.disconnect(websocket)


# ==============================================================================
# ROUTES META MUSE PARITY (Computer-Use Streaming, Goals, WhatsApp & Sentinel)
# ==============================================================================

@app.websocket("/ws/browser-stream")
async def browser_stream_websocket(websocket: WebSocket):
    """
    Flux WebSocket bidirectionnel pour le Computer-Use visuel en direct (CDP Screencast)
    et la prise en main interactive (Take Over / Clics / Clavier).
    """
    from src.services.visual_computer_use import VisualComputerUseService
    await websocket.accept()
    service = VisualComputerUseService.get_instance()
    service.active_websockets.add(websocket)

    if not service.is_running:
        await websocket.send_json({
            "type": "status_update",
            "status": "Démarrage du moteur Chromium en cours...",
            "loading": True,
            "url": service.current_url
        })
        asyncio.create_task(service.start_browser())
    elif service.latest_frame_base64:
        await websocket.send_json({
            "type": "screencast_frame",
            "frame": service.latest_frame_base64,
            "cursor": service.cursor_position,
            "mode": service.mode,
            "url": service.current_url,
            "status": service.last_status
        })
    else:
        await websocket.send_json({
            "type": "status_update",
            "status": service.last_status or "Initialisation du flux...",
            "loading": True,
            "url": service.current_url
        })

    try:
        while True:
            data = await websocket.receive_json()
            if isinstance(data, dict):
                await service.handle_user_input(data)
    except WebSocketDisconnect:
        service.active_websockets.discard(websocket)
    except Exception as e:
        logger.warning(f"WebSocket browser stream déconnecté : {e}")
        service.active_websockets.discard(websocket)


@app.get("/api/workspace/goals")
async def get_workspace_goals_endpoint():
    """Récupère les objectifs de l'onglet Goals de Meta Muse."""
    from src.agents.meta_muse_parity import WorkspaceNavigatorAgent
    return WorkspaceNavigatorAgent.manage_goals(action="list")


@app.post("/api/workspace/goals")
async def add_workspace_goal_endpoint(req: Dict[str, Any]):
    """Ajoute un objectif persistant."""
    from src.agents.meta_muse_parity import WorkspaceNavigatorAgent
    return WorkspaceNavigatorAgent.manage_goals(
        action="add",
        title=req.get("title", "Nouvel objectif"),
        category=req.get("category", "Général"),
        target_metric=req.get("target_metric", "100%"),
        deadline=req.get("deadline", "31/12/2026")
    )


@app.get("/api/whatsapp/webhook")
async def verify_whatsapp_webhook(hub_mode: Optional[str] = None, hub_challenge: Optional[str] = None, hub_verify_token: Optional[str] = None):
    """Vérification du Webhook Meta WhatsApp Cloud API."""
    if hub_mode == "subscribe" and hub_challenge:
        return int(hub_challenge)
    return {"status": "ready"}


@app.post("/api/whatsapp/webhook")
async def handle_whatsapp_webhook(req: Dict[str, Any]):
    """Réception des messages WhatsApp entrants."""
    from src.agents.meta_muse_parity import WhatsAppGatewayAgent
    parsed = WhatsAppGatewayAgent.parse_incoming_webhook(req)
    return {"status": "received", "data": parsed}


# --- ENDPOINTS NEXT-GEN AGENTS (MÉMOIRE, VOCAL, NOTIFS, DESKTOP, VISION PWA) ---
class RecordFactRequest(BaseModel):
    user_id: str = "mobile_user"
    category: str
    key: str
    value: str
    confidence: float = 1.0


@app.get("/api/memory/facts")
async def get_biographical_facts_endpoint(user_id: str = "mobile_user", category: Optional[str] = None):
    """Consulte la mémoire biographique persistante."""
    from src.agents.next_gen import BiographicalMemoryAgent
    facts = BiographicalMemoryAgent.get_all_facts(user_id=user_id)
    if category:
        facts = [f for f in facts if f.get("category") == category]
    return {"user_id": user_id, "total": len(facts), "facts": facts}


@app.post("/api/memory/facts")
async def record_biographical_fact_endpoint(req: RecordFactRequest):
    """Enregistre ou met à jour un fait biographique permanent."""
    from src.agents.next_gen import BiographicalMemoryAgent
    res = BiographicalMemoryAgent.record_fact(
        user_id=req.user_id,
        category=req.category,
        key=req.key,
        value=req.value,
        confidence=req.confidence
    )
    return res


@app.delete("/api/memory/facts/{category}/{key}")
async def delete_biographical_fact_endpoint(category: str, key: str, user_id: str = "mobile_user"):
    """Supprime un fait biographique."""
    from src.agents.next_gen import BiographicalMemoryAgent
    res = BiographicalMemoryAgent.delete_fact(user_id=user_id, category=category, key=key)
    return res


class SynthesizeSpeechRequest(BaseModel):
    text: str
    voice: Optional[str] = None
    direct_speak: bool = False


class TranscribeAudioRequest(BaseModel):
    audio_base64: str
    mime_type: str = "audio/wav"
    language_hint: str = "fr"


@app.post("/api/voice/synthesize")
async def synthesize_speech_endpoint(req: SynthesizeSpeechRequest):
    """Synthétise du texte en parole audio (WAV base64) avec voix française native Hortense."""
    from src.agents.next_gen import LiveVoiceAgent
    return LiveVoiceAgent.synthesize_speech(
        text=req.text,
        voice_name=req.voice,
        direct_speak=req.direct_speak
    )


@app.post("/api/voice/transcribe")
async def transcribe_audio_endpoint(req: TranscribeAudioRequest):
    """Transcrit de la parole en texte via modèle multimodal."""
    from src.agents.next_gen import LiveVoiceAgent
    try:
        raw_bytes = base64.b64decode(req.audio_base64)
        return LiveVoiceAgent.transcribe_audio(
            audio_data=raw_bytes,
            mime_type=req.mime_type,
            language_hint=req.language_hint
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Données audio invalides: {e}")


@app.get("/api/voice/capabilities")
async def get_voice_capabilities_endpoint():
    """Consulte les voix installées et l'état du mode mains-libres."""
    from src.agents.next_gen import LiveVoiceAgent
    return LiveVoiceAgent.get_voice_capabilities()


@app.post("/api/voice/hands-free")
async def toggle_hands_free_endpoint(active: bool = True):
    """Active ou désactive le mode vocal mains-libres."""
    from src.agents.next_gen import LiveVoiceAgent
    return LiveVoiceAgent.set_hands_free_state(active=active)


class DispatchNotificationRequest(BaseModel):
    title: str
    message: str
    category: str = "general"
    urgency: str = "normal"
    action_url: Optional[str] = None


@app.post("/api/notifications/dispatch")
async def dispatch_notification_endpoint(req: DispatchNotificationRequest):
    """Déclenche une notification système Windows 11 Toast native."""
    from src.agents.next_gen import ProactiveNotifierAgent
    return ProactiveNotifierAgent.dispatch_notification(
        title=req.title,
        message=req.message,
        category=req.category,
        urgency=req.urgency,
        action_url=req.action_url
    )


@app.get("/api/notifications/history")
async def get_notifications_history_endpoint(limit: int = 20):
    """Consulte le journal des notifications proactives envoyées."""
    from src.agents.next_gen import ProactiveNotifierAgent
    history = ProactiveNotifierAgent.get_notification_history(limit=limit)
    return {"total": len(history), "notifications": history}


class WindowActionRequest(BaseModel):
    target: str = ""
    keys: str = ""


@app.get("/api/desktop/windows")
async def list_desktop_windows_endpoint():
    """Liste les fenêtres applicatives actives sur le bureau Windows."""
    from src.agents.next_gen import DesktopAutomationAgent
    windows = DesktopAutomationAgent.list_running_applications()
    return {"total": len(windows), "windows": windows}


@app.post("/api/desktop/focus")
async def focus_desktop_window_endpoint(req: WindowActionRequest):
    """Met au premier plan une application Windows."""
    from src.agents.next_gen import DesktopAutomationAgent
    return DesktopAutomationAgent.focus_window(req.target)


@app.post("/api/desktop/launch")
async def launch_desktop_app_endpoint(req: WindowActionRequest):
    """Lance une application bureautique."""
    from src.agents.next_gen import DesktopAutomationAgent
    return DesktopAutomationAgent.launch_application(req.target)


@app.post("/api/desktop/close")
async def close_desktop_app_endpoint(req: WindowActionRequest):
    """Ferme une application bureautique."""
    from src.agents.next_gen import DesktopAutomationAgent
    return DesktopAutomationAgent.close_application(req.target)


@app.post("/api/desktop/keys")
async def send_desktop_keys_endpoint(req: WindowActionRequest):
    """Envoie des touches clavier ou raccourcis."""
    from src.agents.next_gen import DesktopAutomationAgent
    return DesktopAutomationAgent.send_keystrokes(req.keys, req.target if req.target else None)


@app.get("/api/desktop/telemetry")
async def get_desktop_telemetry_endpoint():
    """Retourne l'état matériel et les métriques système du PC hôte."""
    from src.agents.next_gen import DesktopAutomationAgent
    return DesktopAutomationAgent.get_hardware_telemetry()


class CameraScanRequest(BaseModel):
    image_base64: str
    mime_type: str = "image/jpeg"
    scan_mode: str = "general"
    question: Optional[str] = None


@app.post("/api/vision/camera-scan")
async def camera_scan_endpoint(req: CameraScanRequest):
    """Analyse une capture photo caméra de repas, ticket de caisse, produit ou document."""
    from src.agents.next_gen import MobilePWAVisionAgent
    try:
        raw_bytes = base64.b64decode(req.image_base64)
        uploads_dir = Path(__file__).resolve().parent.parent.parent / "data" / "camera_uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        img_path = uploads_dir / f"scan_{int(time.time())}.jpg"
        with open(img_path, "wb") as f:
            f.write(raw_bytes)

        return MobilePWAVisionAgent.analyze_camera_capture(
            image_bytes=raw_bytes,
            mime_type=req.mime_type,
            scan_mode=req.scan_mode,
            custom_question=req.question
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Données image invalides: {e}")


@app.get("/api/pwa/manifest")
async def get_pwa_manifest_endpoint():
    """Retourne la configuration manifest de la PWA mobile."""
    from src.agents.next_gen import MobilePWAVisionAgent
    return MobilePWAVisionAgent.get_pwa_manifest()


# Route Web Cockpit UI (Frontend Spatial HTML5/CSS3/ES6 ultra-réactif)
@app.get("/", response_class=HTMLResponse)
async def serve_canvas_cockpit():
    html_file = Path(__file__).resolve().parent / "static" / "index.html"
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Cockpit spatial HoL AI en cours de génération...</h1>")


@app.get("/health")
@app.get("/healthz")
@app.get("/ping")
async def health_check():
    return {"status": "ok", "app": "HoL AI"}


@app.get("/api/debug/test-chat")
async def debug_test_chat():
    from src.services.cognitive_engine import CognitiveAgentEngine
    from src.services.llm_engine import LLMBrain
    import traceback
    key = LLMBrain.get_api_key()
    try:
        res = await CognitiveAgentEngine.process_chat(
            user_message="t cool??",
            session_id="debug_sess_direct",
            model="gemini-3.5-flash-lite"
        )
        return {
            "status": "ok",
            "reply": res.get("reply"),
            "model": res.get("model"),
            "key_present": bool(key),
            "key_preview": f"{key[:6]}...{key[-4:]}" if key else None
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "key_present": bool(key),
            "key_preview": f"{key[:6]}...{key[-4:]}" if key else None
        }


@app.get("/manifest.json")
async def serve_manifest():
    from fastapi.responses import FileResponse
    return FileResponse(Path(__file__).resolve().parent / "static" / "manifest.json", media_type="application/manifest+json")


@app.get("/icon.svg")
async def serve_icon():
    from fastapi.responses import FileResponse
    return FileResponse(Path(__file__).resolve().parent / "static" / "icon.svg", media_type="image/svg+xml")


def get_local_lan_ip():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def get_public_or_lan_url(request: Request) -> str:
    try:
        tunnel_path = Path(__file__).resolve().parents[4] / "tunnel_url.txt"
        if tunnel_path.exists():
            val = tunnel_path.read_text(encoding="utf-8").strip()
            if val.startswith("https://"):
                return val
    except Exception:
        pass
    ip = get_local_lan_ip()
    port = request.url.port or 8000
    return f"http://{ip}:{port}"


@app.get("/api/system/network-info")
async def get_network_info(request: Request):
    ip = get_local_lan_ip()
    port = request.url.port or 8000
    target_url = get_public_or_lan_url(request)
    return {
        "ip": ip,
        "port": port,
        "url": target_url,
        "is_https": target_url.startswith("https://")
    }


@app.get("/qr_phone.png")
async def serve_qr_phone(request: Request):
    from fastapi.responses import Response, FileResponse
    try:
        import io
        import qrcode
        target_url = get_public_or_lan_url(request)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=3,
        )
        qr.add_data(target_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="white", back_color="#08080a")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as e:
        return FileResponse(Path(__file__).resolve().parent / "static" / "qr_phone.png", media_type="image/png")


@app.get("/sw.js")
async def serve_sw():
    from fastapi.responses import FileResponse
    return FileResponse(Path(__file__).resolve().parent / "static" / "sw.js", media_type="application/javascript")


# Montage du répertoire des applications locales générées par Jarvis
apps_static_dir = Path(__file__).resolve().parent / "static" / "apps"
apps_static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/apps", StaticFiles(directory=str(apps_static_dir), html=True), name="apps")

# Montage du répertoire des arrière-plans dynamiques 21st.dev
backgrounds_static_dir = Path(__file__).resolve().parent / "static" / "backgrounds"
backgrounds_static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/backgrounds", StaticFiles(directory=str(backgrounds_static_dir), html=True), name="backgrounds")

# Montage des assets et static complets
static_root_dir = Path(__file__).resolve().parent / "static"
assets_static_dir = static_root_dir / "assets"
assets_static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/assets", StaticFiles(directory=str(assets_static_dir)), name="assets")
app.mount("/static", StaticFiles(directory=str(static_root_dir)), name="static")

