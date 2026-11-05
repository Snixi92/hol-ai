"""
Moteur de Recherche Visuelle & Enrichissement Image Haute Résolution pour HoL AI (Requirement R6).

Fonctionnalités :
1. Détection et extraction intelligente d'entités visuelles (monuments, merveilles naturelles, chefs-d'œuvre artistiques, faune/flore, instruments scientifiques).
2. Résolveur d'images haute résolution multi-paliers (Wikipedia REST API -> Opensearch canonique -> Fallback Wikipedia EN -> Wikimedia Commons Query API).
3. Payload standardisé pour carte Liquid Glass avec dimensions réelles 4K/HD, métadonnées, badges et lien source vérifié.
4. Tolérance aux pannes, cache mémoire avec TTL et ponts synchrones / asynchrones non-bloquants.
"""

import asyncio
import concurrent.futures
import html
import logging
import re
import time
import urllib.parse
from typing import Any, Dict, List, Optional, Set, Tuple

import httpx

logger = logging.getLogger("hol_ai.visual_search")


class VisualSearchEngine:
    """Moteur de recherche et d'enrichissement d'images haute résolution."""

    # Cache en mémoire avec TTL (par défaut 1 heure = 3600 secondes)
    _cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
    _CACHE_TTL_SECONDS: float = 3600.0

    # Dictionnaire d'entités visuelles reconnues (Monuments, Merveilles, Art, Faune, Sciences)
    KNOWN_VISUAL_ENTITIES: Dict[str, str] = {
        # Monuments & Édifices mondiaux
        "tour eiffel": "Tour Eiffel",
        "eiffel tower": "Tour Eiffel",
        "colisee": "Colisée",
        "colisée": "Colisée",
        "colosseum": "Colisée",
        "big ben": "Big Ben",
        "taj mahal": "Taj Mahal",
        "statue de la liberte": "Statue de la Liberté",
        "statue de la liberté": "Statue de la Liberté",
        "statue of liberty": "Statue de la Liberté",
        "sagrada familia": "Sagrada Família",
        "sagrada família": "Sagrada Família",
        "pyramide de gizeh": "Pyramide de Khéops",
        "pyramides de gizeh": "Pyramides de Gizeh",
        "le mont-saint-michel": "Le Mont-Saint-Michel",
        "le mont saint michel": "Le Mont-Saint-Michel",
        "mont-saint-michel": "Le Mont-Saint-Michel",
        "mont saint-michel": "Le Mont-Saint-Michel",
        "mont saint michel": "Le Mont-Saint-Michel",
        "machu picchu": "Machu Picchu",
        "parthenon": "Parthénon",
        "parthénon": "Parthénon",
        "acropole": "Acropole d'Athènes",
        "sainte-sophie": "Sainte-Sophie (Istanbul)",
        "sainte sophie": "Sainte-Sophie (Istanbul)",
        "hagia sophia": "Sainte-Sophie (Istanbul)",
        "grande muraille de chine": "Grande Muraille",
        "muraille de chine": "Grande Muraille",
        "arc de triomphe": "Arc de triomphe de l'Étoile",
        "notre-dame de paris": "Cathédrale Notre-Dame de Paris",
        "notre dame de paris": "Cathédrale Notre-Dame de Paris",
        "notre-dame": "Cathédrale Notre-Dame de Paris",
        "basilique saint-pierre": "Basilique Saint-Pierre",
        "pont du golden gate": "Pont du Golden Gate",
        "golden gate": "Pont du Golden Gate",
        "sydney opera house": "Opéra de Sydney",
        "opera de sydney": "Opéra de Sydney",
        "opéra de sydney": "Opéra de Sydney",
        "burj khalifa": "Burj Khalifa",
        "chateau de versailles": "Château de Versailles",
        "château de versailles": "Château de Versailles",
        "stonehenge": "Stonehenge",
        "petra": "Pétra",
        "pétra": "Pétra",
        "louvre": "Musée du Louvre",
        "musee du louvre": "Musée du Louvre",
        "musée du louvre": "Musée du Louvre",

        # Merveilles Géographiques & Naturelles
        "grand canyon": "Grand Canyon",
        "baie d'ha long": "Baie d'Along",
        "baie d'along": "Baie d'Along",
        "aurore boreale": "Aurore polaire",
        "aurore boréale": "Aurore polaire",
        "aurores boreales": "Aurore polaire",
        "aurores boréales": "Aurore polaire",
        "mont blanc": "Mont Blanc",
        "salar d'uyuni": "Salar d'Uyuni",
        "fjords de norvege": "Fjord",
        "mont fuji": "Mont Fuji",
        "fujisan": "Mont Fuji",
        "fuji": "Mont Fuji",
        "mont everest": "Everest",
        "everest": "Everest",
        "chutes du niagara": "Chutes du Niagara",
        "niagara falls": "Chutes du Niagara",
        "chutes victoria": "Chutes Victoria",
        "mer morte": "Mer Morte",
        "desert du sahara": "Sahara",
        "désert du sahara": "Sahara",
        "sahara": "Sahara",
        "krakatoa": "Krakatoa",
        "kilimandjaro": "Kilimandjaro",

        # Art & Chefs-d'œuvre
        "la joconde": "La Joconde",
        "mona lisa": "La Joconde",
        "joconde": "La Joconde",
        "la nuit etoilee": "La Nuit étoilée",
        "la nuit étoilée": "La Nuit étoilée",
        "guernica": "Guernica (Picasso)",
        "la naissance de venus": "La Naissance de Vénus (Botticelli)",
        "la naissance de vénus": "La Naissance de Vénus (Botticelli)",
        "la cene": "La Cène (Léonard de Vinci)",
        "la cène": "La Cène (Léonard de Vinci)",
        "le cri": "Le Cri",
        "venus de milo": "Vénus de Milo",
        "vénus de milo": "Vénus de Milo",
        "david de michel-ange": "David (Michel-Ange)",
        "les nympheas": "Les Nymphéas",
        "les nymphéas": "Les Nymphéas",

        # Faune & Flore
        "tigre du bengale": "Tigre du Bengale",
        "panda geant": "Panda géant",
        "panda géant": "Panda géant",
        "sequoia geant": "Séquoia géant",
        "séquoia géant": "Séquoia géant",
        "baobab": "Baobab",

        # Astronomie & Sciences
        "telescope james webb": "James Webb (télescope spatial)",
        "télescope james webb": "James Webb (télescope spatial)",
        "james webb": "James Webb (télescope spatial)",
        "jwst": "James Webb (télescope spatial)",
        "station spatiale internationale": "Station spatiale internationale",
        "iss": "Station spatiale internationale",
        "trou noir m87": "Messier 87",
        "nebuleuse d'orion": "Nébuleuse d'Orion",
        "nébuleuse d'orion": "Nébuleuse d'Orion",
    }

    # Motifs regex pour capturer des intentions visuelles directes
    VISUAL_INTENT_PATTERNS = [
        re.compile(r"(?:photo|image|visuel|illustration|clich[ée]|portrait|tableau|peinture|vue)\s+(?:de|du|d'un|d'une|de\s+la|des)?\s+([A-Za-zÀ-ÖØ-öø-ÿ0-9\s\-']{3,50})", re.IGNORECASE),
        re.compile(r"(?:montre|affiche|faire\s+voir|fais\s+voir|voir|cherche|regarde)\s+(?:moi\s+)?(?:la|le|les|l'|un|une)?\s*([A-Za-zÀ-ÖØ-öø-ÿ0-9\s\-']{3,50})", re.IGNORECASE),
        re.compile(r"(?:[àa]\s+quoi\s+semble|[àa]\s+quoi\s+ressemble|c'est\s+quoi|qu'est-ce\s+que|parle-moi\s+de|parle\s+moi\s+de)\s+(?:la|le|les|l'|du|de\s+la)?\s*([A-Za-zÀ-ÖØ-öø-ÿ0-9\s\-']{3,50})", re.IGNORECASE),
    ]

    STOP_WORDS = {
        "s'il te plait", "s'il te plaît", "svp", "stp", "merci", "en ce moment", "aujourd'hui",
        "s'il vous plait", "s'il vous plaît", "sttp", "directement", "exactement", "rapidement",
        "maintenant", "pour voir", "dans le monde", "en photo", "en image", "en hd", "en 4k"
    }

    @classmethod
    def _normalize_text(cls, text: str) -> str:
        """Nettoie et normalise une chaîne pour la comparaison."""
        if not text:
            return ""
        t = text.lower().strip()
        # Remplacement des apostrophes courbes
        t = t.replace("’", "'").replace("`", "'")
        # Suppression de la ponctuation finale
        t = re.sub(r"[?!.,;:]+$", "", t).strip()
        return t

    @classmethod
    def extract_visual_entities(cls, query_or_text: str) -> List[str]:
        """
        Extrait une liste ordonnée et dédupliquée d'entités visuelles depuis un texte ou une requête.
        Combine dictionnaire O(1), recherche de sous-chaînes et expressions régulières d'intention visuelle.
        """
        if not query_or_text:
            return []

        cleaned_query = cls._normalize_text(query_or_text)
        cleaned_query_no_hyphen = cleaned_query.replace("-", " ")
        detected_entities: List[str] = []
        seen_canonical: Set[str] = set()

        # 1. Correspondance directe dans le dictionnaire des entités connues (recherche de la plus longue sous-chaîne)
        sorted_known = sorted(cls.KNOWN_VISUAL_ENTITIES.keys(), key=len, reverse=True)
        for key in sorted_known:
            pattern = r"\b" + re.escape(key) + r"\b"
            key_no_hyphen = key.replace("-", " ")
            pat_no_hyphen = r"\b" + re.escape(key_no_hyphen) + r"\b"
            if re.search(pattern, cleaned_query) or re.search(pat_no_hyphen, cleaned_query_no_hyphen):
                canonical = cls.KNOWN_VISUAL_ENTITIES[key]
                if canonical not in seen_canonical:
                    seen_canonical.add(canonical)
                    detected_entities.append(canonical)

        # 2. Extraction via expressions régulières d'intention visuelle ("photo de...", "montre-moi...")
        for regex in cls.VISUAL_INTENT_PATTERNS:
            for match in regex.finditer(query_or_text):
                raw_entity = match.group(1).strip()
                # Nettoyage des stop words
                norm_cand = cls._normalize_text(raw_entity)
                for sw in cls.STOP_WORDS:
                    if norm_cand.endswith(sw):
                        norm_cand = norm_cand[:-len(sw)].strip()

                if len(norm_cand) >= 3:
                    # Vérifier si cela correspond à une entité connue
                    if norm_cand in cls.KNOWN_VISUAL_ENTITIES:
                        can = cls.KNOWN_VISUAL_ENTITIES[norm_cand]
                        if can not in seen_canonical:
                            seen_canonical.add(can)
                            detected_entities.append(can)
                    else:
                        # Candidat libre plausible (capitalisé)
                        capitalized_cand = raw_entity.strip().title()
                        if capitalized_cand not in seen_canonical and len(capitalized_cand.split()) <= 5:
                            seen_canonical.add(capitalized_cand)
                            detected_entities.append(capitalized_cand)

        return detected_entities

    @classmethod
    async def _resolve_wikipedia_summary(cls, entity: str, lang: str = "fr", timeout: float = 4.0) -> Optional[Dict[str, Any]]:
        """Interroge l'API REST Summary de Wikipedia pour une entité donnée."""
        formatted_title = entity.strip().replace(" ", "_")
        url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(formatted_title)}"
        headers = {
            "User-Agent": "HoL-AI-VisualSearch/1.0 (https://hol-ai.local; contact@hol-ai.local)"
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    # Vérifier si l'image est présente
                    if data.get("originalimage") or data.get("thumbnail"):
                        return data
                elif resp.status_code in (301, 302, 307, 308):
                    loc = resp.headers.get("location")
                    if loc:
                        resp_redir = await client.get(loc, headers=headers)
                        if resp_redir.status_code == 200:
                            data = resp_redir.json()
                            if data.get("originalimage") or data.get("thumbnail"):
                                return data
        except Exception as e:
            logger.debug(f"Wikipedia summary lookup exception ({lang}, {entity}): {e}")

        return None

    @classmethod
    async def _resolve_wikipedia_opensearch(cls, entity: str, lang: str = "fr", timeout: float = 4.0) -> Optional[str]:
        """Utilise l'API Opensearch de Wikipedia pour trouver le titre canonique exact."""
        url = f"https://{lang}.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(entity)}&limit=3&namespace=0&format=json"
        headers = {
            "User-Agent": "HoL-AI-VisualSearch/1.0 (https://hol-ai.local; contact@hol-ai.local)"
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if len(data) >= 2 and data[1]:
                        # Premier résultat canonique
                        return data[1][0]
        except Exception as e:
            logger.debug(f"Wikipedia opensearch lookup exception ({lang}, {entity}): {e}")

        return None

    @classmethod
    async def _resolve_wikimedia_commons(cls, entity: str, timeout: float = 4.0) -> Optional[Dict[str, Any]]:
        """Recherche une photo haute résolution sur Wikimedia Commons en dernier recours."""
        q = urllib.parse.quote(entity)
        url = (
            f"https://commons.wikimedia.org/w/api.php?action=query&generator=search"
            f"&gsrsearch={q}&gsrnamespace=6&gsrlimit=1&prop=imageinfo"
            f"&iiprop=url|size|extmetadata&format=json"
        )
        headers = {
            "User-Agent": "HoL-AI-VisualSearch/1.0 (https://hol-ai.local; contact@hol-ai.local)"
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    pages = data.get("query", {}).get("pages", {})
                    if pages:
                        first_page = next(iter(pages.values()))
                        image_info_list = first_page.get("imageinfo", [])
                        if image_info_list:
                            info = image_info_list[0]
                            file_url = info.get("url")
                            w = info.get("width", 1920)
                            h = info.get("height", 1080)
                            title_clean = first_page.get("title", "").replace("File:", "").replace("Fichier:", "")
                            title_clean = re.sub(r"\.[a-zA-Z0-9]+$", "", title_clean).replace("_", " ")

                            return {
                                "title": entity.title() if len(entity) > 2 else title_clean,
                                "description": f"Photographie d'archive Wikimedia Commons pour {entity}.",
                                "originalimage": {
                                    "source": file_url,
                                    "width": w,
                                    "height": h
                                },
                                "thumbnail": {
                                    "source": info.get("thumburl") or file_url,
                                    "width": min(w, 800),
                                    "height": int(h * min(w, 800) / max(w, 1))
                                },
                                "content_urls": {
                                    "desktop": {
                                        "page": info.get("descriptionurl") or f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(first_page.get('title', ''))}"
                                    }
                                },
                                "source_name": "Wikimedia Commons"
                            }
        except Exception as e:
            logger.debug(f"Wikimedia commons lookup exception ({entity}): {e}")

        return None

    @classmethod
    def _compute_badge(cls, width: int, height: int) -> str:
        """Génère un badge élégant adapté à la résolution constatée."""
        max_dim = max(width, height)
        if max_dim >= 3840:
            return "Photographie Ultra HD 4K"
        elif max_dim >= 2560:
            return "Photographie 2K Quad HD"
        elif max_dim >= 1920:
            return "Photographie Haute Résolution (HD)"
        return "Photographie Haute Résolution"

    @classmethod
    async def search_visual_entity(cls, entity: str, lang: str = "fr") -> Optional[Dict[str, Any]]:
        """
        Recherche une entité visuelle et retourne un dictionnaire de résultat riche.
        Applique la stratégie multi-paliers :
        1. Wikipedia Summary dans la langue demandée.
        2. Wikipedia Opensearch (résolution de titre) puis Summary.
        3. Fallback Wikipedia English si la langue demandée est différente.
        4. Fallback Wikimedia Commons API.
        """
        if not entity or not entity.strip():
            return None

        clean_entity = entity.strip()
        cache_key = f"{lang}:{clean_entity.lower()}"

        # Vérification du cache TTL
        now = time.time()
        if cache_key in cls._cache:
            ts, cached_val = cls._cache[cache_key]
            if now - ts < cls._CACHE_TTL_SECONDS:
                return cached_val

        wiki_data: Optional[Dict[str, Any]] = None
        source_name = "Wikipedia"

        # Tier 1 : Wikipedia Summary direct
        wiki_data = await cls._resolve_wikipedia_summary(clean_entity, lang=lang)

        # Tier 1.5 : Opensearch canonical resolution puis Summary
        if not wiki_data:
            canonical_title = await cls._resolve_wikipedia_opensearch(clean_entity, lang=lang)
            if canonical_title and canonical_title.lower() != clean_entity.lower():
                wiki_data = await cls._resolve_wikipedia_summary(canonical_title, lang=lang)

        # Tier 2 : Fallback Wikipedia English
        if not wiki_data and lang != "en":
            wiki_data = await cls._resolve_wikipedia_summary(clean_entity, lang="en")
            if not wiki_data:
                en_canonical = await cls._resolve_wikipedia_opensearch(clean_entity, lang="en")
                if en_canonical:
                    wiki_data = await cls._resolve_wikipedia_summary(en_canonical, lang="en")

        # Tier 3 : Fallback Wikimedia Commons API
        if not wiki_data:
            commons_data = await cls._resolve_wikimedia_commons(clean_entity)
            if commons_data:
                wiki_data = commons_data
                source_name = commons_data.get("source_name", "Wikimedia Commons")

        if not wiki_data:
            return None

        # Extraction des caractéristiques de l'image
        orig = wiki_data.get("originalimage") or {}
        thumb = wiki_data.get("thumbnail") or {}

        image_url = orig.get("source") or thumb.get("source")
        if not image_url:
            return None

        thumbnail_url = thumb.get("source") or image_url
        width = int(orig.get("width") or thumb.get("width") or 1920)
        height = int(orig.get("height") or thumb.get("height") or 1080)

        title = wiki_data.get("title") or clean_entity.title()
        description = wiki_data.get("extract") or wiki_data.get("description") or f"Visuel haute résolution de {title}."
        if len(description) > 280:
            description = description[:277] + "..."

        content_urls = wiki_data.get("content_urls", {})
        source_url = (
            content_urls.get("desktop", {}).get("page")
            or f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
        )

        badge = cls._compute_badge(width, height)

        result_payload = {
            "type": "visual_card",
            "title": title,
            "description": description,
            "image_url": image_url,
            "thumbnail_url": thumbnail_url,
            "source": source_name,
            "source_url": source_url,
            "dimensions": {
                "width": width,
                "height": height
            },
            "badge": badge
        }

        # Mise en cache
        cls._cache[cache_key] = (now, result_payload)
        return result_payload

    @classmethod
    async def enrich_with_visuals(cls, text_or_query: str, lang: str = "fr") -> List[Dict[str, Any]]:
        """
        Analyse le texte, extrait les entités visuelles pertinentes et génère
        la liste des cartes visuelles Liquid Glass.
        """
        entities = cls.extract_visual_entities(text_or_query)

        # Si aucune entité n'a été extraite via dictionnaire/regex, et que la requête est courte et ciblée,
        # tester la requête elle-même comme entité potentielle.
        if not entities:
            cleaned = cls._normalize_text(text_or_query)
            # Retirer d'éventuels préfixes de commande
            cleaned = re.sub(r"^(?:peux-tu\s+me\s+montrer|montre-moi|affiche|photo\s+de|image\s+de|cherche\s+l'image\s+de)\s+", "", cleaned)
            words = cleaned.split()
            if 1 <= len(words) <= 5 and not any(w in cleaned for w in ["bonjour", "salut", "comment", "pourquoi", "météo", "briefing"]):
                entities = [cleaned.title()]

        if not entities:
            return []

        # Recherche concurrente pour les entités extraites (maximum 2 pour éviter l'encombrement)
        tasks = [cls.search_visual_entity(ent, lang=lang) for ent in entities[:2]]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        cards: List[Dict[str, Any]] = []
        for r in results:
            if isinstance(r, dict) and r.get("image_url"):
                cards.append(r)

        return cards

    # --- PONTS SYNCHRONES ROBUSTES ---

    @classmethod
    def search_visual_entity_sync(cls, entity: str, lang: str = "fr") -> Optional[Dict[str, Any]]:
        """Pont synchrone vers search_visual_entity pour contextes sans await."""
        coro = cls.search_visual_entity(entity, lang=lang)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    return pool.submit(asyncio.run, coro).result()
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            return asyncio.run(coro)

    @classmethod
    def enrich_with_visuals_sync(cls, text_or_query: str, lang: str = "fr") -> List[Dict[str, Any]]:
        """Pont synchrone vers enrich_with_visuals pour contextes sans await."""
        coro = cls.enrich_with_visuals(text_or_query, lang=lang)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    return pool.submit(asyncio.run, coro).result()
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            return asyncio.run(coro)
