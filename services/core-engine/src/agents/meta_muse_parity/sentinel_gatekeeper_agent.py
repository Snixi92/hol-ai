"""
SentinelGatekeeperAgent : Démon de sécurité hors-bande et gardien de politiques pour HoL AI.
Inspiré du système Sentinel de Meta Muse :
- Analyse du trafic sortant et des commandes d'outils en dehors du flux principal du LLM.
- Détection des tentatives d'injections de prompt indirectes (ex: via emails ou pages web compromises).
- Interception des opérations critiques (dépenses d'argent, suppression de fichiers, envois d'emails).
- Décision autonome : APPROVED (autorisé), BLOCKED (bloqué) ou REQUIRES_HUMAN_CONFIRMATION.
"""
import re
import time
from typing import Dict, Any, List, Optional


class SentinelGatekeeperAgent:
    """Agent gardien de politiques et pare-feu hors-bande protégeant l'utilisateur et le système."""

    INJECTION_PATTERNS = [
        r"(?i)ignore\s+(?:all\s+)?previous\s+instructions",
        r"(?i)forget\s+(?:all\s+)?prior\s+rules",
        r"(?i)you\s+are\s+now\s+in\s+dan\s+mode",
        r"(?i)system\s*override",
        r"(?i)exfiltrat(?:e|ion)",
        r"(?i)send\s+(?:the\s+)?(?:password|key|token|cookie|creds?)\s+to",
        r"(?i)curl\s+https?:\/\/.*?\?data=",
    ]

    DESTRUCTIVE_COMMAND_PATTERNS = [
        r"(?i)rm\s+-[rRf]{1,3}\s+[/~]",
        r"(?i)format\s+[c-z]:",
        r"(?i)del\s+\/[fF]\s+\/[sS]\s+\/[qQ]\s+[cC]:\\",
        r"(?i)drop\s+database",
        r"(?i)chmod\s+-R\s+777\s+\/",
        r"(?i)(?:cat|type|head|tail|more|less)\s+(?:\/etc\/(?:passwd|shadow|sudoers)|c:\\windows\\system32\\config)",
    ]

    @classmethod
    def audit_action(
        cls,
        action_type: str,
        target_resource: str,
        payload_preview: str = "",
        estimated_cost_eur: float = 0.0
    ) -> Dict[str, Any]:
        """
        Évalue une action avant exécution et émet le verdict de Sentinel.
        """
        t0 = time.time()
        combined_text = f"{action_type} {target_resource} {payload_preview}"

        for pat in cls.INJECTION_PATTERNS:
            if re.search(pat, combined_text):
                return {
                    "verdict": "BLOCKED",
                    "threat_level": "CRITICAL",
                    "reason": "Tentative d'injection de prompt indirecte détectée dans le payload.",
                    "action_type": action_type,
                    "target_resource": target_resource,
                    "requires_user_approval": False,
                    "duration_ms": round((time.time() - t0) * 1000, 1),
                    "verbal_reply": "🛡️ SENTINEL : Action bloquée ! Détection d'une menace d'injection ou d'évasion de prompt."
                }

        for pat in cls.DESTRUCTIVE_COMMAND_PATTERNS:
            if re.search(pat, combined_text):
                return {
                    "verdict": "BLOCKED",
                    "threat_level": "CRITICAL",
                    "reason": "Commande système destructrice interdite par la politique de sécurité.",
                    "action_type": action_type,
                    "target_resource": target_resource,
                    "requires_user_approval": False,
                    "duration_ms": round((time.time() - t0) * 1000, 1),
                    "verbal_reply": "🛡️ SENTINEL : Action bloquée ! Commande destructrice interdite."
                }

        if estimated_cost_eur > 0 or action_type in ["financial_payment", "send_email", "delete_file"]:
            return {
                "verdict": "REQUIRES_HUMAN_CONFIRMATION",
                "threat_level": "MODERATE",
                "reason": (
                    f"Opération financière ({estimated_cost_eur:.2f} €) ou impactante nécessitant "
                    "l'approbation explicite de l'utilisateur."
                ),
                "action_type": action_type,
                "target_resource": target_resource,
                "requires_user_approval": True,
                "duration_ms": round((time.time() - t0) * 1000, 1),
                "verbal_reply": f"🛡️ SENTINEL : Approbation humaine requise pour l'opération '{action_type}'."
            }

        return {
            "verdict": "APPROVED",
            "threat_level": "SAFE",
            "reason": "Action conforme aux politiques de sécurité Sentinel.",
            "action_type": action_type,
            "target_resource": target_resource,
            "requires_user_approval": False,
            "duration_ms": round((time.time() - t0) * 1000, 1),
            "verbal_reply": f"🛡️ SENTINEL : Action '{action_type}' vérifiée et autorisée."
        }
