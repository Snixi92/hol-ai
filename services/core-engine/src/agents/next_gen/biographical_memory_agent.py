"""
BiographicalMemoryAgent : Cerveau Mémoriel Biographique Persistant pour HoL AI.
Maintient une mémoire épisodique et sémantique permanente dans une base SQLite locale.
Enregistre pour toujours les faits, préférences, matériel, localisation et habitudes de l'utilisateur
pour personnaliser les échanges sans jamais avoir besoin de lui redemander qui il est.
"""
import os
import sqlite3
import time
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("hol_ai.biographical_memory")

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
DB_PATH = DATA_DIR / "biographical_memory.db"


class BiographicalMemoryAgent:
    """Agent spécialiste de la mémoire biographique long-terme de l'utilisateur."""

    _initialized: bool = False

    @classmethod
    def _get_db_connection(cls) -> sqlite3.Connection:
        """Crée ou ouvre la base de données SQLite locale."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def initialize_db(cls):
        """Initialise le schéma de base de données si nécessaire."""
        if cls._initialized:
            return
        conn = cls._get_db_connection()
        try:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_facts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        category TEXT NOT NULL,
                        key TEXT NOT NULL,
                        value TEXT NOT NULL,
                        confidence REAL DEFAULT 1.0,
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL,
                        UNIQUE(user_id, category, key)
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS conversation_episodes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        topic TEXT NOT NULL,
                        summary TEXT NOT NULL,
                        timestamp REAL NOT NULL
                    )
                """)
            cls._initialized = True
            # Ensemencement initial des faits connus confirmés
            cls._seed_initial_facts()
            logger.info(f"✅ Mémoire biographique initialisée sur : {DB_PATH}")
        finally:
            conn.close()

    @classmethod
    def _seed_initial_facts(cls):
        """Initialise les faits biographiques établis lors des sessions précédentes."""
        initial_facts = [
            ("hardware", "primary_device", "PC Portable Gamer Lenovo (Windows 11)", 1.0),
            ("hardware", "management_app", "Lenovo Vantage", 1.0),
            ("hardware", "sought_gpu", "NVIDIA GeForce RTX 5060", 0.95),
            ("location", "city", "Vienne (38200, Isère)", 1.0),
            ("location", "region", "Auvergne-Rhône-Alpes", 0.9),
            ("preferences", "language", "Français (avec compréhension parfaite de la Darija)", 1.0),
            ("preferences", "deal_hunting", "Recherche toujours le tarif plancher vérifié, occasion certifiée ou neuf le moins cher", 0.95),
            ("habits", "frequent_apps", "Lenovo Vantage, Discord, Chrome, Spotify", 0.9)
        ]
        for cat, key, val, conf in initial_facts:
            cls.record_fact("mobile_user", cat, key, val, confidence=conf)

    @classmethod
    def record_fact(
        cls,
        user_id: str,
        category: str,
        key: str,
        value: str,
        confidence: float = 1.0
    ) -> Dict[str, Any]:
        """Enregistre ou met à jour un fait biographique permanent."""
        cls.initialize_db()
        conn = cls._get_db_connection()
        now = time.time()
        try:
            with conn:
                conn.execute("""
                    INSERT INTO user_facts (user_id, category, key, value, confidence, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id, category, key) DO UPDATE SET
                        value = excluded.value,
                        confidence = excluded.confidence,
                        updated_at = excluded.updated_at
                """, (user_id, category.lower(), key.lower(), value.strip(), confidence, now, now))

            return {
                "success": True,
                "status": "recorded",
                "user_id": user_id,
                "category": category,
                "key": key,
                "value": value,
                "confidence": confidence
            }
        finally:
            conn.close()

    @classmethod
    def get_fact(cls, user_id: str, category: str, key: str) -> Optional[Dict[str, Any]]:
        """Récupère un fait spécifique par catégorie et clé."""
        cls.initialize_db()
        conn = cls._get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, category, key, value, confidence, created_at, updated_at
                FROM user_facts
                WHERE user_id = ? AND category = ? AND key = ?
            """, (user_id, category.lower(), key.lower()))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @classmethod
    def get_all_facts(cls, user_id: str = "mobile_user") -> List[Dict[str, Any]]:
        """Récupère l'ensemble des faits mémorisés pour un utilisateur."""
        cls.initialize_db()
        conn = cls._get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, category, key, value, confidence, updated_at
                FROM user_facts
                WHERE user_id = ?
                ORDER BY category, key
            """, (user_id,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @classmethod
    def delete_fact(cls, user_id: Any = "mobile_user", category: Optional[str] = None, key: Optional[str] = None, fact_id: Optional[int] = None) -> Dict[str, Any]:
        """Supprime un fait de la mémoire par ID ou par (user_id, category, key)."""
        cls.initialize_db()
        conn = cls._get_db_connection()
        try:
            with conn:
                if category and key:
                    cursor = conn.execute(
                        "DELETE FROM user_facts WHERE user_id = ? AND category = ? AND key = ?",
                        (str(user_id), category.lower(), key.lower())
                    )
                elif fact_id is not None:
                    cursor = conn.execute("DELETE FROM user_facts WHERE id = ?", (int(fact_id),))
                else:
                    cursor = conn.execute("DELETE FROM user_facts WHERE id = ?", (int(user_id),))
                count = cursor.rowcount
                return {"success": count > 0, "deleted_count": count}
        finally:
            conn.close()

    @classmethod
    def get_biographical_context(cls, user_id: str = "mobile_user") -> str:
        """
        Formate une synthèse biographique concise pour injection directe dans le prompt système
        du moteur cognitif et de l'orchestrateur.
        """
        facts = cls.get_all_facts(user_id)
        if not facts:
            return ""

        by_cat: Dict[str, List[str]] = {}
        for f in facts:
            cat = f["category"].upper()
            by_cat.setdefault(cat, []).append(f"- {f['key'].replace('_', ' ').capitalize()} : {f['value']}")

        lines = [
            "MÉMOIRE BIOGRAPHIQUE PERMANENTE DE L'UTILISATEUR (NE JAMAIS OUBLIER NI REDEMANDER) :"
        ]
        for cat, items in by_cat.items():
            lines.append(f"[{cat}]")
            lines.extend(items)

        lines.append(
            "Directive : Utilise ces informations naturellement pour personnaliser tes réponses avec elle "
            "(ex: tu sais qu'elle est Capricorne ascendant Lion, née le 11 janvier 2004 au Maroc, basée en France vers Vienne 38, "
            "perfectionniste, passionnée de skincare K-Beauty & Project Pan, trilingue FR/EN/Darija, et qu'elle a horreur qu'on lui serve des réponses génériques ou vagues)."
        )
        return "\n".join(lines)

    @classmethod
    def auto_learn_from_interaction(
        cls,
        user_message: str,
        assistant_reply: str,
        user_id: str = "mobile_user"
    ) -> List[Dict[str, Any]]:
        """
        Scanne de manière autonome le message utilisateur pour extraire de nouveaux faits biographiques
        (ville, matériel, préférences de marques, budget).
        """
        cls.initialize_db()
        learned: List[Dict[str, Any]] = []
        msg_clean = user_message.strip()
        msg_low = msg_clean.lower()

        # 1. Détection de localisation (ex: "à Vienne 38", "à Lyon", "sur Paris")
        m_loc = re.search(r"\b(?:à|dans|vers|sur|habite\s+à|suis\s+à)\s+([A-Za-zÀ-ÖØ-öø-ÿ\-]+(?:\s+\d{2,5})?)\b", msg_clean, re.IGNORECASE)
        if m_loc:
            loc_candidate = m_loc.group(1).strip()
            # Filtrer les faux positifs courants
            if loc_candidate.lower() not in ["paris", "quoi", "combien", "amazon", "cdiscount", "fond", "jour", "heure", "coup"]:
                res = cls.record_fact(user_id, "location", "city", loc_candidate, confidence=0.9)
                learned.append(res)

        # 2. Détection d'équipement matériel (ex: "mon pc lenovo", "ma ps5", "mon iphone 15")
        if "lenovo" in msg_low and any(w in msg_low for w in ["mon", "mon pc", "pc", "vantage"]):
            learned.append(cls.record_fact(user_id, "hardware", "primary_device", "PC Lenovo", confidence=0.95))
        if "rtx 5060" in msg_low or "5060" in msg_low:
            learned.append(cls.record_fact(user_id, "hardware", "sought_gpu", "RTX 5060", confidence=0.9))
        if "ps5" in msg_low and any(w in msg_low for w in ["ma", "console", "joue"]):
            learned.append(cls.record_fact(user_id, "gaming", "console", "PlayStation 5", confidence=0.85))

        # 3. Détection d'applications régulières
        app_keywords = ["lenovo vantage", "discord", "spotify", "steam", "chrome", "vscode", "netflix"]
        for app in app_keywords:
            if app in msg_low:
                learned.append(cls.record_fact(user_id, "habits", f"app_{app.replace(' ', '_')}", app.title(), confidence=0.8))

        # 4. Détection de budget (ex: "budget de 500 euros", "budget max 600€")
        m_budget = re.search(r"budget(?:\s+max)?(?:\s+de|\s+est\s+de)?\s+(\d+)\s*(?:€|euros?)", msg_clean, re.IGNORECASE)
        if m_budget:
            learned.append(cls.record_fact(user_id, "budget", "budget_max", f"{m_budget.group(1)}€", confidence=0.9))

        return learned
