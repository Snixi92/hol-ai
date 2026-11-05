"""
In-Memory Tool Registry and Inverted Search Index for HoL AI.
Indexes 1,079 verified no-auth public APIs across 49 categories.
Provides sub-millisecond retrieval (<1ms) and sub-50ms startup loading.
Features multilingual aliasing for French, Moroccan Darija, Spanish, and English.
Includes curated executable schemas for high-utility APIs (Weather, Crypto, Finance, etc.).
"""

import json
import logging
import os
import re
import threading
import time
import unicodedata
from typing import Any, Dict, List, Optional, Set, Tuple

from src.tools.models import (
    ParameterLocation,
    ToolAuthType,
    ToolDefinition,
    ToolExecutionType,
    ToolParameter,
    ToolQueryResult,
)

logger = logging.getLogger("hol_ai.tools.public_registry")

# Multilingual stopwords across English, French, and Spanish
STOPWORDS: Set[str] = {
    # English
    "the", "a", "an", "and", "or", "of", "for", "in", "on", "at", "to", "from",
    "by", "with", "about", "is", "are", "was", "were", "it", "this", "that",
    "be", "as", "into", "all", "any", "api", "apis", "free", "data", "service",
    # French
    "le", "la", "les", "de", "du", "des", "un", "une", "et", "ou", "pour",
    "dans", "sur", "en", "par", "avec", "est", "sont", "ce", "cette", "ces",
    "qui", "que", "aux", "donnees", "service", "gratuit", "ligne",
    # Spanish
    "el", "la", "los", "las", "un", "una", "unos", "unas", "y", "o", "por",
    "para", "en", "con", "es", "son", "del", "al", "que", "datos", "servicio"
}

# Multilingual category & keyword aliases
# Maps language-specific terms (FR, Darija, ES, EN) to primary categories and query tokens
MULTILINGUAL_ALIASES: Dict[str, Dict[str, Any]] = {
    # Weather / Météo / Taqs
    "meteo": {"category": "Weather", "tokens": ["weather", "forecast", "temperature", "climate"], "boost_tools": ["weather_open_meteo"]},
    "temperature": {"category": "Weather", "tokens": ["weather", "forecast", "meteo", "degrees"], "boost_tools": ["weather_open_meteo"]},
    "pluie": {"category": "Weather", "tokens": ["weather", "rain", "precipitation", "meteo"], "boost_tools": ["weather_open_meteo"]},
    "climat": {"category": "Weather", "tokens": ["weather", "climate", "meteo", "atmosphere"], "boost_tools": ["weather_open_meteo"]},
    "prevision": {"category": "Weather", "tokens": ["weather", "forecast", "meteo"], "boost_tools": ["weather_open_meteo"]},
    "previsions": {"category": "Weather", "tokens": ["weather", "forecast", "meteo"], "boost_tools": ["weather_open_meteo"]},
    "vent": {"category": "Weather", "tokens": ["weather", "wind", "speed"], "boost_tools": ["weather_open_meteo"]},
    "taqs": {"category": "Weather", "tokens": ["weather", "forecast", "climate"], "boost_tools": ["weather_open_meteo"]},
    "jaw": {"category": "Weather", "tokens": ["weather", "forecast", "climate"], "boost_tools": ["weather_open_meteo"]},
    "shta": {"category": "Weather", "tokens": ["weather", "rain", "forecast"], "boost_tools": ["weather_open_meteo"]},
    "chta": {"category": "Weather", "tokens": ["weather", "rain", "forecast"], "boost_tools": ["weather_open_meteo"]},
    "tiempo": {"category": "Weather", "tokens": ["weather", "forecast", "climate"], "boost_tools": ["weather_open_meteo"]},
    "pronostico": {"category": "Weather", "tokens": ["weather", "forecast"], "boost_tools": ["weather_open_meteo"]},

    # Cryptocurrency / Crypto / Flous
    "crypto": {"category": "Cryptocurrency", "tokens": ["cryptocurrency", "bitcoin", "blockchain", "market", "price"], "boost_tools": ["crypto_coingecko"]},
    "cryptos": {"category": "Cryptocurrency", "tokens": ["cryptocurrency", "bitcoin", "ethereum", "solana"], "boost_tools": ["crypto_coingecko"]},
    "cryptomonnaie": {"category": "Cryptocurrency", "tokens": ["cryptocurrency", "bitcoin", "ethereum"], "boost_tools": ["crypto_coingecko"]},
    "cryptomonnaies": {"category": "Cryptocurrency", "tokens": ["cryptocurrency", "bitcoin", "ethereum"], "boost_tools": ["crypto_coingecko"]},
    "cours": {"category": "Cryptocurrency", "tokens": ["price", "market", "currency", "quote"], "boost_tools": ["crypto_coingecko", "finance_exchangerate_api"]},
    "prix": {"category": "Cryptocurrency", "tokens": ["price", "market", "quote", "rate"], "boost_tools": ["crypto_coingecko", "finance_exchangerate_api"]},
    "cotation": {"category": "Cryptocurrency", "tokens": ["price", "quote", "market"], "boost_tools": ["crypto_coingecko"]},
    "bitcoin": {"category": "Cryptocurrency", "tokens": ["crypto", "cryptocurrency", "btc", "market"], "boost_tools": ["crypto_coingecko"]},
    "btc": {"category": "Cryptocurrency", "tokens": ["crypto", "cryptocurrency", "bitcoin"], "boost_tools": ["crypto_coingecko"]},
    "ethereum": {"category": "Cryptocurrency", "tokens": ["crypto", "cryptocurrency", "eth"], "boost_tools": ["crypto_coingecko"]},
    "eth": {"category": "Cryptocurrency", "tokens": ["crypto", "cryptocurrency", "ethereum"], "boost_tools": ["crypto_coingecko"]},
    "solana": {"category": "Cryptocurrency", "tokens": ["crypto", "cryptocurrency", "sol"], "boost_tools": ["crypto_coingecko"]},
    "flous": {"category": "Finance", "tokens": ["finance", "money", "currency", "exchange", "crypto"], "boost_tools": ["crypto_coingecko", "finance_exchangerate_api"]},
    "chhal": {"category": "Finance", "tokens": ["price", "rate", "cost", "currency"], "boost_tools": ["crypto_coingecko", "finance_exchangerate_api"]},
    "cripto": {"category": "Cryptocurrency", "tokens": ["cryptocurrency", "bitcoin", "blockchain"], "boost_tools": ["crypto_coingecko"]},
    "criptomoneda": {"category": "Cryptocurrency", "tokens": ["cryptocurrency", "bitcoin"], "boost_tools": ["crypto_coingecko"]},

    # Finance & Currency Exchange / Sarf / Devises
    "devises": {"category": "Currency Exchange", "tokens": ["currency", "exchange", "rate", "forex"], "boost_tools": ["finance_exchangerate_api"]},
    "devise": {"category": "Currency Exchange", "tokens": ["currency", "exchange", "rate"], "boost_tools": ["finance_exchangerate_api"]},
    "taux": {"category": "Currency Exchange", "tokens": ["rate", "exchange", "currency"], "boost_tools": ["finance_exchangerate_api"]},
    "change": {"category": "Currency Exchange", "tokens": ["exchange", "currency", "forex"], "boost_tools": ["finance_exchangerate_api"]},
    "bourse": {"category": "Finance", "tokens": ["stock", "market", "shares", "finance"], "boost_tools": ["finance_exchangerate_api"]},
    "actions": {"category": "Finance", "tokens": ["stock", "shares", "equity", "market"], "boost_tools": ["finance_exchangerate_api"]},
    "monnaie": {"category": "Currency Exchange", "tokens": ["currency", "money", "exchange"], "boost_tools": ["finance_exchangerate_api"]},
    "euro": {"category": "Currency Exchange", "tokens": ["currency", "exchange", "eur"], "boost_tools": ["finance_exchangerate_api"]},
    "dollar": {"category": "Currency Exchange", "tokens": ["currency", "exchange", "usd"], "boost_tools": ["finance_exchangerate_api"]},
    "dirham": {"category": "Currency Exchange", "tokens": ["currency", "exchange", "mad"], "boost_tools": ["finance_exchangerate_api"]},
    "sarf": {"category": "Currency Exchange", "tokens": ["currency", "exchange", "rate", "money"], "boost_tools": ["finance_exchangerate_api"]},
    "divisa": {"category": "Currency Exchange", "tokens": ["currency", "exchange", "forex"], "boost_tools": ["finance_exchangerate_api"]},
    "divisas": {"category": "Currency Exchange", "tokens": ["currency", "exchange", "forex"], "boost_tools": ["finance_exchangerate_api"]},
    "finanzas": {"category": "Finance", "tokens": ["finance", "money", "market"], "boost_tools": ["finance_exchangerate_api"]},

    # Jokes & Entertainment / Blagues / Nokat
    "blague": {"category": "Entertainment", "tokens": ["joke", "humor", "funny", "pun"], "boost_tools": ["entertainment_jokeapi"]},
    "blagues": {"category": "Entertainment", "tokens": ["joke", "jokes", "humor", "funny"], "boost_tools": ["entertainment_jokeapi"]},
    "humour": {"category": "Entertainment", "tokens": ["humor", "joke", "funny", "comedy"], "boost_tools": ["entertainment_jokeapi"]},
    "drole": {"category": "Entertainment", "tokens": ["funny", "humor", "joke"], "boost_tools": ["entertainment_jokeapi"]},
    "rire": {"category": "Entertainment", "tokens": ["laugh", "joke", "humor"], "boost_tools": ["entertainment_jokeapi"]},
    "nokat": {"category": "Entertainment", "tokens": ["joke", "jokes", "humor", "funny"], "boost_tools": ["entertainment_jokeapi"]},
    "nokta": {"category": "Entertainment", "tokens": ["joke", "humor", "funny"], "boost_tools": ["entertainment_jokeapi"]},
    "dahk": {"category": "Entertainment", "tokens": ["joke", "humor", "funny"], "boost_tools": ["entertainment_jokeapi"]},
    "chiste": {"category": "Entertainment", "tokens": ["joke", "humor", "funny"], "boost_tools": ["entertainment_jokeapi"]},
    "chistes": {"category": "Entertainment", "tokens": ["joke", "jokes", "humor"], "boost_tools": ["entertainment_jokeapi"]},

    # Facts & Trivia / Faits
    "fait": {"category": "Animals", "tokens": ["fact", "facts", "trivia", "knowledge"], "boost_tools": ["animals_catfact"]},
    "faits": {"category": "Animals", "tokens": ["facts", "fact", "trivia", "knowledge"], "boost_tools": ["animals_catfact"]},
    "anecdote": {"category": "Animals", "tokens": ["fact", "trivia", "curiosity"], "boost_tools": ["animals_catfact"]},
    "anecdotes": {"category": "Animals", "tokens": ["facts", "trivia", "curiosity"], "boost_tools": ["animals_catfact"]},
    "hecho": {"category": "Animals", "tokens": ["fact", "trivia", "data"], "boost_tools": ["animals_catfact"]},
    "hechos": {"category": "Animals", "tokens": ["facts", "trivia", "data"], "boost_tools": ["animals_catfact"]},

    # Animals / Animaux / Qitat
    "animaux": {"category": "Animals", "tokens": ["animals", "animal", "pets", "wildlife"], "boost_tools": ["animals_catfact"]},
    "animal": {"category": "Animals", "tokens": ["animal", "animals", "pet", "species"], "boost_tools": ["animals_catfact"]},
    "chat": {"category": "Animals", "tokens": ["cat", "cats", "feline", "facts"], "boost_tools": ["animals_catfact"]},
    "chats": {"category": "Animals", "tokens": ["cats", "cat", "feline", "facts"], "boost_tools": ["animals_catfact"]},
    "chien": {"category": "Animals", "tokens": ["dog", "dogs", "canine"], "boost_tools": ["animals_catfact"]},
    "chiens": {"category": "Animals", "tokens": ["dogs", "dog", "canine"], "boost_tools": ["animals_catfact"]},
    "qitta": {"category": "Animals", "tokens": ["cat", "cats", "animals"], "boost_tools": ["animals_catfact"]},
    "qitat": {"category": "Animals", "tokens": ["cats", "cat", "animals"], "boost_tools": ["animals_catfact"]},
    "mouch": {"category": "Animals", "tokens": ["cat", "cats", "animals"], "boost_tools": ["animals_catfact"]},
    "gato": {"category": "Animals", "tokens": ["cat", "cats", "feline"], "boost_tools": ["animals_catfact"]},
    "gatos": {"category": "Animals", "tokens": ["cats", "cat", "feline"], "boost_tools": ["animals_catfact"]},
    "perro": {"category": "Animals", "tokens": ["dog", "dogs", "canine"], "boost_tools": ["animals_catfact"]},

    # Geocoding & Addresses / Géocodage / Kharieta
    "geocodage": {"category": "Geocoding", "tokens": ["geocoding", "address", "coordinates", "gps", "location"], "boost_tools": ["geocoding_adresse_data_gouv", "geocoding_nominatim"]},
    "geocoding": {"category": "Geocoding", "tokens": ["geocoding", "address", "coordinates", "location"], "boost_tools": ["geocoding_adresse_data_gouv", "geocoding_nominatim"]},
    "adresse": {"category": "Geocoding", "tokens": ["address", "geocoding", "location", "place"], "boost_tools": ["geocoding_adresse_data_gouv", "geocoding_nominatim"]},
    "adresses": {"category": "Geocoding", "tokens": ["address", "geocoding", "location"], "boost_tools": ["geocoding_adresse_data_gouv", "geocoding_nominatim"]},
    "coordonnees": {"category": "Geocoding", "tokens": ["coordinates", "gps", "latitude", "longitude"], "boost_tools": ["geocoding_adresse_data_gouv", "geocoding_nominatim"]},
    "gps": {"category": "Geocoding", "tokens": ["coordinates", "gps", "location", "geocoding"], "boost_tools": ["geocoding_adresse_data_gouv", "geocoding_nominatim"]},
    "carte": {"category": "Geocoding", "tokens": ["map", "maps", "openstreetmap", "geography"], "boost_tools": ["geocoding_nominatim"]},
    "ville": {"category": "Geocoding", "tokens": ["city", "address", "geocoding", "location"], "boost_tools": ["geocoding_adresse_data_gouv", "geocoding_nominatim"]},
    "kharieta": {"category": "Geocoding", "tokens": ["map", "location", "coordinates"], "boost_tools": ["geocoding_nominatim"]},
    "blassa": {"category": "Geocoding", "tokens": ["location", "place", "address"], "boost_tools": ["geocoding_nominatim"]},
    "mdina": {"category": "Geocoding", "tokens": ["city", "place", "location"], "boost_tools": ["geocoding_nominatim"]},
    "direccion": {"category": "Geocoding", "tokens": ["address", "geocoding", "location"], "boost_tools": ["geocoding_nominatim"]},
    "mapa": {"category": "Geocoding", "tokens": ["map", "geocoding", "location"], "boost_tools": ["geocoding_nominatim"]},

    # Health / Santé / Seha
    "sante": {"category": "Health", "tokens": ["health", "medical", "medicine", "doctor"], "boost_tools": []},
    "medical": {"category": "Health", "tokens": ["medical", "health", "hospital", "disease"], "boost_tools": []},
    "hopital": {"category": "Health", "tokens": ["hospital", "medical", "health"], "boost_tools": []},
    "medicament": {"category": "Health", "tokens": ["drug", "medicine", "pharmacy"], "boost_tools": []},
    "seha": {"category": "Health", "tokens": ["health", "medical", "medicine"], "boost_tools": []},
    "salud": {"category": "Health", "tokens": ["health", "medical", "medicine"], "boost_tools": []},

    # Sports & Fitness
    "sport": {"category": "Sports & Fitness", "tokens": ["sport", "sports", "football", "fitness"], "boost_tools": []},
    "sports": {"category": "Sports & Fitness", "tokens": ["sports", "sport", "football", "athletics"], "boost_tools": []},
    "football": {"category": "Sports & Fitness", "tokens": ["football", "soccer", "match", "league"], "boost_tools": []},
    "foot": {"category": "Sports & Fitness", "tokens": ["football", "soccer", "match"], "boost_tools": []},
    "kora": {"category": "Sports & Fitness", "tokens": ["football", "soccer", "sports"], "boost_tools": []},
    "deporte": {"category": "Sports & Fitness", "tokens": ["sport", "sports", "futbol"], "boost_tools": []},

    # Food & Drink / Nourriture / Makla
    "nourriture": {"category": "Food & Drink", "tokens": ["food", "recipes", "cooking", "nutrition"], "boost_tools": []},
    "recette": {"category": "Food & Drink", "tokens": ["recipe", "recipes", "food", "cooking"], "boost_tools": []},
    "recettes": {"category": "Food & Drink", "tokens": ["recipes", "recipe", "cooking", "food"], "boost_tools": []},
    "cuisine": {"category": "Food & Drink", "tokens": ["cooking", "food", "recipe"], "boost_tools": []},
    "makla": {"category": "Food & Drink", "tokens": ["food", "cooking", "meal"], "boost_tools": []},
    "comida": {"category": "Food & Drink", "tokens": ["food", "recipes", "meal"], "boost_tools": []},

    # Music / Musique
    "musique": {"category": "Music", "tokens": ["music", "songs", "artist", "album", "audio"], "boost_tools": []},
    "chanson": {"category": "Music", "tokens": ["song", "music", "lyrics"], "boost_tools": []},
    "chansons": {"category": "Music", "tokens": ["songs", "music", "lyrics"], "boost_tools": []},
    "moussiqa": {"category": "Music", "tokens": ["music", "songs", "artist"], "boost_tools": []},
    "musica": {"category": "Music", "tokens": ["music", "song", "artist"], "boost_tools": []},

    # News / Actualités / Akhbar
    "actualite": {"category": "News", "tokens": ["news", "articles", "press", "media"], "boost_tools": []},
    "actualites": {"category": "News", "tokens": ["news", "headlines", "articles"], "boost_tools": []},
    "nouvelles": {"category": "News", "tokens": ["news", "events", "press"], "boost_tools": []},
    "journal": {"category": "News", "tokens": ["news", "newspaper", "press"], "boost_tools": []},
    "akhbar": {"category": "News", "tokens": ["news", "press", "articles"], "boost_tools": []},
    "noticias": {"category": "News", "tokens": ["news", "articles", "press"], "boost_tools": []},

    # Books / Livres
    "livre": {"category": "Books", "tokens": ["books", "book", "author", "literature"], "boost_tools": []},
    "livres": {"category": "Books", "tokens": ["books", "literature", "author"], "boost_tools": []},
    "ktab": {"category": "Books", "tokens": ["book", "books", "author"], "boost_tools": []},
    "libro": {"category": "Books", "tokens": ["book", "books", "literature"], "boost_tools": []},
}


def normalize_string(text: str) -> str:
    """Normalize text using NFKD decomposition, strip combining accents, and lowercase."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.lower().strip()


def tokenize(text: str) -> List[str]:
    """Tokenize a string into normalized, non-stopword alphanumeric tokens."""
    norm = normalize_string(text)
    raw_tokens = re.findall(r"\b[a-z0-9_-]{2,}\b", norm)
    return [t for t in raw_tokens if t not in STOPWORDS]


class PublicApiRegistry:
    """
    In-memory registry and inverted index for 1,079 no-auth public APIs.
    Thread-safe singleton with sub-millisecond keyword and category search.
    """
    _instance: Optional["PublicApiRegistry"] = None
    _lock = threading.Lock()

    def __init__(self, data_path: Optional[str] = None) -> None:
        """Initialize the registry and build the in-memory inverted index."""
        self._lock = threading.RLock()
        self._tools: Dict[str, ToolDefinition] = {}
        self._tool_id_aliases: Dict[str, str] = {}
        self._categories: Dict[str, List[str]] = {}
        self._curated_tools: Dict[str, ToolDefinition] = {}
        self._inverted_index: Dict[str, Dict[str, float]] = {}
        self._load_time_ms: float = 0.0

        if data_path is None:
            # Default to services/core-engine/data/public_apis/parsed_apis.json
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            data_path = os.path.join(base_dir, "data", "public_apis", "parsed_apis.json")

        self._data_path = data_path
        self._load_and_index()

    @classmethod
    def get_instance(cls, data_path: Optional[str] = None) -> "PublicApiRegistry":
        """Thread-safe singleton accessor."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(data_path=data_path)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (mainly for test isolation)."""
        with cls._lock:
            cls._instance = None

    def _init_curated_tools(self) -> Dict[str, ToolDefinition]:
        """Define high-utility curated executable tools."""
        curated: Dict[str, ToolDefinition] = {}

        # 1. Open-Meteo (Weather)
        open_meteo = ToolDefinition(
            id="weather_open_meteo",
            name="Open-Meteo",
            category="Weather",
            description="Real-time meteorological forecast and current weather conditions by latitude/longitude coordinates (Open-Meteo API)",
            url="https://open-meteo.com/",
            endpoint_url="https://api.open-meteo.com/v1/forecast",
            http_method="GET",
            auth_type=ToolAuthType.NO_AUTH,
            execution_type=ToolExecutionType.DIRECT_REST,
            https_support=True,
            cors_support="Yes",
            is_curated=True,
            timeout_sec=5.0,
            cache_ttl_sec=300,
            parameters=[
                ToolParameter(
                    name="latitude",
                    type="number",
                    location=ParameterLocation.QUERY,
                    required=True,
                    default=48.8566,
                    description="Latitude coordinate (e.g. 48.8566 for Paris, 33.5731 for Casablanca)"
                ),
                ToolParameter(
                    name="longitude",
                    type="number",
                    location=ParameterLocation.QUERY,
                    required=True,
                    default=2.3522,
                    description="Longitude coordinate (e.g. 2.3522 for Paris, -7.5898 for Casablanca)"
                ),
                ToolParameter(
                    name="current",
                    type="string",
                    location=ParameterLocation.QUERY,
                    default="temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
                    description="Comma-separated current weather variables"
                ),
                ToolParameter(
                    name="hourly",
                    type="string",
                    location=ParameterLocation.QUERY,
                    default="temperature_2m,weather_code",
                    description="Comma-separated hourly variables"
                ),
                ToolParameter(
                    name="daily",
                    type="string",
                    location=ParameterLocation.QUERY,
                    default="weather_code,temperature_2m_max,temperature_2m_min",
                    description="Comma-separated daily variables"
                ),
                ToolParameter(
                    name="timezone",
                    type="string",
                    location=ParameterLocation.QUERY,
                    default="auto",
                    description="Timezone identifier, e.g. auto, Europe/Paris, Africa/Casablanca"
                ),
            ],
            tags=["weather", "meteo", "climat", "temperature", "forecast", "taqs", "jaw", "tiempo", "pluie", "prevision"]
        )
        curated["weather_open_meteo"] = open_meteo

        # 2. CoinGecko (Cryptocurrency)
        coingecko = ToolDefinition(
            id="crypto_coingecko",
            name="CoinGecko",
            category="Cryptocurrency",
            description="Real-time cryptocurrency prices, 24h market trends and volume from CoinGecko API",
            url="http://www.coingecko.com/api",
            endpoint_url="https://api.coingecko.com/api/v3/simple/price",
            http_method="GET",
            auth_type=ToolAuthType.NO_AUTH,
            execution_type=ToolExecutionType.DIRECT_REST,
            https_support=True,
            cors_support="Yes",
            is_curated=True,
            timeout_sec=5.0,
            cache_ttl_sec=120,
            parameters=[
                ToolParameter(
                    name="ids",
                    type="string",
                    location=ParameterLocation.QUERY,
                    required=True,
                    default="bitcoin,ethereum,solana",
                    description="Comma-separated crypto asset IDs: bitcoin, ethereum, solana, ripple, cardano"
                ),
                ToolParameter(
                    name="vs_currencies",
                    type="string",
                    location=ParameterLocation.QUERY,
                    required=True,
                    default="usd,eur",
                    description="Comma-separated target fiat currencies: usd, eur, gbp, mad"
                ),
                ToolParameter(
                    name="include_24hr_change",
                    type="string",
                    location=ParameterLocation.QUERY,
                    default="true",
                    description="Include 24h market price change percentage"
                ),
            ],
            tags=["crypto", "cryptocurrency", "bitcoin", "ethereum", "solana", "btc", "eth", "cours", "prix", "flous", "blockchain", "cotation"]
        )
        curated["crypto_coingecko"] = coingecko

        # 3. ExchangeRate-API (Currency Exchange / Finance / Forex)
        exchangerate = ToolDefinition(
            id="finance_exchangerate_api",
            name="ExchangeRate-API",
            category="Currency Exchange",
            description="Live fiat currency exchange rates and forex quotes from open.er-api.com",
            url="https://exchangerate.dev/docs",
            endpoint_url="https://open.er-api.com/v6/latest/EUR",
            http_method="GET",
            auth_type=ToolAuthType.NO_AUTH,
            execution_type=ToolExecutionType.DIRECT_REST,
            https_support=True,
            cors_support="Yes",
            is_curated=True,
            timeout_sec=5.0,
            cache_ttl_sec=600,
            parameters=[
                ToolParameter(
                    name="base_currency",
                    type="string",
                    location=ParameterLocation.PATH,
                    default="EUR",
                    description="Base currency code: EUR, USD, MAD, GBP, CAD, JPY"
                )
            ],
            tags=["finance", "currency", "exchange", "forex", "taux", "devises", "change", "sarf", "flous", "euro", "dollar", "dirham", "mad", "usd"]
        )
        curated["finance_exchangerate_api"] = exchangerate
        curated["forex_exchangerate"] = exchangerate

        # 4. JokeAPI (Entertainment)
        jokeapi = ToolDefinition(
            id="entertainment_jokeapi",
            name="JokeAPI",
            category="Entertainment",
            description="Programming, tech, and miscellaneous clean humor and jokes from JokeAPI",
            url="https://v2.jokeapi.dev/",
            endpoint_url="https://v2.jokeapi.dev/joke/Any",
            http_method="GET",
            auth_type=ToolAuthType.NO_AUTH,
            execution_type=ToolExecutionType.DIRECT_REST,
            https_support=True,
            cors_support="Yes",
            is_curated=True,
            timeout_sec=5.0,
            cache_ttl_sec=60,
            parameters=[
                ToolParameter(
                    name="category",
                    type="string",
                    location=ParameterLocation.PATH,
                    default="Any",
                    description="Joke category: Any, Programming, Misc, Pun"
                ),
                ToolParameter(
                    name="type",
                    type="string",
                    location=ParameterLocation.QUERY,
                    default="single",
                    description="Joke structure: single (one-liner) or twopart (setup & delivery)"
                ),
                ToolParameter(
                    name="safe-mode",
                    type="string",
                    location=ParameterLocation.QUERY,
                    default="true",
                    description="Enable safe mode to filter NSFW/offensive humor"
                )
            ],
            tags=["joke", "jokes", "humor", "blague", "humour", "nokat", "nukta", "dahk", "chiste", "funny", "geek", "programming"]
        )
        curated["entertainment_jokeapi"] = jokeapi

        # 5. CatFact Ninja (Animals)
        catfact = ToolDefinition(
            id="animals_catfact",
            name="Cat Facts",
            category="Animals",
            description="Random verified facts and trivia about domestic and wild cats from CatFact Ninja",
            url="https://catfact.ninja/",
            endpoint_url="https://catfact.ninja/fact",
            http_method="GET",
            auth_type=ToolAuthType.NO_AUTH,
            execution_type=ToolExecutionType.DIRECT_REST,
            https_support=True,
            cors_support="Yes",
            is_curated=True,
            timeout_sec=5.0,
            cache_ttl_sec=60,
            parameters=[
                ToolParameter(
                    name="max_length",
                    type="integer",
                    location=ParameterLocation.QUERY,
                    default=140,
                    description="Maximum character length of returned fact"
                )
            ],
            tags=["animals", "cats", "chat", "faits", "facts", "qitat", "mouch", "gatos", "anecdote", "trivia"]
        )
        curated["animals_catfact"] = catfact

        # 6. adresse.data.gouv.fr (Geocoding)
        adresse_gouv = ToolDefinition(
            id="geocoding_adresse_data_gouv",
            name="adresse.data.gouv.fr",
            category="Geocoding",
            description="Official French national address geocoding API to convert street addresses to GPS coordinates (BAN)",
            url="https://adresse.data.gouv.fr",
            endpoint_url="https://api-adresse.data.gouv.fr/search/",
            http_method="GET",
            auth_type=ToolAuthType.NO_AUTH,
            execution_type=ToolExecutionType.DIRECT_REST,
            https_support=True,
            cors_support="Yes",
            is_curated=True,
            timeout_sec=5.0,
            cache_ttl_sec=1800,
            parameters=[
                ToolParameter(
                    name="q",
                    type="string",
                    location=ParameterLocation.QUERY,
                    required=True,
                    description="Street address, place, or postal code in France (e.g. '8 boulevard du port amiens')"
                ),
                ToolParameter(
                    name="limit",
                    type="integer",
                    location=ParameterLocation.QUERY,
                    default=5,
                    description="Maximum number of candidate locations to return"
                )
            ],
            tags=["geocoding", "adresse", "france", "coordonnees", "gps", "lieu", "ville", "position", "paris", "ban"]
        )
        curated["geocoding_adresse_data_gouv"] = adresse_gouv

        # 7. Nominatim OpenStreetMap (Geocoding)
        nominatim = ToolDefinition(
            id="geocoding_nominatim",
            name="Nominatim",
            category="Geocoding",
            description="Worldwide OpenStreetMap geocoding and reverse geocoding API to find cities, countries, and landmarks",
            url="https://nominatim.org/release-docs/latest/api/Overview/",
            endpoint_url="https://nominatim.openstreetmap.org/search",
            http_method="GET",
            auth_type=ToolAuthType.NO_AUTH,
            execution_type=ToolExecutionType.DIRECT_REST,
            https_support=True,
            cors_support="Yes",
            is_curated=True,
            timeout_sec=5.0,
            cache_ttl_sec=3600,
            parameters=[
                ToolParameter(
                    name="q",
                    type="string",
                    location=ParameterLocation.QUERY,
                    required=True,
                    description="Global address, city, country, or point of interest (e.g. 'Casablanca', 'Tokyo')"
                ),
                ToolParameter(
                    name="format",
                    type="string",
                    location=ParameterLocation.QUERY,
                    default="json",
                    description="Output format: json"
                ),
                ToolParameter(
                    name="limit",
                    type="integer",
                    location=ParameterLocation.QUERY,
                    default=3,
                    description="Maximum locations to return"
                )
            ],
            tags=["geocoding", "maps", "openstreetmap", "carte", "monde", "geographie", "position", "gps", "kharieta", "ville", "monde"]
        )
        curated["geocoding_nominatim"] = nominatim

        return curated

    def _generate_tool_id(self, category: str, name: str, existing_ids: Set[str]) -> str:
        """Generate a deterministic, unique slug ID for a tool."""
        cat_slug = re.sub(r"[^a-z0-9]+", "_", normalize_string(category)).strip("_")
        name_slug = re.sub(r"[^a-z0-9]+", "_", normalize_string(name)).strip("_")
        base_id = f"{cat_slug}_{name_slug}"
        if base_id not in existing_ids:
            return base_id
        suffix = 2
        while f"{base_id}_{suffix}" in existing_ids:
            suffix += 1
        return f"{base_id}_{suffix}"

    def _match_curated_tool(self, item: Dict[str, Any], tool_id: str = "") -> Optional[Tuple[str, ToolDefinition]]:
        """Check if a catalog entry matches one of our curated high-value tools."""
        name_lower = item.get("name", "").lower().strip()
        cat_lower = item.get("category", "").lower().strip()
        url_lower = item.get("url", "").lower().strip()

        # Strict match on Open-Meteo to prevent collision with Open-Meteo Ensemble
        if name_lower == "open-meteo" and cat_lower == "weather":
            return "weather_open_meteo", self._curated_tools["weather_open_meteo"]
        if "coingecko" in name_lower and "crypto" in cat_lower:
            return "crypto_coingecko", self._curated_tools["crypto_coingecko"]
        if ("exchangerate" in name_lower or "exchange rate" in name_lower) and "currency" in cat_lower:
            return "finance_exchangerate_api", self._curated_tools["finance_exchangerate_api"]
        if "jokeapi" in name_lower and cat_lower == "entertainment":
            return "entertainment_jokeapi", self._curated_tools["entertainment_jokeapi"]
        if "cat facts" in name_lower and "catfact.ninja" in url_lower:
            return "animals_catfact", self._curated_tools["animals_catfact"]
        if "adresse.data.gouv.fr" in url_lower or ("adresse" in name_lower and cat_lower == "geocoding"):
            return "geocoding_adresse_data_gouv", self._curated_tools["geocoding_adresse_data_gouv"]
        if "nominatim" in name_lower and cat_lower == "geocoding":
            return "geocoding_nominatim", self._curated_tools["geocoding_nominatim"]

        return None

    def _load_and_index(self) -> None:
        """Load JSON dataset and build the inverted keyword index atomically."""
        t0 = time.perf_counter()
        curated_tools = self._init_curated_tools()

        if not os.path.isfile(self._data_path):
            logger.error("Catalog dataset file not found: %s", self._data_path)
            self._load_time_ms = (time.perf_counter() - t0) * 1000
            return

        with open(self._data_path, "r", encoding="utf-8") as f:
            raw_entries: List[Dict[str, Any]] = json.load(f)

        new_tools: Dict[str, ToolDefinition] = {}
        new_aliases: Dict[str, str] = {}
        new_categories: Dict[str, List[str]] = {}
        new_inverted_index: Dict[str, Dict[str, float]] = {}

        # Pre-seed aliases for curated aliases
        new_aliases["forex_exchangerate"] = "finance_exchangerate_api"

        existing_ids: Set[str] = set()

        # Temporarily assign curated_tools so _match_curated_tool can reference them
        self._curated_tools = curated_tools

        for item in raw_entries:
            category = item.get("category", "").strip()
            name = item.get("name", "").strip()
            url = item.get("url", "").strip()
            description = item.get("description", "").strip()
            https_str = str(item.get("https", "Yes")).strip().replace("`", "")
            cors_str = str(item.get("cors", "Unknown")).strip().replace("`", "")

            # Generate unique base ID
            gen_id = self._generate_tool_id(category, name, existing_ids)

            # Check if this item is one of our curated tools
            curated_match = self._match_curated_tool(item, gen_id)
            if curated_match is not None:
                canonical_id, curated_def = curated_match
                actual_id = canonical_id
                tool_def = curated_def
                new_aliases[canonical_id] = actual_id
                new_aliases[gen_id] = actual_id
            else:
                actual_id = gen_id
                tool_def = ToolDefinition(
                    id=actual_id,
                    name=name,
                    category=category,
                    description=description,
                    url=url,
                    endpoint_url=url if url.endswith(".json") or "/api/" in url else None,
                    http_method="GET",
                    auth_type=ToolAuthType.NO_AUTH,
                    execution_type=ToolExecutionType.GENERIC_HTTP,
                    https_support=https_str.lower() == "yes",
                    cors_support=cors_str if cors_str in ("Yes", "No", "Unknown") else "Unknown",
                    is_curated=False
                )

            existing_ids.add(actual_id)
            existing_ids.add(gen_id)

            # Store in tools map by its assigned unique / canonical ID (exactly 1,079 tools)
            new_tools[actual_id] = tool_def

            # Track in categories
            if category not in new_categories:
                new_categories[category] = []
            new_categories[category].append(actual_id)

            # Build inverted index
            self._index_tool_to(new_inverted_index, actual_id, tool_def)

        with self._lock:
            self._curated_tools = curated_tools
            self._tools = new_tools
            self._tool_id_aliases = new_aliases
            self._categories = new_categories
            self._inverted_index = new_inverted_index
            self._load_time_ms = (time.perf_counter() - t0) * 1000

        logger.info(
            "PublicApiRegistry initialized in %.2f ms. Total tools: %d, Categories: %d, Vocabulary: %d",
            self._load_time_ms,
            len(raw_entries),
            len(self._categories),
            len(self._inverted_index)
        )

    def _index_tool_to(self, index: Dict[str, Dict[str, float]], tool_id: str, tool: ToolDefinition) -> None:
        """Tokenize tool metadata and insert weighted postings into specified inverted index."""
        # Tokens from name (weight 3.0)
        for tok in tokenize(tool.name):
            self._add_posting_to(index, tok, tool_id, 3.0)

        # Tokens from category (weight 2.5)
        for tok in tokenize(tool.category):
            self._add_posting_to(index, tok, tool_id, 2.5)

        # Tokens from tags (weight 2.5)
        for tag in tool.tags:
            for tok in tokenize(tag):
                self._add_posting_to(index, tok, tool_id, 2.5)

        # Tokens from description (weight 1.0)
        for tok in tokenize(tool.description):
            self._add_posting_to(index, tok, tool_id, 1.0)

    def _add_posting_to(self, index: Dict[str, Dict[str, float]], token: str, tool_id: str, weight: float) -> None:
        """Add or accumulate a weighted posting for a token in specified index."""
        if token not in index:
            index[token] = {}
        index[token][tool_id] = index[token].get(tool_id, 0.0) + weight

    def _index_tool(self, tool_id: str, tool: ToolDefinition) -> None:
        """Tokenize tool metadata and insert weighted postings into the inverted index."""
        self._index_tool_to(self._inverted_index, tool_id, tool)

    def _add_posting(self, token: str, tool_id: str, weight: float) -> None:
        """Add or accumulate a weighted posting for a token."""
        self._add_posting_to(self._inverted_index, token, tool_id, weight)

    def _expand_query(self, query: str) -> Tuple[List[str], Optional[str], List[str]]:
        """
        Analyze query for multilingual aliases.
        Returns: (expanded_tokens, inferred_category, boost_tool_ids)
        """
        norm_query = normalize_string(query)
        raw_tokens = tokenize(query)
        expanded_tokens: Set[str] = set(raw_tokens)
        inferred_category: Optional[str] = None
        boost_tool_ids: List[str] = []

        # Check full query words against multilingual alias dictionary
        query_words = re.findall(r"\b[a-z0-9_-]+\b", norm_query)
        for word in query_words:
            if word in MULTILINGUAL_ALIASES:
                alias_info = MULTILINGUAL_ALIASES[word]
                if inferred_category is None:
                    inferred_category = alias_info.get("category")
                for tok in alias_info.get("tokens", []):
                    expanded_tokens.add(tok)
                for boost_id in alias_info.get("boost_tools", []):
                    boost_tool_ids.append(boost_id)

        return list(expanded_tokens), inferred_category, boost_tool_ids

    def search_tools(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 5
    ) -> List[ToolDefinition]:
        """
        Search tools matching query and optional category filter.
        Returns top_k ToolDefinition objects.
        """
        query_results = self.search(query=query, category=category, top_k=top_k)
        definitions: List[ToolDefinition] = []
        for res in query_results:
            tool = self.get_tool_by_id(res.tool_id)
            if tool is not None:
                definitions.append(tool)
        return definitions

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 5
    ) -> List[ToolQueryResult]:
        """
        Fast in-memory ranked search (<1ms) supporting multilingual queries.
        Returns ranked list of ToolQueryResult objects with relevance scores.
        """
        if not query.strip():
            if not category:
                return []
            # Category browsing mode
            cat_tools = self._categories.get(category, [])
            results = []
            tools = self._tools
            for tid in cat_tools[:top_k]:
                tool = tools.get(tid)
                if tool is None:
                    continue
                results.append(ToolQueryResult(
                    tool_id=tool.id,
                    name=tool.name,
                    category=tool.category,
                    description=tool.description,
                    relevance_score=1.0,
                    endpoint_available=bool(tool.endpoint_url),
                    is_curated=tool.is_curated
                ))
            return results

        expanded_tokens, alias_category, boost_tool_ids = self._expand_query(query)
        effective_category = category or alias_category

        scores: Dict[str, float] = {}

        # Accumulate inverted index scores
        for tok in expanded_tokens:
            postings = self._inverted_index.get(tok, {})
            for tool_id, weight in postings.items():
                scores[tool_id] = scores.get(tool_id, 0.0) + weight

        # Direct boost for curated alias tools matching intent
        tools = self._tools
        for boost_id in boost_tool_ids:
            resolved_id = self._tool_id_aliases.get(boost_id, boost_id)
            if boost_id in tools:
                scores[boost_id] = scores.get(boost_id, 0.0) + 15.0
            elif resolved_id in tools:
                scores[resolved_id] = scores.get(resolved_id, 0.0) + 15.0

        # Filter and rank
        ranked_items: List[Tuple[str, float]] = []
        for tool_id, score in scores.items():
            tool = tools.get(tool_id)
            if tool is None:
                continue

            # Category filter
            if effective_category and tool.category.lower() != effective_category.lower():
                # Allow a small penalty instead of dropping if strongly matching query
                score *= 0.5

            # Curated bonus for real-time execution viability
            if tool.is_curated:
                score += 3.0

            ranked_items.append((tool_id, score))

        ranked_items.sort(key=lambda x: x[1], reverse=True)

        results: List[ToolQueryResult] = []
        for tid, score in ranked_items[:top_k]:
            tool = tools.get(tid)
            if tool is None:
                continue
            results.append(ToolQueryResult(
                tool_id=tool.id,
                name=tool.name,
                category=tool.category,
                description=tool.description,
                relevance_score=round(score, 3),
                endpoint_available=bool(tool.endpoint_url),
                is_curated=tool.is_curated
            ))

        return results

    def get_tool_by_id(self, tool_id: str) -> Optional[ToolDefinition]:
        """
        Retrieve a ToolDefinition by its unique ID or canonical alias.
        Returns None if not found.
        """
        tools = self._tools
        if tool_id in tools:
            return tools[tool_id]
        aliases = self._tool_id_aliases
        if tool_id in aliases:
            resolved_id = aliases[tool_id]
            return tools.get(resolved_id)
        return None

    def get_categories(self) -> List[Dict[str, Any]]:
        """
        Return list of all categories with total tool count and curated count,
        sorted by tool count descending.
        """
        cat_list = []
        tools = self._tools
        for cat_name, tool_ids in self._categories.items():
            curated_count = sum(1 for tid in tool_ids if tid in tools and tools[tid].is_curated)
            cat_list.append({
                "category": cat_name,
                "count": len(tool_ids),
                "curated_count": curated_count
            })
        cat_list.sort(key=lambda x: x["count"], reverse=True)
        return cat_list

    def get_stats(self) -> Dict[str, Any]:
        """Return diagnostic metrics and statistics of the loaded registry."""
        tools = self._tools
        categories = self._categories
        curated_tools = self._curated_tools

        total_tools = len(tools)
        total_from_cats = sum(len(ids) for ids in categories.values())
        curated_count = len(set(t.id for t in curated_tools.values()))

        cors_counts: Dict[str, int] = {"Yes": 0, "No": 0, "Unknown": 0}
        for ids in categories.values():
            for tid in ids:
                tool = tools.get(tid)
                if tool:
                    cors_counts[tool.cors_support] = cors_counts.get(tool.cors_support, 0) + 1

        return {
            "total_tools": total_tools,
            "no_auth_count": total_tools,
            "categories_count": len(categories),
            "curated_count": curated_count,
            "curated_tools_count": curated_count,
            "cors_distribution": cors_counts,
            "indexed_vocabulary_size": len(self._inverted_index),
            "load_time_ms": round(self._load_time_ms, 2)
        }

    def list_tools(
        self,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ToolDefinition]:
        """Paginated listing of tools, optionally filtered by category."""
        if category:
            tool_ids = self._categories.get(category, [])
        else:
            # Flatten all categories maintaining stable order
            tool_ids = []
            for ids in self._categories.values():
                tool_ids.extend(ids)

        paginated_ids = tool_ids[offset:offset + limit]
        tools = self._tools
        return [tools[tid] for tid in paginated_ids if tid in tools]

    def get_curated_tools(self) -> List[ToolDefinition]:
        """Return list of all curated tool definitions."""
        return list(self._curated_tools.values())

    def reload(self, data_path: Optional[str] = None) -> None:
        """Reload catalog dataset from disk and rebuild index atomically and thread-safely."""
        with self._lock:
            if data_path:
                self._data_path = data_path
            self._load_and_index()
