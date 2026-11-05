# -*- coding: utf-8 -*-
"""
Agent Runtime Harness pour HoL AI (Production-Grade Agent Execution Scaffolding).

Fournit :
1. Sandboxing & Sentinel Gatekeeper (sécurité, validation d'arguments, path traversal).
2. Circuit Breaker & Anti-Runaway Loop Protection (plafonnement d'itérations, détection de répétitions).
3. Fault Tolerance & Exception Shielding (isolation des erreurs d'outils, auto-guérison).
4. Télémétrie en temps réel & Intégration Tool-Calls-Section (21st.dev heygaia).
"""

import time
import functools
import inspect
import logging
import json
from typing import Dict, Any, List, Optional, Callable, Set

logger = logging.getLogger("hol_ai.agent_harness")


TOOL_METADATA_MAP: Dict[str, Dict[str, str]] = {
    "triage_and_clean_inbox": {
        "app_name": "Gmail",
        "title": "Triage et nettoyage de la boîte de réception",
        "icon": "gmail"
    },
    "manage_calendar_and_conflicts": {
        "app_name": "Google Calendar",
        "title": "Gestion de l'agenda et des réunions",
        "icon": "calendar"
    },
    "hunt_product_deals": {
        "app_name": "Product Hunter",
        "title": "Comparateur de prix multi-boutiques",
        "icon": "shopping"
    },
    "scrape_live_store_offer": {
        "app_name": "Stealth Scraper",
        "title": "Extraction en direct d'offre e-commerce",
        "icon": "shopping"
    },
    "search_internet_live": {
        "app_name": "Web Search",
        "title": "Recherche web en temps réel",
        "icon": "search"
    },
    "search_web_research": {
        "app_name": "Web Research",
        "title": "Audit web approfondi multi-sources",
        "icon": "search"
    },
    "read_webpage_content": {
        "app_name": "Web Reader",
        "title": "Extraction et lecture de page web",
        "icon": "file-text"
    },
    "execute_python_code": {
        "app_name": "Python Sandbox",
        "title": "Exécution sécurisée de script Python",
        "icon": "terminal"
    },
    "execute_terminal_command": {
        "app_name": "Windows Terminal",
        "title": "Commande console système",
        "icon": "terminal"
    },
    "launch_application": {
        "app_name": "Windows OS",
        "title": "Lancement d'application de bureau",
        "icon": "monitor"
    },
    "close_application": {
        "app_name": "Windows OS",
        "title": "Fermeture d'application de bureau",
        "icon": "monitor"
    },
    "control_desktop_window": {
        "app_name": "Desktop Window Manager",
        "title": "Contrôle actif des fenêtres et touches",
        "icon": "monitor"
    },
    "track_parcel": {
        "app_name": "Logistics Tracker",
        "title": "Suivi de colis multi-transporteurs",
        "icon": "truck"
    },
    "calculate_margin_and_vat": {
        "app_name": "Finance CFO",
        "title": "Calcul de marge nette, TVA et commission",
        "icon": "dollar-sign"
    },
    "create_local_web_app": {
        "app_name": "Code Studio",
        "title": "Génération et déploiement d'app web locale",
        "icon": "code"
    },
    "generate_data_chart": {
        "app_name": "Data Visualizer",
        "title": "Création de graphique analytique interactif",
        "icon": "chart"
    },
    "create_social_post": {
        "app_name": "Social Manager",
        "title": "Rédaction et planification de post social",
        "icon": "share-2"
    },
    "publish_social_post": {
        "app_name": "Social Manager",
        "title": "Publication en direct sur réseau social",
        "icon": "share-2"
    },
    "fetch_public_api_data": {
        "app_name": "API Gateway",
        "title": "Interrogation d'API publique certifiée",
        "icon": "globe"
    },
    "delegate_to_subagent": {
        "app_name": "Multi-Agent System",
        "title": "Délégation de mission à un sous-agent",
        "icon": "bot"
    },
    "create_visual_artifact": {
        "app_name": "Artifacts Studio",
        "title": "Création d'artefact Markdown / Mermaid",
        "icon": "layers"
    },
    "diagnose_system_error": {
        "app_name": "System Debugger",
        "title": "Diagnostic et correction d'erreur",
        "icon": "alert-circle"
    },
    "create_architectural_plan": {
        "app_name": "System Architect",
        "title": "Élaboration de plan d'architecture",
        "icon": "compass"
    },
    "audit_subscriptions": {
        "app_name": "Finance Auditor",
        "title": "Scan et audit des abonnements récurrents",
        "icon": "credit-card"
    },
    "scan_meal_nutrition": {
        "app_name": "Nutrition Vision",
        "title": "Analyse nutritionnelle et calorique de repas",
        "icon": "utensils"
    },
    "record_biographical_fact": {
        "app_name": "Biographical Memory",
        "title": "Enregistrement de fait en mémoire persistante",
        "icon": "database"
    },
    "get_biographical_memory": {
        "app_name": "Biographical Memory",
        "title": "Consultation de la mémoire biographique",
        "icon": "database"
    },
    "synthesize_speech_voice": {
        "app_name": "Live Voice",
        "title": "Synthèse et diffusion vocale réaliste",
        "icon": "mic"
    },
    "send_desktop_notification": {
        "app_name": "Windows Notifier",
        "title": "Envoi de notification Toast Windows",
        "icon": "bell"
    },
    "launch_visual_computer_use": {
        "app_name": "Virtual Browser",
        "title": "Démarrage de navigateur virtuel Chromium",
        "icon": "external-link"
    },
    "run_visual_browser_task": {
        "app_name": "Virtual Browser",
        "title": "Exécution d'action sur navigateur distant",
        "icon": "mouse-pointer"
    }
}


class AgentRuntimeHarness:
    """
    Harnais d'exécution en temps réel pour l'agent cognitif de HoL AI.
    Supervise chaque cycle d'interaction, protège le système, compte les sauts et formate la télémétrie.
    """

    def __init__(
        self,
        session_id: str,
        max_tool_calls: int = 10,
        max_repeated_calls: int = 3,
        status_emitter: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        self.session_id = session_id
        self.max_tool_calls = max_tool_calls
        self.max_repeated_calls = max_repeated_calls
        self.status_emitter = status_emitter

        # Métriques et état d'exécution
        self.tool_call_count = 0
        self.recorded_tool_calls: List[Dict[str, Any]] = []
        self.call_signatures_history: List[str] = []
        self.blocked_calls: List[Dict[str, Any]] = []
        self.shielded_errors: List[Dict[str, Any]] = []
        self.start_time = time.perf_counter()

    def _emit(self, text: str, step: str = "status", extra: Optional[Dict[str, Any]] = None):
        """Transmet un événement d'exécution en temps réel."""
        if self.status_emitter:
            payload = {"text": text, "step": step}
            if extra:
                payload.update(extra)
            try:
                self.status_emitter(payload)
            except Exception as e:
                logger.debug(f"Harness status emit error: {e}")

    def _check_security_guardrails(self, func_name: str, kwargs: Dict[str, Any]) -> Optional[str]:
        """
        Vérifie les règles Sentinel Gatekeeper avant l'exécution d'un outil sensible.
        Renvoie un message de blocage si une menace est détectée, None si l'action est saine.
        """
        # 1. Vérification Path Traversal sur tous les arguments de type chemin
        for k, val in kwargs.items():
            if isinstance(val, str):
                if "../.." in val or "..\\.." in val:
                    return f"Action bloquée par Sentinel : tentative de Path Traversal détectée dans le paramètre '{k}'."
                if any(p in val.lower() for p in ["/etc/shadow", "/etc/passwd", "system32\\config", "system32\\sam"]):
                    return f"Action bloquée par Sentinel : accès refusé aux ressources système critiques dans '{k}'."

        # 2. Commandes Shell à risque
        if func_name == "execute_terminal_command":
            cmd = str(kwargs.get("command", "")).lower()
            dangerous_patterns = [
                "rmdir /s /q c:\\", "format c:", "del /f /s /q c:\\",
                ":(){ :|:& };:", "drop database", "shutdown /r /t 0"
            ]
            for pat in dangerous_patterns:
                if pat in cmd:
                    return f"Action bloquée par Sentinel : commande potentiellement destructrice '{cmd}' neutralisée."

        # 3. Écriture / Édition de code protégée
        if func_name in ["write_code_file", "edit_code_file"]:
            file_path = str(kwargs.get("file_path", "")).lower()
            if any(file_path.endswith(ext) for ext in [".exe", ".dll", ".sys", ".bat", ".vbs"]):
                return f"Action bloquée par Sentinel : interdiction d'écrire des exécutables binaires ou scripts système bruts."

        return None

    def wrap_tool(self, original_func: Callable) -> Callable:
        """
        Enveloppe chirurgicalement une fonction d'outil dans le harnais d'exécution.
        Conserve impérativement le nom, la signature et la docstring pour l'inspection Google GenAI.
        """
        func_name = original_func.__name__
        meta = TOOL_METADATA_MAP.get(func_name, {
            "app_name": "HoL Tool",
            "title": func_name.replace("_", " ").title(),
            "icon": "code"
        })

        @functools.wraps(original_func)
        def sandboxed_tool_wrapper(*args, **kwargs):
            # 1. Protection Anti-Runaway (Circuit Breaker)
            self.tool_call_count += 1
            call_sig = f"{func_name}:{json.dumps(kwargs, sort_keys=True, default=str)}"
            self.call_signatures_history.append(call_sig)

            # Vérification du plafond total
            if self.tool_call_count > self.max_tool_calls:
                err_msg = f"Circuit Breaker activé : plafond de {self.max_tool_calls} outils atteint pour ce tour. Synthétise ta réponse maintenant."
                logger.warning(f"🛡️ [Harness] {err_msg}")
                return err_msg

            # Détection de boucle répétitive (même outil + mêmes arguments 3 fois consécutives)
            if len(self.call_signatures_history) >= self.max_repeated_calls:
                last_n = self.call_signatures_history[-self.max_repeated_calls:]
                if len(set(last_n)) == 1:
                    err_msg = f"Circuit Breaker : boucle répétitive détectée sur '{func_name}'. Synthétise directement tes observations."
                    logger.warning(f"🛡️ [Harness] {err_msg}")
                    return err_msg

            # 2. Vérification Sentinel Gatekeeper
            block_reason = self._check_security_guardrails(func_name, kwargs)
            if block_reason:
                self.blocked_calls.append({
                    "tool": func_name,
                    "reason": block_reason,
                    "timestamp": time.time()
                })
                logger.warning(f"🛡️ [Harness Sentinel Blocked] {func_name}: {block_reason}")
                return block_reason

            # 3. Notification en temps réel au client / UI
            self._emit(
                text=f"⚡ Exécution de {meta['title']}...",
                step="tool_calling",
                extra={"tool": func_name, "app": meta["app_name"]}
            )

            # 4. Exécution chronométrée avec bouclier d'exception (Fault Tolerance)
            t_start = time.perf_counter()
            tool_status = "completed"
            raw_output = ""
            error_details = None

            try:
                raw_output = original_func(*args, **kwargs)
            except Exception as ex:
                tool_status = "failed"
                error_details = str(ex)
                raw_output = f"Échec de l'outil '{func_name}' : {error_details}. Adapte ta réponse ou tente une alternative."
                self.shielded_errors.append({
                    "tool": func_name,
                    "error": error_details,
                    "kwargs": kwargs
                })
                logger.error(f"🛡️ [Harness Shielded Exception] {func_name}: {ex}", exc_info=True)

            latency_ms = round((time.perf_counter() - t_start) * 1000, 1)

            # Formatage résumé de la sortie pour le tiroir d'outils UI
            output_summary = str(raw_output)
            if len(output_summary) > 280:
                output_summary = output_summary[:280] + "..."

            # 5. Enregistrement dans le journal de télémétrie
            tool_record = {
                "id": f"tc-{self.tool_call_count}-{int(time.time()*1000)%100000}",
                "tool": func_name,
                "name": func_name,
                "title": meta["title"],
                "app_name": meta["app_name"],
                "icon": meta["icon"],
                "status": tool_status,
                "latency_ms": latency_ms,
                "parameters": kwargs,
                "output": output_summary,
                "timestamp": time.time()
            }
            if error_details:
                tool_record["error"] = error_details

            self.recorded_tool_calls.append(tool_record)

            logger.info(
                f"🛡️ [Harness Tool Call] {func_name} ({meta['app_name']}) "
                f"en {latency_ms}ms -> {tool_status.upper()}"
            )

            return raw_output

        return sandboxed_tool_wrapper

    def build_tool_calls_card(self) -> Optional[Dict[str, Any]]:
        """
        Génère la carte interactive conforme pour le composant UI heygaia/tool-calls-section.
        Renvoie None si aucun outil n'a été appelé pendant ce tour.
        """
        if not self.recorded_tool_calls:
            return None

        total_latency = sum(tc.get("latency_ms", 0) for tc in self.recorded_tool_calls)

        return {
            "type": "tool_calls_section",
            "data": {
                "tool_calls": self.recorded_tool_calls,
                "total_tools": len(self.recorded_tool_calls),
                "total_latency_ms": round(total_latency, 1),
                "default_expanded": True,
                "engine_harness": "HoL-AI-Runtime-Harness-v1"
            }
        }

    def get_audit_summary(self) -> Dict[str, Any]:
        """Retourne les métriques d'audit pour le monitoring et les logs système."""
        elapsed_ms = round((time.perf_counter() - self.start_time) * 1000, 1)
        return {
            "session_id": self.session_id,
            "total_calls": self.tool_call_count,
            "completed": sum(1 for tc in self.recorded_tool_calls if tc["status"] == "completed"),
            "failed": sum(1 for tc in self.recorded_tool_calls if tc["status"] == "failed"),
            "blocked_by_security": len(self.blocked_calls),
            "shielded_errors": len(self.shielded_errors),
            "harness_elapsed_ms": elapsed_ms,
            "tool_records": self.recorded_tool_calls
        }
