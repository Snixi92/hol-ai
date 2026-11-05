"""
Conversation Store & Persistent SQLite Database for HoL AI (Requirement R2).
Fournit la persistance locale complète des discussions, des messages,
des cartes interactives et des traces de raisonnement avec mode WAL.
"""
import asyncio
import json
import logging
import os
import re
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("hol_ai.conversation_store")


class ConversationStore:
    """Gestionnaire de persistance SQLite avec mode WAL pour HoL AI."""

    _instance: Optional["ConversationStore"] = None

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Emplacement par défaut : services/core-engine/data/conversations.db
            base_dir = Path(__file__).resolve().parent.parent.parent
            data_dir = base_dir / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(data_dir / "conversations.db")
        else:
            self.db_path = str(db_path)
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._lock = threading.RLock()
        self._initialized = False

    @classmethod
    def get_instance(cls, db_path: Optional[str] = None) -> "ConversationStore":
        if cls._instance is None or (db_path and cls._instance.db_path != str(db_path)):
            cls._instance = cls(db_path)
        return cls._instance

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        return conn

    async def init_db(self) -> None:
        """Initialise le schéma de base de données SQLite."""
        def _sync_init():
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS conversations (
                            id TEXT PRIMARY KEY,
                            user_id TEXT NOT NULL DEFAULT 'mobile_user',
                            title TEXT NOT NULL DEFAULT 'Nouvelle discussion',
                            created_at REAL NOT NULL,
                            updated_at REAL NOT NULL,
                            is_pinned INTEGER DEFAULT 0,
                            is_archived INTEGER DEFAULT 0,
                            thinking_level TEXT DEFAULT 'standard',
                            model TEXT DEFAULT 'gemini-3.5-flash-lite',
                            metadata TEXT DEFAULT '{}'
                        );
                    """)
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_conversations_user 
                        ON conversations(user_id, updated_at DESC);
                    """)
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_conversations_pinned 
                        ON conversations(user_id, is_pinned DESC, updated_at DESC);
                    """)
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS messages (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            conversation_id TEXT NOT NULL,
                            role TEXT NOT NULL,
                            content TEXT NOT NULL,
                            cards_json TEXT DEFAULT '[]',
                            thoughts TEXT DEFAULT NULL,
                            thinking_level TEXT DEFAULT 'standard',
                            timestamp REAL NOT NULL,
                            FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                        );
                    """)
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_messages_conv 
                        ON messages(conversation_id, timestamp ASC);
                    """)
                    conn.commit()

        await asyncio.to_thread(_sync_init)
        self._initialized = True
        logger.info(f"💾 Base de données SQLite de persistance initialisée : {self.db_path} (WAL mode actif)")

    def _ensure_initialized_sync(self):
        with self._lock:
            if not self._initialized:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS conversations (
                            id TEXT PRIMARY KEY,
                            user_id TEXT NOT NULL DEFAULT 'mobile_user',
                            title TEXT NOT NULL DEFAULT 'Nouvelle discussion',
                            created_at REAL NOT NULL,
                            updated_at REAL NOT NULL,
                            is_pinned INTEGER DEFAULT 0,
                            is_archived INTEGER DEFAULT 0,
                            thinking_level TEXT DEFAULT 'standard',
                            model TEXT DEFAULT 'gemini-3.5-flash-lite',
                            metadata TEXT DEFAULT '{}'
                        );
                    """)
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS messages (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            conversation_id TEXT NOT NULL,
                            role TEXT NOT NULL,
                            content TEXT NOT NULL,
                            cards_json TEXT DEFAULT '[]',
                            thoughts TEXT DEFAULT NULL,
                            thinking_level TEXT DEFAULT 'standard',
                            timestamp REAL NOT NULL,
                            FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                        );
                    """)
                    conn.commit()
                self._initialized = True

    async def create_conversation(
        self,
        id: Optional[str] = None,
        user_id: str = "mobile_user",
        title: Optional[str] = None,
        is_pinned: bool = False,
        is_archived: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
        thinking_level: str = "standard",
        model: str = "gemini-3.5-flash-lite"
    ) -> Dict[str, Any]:
        """Crée une nouvelle conversation persistante."""
        conv_id = id or f"conv_{int(time.time() * 1000):x}"
        now = time.time()
        conv_title = (title or "Nouvelle discussion").strip()
        meta_json = json.dumps(metadata or {}, ensure_ascii=False)

        def _sync_create():
            with self._lock:
                self._ensure_initialized_sync()
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO conversations (id, user_id, title, created_at, updated_at, is_pinned, is_archived, thinking_level, model, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(id) DO UPDATE SET
                            title=excluded.title,
                            updated_at=excluded.updated_at,
                            is_pinned=excluded.is_pinned,
                            is_archived=excluded.is_archived,
                            metadata=excluded.metadata;
                        """,
                        (
                            conv_id,
                            user_id,
                            conv_title,
                            now,
                            now,
                            1 if is_pinned else 0,
                            1 if is_archived else 0,
                            thinking_level,
                            model,
                            meta_json
                        )
                    )
                    conn.commit()

        await asyncio.to_thread(_sync_create)

        return {
            "id": conv_id,
            "user_id": user_id,
            "title": conv_title,
            "created_at": now,
            "updated_at": now,
            "is_pinned": bool(is_pinned),
            "is_archived": bool(is_archived),
            "thinking_level": thinking_level,
            "model": model,
            "metadata": metadata or {},
            "messages": []
        }

    async def get_conversation(self, conversation_id: str, include_messages: bool = True) -> Optional[Dict[str, Any]]:
        """Récupère une conversation par son identifiant avec tous ses messages."""
        def _sync_get():
            with self._lock:
                self._ensure_initialized_sync()
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
                    row = cursor.fetchone()
                    if not row:
                        return None

                    conv = dict(row)
                    conv["is_pinned"] = bool(conv["is_pinned"])
                    conv["is_archived"] = bool(conv["is_archived"])
                    try:
                        conv["metadata"] = json.loads(conv.get("metadata") or "{}")
                    except Exception:
                        conv["metadata"] = {}

                    messages = []
                    if include_messages:
                        cursor.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC, id ASC", (conversation_id,))
                        for m_row in cursor.fetchall():
                            m_dict = dict(m_row)
                            try:
                                m_dict["cards"] = json.loads(m_dict.get("cards_json") or "[]")
                            except Exception:
                                m_dict["cards"] = []
                            # Aliases pour compatibilité transversale
                            m_dict["sender"] = m_dict["role"]
                            m_dict["text"] = m_dict["content"]
                            m_dict["created_at"] = m_dict["timestamp"]
                            messages.append(m_dict)

                    conv["messages"] = messages
                    conv["turns_count"] = len(messages)
                    return conv

        return await asyncio.to_thread(_sync_get)

    @staticmethod
    def _calculate_time_bucket(timestamp: float, now: Optional[float] = None) -> str:
        """
        Calcule la tranche chronologique d'un timestamp :
        - today : depuis minuit aujourd'hui
        - last_7_days : entre 7 jours et minuit aujourd'hui
        - last_30_days : entre 30 jours et 7 jours
        - older : antérieur à 30 jours
        """
        ref_time = now if now is not None else time.time()
        # Minuit aujourd'hui en heure locale
        dt_now = datetime.fromtimestamp(ref_time)
        start_of_today = datetime(dt_now.year, dt_now.month, dt_now.day).timestamp()

        if timestamp >= start_of_today:
            return "today"
        elif timestamp >= (start_of_today - 6 * 86400):
            return "last_7_days"
        elif timestamp >= (start_of_today - 29 * 86400):
            return "last_30_days"
        else:
            return "older"

    async def list_conversations(
        self,
        user_id: Optional[str] = None,
        include_archived: bool = False,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Liste les discussions avec pagination, recherche textuelle et regroupement chronologique.
        Renvoie la liste des conversations et le comptage par time_bucket.
        """
        now = time.time()

        def _sync_list():
            with self._lock:
                self._ensure_initialized_sync()
                with self._get_connection() as conn:
                    cursor = conn.cursor()

                    query = "SELECT * FROM conversations WHERE 1=1"
                    params = []

                    if user_id:
                        query += " AND user_id = ?"
                        params.append(user_id)

                    if not include_archived:
                        query += " AND is_archived = 0"

                    if search and search.strip():
                        query += " AND (title LIKE ? OR id IN (SELECT conversation_id FROM messages WHERE content LIKE ?))"
                        pattern = f"%{search.strip()}%"
                        params.extend([pattern, pattern])

                    # Tri : Épinglés en tête, puis par date de dernière mise à jour décroissante
                    query += " ORDER BY is_pinned DESC, updated_at DESC LIMIT ? OFFSET ?"
                    params.extend([limit, offset])

                    cursor.execute(query, params)
                    rows = cursor.fetchall()

                    conversations = []
                    buckets_count = {
                        "today": 0,
                        "last_7_days": 0,
                        "last_30_days": 0,
                        "older": 0
                    }

                    for row in rows:
                        c = dict(row)
                        c["is_pinned"] = bool(c["is_pinned"])
                        c["is_archived"] = bool(c["is_archived"])
                        try:
                            c["metadata"] = json.loads(c.get("metadata") or "{}")
                        except Exception:
                            c["metadata"] = {}

                        bucket = self._calculate_time_bucket(c["updated_at"], now)
                        c["time_bucket"] = bucket
                        if not c["is_archived"]:
                            buckets_count[bucket] = buckets_count.get(bucket, 0) + 1

                        # Nombre de tours et dernier aperçu
                        cursor.execute("SELECT COUNT(*), content FROM messages WHERE conversation_id = ? ORDER BY id DESC LIMIT 1", (c["id"],))
                        turn_row = cursor.fetchone()
                        turns_count = turn_row[0] if turn_row else 0
                        last_preview = turn_row[1] if turn_row and turn_row[1] else ""
                        c["turns_count"] = turns_count
                        c["last_preview"] = (last_preview[:80] + "...") if len(last_preview) > 80 else last_preview

                        conversations.append(c)

                    return {
                        "conversations": conversations,
                        "buckets": buckets_count,
                        "total": len(conversations)
                    }

        return await asyncio.to_thread(_sync_list)

    async def update_conversation(
        self,
        conversation_id: str,
        title: Optional[str] = None,
        is_pinned: Optional[bool] = None,
        is_archived: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Met à jour les métadonnées d'une conversation (titre, épinglage, archivage)."""
        def _sync_update():
            with self._lock:
                self._ensure_initialized_sync()
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
                    row = cursor.fetchone()
                    if not row:
                        return None

                    updates = []
                    params = []

                    if title is not None:
                        updates.append("title = ?")
                        params.append(title.strip())

                    if is_pinned is not None:
                        updates.append("is_pinned = ?")
                        params.append(1 if is_pinned else 0)

                    if is_archived is not None:
                        updates.append("is_archived = ?")
                        params.append(1 if is_archived else 0)

                    if metadata is not None:
                        updates.append("metadata = ?")
                        params.append(json.dumps(metadata, ensure_ascii=False))

                    if not updates:
                        return dict(row)

                    updates.append("updated_at = ?")
                    params.append(time.time())

                    params.append(conversation_id)
                    query = f"UPDATE conversations SET {', '.join(updates)} WHERE id = ?"
                    cursor.execute(query, params)
                    conn.commit()

                    cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
                    updated_row = cursor.fetchone()
                    res = dict(updated_row)
                    res["is_pinned"] = bool(res["is_pinned"])
                    res["is_archived"] = bool(res["is_archived"])
                    try:
                        res["metadata"] = json.loads(res.get("metadata") or "{}")
                    except Exception:
                        res["metadata"] = {}
                    return res

        return await asyncio.to_thread(_sync_update)

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Supprime une conversation et tous ses messages associés."""
        def _sync_delete():
            with self._lock:
                self._ensure_initialized_sync()
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM conversations WHERE id = ?", (conversation_id,))
                    if not cursor.fetchone():
                        return False

                    cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
                    cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
                    conn.commit()
                    return True

        return await asyncio.to_thread(_sync_delete)

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        cards: Optional[List[Dict[str, Any]]] = None,
        thoughts: Optional[str] = None,
        thinking_level: Optional[str] = None,
        timestamp: Optional[float] = None,
        # Aliases facultatifs
        sender: Optional[str] = None,
        text: Optional[str] = None,
        created_at: Optional[float] = None
    ) -> Dict[str, Any]:
        """Ajoute un message à une conversation et actualise sa date de mise à jour."""
        effective_role = role or sender or "user"
        effective_content = content if content is not None else (text or "")
        effective_time = timestamp or created_at or time.time()
        effective_cards = cards or []
        cards_json = json.dumps(effective_cards, ensure_ascii=False)
        effective_level = thinking_level or "standard"

        def _sync_add():
            with self._lock:
                self._ensure_initialized_sync()
                with self._get_connection() as conn:
                    cursor = conn.cursor()

                    # S'assurer que la conversation existe
                    cursor.execute("SELECT id FROM conversations WHERE id = ?", (conversation_id,))
                    if not cursor.fetchone():
                        cursor.execute(
                            """
                            INSERT INTO conversations (id, user_id, title, created_at, updated_at)
                            VALUES (?, 'mobile_user', 'Nouvelle discussion', ?, ?)
                            """,
                            (conversation_id, effective_time, effective_time)
                        )

                    cursor.execute(
                        """
                        INSERT INTO messages (conversation_id, role, content, cards_json, thoughts, thinking_level, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            conversation_id,
                            effective_role,
                            effective_content,
                            cards_json,
                            thoughts,
                            effective_level,
                            effective_time
                        )
                    )
                    msg_id = cursor.lastrowid

                    # Mettre à jour le timestamp de la conversation
                    cursor.execute(
                        "UPDATE conversations SET updated_at = ? WHERE id = ?",
                        (effective_time, conversation_id)
                    )
                    conn.commit()

                    return {
                        "id": msg_id,
                        "conversation_id": conversation_id,
                        "role": effective_role,
                        "sender": effective_role,
                        "content": effective_content,
                        "text": effective_content,
                        "cards": effective_cards,
                        "thoughts": thoughts,
                        "thinking_level": effective_level,
                        "timestamp": effective_time,
                        "created_at": effective_time
                    }

        return await asyncio.to_thread(_sync_add)

    @staticmethod
    def generate_nlp_title(raw_text: str) -> str:
        """Génère un titre ultra-concis (3 à 5 mots) par heuristique NLP déterministe hors-ligne."""
        if not raw_text or not raw_text.strip():
            return "Nouvelle discussion"

        clean = raw_text.strip()
        # Retirer ponctuation superficielle
        clean = re.sub(r"[?!.,:;\"'«»()[\]{}—\-_/]+", " ", clean)

        stop_words = {
            "bonjour", "salut", "peux", "tu", "peux-tu", "stp", "sil", "te", "plait", "plaît",
            "merci", "cherche", "trouve", "trouve-moi", "donne-moi", "dis-moi", "quel", "quelle",
            "quels", "quelles", "est", "le", "la", "les", "un", "une", "des", "du", "de", "pour",
            "dans", "sur", "avec", "et", "ou", "a", "à", "en", "je", "voudrais", "aimerais",
            "vas", "regarde", "check", "fais", "moi", "me", "stpl", "please", "nous", "vous", "lui"
        }

        tokens = [w for w in clean.split() if w.lower() not in stop_words and len(w) > 1]

        if not tokens:
            # Fallback sur les premiers mots bruts
            tokens = clean.split()[:4]

        selected = tokens[:5]
        title = " ".join(selected)

        # Majuscule initiale
        if title:
            title = title[0].upper() + title[1:]

        # Limite stricte à 38 caractères
        if len(title) > 38:
            title = title[:35].rstrip() + "..."

        return title or "Nouvelle discussion"

    async def generate_title_from_first_message(self, conversation_id: str, custom_text: Optional[str] = None) -> str:
        """
        Génère un titre concis à partir du premier échange utilisateur.
        Tente d'abord le LLM si disponible, puis applique le fallback NLP déterministe.
        Met à jour la conversation et renvoie le titre généré.
        """
        text_to_summarize = custom_text
        if not text_to_summarize:
            def _get_first_user_msg():
                with self._lock:
                    self._ensure_initialized_sync()
                    with self._get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT content FROM messages WHERE conversation_id = ? AND role = 'user' ORDER BY id ASC LIMIT 1",
                            (conversation_id,)
                        )
                        row = cursor.fetchone()
                        return row[0] if row else None

            text_to_summarize = await asyncio.to_thread(_get_first_user_msg)

        if not text_to_summarize:
            return "Nouvelle discussion"

        generated_title: Optional[str] = None

        # Tentative LLM si disponible
        try:
            from src.services.llm_engine import LLMBrain
            if LLMBrain.get_api_key():
                prompt = f"Génère un titre ultra-concis de 3 à 5 mots maximum sans ponctuation ni guillemets pour cette requête utilisateur : '{text_to_summarize}'"
                resp = await LLMBrain.generate_conversational_response(
                    user_message=prompt,
                    tool_results={},
                    context_history=[]
                )
                cleaned = re.sub(r'["\n\r*.]', '', resp).strip()
                if cleaned and len(cleaned.split()) <= 7 and len(cleaned) <= 50:
                    generated_title = cleaned[0].upper() + cleaned[1:]
        except Exception as e:
            logger.debug(f"LLM auto-titling indisponible : {e}")

        if not generated_title:
            generated_title = self.generate_nlp_title(text_to_summarize)

        # Mise à jour en base
        def _sync_save_title():
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                        (generated_title, time.time(), conversation_id)
                    )
                    conn.commit()

        await asyncio.to_thread(_sync_save_title)
        return generated_title

    async def export_conversation_markdown(self, conversation_id: str) -> str:
        """Exporte l'historique complet d'une conversation au format Markdown élégant."""
        conv = await self.get_conversation(conversation_id, include_messages=True)
        if not conv:
            raise ValueError(f"Conversation {conversation_id} introuvable")

        title = conv.get("title") or "Discussion sans titre"
        created_dt = datetime.fromtimestamp(conv.get("created_at", time.time()), timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        model = conv.get("model") or "gemini-3.5-flash-lite"
        turns = conv.get("turns_count", 0)

        lines = [
            f"# {title}",
            "",
            f"- **Date** : {created_dt}",
            f"- **ID Discussion** : `{conversation_id}`",
            f"- **Modèle** : {model}",
            f"- **Échanges** : {turns} messages",
            "",
            "---",
            ""
        ]

        messages = conv.get("messages", [])
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "").strip()
            msg_dt = datetime.fromtimestamp(m.get("timestamp", time.time()), timezone.utc).strftime("%H:%M:%S")

            if role == "user":
                lines.append(f"### 👤 Utilisateur *({msg_dt})*")
                lines.append("")
                lines.append(content)
                lines.append("")
            else:
                lines.append(f"### 🤖 HoL AI *({msg_dt})*")
                lines.append("")
                thoughts = m.get("thoughts")
                if thoughts and thoughts.strip():
                    lines.append("> **Raisonnement interne :**")
                    for t_line in thoughts.strip().splitlines():
                        lines.append(f"> {t_line}")
                    lines.append("")

                lines.append(content)
                lines.append("")

                cards = m.get("cards", [])
                if cards:
                    lines.append("#### 📦 Éléments interactifs associés :")
                    for card in cards:
                        c_type = card.get("type", "card")
                        c_data = card.get("data", {})
                        if c_type == "deal":
                            prod = c_data.get("product", "Produit")
                            price = c_data.get("current_drop_price_eur", "")
                            plat = c_data.get("platform", "")
                            lines.append(f"- **Offre E-commerce** : {prod} — {price} € sur {plat}")
                        elif c_type == "second_hand_deals":
                            lines.append(f"- **Comparatif Reconditionné** : {c_data.get('product', '')}")
                        elif c_type == "jarvis_briefing":
                            lines.append(f"- **Briefing Matinal** : météo & actualités synthétisées")
                        else:
                            lines.append(f"- **Carte {c_type}** : {json.dumps(c_data, ensure_ascii=False)[:100]}...")
                    lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    async def export_conversation_json(self, conversation_id: str) -> Dict[str, Any]:
        """Exporte l'historique complet d'une conversation sous forme d'objet JSON standard."""
        conv = await self.get_conversation(conversation_id, include_messages=True)
        if not conv:
            raise ValueError(f"Conversation {conversation_id} introuvable")

        return {
            "version": "1.0",
            "exported_at": time.time(),
            "conversation": conv
        }
