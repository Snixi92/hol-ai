"""
Moteur de Recherche Universel & Scraping Web Illimité (OmniSearch & Web Intelligence).
Permet à HoL AI de chercher sur TOUT INTERNET sans se limiter à une seule base :
- Neuf & Boutiques Spécialisées : Sephora, Nocibé, Fnac, Darty, Boulanger, Amazon, Cdiscount, Notino, etc.
- Occasion & Reconditionné : Leboncoin, Vinted, Back Market, Rakuten, eBay, Recommerce.
- Qualification Interactive : Détection des demandes ouvertes et génération de questions / chips interactifs.
"""
import re
import urllib.parse
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("hol_ai.omni_scraper")


class OmniScraperService:
    CATEGORIES = {
        "BEAUTY": [
            "maquillage", "palette", "crème", "creme", "fond de teint", "fard", "fards",
            "rouge a levre", "rouge à lèvres", "mascara", "sérum", "serum", "beauté", "beaute",
            "parfum", "cosmétique", "cosmetique", "soin", "peau", "anti-âge", "anti-rides",
            "blush", "contouring", "highlighter", "pinceau", "eyeliner", "lotion", "hydratant",
            "hydratante", "nettoyant", "shampooing", "shampoing"
        ],
        "TECH": [
            "pc", "ordinateur", "laptop", "tel", "téléphone", "telephone", "smartphone", "iphone",
            "samsung", "xiaomi", "pixel", "gpu", "carte graphique", "rtx", "ps5", "console",
            "switch", "xbox", "écran", "ecran", "tablette", "ipad", "écouteurs", "ecouteurs",
            "casque", "macbook", "airpods", "montre connectée", "smartwatch", "processeur", "ssd"
        ],
        "FASHION": [
            "vêtement", "vetement", "vêtements", "vetements", "sweat", "hoodie", "veste", "manteau",
            "robe", "pantalon", "jean", "sneakers", "baskets", "chaussures", "chaussure", "sac",
            "t-shirt", "pull", "blouson", "costume"
        ],
        "HOME_APPLIANCES": [
            "aspirateur", "robot", "lave-linge", "machine a laver", "frigo", "réfrigérateur",
            "machine à café", "cafetière", "meuble", "canapé", "lit", "matelas", "bricolage",
            "outillage", "perceuse", "tondeuse", "four", "micro-onde"
        ]
    }

    @classmethod
    def detect_category(cls, text: str) -> str:
        """Détecte la catégorie produit à partir du texte."""
        t = str(text or "").lower()
        for cat, keywords in cls.CATEGORIES.items():
            if any(re.search(rf"\b{re.escape(k)}\b", t) or k in t for k in keywords):
                return cat
        return "GENERAL"

    SPECIFIC_QUALIFIERS = [
        "cerave", "la roche posay", "huda", "nyx", "kiko", "too faced", "fenty", "dior", "chanel",
        "l'oreal", "garnier", "nivea", "avene", "avène", "bioderma", "the ordinary",
        "apple", "iphone", "samsung", "xiaomi", "asus", "lenovo", "dell", "hp", "acer", "macbook",
        "sony", "nintendo", "playstation", "xbox",
        "rtx", "gtx", "intel", "ryzen", "oled", "4k", "144hz", "512go", "1to", "16go", "32go",
        "xr", "xs", "11", "12", "13", "14", "15", "16", "se", "4060", "4070", "4080", "5060",
        "m1", "m2", "m3", "m4",
        "peau sèche", "peau seche", "peau grasse", "peau mixte", "spf", "acide hyaluronique",
        "retinol", "nude", "rose quartz", "airpods"
    ]

    GENERIC_TRIGGERS = [
        "crème", "creme", "palette", "maquillage", "pc", "ordinateur", "laptop",
        "téléphone", "telephone", "tel", "smartphone", "montre", "sneakers", "baskets",
        "parfum", "sac", "aspirateur", "casque", "écouteurs", "ecouteurs"
    ]

    @classmethod
    def is_ambiguous_or_open(cls, query: str) -> bool:
        """
        Détermine si la requête utilisateur est ouverte / imprécise et mérite des questions
        de qualification (ex: 'trouve moi une crème', 'palette de maquillage', 'un pc', 'un tel').
        """
        ql = str(query or "").strip().lower()
        has_trigger = any(re.search(rf"\b{re.escape(t)}\b", ql) or t in ql for t in cls.GENERIC_TRIGGERS)
        if not has_trigger:
            return False

        has_qualifier = any(qword in ql for qword in cls.SPECIFIC_QUALIFIERS)
        return not has_qualifier

    @classmethod
    def generate_interactive_questions(cls, query: str, category: str) -> Dict[str, Any]:
        """Génère les questions interactives et les chips cliquables rapides."""
        q_lower = str(query or "").lower()

        if category == "BEAUTY":
            if any(k in q_lower for k in ["crème", "creme", "soin", "peau"]):
                return {
                    "title": "🧴 Précisions pour cibler la crème idéale sur tout le Web",
                    "questions": [
                        "Quel est ton type de peau (sèche, mixte, grasse ou sensible) ?",
                        "Préfères-tu une crème hydratante légère de jour (avec SPF) ou un soin riche de nuit ?",
                        "Quel est ton budget : parapharmacie accessible (CeraVe, La Roche-Posay ~12€) ou soin premium (Sephora) ?"
                    ],
                    "quick_chips": [
                        {"label": "🌵 Peau très sèche & déshydratée", "query": "crème hydratante peau très sèche et sensible"},
                        {"label": "💧 Peau normale à mixte", "query": "crème hydratante visage peau mixte légère"},
                        {"label": "✨ Peau grasse (Effet Matifiant)", "query": "crème matifiante peau grasse sans huile"},
                        {"label": "☀️ Avec protection SPF", "query": "crème hydratante visage jour avec SPF"},
                        {"label": "🏷️ Parapharmacie CeraVe (< 15€)", "query": "crème hydratante visage cerave pas cher"},
                        {"label": "💎 Soin Expert Sephora", "query": "crème hydratante visage premium sephora"}
                    ]
                }
            else:
                return {
                    "title": "💄 Précisions pour ta palette de maquillage sur tout le Web",
                    "questions": [
                        "Recherches-tu une palette pour les yeux (fards à paupières) ou pour le teint (blush, contouring, highlighter) ?",
                        "Quel style de teintes préfères-tu : nudes / neutres pour le quotidien ou couleurs vibrantes / irisées ?",
                        "Tu cherches du neuf scellé (Sephora, Nocibé) ou des affaires d'occasion / neuves sous blister sur Vinted ?"
                    ],
                    "quick_chips": [
                        {"label": "👁️ Fards Yeux Nude & Chauds", "query": "palette fards à paupières nude teintes chaudes"},
                        {"label": "🌈 Fards Colorés & Pailletés", "query": "palette fards yeux colorés pigmentés"},
                        {"label": "✨ Palette Teint (Blush & Glow)", "query": "palette teint blush highlighter contouring"},
                        {"label": "🏷️ Petit budget (< 20€)", "query": "palette maquillage pas cher drugstore nyx kiko"},
                        {"label": "👑 Marque Pro (Huda / Too Faced)", "query": "palette fards à paupières huda beauty sephora"},
                        {"label": "♻️ Bonnes affaires Vinted", "query": "palette maquillage neuve sur vinted"}
                    ]
                }

        elif category == "TECH":
            if any(k in q_lower for k in ["pc", "laptop", "ordinateur"]):
                return {
                    "title": "💻 Précisions pour trouver le PC portable parfait sur le Web",
                    "questions": [
                        "Quel sera ton usage principal : Gaming (carte RTX), Études / Bureautique, ou Montage / Création 3D ?",
                        "Préfères-tu du neuf garanti ou du reconditionné certifié (Back Market, Leboncoin) pour payer moins cher ?",
                        "Quelle est ta limite de budget ?"
                    ],
                    "quick_chips": [
                        {"label": "🎮 Gaming avec GPU RTX", "query": "pc portable gamer rtx le moins cher"},
                        {"label": "💼 Bureautique & Études (Léger & Autonome)", "query": "pc portable bureautique rapide léger et autonome"},
                        {"label": "♻️ Reconditionné garanti (Back Market)", "query": "pc portable reconditionné garantie back market"},
                        {"label": "🏷️ Occasion Leboncoin", "query": "pc portable occasion leboncoin bon état"},
                        {"label": "💰 Budget < 500€", "query": "pc portable performant moins de 500 euros"},
                        {"label": "💰 Budget 800€ - 1000€", "query": "pc portable gaming budget 800 à 1000 euros"}
                    ]
                }
            else:
                return {
                    "title": "📱 Précisions pour choisir ton smartphone sur le Web",
                    "questions": [
                        "Tu préfères Apple iPhone (iOS) ou Android (Samsung, Xiaomi, Google Pixel) ?",
                        "Préfères-tu du neuf ou du reconditionné garanti / occasion (Leboncoin, Back Market) ?",
                        "Quelle est ta tranche de prix cible ?"
                    ],
                    "quick_chips": [
                        {"label": "🍎 iPhone (iOS)", "query": "iphone le moins cher reconditionné"},
                        {"label": "🤖 Android (Samsung / Xiaomi)", "query": "smartphone android rapport qualité prix"},
                        {"label": "♻️ Back Market (Garanti 1 an)", "query": "smartphone reconditionné back market garanti"},
                        {"label": "🏷️ Leboncoin (Occasion)", "query": "smartphone occasion leboncoin"},
                        {"label": "💰 Moins de 200€", "query": "smartphone pas cher moins de 200 euros"},
                        {"label": "💰 Moins de 400€", "query": "smartphone milieu de gamme moins de 400 euros"}
                    ]
                }

        # Catégorie générale
        return {
            "title": f"🔍 Précisions pour cibler '{query}' sur tout le Web",
            "questions": [
                "Recherches-tu ce produit neuf en boutique ou en occasion / reconditionné (Leboncoin, Vinted, Back Market) ?",
                "As-tu une marque spécifique ou un budget maximum en tête ?"
            ],
            "quick_chips": [
                {"label": "🆕 Neuf avec garantie officielle", "query": f"{query} neuf officiel"},
                {"label": "♻️ Occasion / Seconde main (Leboncoin)", "query": f"{query} occasion leboncoin"},
                {"label": "🏷️ Le moins cher possible", "query": f"{query} le moins cher bon plan"},
                {"label": "⚡ Comparer tous les marchands", "query": f"{query} comparateur prix"}
            ]
        }

    @classmethod
    def generate_all_platform_links(cls, product_name: str, category: str) -> Dict[str, Any]:
        """
        Génère les liens de recherche directs vers l'ensemble des plateformes majeures du web,
        séparées entre Neuf/Retail et Occasion/Reconditionné.
        """
        clean_q = re.sub(r"(trouve|cherche|achète|pour moi|pas cher|pas chère|le moins cher|le moin chère)", "", product_name, flags=re.IGNORECASE).strip()
        encoded = urllib.parse.quote_plus(clean_q or product_name)

        # 1. Plateformes Occasion & Seconde Main (Toujours incluses !)
        occasion_platforms = [
            {
                "platform": "Leboncoin",
                "badge": "Occasion Particuliers & Pros",
                "color": "#ea580c",
                "icon": "🟠",
                "url": f"https://www.leboncoin.fr/recherche?text={encoded}"
            },
            {
                "platform": "Vinted",
                "badge": "Mode, Beauté & Seconde Main",
                "color": "#06b6d4",
                "icon": "👗",
                "url": f"https://www.vinted.fr/catalog?search_text={encoded}"
            },
            {
                "platform": "Back Market",
                "badge": "Reconditionné Garanti 1 an",
                "color": "#16a34a",
                "icon": "♻️",
                "url": f"https://www.backmarket.fr/fr-fr/search?q={encoded}"
            },
            {
                "platform": "Rakuten",
                "badge": "Neuf & Occasion Garanti",
                "color": "#dc2626",
                "icon": "🔴",
                "url": f"https://fr.shopping.rakuten.com/search/{encoded}"
            },
            {
                "platform": "eBay.fr",
                "badge": "Achat direct & Enchères",
                "color": "#eab308",
                "icon": "🏷️",
                "url": f"https://www.ebay.fr/sch/i.html?_nkw={encoded}"
            }
        ]

        # 2. Boutiques Retail Spécialisées selon la catégorie
        retail_platforms = []

        if category == "BEAUTY":
            retail_platforms = [
                {
                    "platform": "Sephora",
                    "badge": "Boutique Officielle Beauté",
                    "color": "#111827",
                    "icon": "💄",
                    "url": f"https://www.sephora.fr/recherche/?q={encoded}"
                },
                {
                    "platform": "Nocibé",
                    "badge": "Parfumerie & Soins",
                    "color": "#e11d48",
                    "icon": "✨",
                    "url": f"https://www.nocibe.fr/recherche?q={encoded}"
                },
                {
                    "platform": "Marionnaud",
                    "badge": "Institut & Cosmétiques",
                    "color": "#9333ea",
                    "icon": "🌸",
                    "url": f"https://www.marionnaud.fr/search?text={encoded}"
                },
                {
                    "platform": "Amazon Beauté",
                    "badge": "Livraison Express Prime",
                    "color": "#059669",
                    "icon": "📦",
                    "url": f"https://www.amazon.fr/s?k={encoded}"
                }
            ]
        elif category == "TECH":
            retail_platforms = [
                {
                    "platform": "Amazon.fr",
                    "badge": "Stock & Prime 1J",
                    "color": "#059669",
                    "icon": "📦",
                    "url": f"https://www.amazon.fr/s?k={encoded}"
                },
                {
                    "platform": "Cdiscount",
                    "badge": "Marketplace France / CDAV",
                    "color": "#0284c7",
                    "icon": "🛒",
                    "url": f"https://www.cdiscount.com/search/10/{encoded}.html"
                },
                {
                    "platform": "Fnac.com",
                    "badge": "Retrait 1h en magasin",
                    "color": "#d97706",
                    "icon": "🟡",
                    "url": f"https://www.fnac.com/SearchResult/ResultList.aspx?Search={encoded}"
                },
                {
                    "platform": "Darty",
                    "badge": "Garantie & SAV France",
                    "color": "#dc2626",
                    "icon": "🔴",
                    "url": f"https://www.darty.com/nav/recherche/{encoded}.html"
                },
                {
                    "platform": "Boulanger",
                    "badge": "Expertise & Stock Magasin",
                    "color": "#ea580c",
                    "icon": "🟠",
                    "url": f"https://www.boulanger.com/resultats?tr={encoded}"
                }
            ]
        elif category == "FASHION":
            retail_platforms = [
                {
                    "platform": "Zalando",
                    "badge": "Mode & Retours Gratuits",
                    "color": "#f97316",
                    "icon": "👟",
                    "url": f"https://www.zalando.fr/catalogue/?q={encoded}"
                },
                {
                    "platform": "ASOS",
                    "badge": "Tendances & Vêtements",
                    "color": "#111827",
                    "icon": "👕",
                    "url": f"https://www.asos.com/fr/search/?q={encoded}"
                },
                {
                    "platform": "Hacoo",
                    "badge": "Dropshipping & Tendance",
                    "color": "#ec4899",
                    "icon": "🔥",
                    "url": f"https://www.hacoo.app/search?q={encoded}"
                }
            ]
        else:
            retail_platforms = [
                {
                    "platform": "Amazon.fr",
                    "badge": "Grand Magasin Web",
                    "color": "#059669",
                    "icon": "📦",
                    "url": f"https://www.amazon.fr/s?k={encoded}"
                },
                {
                    "platform": "Cdiscount",
                    "badge": "E-Commerce France",
                    "color": "#0284c7",
                    "icon": "🛒",
                    "url": f"https://www.cdiscount.com/search/10/{encoded}.html"
                },
                {
                    "platform": "Google Shopping",
                    "badge": "Comparateur Tous Marchands",
                    "color": "#4285f4",
                    "icon": "🌐",
                    "url": f"https://www.google.com/search?tbm=shop&q={encoded}"
                },
                {
                    "platform": "Idealo.fr",
                    "badge": "Comparateur Prix & Historique",
                    "color": "#0284c7",
                    "icon": "📊",
                    "url": f"https://www.idealo.fr/preise/recherche.html?q={encoded}"
                }
            ]

        return {
            "retail": retail_platforms,
            "occasion": occasion_platforms
        }

    _scrape_cache: Dict[str, List[Dict[str, str]]] = {}

    @classmethod
    def live_web_scrape(cls, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Scrape le web en direct via DuckDuckGo Search (DDGS) pour extraire de vraies annonces
        et résultats marchands réels avec titre, URL et extrait de prix.
        Muni d'un cache mémoire pour l'absorption des pics de charge et requêtes répétées.
        """
        clean_q = re.sub(r"(trouve|cherche|achète|pour moi|le moins cher|le moin chère)", "", query, flags=re.IGNORECASE).strip()
        cache_key = f"{clean_q.lower()}_{max_results}"
        if not hasattr(cls, "_scrape_cache"):
            cls._scrape_cache = {}
        if cache_key in cls._scrape_cache:
            return list(cls._scrape_cache[cache_key])

        search_terms = f"{clean_q} prix acheter neuf occasion"

        extracted = []
        try:
            try:
                from duckduckgo_search import DDGS
            except ImportError:
                try:
                    from ddgs import DDGS
                except ImportError:
                    DDGS = None
            with DDGS(timeout=3) as ddgs:
                results = list(ddgs.text(search_terms, region="fr-fr", max_results=max_results))
                for r in results:
                    title = r.get("title", "")
                    href = r.get("href", "")
                    snippet = r.get("body", "")

                    if not href or not title:
                        continue

                    # Extraire le nom de domaine propre
                    domain = ""
                    try:
                        domain = urllib.parse.urlparse(href).netloc.replace("www.", "")
                    except Exception:
                        pass

                    # Détection d'un prix dans l'extrait
                    price_match = re.search(r"(\d+[\,\.]\d{2}|\d+)\s*€", snippet)
                    found_price = price_match.group(0) if price_match else None

                    extracted.append({
                        "title": title,
                        "url": href,
                        "domain": domain,
                        "snippet": snippet[:150] + "..." if len(snippet) > 150 else snippet,
                        "estimated_price": found_price
                    })
        except Exception as e:
            logger.warning(f"Erreur lors du scraping direct DDGS : {e}")

        if len(cls._scrape_cache) > 500:
            cls._scrape_cache = dict(list(cls._scrape_cache.items())[-250:])
        cls._scrape_cache[cache_key] = extracted
        return extracted

    @classmethod
    def hunt_omni_product(cls, query: str, context_product: Optional[str] = None) -> Dict[str, Any]:
        """
        Point d'entrée omni-canal :
        1. Détecte la catégorie (Beauté, Tech, Mode, Maison, Général).
        2. Détecte si une qualification / clarification interactive est souhaitable.
        3. Génère les liens directs pour TOUTES les plateformes (Neuf ET Occasion).
        4. Exécute un scraping web réel multi-sources.
        """
        effective_query = query
        if not effective_query and context_product:
            effective_query = context_product

        category = cls.detect_category(effective_query)
        is_ambiguous = cls.is_ambiguous_or_open(effective_query)
        platforms_map = cls.generate_all_platform_links(effective_query, category)
        live_offers = cls.live_web_scrape(effective_query, max_results=4)

        clarification_data = None
        if is_ambiguous:
            clarification_data = cls.generate_interactive_questions(effective_query, category)

        # Déterminer si l'utilisateur demandait expressément de l'occasion
        wants_occasion = any(w in effective_query.lower() for w in ["occasion", "reconditionné", "reconditionne", "seconde main", "vinted", "leboncoin", "backmarket", "back market"])

        market_insight = (
            f"🌐 Scan en direct sur tout le Web (Neuf, Reconditionné et Occasion) pour '{effective_query}'. "
            f"Accès instantané à Leboncoin, Vinted, Back Market et aux boutiques officielles."
        )

        return {
            "source": "OMNI_WEB_INTELLIGENCE",
            "is_omni_search": True,
            "is_clarification_needed": is_ambiguous,
            "interactive_clarification": clarification_data,
            "product": effective_query.title(),
            "category": category,
            "wants_occasion": wants_occasion,
            "retail_platforms": platforms_map["retail"],
            "occasion_platforms": platforms_map["occasion"],
            "live_web_offers": live_offers,
            "market_insight": market_insight,
            "watch_status": "OMNI_MONITORING_ACTIVE",
            "requires_user_approval": False
        }
