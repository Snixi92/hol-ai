"""
Tests de validation de la parité linguistique stricte (effet miroir) dans HoL AI.
Vérifie que :
1. La détection linguistique est précise (fr, darija, darija_fr, en, es).
2. Les directives système interdisent formellement le mélange non sollicité.
3. Les réponses générées pour le français ne contiennent aucun mot de Darija/Arabe (ex: khouya, safi).
4. Les réponses pour la Darija s'expriment fidèlement en Darija.
"""
import pytest
import re
from src.services.llm_engine import LLMBrain
from src.services.cognitive_engine import CognitiveAgentEngine


def test_language_detection_accuracy():
    # Français
    assert LLMBrain.detect_language("Bonjour, peux-tu me donner la météo et fermer Steam ?") == "fr"
    assert LLMBrain.detect_language("J'aimerais acheter un nouvel ordinateur portable pour mes études.") == "fr"
    assert LLMBrain.detect_language("Ouvre la calculatrice s'il te plaît.") == "fr"

    # Darija pure
    assert LLMBrain.detect_language("Salam kidayr labas 3lik ach kadir daba ?") == "darija"
    assert LLMBrain.detect_language("Chouf lya chhal kayn f l-flous o wach mrigel hadchi") == "darija"
    assert LLMBrain.detect_language("السلام عليكم كيداير لاباس عليك") == "darija"

    # Darija / Français mixé (Code-switching)
    assert LLMBrain.detect_language("Salam khouya tu peux m'ouvrir Chrome stp ?") == "darija_fr"
    assert LLMBrain.detect_language("Chouf lya le prix dyal cette commande avec la livraison") == "darija_fr"

    # Anglais
    assert LLMBrain.detect_language("Hello, can you please find me the cheapest laptop?") == "en"
    assert LLMBrain.detect_language("Close the browser and check my revenue, please.") == "en"

    # Espagnol
    assert LLMBrain.detect_language("Hola amigo, ¿puedes abrir el navegador y buscar ofertas?") == "es"
    assert LLMBrain.detect_language("Buenas tardes, gracias por tu ayuda con este producto barato.") == "es"


def test_system_prompt_language_directives():
    # Prompt Français
    prompt_fr = CognitiveAgentEngine._build_system_prompt(detected_lang="fr")
    assert "DIRECTIVE LINGUISTIQUE ABSOLUE (STRICTEMENT EN FRANÇAIS)" in prompt_fr
    assert "INTERDICTION FORMELLE ET TOTALE d'utiliser le moindre mot en Darija" in prompt_fr
    assert "Tu t'exprimes avec aisance en Français, en Anglais pour le jargon tech/business, et tu maîtrises l'Espagnol et la Darija" not in prompt_fr

    # Prompt Darija
    prompt_darija = CognitiveAgentEngine._build_system_prompt(detected_lang="darija")
    assert "DIRECTIVE LINGUISTIQUE ABSOLUE (DARIJA MAROCAINE AUTHENTIQUE)" in prompt_darija
    assert "en alphabet latin/Arabizi ou en alphabet arabe" in prompt_darija

    # Prompt Anglais
    prompt_en = CognitiveAgentEngine._build_system_prompt(detected_lang="en")
    assert "STRICT LANGUAGE DIRECTIVE (ENGLISH ONLY)" in prompt_en

    # Prompt Espagnol
    prompt_es = CognitiveAgentEngine._build_system_prompt(detected_lang="es")
    assert "DIRECTIVA LINGÜÍSTICA ESTRICTA (SOLO ESPAÑOL)" in prompt_es


def test_fallback_responses_respect_language():
    tool_data = {
        "agent_3_logistics": {
            "product": "iPhone XR",
            "is_second_hand_deal": True,
            "current_drop_price_eur": 69,
            "pro_reconditioned_price_eur": 139
        }
    }

    # Fallback Français -> Aucun "Khouya"
    reply_fr = LLMBrain._get_fallback_conversational_response(
        user_message="Trouve-moi un iPhone XR pas cher",
        tool_results=tool_data,
        detected_lang="fr"
    )
    assert "khouya" not in reply_fr.lower()
    assert "khti" not in reply_fr.lower()
    assert "safi" not in reply_fr.lower()
    assert "J'ai fouillé tout le marché" in reply_fr

    # Fallback Darija -> Présence de Darija
    reply_darija = LLMBrain._get_fallback_conversational_response(
        user_message="Chouf lya iPhone XR rkhis",
        tool_results=tool_data,
        detected_lang="darija"
    )
    assert "Khouya" in reply_darija or "khouya" in reply_darija.lower()


@pytest.mark.asyncio
async def test_live_agent_language_parity_french():
    """Vérifie qu'un message 100% français reçoit une réponse 100% française sans mot de Darija."""
    res = await CognitiveAgentEngine.process_chat(
        user_message="Bonjour, peux-tu me résumer en deux phrases ce que tu es capable de faire pour m'aider aujourd'hui ?",
        session_id="test_lang_fr"
    )
    reply = res.get("reply", "")
    assert len(reply) > 20
    # Vérification stricte : aucun mot de Darija courant dans la réponse en français
    forbidden_words = ["khouya", "khoya", "khti", "safi", "dakchi", "mrigel", "nadi", "daba", "tbarkallah", "walou"]
    reply_lower = reply.lower()
    for word in forbidden_words:
        assert re.search(r"\b" + word + r"\b", reply_lower) is None, f"Le mot interdit '{word}' est apparu dans la réponse française !"


@pytest.mark.asyncio
async def test_live_agent_language_parity_darija():
    """Vérifie qu'un message en Darija reçoit une réponse authentique en Darija."""
    res = await CognitiveAgentEngine.process_chat(
        user_message="Salam kidayr labas 3lik ? Chno tqder dir lya daba f 2 kelmat ?",
        session_id="test_lang_darija"
    )
    reply = res.get("reply", "")
    assert len(reply) > 15
    # La réponse doit contenir des marqueurs de Darija / Arabizi ou de l'arabe
    reply_lower = reply.lower()
    has_darija_marker = any(
        re.search(r"\b" + w + r"\b", reply_lower) for w in ["labas", "mrigel", "khouya", "khti", "daba", "n-qder", "lik", "m3ak", "kayn", "safi", "nadi", "chouf", "kolchi", "hmdlh"]
    ) or any('\u0600' <= c <= '\u06FF' for c in reply)
    assert has_darija_marker, f"La réponse en Darija ne contient aucun marqueur authentique : {reply}"
