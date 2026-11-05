"""
Gestionnaire de Sessions & Mémoire Conversationnelle Multi-Tours (Muse-X OS).
Maintient l'état conversationnel, l'historique des échanges, et résout automatiquement
les anaphores et requêtes elliptiques (ex: 'et sur cdiscount??', 'combien ça coûte ?', 'ferme le', 'ouvre mes fichiers').
"""
import time
import re
from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    role: str  # 'user' | 'assistant'
    content: str
    timestamp: float = Field(default_factory=time.time)
    cards: Optional[List[Dict[str, Any]]] = None


class ConversationSession:
    def __init__(self, session_id: str, user_id: str = "mobile_user"):
        self.session_id: str = session_id
        self.user_id: str = user_id
        self.history: List[ChatTurn] = []
        self.last_product: Optional[str] = None
        self.last_platform: Optional[str] = None
        self.last_app: Optional[str] = None
        self.last_app_action: Optional[str] = None
        self.last_cards: List[Dict[str, Any]] = []
        self.last_action_id: Optional[str] = None
        self.created_at: float = time.time()
        self.updated_at: float = time.time()

    def add_user_message(self, message: str) -> None:
        self.history.append(ChatTurn(role="user", content=message))
        self.updated_at = time.time()
        # Détection d'une éventuelle application mentionnée
        app = SessionManager.extract_app_mention(message)
        if app:
            self.last_app = app
        # Conserver au maximum les 30 derniers tours
        if len(self.history) > 30:
            self.history.pop(0)

    def add_assistant_message(self, reply: str, cards: Optional[List[Dict[str, Any]]] = None) -> None:
        self.history.append(ChatTurn(role="assistant", content=reply, cards=cards))
        self.updated_at = time.time()
        if cards:
            self.last_cards = cards
            for c in cards:
                # Détection et mémorisation du produit actif
                if c.get("type") == "deal" and isinstance(c.get("data"), dict):
                    prod = c["data"].get("product")
                    if prod and len(str(prod).strip()) > 2 and str(prod).lower() not in ["et ??", "et", "article multi-sourcing"]:
                        prod_str = str(prod).strip()
                        if " sur " in prod_str:
                            prod_str = prod_str.split(" sur ")[0].strip()
                        if "Trouve " in prod_str:
                            prod_str = prod_str.replace("Trouve ", "").strip()
                        if len(prod_str) > 50:
                            # Extraction concise des premiers mots clés
                            words = prod_str.split()
                            prod_str = " ".join(words[:5])
                        self.last_product = prod_str
                    plat = c["data"].get("platform")
                    if plat:
                        self.last_platform = str(plat).strip()
                # Détection et mémorisation de l'application active
                elif c.get("type") == "app_launcher" and isinstance(c.get("data"), dict):
                    app_name = c["data"].get("app") or c["data"].get("display_name")
                    if app_name and str(app_name).strip():
                        self.last_app = str(app_name).strip()
                        self.last_app_action = c["data"].get("action")

        if len(self.history) > 30:
            self.history.pop(0)

    def get_formatted_history(self, max_turns: int = 10) -> List[Dict[str, str]]:
        """Retourne l'historique au format standard [{'role': 'user'|'assistant', 'content': '...'}]"""
        recent = self.history[-max_turns:]
        return [{"role": t.role, "content": t.content} for t in recent]


class SessionManager:
    """Gestionnaire singleton des sessions multi-tours en mémoire."""
    _sessions: Dict[str, ConversationSession] = {}

    KNOWN_APP_KEYWORDS: Dict[str, str] = {
        # Fichiers & Explorateur
        "explorateur de fichiers": "l'explorateur de fichiers",
        "explorateur": "l'explorateur de fichiers",
        "mes fichiers": "l'explorateur de fichiers",
        "mon fichier": "l'explorateur de fichiers",
        "les fichiers": "l'explorateur de fichiers",
        "fichiers": "l'explorateur de fichiers",
        "fichier": "l'explorateur de fichiers",
        "mes dossiers": "l'explorateur de fichiers",
        "mon dossier": "l'explorateur de fichiers",
        "dossiers": "l'explorateur de fichiers",
        "dossier": "l'explorateur de fichiers",
        "mes documents": "l'explorateur de fichiers",
        "documents": "l'explorateur de fichiers",
        "telechargements": "l'explorateur de fichiers",
        "mes telechargements": "l'explorateur de fichiers",
        # Calculatrice
        "calculatrice": "la calculatrice",
        "calculette": "la calculatrice",
        "calcul": "la calculatrice",
        # Bloc-notes
        "bloc-notes": "le bloc-notes",
        "bloc notes": "le bloc-notes",
        "notepad": "le bloc-notes",
        "mes notes": "le bloc-notes",
        "notes": "le bloc-notes",
        # Steam & Jeux
        "steam": "Steam",
        "fortnite": "Fortnite",
        "gta 5": "Grand Theft Auto V",
        "gta v": "Grand Theft Auto V",
        "gta": "Grand Theft Auto V",
        "roblox": "Roblox",
        "red dead redemption": "Red Dead Redemption 2",
        "red dead": "Red Dead Redemption 2",
        "rdr2": "Red Dead Redemption 2",
        # Discord & Messageries
        "discord": "Discord",
        "whatsapp": "WhatsApp",
        "telegram": "Telegram",
        # Spotify & Musique
        "spotify": "Spotify",
        "ma musique": "Spotify",
        "musique": "Spotify",
        # Navigateurs
        "google chrome": "Google Chrome",
        "chrome": "Google Chrome",
        "mon navigateur": "Google Chrome",
        "navigateur": "Google Chrome",
        "firefox": "Firefox",
        "edge": "Microsoft Edge",
        # Système & Paramètres
        "gestionnaire des taches": "le gestionnaire des tâches",
        "gestionnaire de taches": "le gestionnaire des tâches",
        "taskmgr": "le gestionnaire des tâches",
        "mes parametres": "les paramètres",
        "parametres": "les paramètres",
        "paramètres": "les paramètres",
        "mes reglages": "les paramètres",
        "reglages": "les paramètres",
        "réglages": "les paramètres",
        "paint": "Paint",
        "photos": "Photos",
        "camera": "la caméra",
        # Constructeurs & Outils
        "lenovo vantage": "Lenovo Vantage",
        "vantage": "Lenovo Vantage",
        "lenovo": "Lenovo Vantage",
        "openiv": "OpenIV",
        "lm studio": "LM Studio",
        "nuvio": "Nuvio",
        "terminal": "le terminal",
        "powershell": "PowerShell",
        "cmd": "l'invite de commande",
        # Bureautique & Dev
        "visual studio code": "Visual Studio Code",
        "vs code": "Visual Studio Code",
        "vscode": "Visual Studio Code",
        "word": "Word",
        "excel": "Excel",
        "powerpoint": "PowerPoint",
        "antigravity": "Antigravity"
    }

    @classmethod
    def get_or_create(cls, session_id: Optional[str] = None, user_id: str = "mobile_user") -> ConversationSession:
        sid = session_id or f"sess_{user_id}"
        if sid not in cls._sessions:
            cls._sessions[sid] = ConversationSession(session_id=sid, user_id=user_id)
        session = cls._sessions[sid]
        session.user_id = user_id
        return session

    @classmethod
    def extract_app_mention(cls, text: str) -> Optional[str]:
        """Extrait le nom d'une application mentionnée dans un message utilisateur."""
        if not text:
            return None
        text_lower = text.lower().strip()

        # Si c'est juste un pronom d'anaphore pur ("ferme le", "ouvre la", "seddo"), ignorer
        anaphora_close = [
            r"^(?:s'il te pla[îi]t\s+)?(?:peux-tu\s+)?(?:ferme|fermer|quitte|quitter|arr[êe]te|arr[êe]ter|stop|kill|éteins|eteins)\s*[- ]?(?:le|la|les|l'|ça|ca|cette\s+appli(?:cation)?|l'appli(?:cation)?)\b(?:\s+s'il te pla[îi]t|\s+stp|\s+merci|[.!]|\s+tout de suite)*$",
            r"^(?:s'il te pla[îi]t\s+)?(?:peux-tu|tu\s+peux)?\s*(?:le|la|les|l')\s*(?:fermer|quitter|arr[êe]ter|stop|kill)\b(?:\s+s'il te pla[îi]t|\s+stp|\s+merci|[.!]|\s+tout de suite)*$",
            r"^(?:ferme|fermer|quitte|quitter|arr[êe]te|arr[êe]ter|stop|kill)\s*$",
            r"^(?:sedd?o|sedd?u|sedd?ha|sedha|cheddo|sed\s+h[ae]da|sedd?\s+had\s+l'?appli|sedd?\s+hadchi)\b",
        ]
        anaphora_open = [
            r"^(?:s'il te pla[îi]t\s+)?(?:peux-tu\s+)?(?:ouvre|ouvrir|lance|lancer|relance|relancer|red[ée]marre|red[ée]marrer|start)\s*[- ]?(?:le|la|les|l'|ça|ca|cette\s+appli(?:cation)?|l'appli(?:cation)?)\b(?:\s+s'il te pla[îi]t|\s+stp|\s+merci|[.!]|\s+tout de suite)*$",
            r"^(?:s'il te pla[îi]t\s+)?(?:peux-tu|tu\s+peux)?\s*(?:le|la|les|l')\s*(?:ouvrir|lancer|relancer|red[ée]marrer|start)\b(?:\s+s'il te pla[îi]t|\s+stp|\s+merci|[.!]|\s+tout de suite)*$",
            r"^(?:ouvre|ouvrir|lance|lancer|relance|relancer)\s*$",
            r"^(?:7ell?o|hell?o|7ell?ha|hell?ha|ftaho|ftahha|7ell?\s+had\s+l'?appli|hell?\s+had\s+l'?appli)\b",
        ]
        if any(re.search(p, text_lower) for p in anaphora_close + anaphora_open):
            return None

        # 1. Vérification d'une commande explicite type "ouvre X" ou "ferme X"
        m_cmd = re.search(
            r"\b(?:ouvre|ouvrir|lance|lancer|ferme|fermer|quitte|quitter|arr[êe]te|arr[êe]ter|kill|stop)\s+(?:(?:le|la|les|l'|mon|ma|mes)\s+)?([a-zA-Z0-9_\- ]+?)(?:\s+s'il te pla[îi]t|\s+stp|\s+merci|[.!]|\s+tout de suite)*$",
            text_lower
        )
        if m_cmd:
            candidate = m_cmd.group(1).strip()
            # Chercher dans notre dictionnaire connu
            for k, app_name in sorted(cls.KNOWN_APP_KEYWORDS.items(), key=lambda x: len(x[0]), reverse=True):
                if k == candidate or k in candidate:
                    return app_name
            if candidate and len(candidate) > 2 and candidate not in ["le", "la", "les", "ça", "ca", "appli", "application"]:
                return candidate.title()

        # 2. Vérification dans une phrase de conversation générale (ex: "tu penses quoi de steam ?", "j'adore discord")
        for k, app_name in sorted(cls.KNOWN_APP_KEYWORDS.items(), key=lambda x: len(x[0]), reverse=True):
            pattern = rf"\b{re.escape(k)}\b"
            if re.search(pattern, text_lower):
                return app_name

        return None

    @classmethod
    def resolve_anaphora_and_context(cls, session: ConversationSession, raw_message: str) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Analyse une requête utilisateur et résout les ellipses / anaphores :
        - Détecte si le message est une question de suivi sur un produit ('et sur cdiscount??').
        - Détecte si le message est une commande anaphorique sur une application ('ferme le', 'relance le', 'seddo').
        - Détecte les synonymes naturels (ex: 'ouvre mes fichiers' -> Explorateur de fichiers).
        
        Retourne : (effective_message, resolved_product, detected_platform)
        """
        msg_clean = (raw_message or "").strip()
        msg_lower = msg_clean.lower()

        # 1. Détection de plateforme e-commerce
        detected_platform: Optional[str] = None
        if "cdiscount" in msg_lower:
            detected_platform = "Cdiscount"
        elif "aliexpress" in msg_lower:
            detected_platform = "AliExpress"
        elif "amazon" in msg_lower:
            detected_platform = "Amazon.fr"
        elif "leboncoin" in msg_lower or "lbc" in msg_lower:
            detected_platform = "Leboncoin"
        elif "vinted" in msg_lower:
            detected_platform = "Vinted"
        elif "alibaba" in msg_lower:
            detected_platform = "Alibaba"
        elif "dhgate" in msg_lower:
            detected_platform = "DHgate"
        elif "hacoo" in msg_lower:
            detected_platform = "Hacoo"
        elif "fnac" in msg_lower:
            detected_platform = "Fnac"
        elif "boulanger" in msg_lower:
            detected_platform = "Boulanger"
        elif "ldlc" in msg_lower:
            detected_platform = "LDLC"

        # 2. Gestion prioritaire : Explorateur de fichiers & Fichiers
        files_open_re = re.compile(
            r"^(?:s'il te pla[îi]t\s+)?(?:peux-tu\s+)?(?:ouvre|ouvrir|lance|lancer)\s+(?:(?:mes|les|mon|l'|l\s*')\s*)?(?:fichiers?|dossiers?|documents?|explorateur(?:\s+de\s+fichiers?)?)\b",
            re.IGNORECASE
        )
        files_close_re = re.compile(
            r"^(?:s'il te pla[îi]t\s+)?(?:peux-tu\s+)?(?:ferme|fermer|quitte|quitter|arr[êe]te|arr[êe]ter)\s+(?:(?:mes|les|mon|l'|l\s*')\s*)?(?:fichiers?|dossiers?|documents?|explorateur(?:\s+de\s+fichiers?)?)\b",
            re.IGNORECASE
        )
        if files_open_re.search(msg_clean):
            session.last_app = "l'explorateur de fichiers"
            session.last_app_action = "launch"
            return "Ouvre l'explorateur de fichiers", session.last_product, detected_platform

        if files_close_re.search(msg_clean):
            session.last_app = "l'explorateur de fichiers"
            session.last_app_action = "close"
            return "Ferme l'explorateur de fichiers", session.last_product, detected_platform

        # 3. Résolution d'anaphores / pronoms de FERMETURE d'application
        close_pronoun_patterns = [
            r"^(?:s'il te pla[îi]t\s+)?(?:peux-tu\s+)?(?:ferme|fermer|quitte|quitter|arr[êe]te|arr[êe]ter|stop|kill|éteins|eteins)\s*[- ]?(?:le|la|les|l'|ça|ca|cette\s+appli(?:cation)?|l'appli(?:cation)?)\b(?:\s+s'il te pla[îi]t|\s+stp|\s+merci|[.!]|\s+tout de suite)*$",
            r"^(?:s'il te pla[îi]t\s+)?(?:peux-tu|tu\s+peux)?\s*(?:le|la|les|l')\s*(?:fermer|quitter|arr[êe]ter|stop|kill)\b(?:\s+s'il te pla[îi]t|\s+stp|\s+merci|[.!]|\s+tout de suite)*$",
            r"^(?:ferme|fermer|quitte|quitter|arr[êe]te|arr[êe]ter|stop|kill)\s*$",
            r"^(?:sedd?o|sedd?u|sedd?ha|sedha|cheddo|sed\s+h[ae]da|sedd?\s+had\s+l'?appli|sedd?\s+hadchi)\b",
        ]
        if any(re.search(p, msg_clean, re.IGNORECASE) for p in close_pronoun_patterns):
            if session.last_app:
                session.last_app_action = "close"
                effective_msg = f"Ferme {session.last_app}"
                return effective_msg, session.last_product, detected_platform

        # 4. Résolution d'anaphores / pronoms d'OUVERTURE d'application
        open_pronoun_patterns = [
            r"^(?:s'il te pla[îi]t\s+)?(?:peux-tu\s+)?(?:ouvre|ouvrir|lance|lancer|relance|relancer|red[ée]marre|red[ée]marrer|start)\s*[- ]?(?:le|la|les|l'|ça|ca|cette\s+appli(?:cation)?|l'appli(?:cation)?)\b(?:\s+s'il te pla[îi]t|\s+stp|\s+merci|[.!]|\s+tout de suite)*$",
            r"^(?:s'il te pla[îi]t\s+)?(?:peux-tu|tu\s+peux)?\s*(?:le|la|les|l')\s*(?:ouvrir|lancer|relancer|red[ée]marrer|start)\b(?:\s+s'il te pla[îi]t|\s+stp|\s+merci|[.!]|\s+tout de suite)*$",
            r"^(?:ouvre|ouvrir|lance|lancer|relance|relancer)\s*$",
            r"^(?:7ell?o|hell?o|7ell?ha|hell?ha|ftaho|ftahha|7ell?\s+had\s+l'?appli|hell?\s+had\s+l'?appli)\b",
        ]
        if any(re.search(p, msg_clean, re.IGNORECASE) for p in open_pronoun_patterns):
            if session.last_app:
                session.last_app_action = "launch"
                effective_msg = f"Ouvre {session.last_app}"
                return effective_msg, session.last_product, detected_platform

        # 5. Détection anaphore produit e-commerce (ex: "et sur cdiscount??", "regarde sur aliexpress stp")
        is_followup_pattern = bool(re.search(
            r"^(et\s+(sur|chez|pour|dans|avec|le|la|les|en)?|regarde\s+(sur|chez|dans)?|check\s+(sur|chez|dans)?|cherche\s+(sur|chez|dans)?|voir\s+(sur|chez|dans)?|combien|quel\s+est\s+le\s+prix|y\s*a\s*d'autres|trouve\s+moins\s+cher|tu\s+as\s+autre\s+chose|et\s+l[aà]-bas)\b",
            msg_lower
        )) or msg_lower.startswith("et ") or msg_lower.startswith("et?")

        from src.services.product_hunter import ProductHunterService
        substantive = ProductHunterService.extract_substantive_product(msg_clean)

        # Si un substantif clair est présent dans le message actuel
        if substantive and len(substantive) >= 3 and substantive.lower() not in ["et", "cdiscount", "amazon"]:
            session.last_product = substantive
            if detected_platform:
                session.last_platform = detected_platform
            return msg_clean, substantive, detected_platform

        # Si c'est une ellipse SANS produit explicite (ex: "et sur cdiscount??")
        if (is_followup_pattern or not substantive) and session.last_product:
            target_plat = detected_platform or session.last_platform or "Cdiscount"
            effective_msg = f"Trouve {session.last_product} sur {target_plat}"
            return effective_msg, session.last_product, target_plat

        # Pas de contexte antérieur disponible
        return msg_clean, None, detected_platform

    @classmethod
    def clear_all(cls):
        """Réinitialise toutes les sessions (pour les tests)."""
        cls._sessions.clear()
