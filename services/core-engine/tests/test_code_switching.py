"""
Tests unitaires pour le Cœur Neuronal Polyglotte & Code-Switching (Phase 3).
Vérifie la détection linguistique, les instructions système et les réponses conversationnelles
en Français, Anglais, Espagnol et Darija Marocaine authentique.
"""
import pytest
from src.services.llm_engine import LLMBrain


def test_language_detection_darija():
    """Vérifie la détection d'expressions en Darija marocaine authentique."""
    darija_samples = [
        "Khouya, l-affaire raha mzyana bzzaf, chouf lina chi deal",
        "Safi dakchi mrigel, kolchi nadi",
        "Kayn wahed l-offre nadi bzzaf f Amazon",
        "Bghit n-chouf chhal l-prix dial had l-colis",
        "Tbarkallah 3lik akhay, lah i7afdek",
        "Salam khouya, fin wsel l-colis diali ?"
    ]
    for sample in darija_samples:
        detected = LLMBrain.detect_language(sample)
        assert detected in ["darija", "darija_fr"], f"Échec de détection Darija pour: {sample}"


def test_language_detection_arabic_script():
    """Vérifie la détection des requêtes saisies en caractères arabes."""
    arabic_sample = "خويا بغيت نعرف فين وصل الكولي ديالي"
    detected = LLMBrain.detect_language(arabic_sample)
    assert detected in ["darija", "darija_fr"]


def test_language_detection_french():
    """Vérifie la détection de requêtes en Français standard."""
    fr_sample = "Suis mon colis UPS et calcule ma marge nette sur cette vente."
    assert LLMBrain.detect_language(fr_sample) == "fr"


def test_language_detection_english():
    """Vérifie la détection de requêtes en Anglais."""
    en_sample = "Hello, what's up? Find me the best deal on this laptop with fastest shipping."
    assert LLMBrain.detect_language(en_sample) == "en"


def test_language_detection_spanish():
    """Vérifie la détection de requêtes en Espagnol."""
    es_sample = "Hola amigo, ¿dónde puedo encontrar una buena oferta en el mercado inmobiliario?"
    assert LLMBrain.detect_language(es_sample) == "es"


def test_code_switching_system_instruction():
    """Vérifie que l'instruction système intègre explicitement les 4 langues et le code-switching."""
    instruction = LLMBrain._build_system_instruction()
    assert "Français" in instruction
    assert "Anglais" in instruction
    assert "Espagnol" in instruction
    assert "Darija Marocaine authentique" in instruction
    assert "Code-Switching" in instruction
    assert "Khouya, l-affaire raha mzyana bzzaf..." in instruction
    assert "Safi dakchi mrigel..." in instruction
    assert "Kayn wahed l-offre nadi..." in instruction


def test_no_key_guidance_multilingual():
    """Vérifie que le guidage sans clé s'adapte à la langue de l'interlocuteur."""
    # En Darija
    guidance_darija = LLMBrain._no_key_guidance("Khouya bghit deal", detected_lang="darija")
    assert "Khouya" in guidance_darija
    assert "mrigel" in guidance_darija

    # En Espagnol
    guidance_es = LLMBrain._no_key_guidance("Hola amigo", detected_lang="es")
    assert "cerebro IA" in guidance_es or "Ajustes" in guidance_es

    # En Anglais
    guidance_en = LLMBrain._no_key_guidance("Hey bro", detected_lang="en")
    assert "LLM brain is connected" in guidance_en

    # En Français
    guidance_fr = LLMBrain._no_key_guidance("Bonjour HoL AI", detected_lang="fr")
    assert "cerveau IA (LLM)" in guidance_fr


def test_fallback_conversational_response_darija():
    """Vérifie le message de secours conversationnel avec code-switching Darija authentique."""
    tool_results = {
        "agent_3_logistics": {
            "product": "PS5 Slim",
            "platform": "Amazon.fr",
            "current_drop_price_eur": 429.0
        }
    }
    fallback = LLMBrain._get_fallback_conversational_response(
        user_message="Khouya chouf lina had l-affaire",
        tool_results=tool_results,
        detected_lang="darija"
    )
    assert "Khouya, l-affaire raha mzyana bzzaf !" in fallback
    assert "dakchi mrigel" in fallback
    assert "offre nadi" in fallback
