"""
Tests unitaires de validation pour l'anaphore multi-tours et les synonymes d'applications.
Vérifie :
1. La détection et mémorisation automatique de l'application active dans la session.
2. La résolution contextuelle des pronoms ('ferme le', 'relance le', 'seddo', '7ello').
3. Le support des synonymes naturels ('ouvre mes fichiers' -> Explorateur de fichiers).
4. La transition fluide entre discussion et action ('tu penses quoi de steam ?' -> 'ferme le').
"""
import pytest
from src.services.session_manager import SessionManager, ConversationSession
from src.services.app_launcher import AppLauncherService


@pytest.fixture(autouse=True)
def clean_sessions():
    """Nettoie toutes les sessions avant chaque test."""
    SessionManager.clear_all()
    yield
    SessionManager.clear_all()


def test_extract_app_mention():
    """Vérifie l'extraction du nom de l'application dans les requêtes directes et conversationnelles."""
    assert SessionManager.extract_app_mention("ouvre steam") == "Steam"
    assert SessionManager.extract_app_mention("ferme discord") == "Discord"
    assert SessionManager.extract_app_mention("tu penses quoi de steam ?") == "Steam"
    assert SessionManager.extract_app_mention("j'adore spotify") == "Spotify"
    assert SessionManager.extract_app_mention("ouvre ma musique") == "Spotify"
    assert SessionManager.extract_app_mention("ouvre mes fichiers") == "l'explorateur de fichiers"
    assert SessionManager.extract_app_mention("ferme la calculatrice") == "la calculatrice"
    assert SessionManager.extract_app_mention("lance lenovo vantage") == "Lenovo Vantage"

    # Les pronoms purs ne doivent PAS être extraits comme une nouvelle application
    assert SessionManager.extract_app_mention("ferme le") is None
    assert SessionManager.extract_app_mention("ferme-la") is None
    assert SessionManager.extract_app_mention("ouvre le") is None
    assert SessionManager.extract_app_mention("seddo") is None
    assert SessionManager.extract_app_mention("7ello") is None


def test_multiturn_steam_close_pronoun():
    """Test du scénario utilisateur : 'Ouvre Steam' puis 'ferme le'."""
    session = SessionManager.get_or_create("test_steam_session")

    # Tour 1 : L'utilisateur demande d'ouvrir Steam
    eff_msg_1, _, _ = SessionManager.resolve_anaphora_and_context(session, "Ouvre Steam")
    assert eff_msg_1 == "Ouvre Steam"
    session.add_user_message("Ouvre Steam")
    assert session.last_app == "Steam"

    # L'assistant répond avec la carte de lancement
    session.add_assistant_message("Steam est lancé.", cards=[{
        "type": "app_launcher",
        "data": {"action": "launch", "app": "Steam", "display_name": "Steam", "status": "launched"}
    }])
    assert session.last_app == "Steam"

    # Tour 2 : L'utilisateur dit 'ferme le'
    eff_msg_2, _, _ = SessionManager.resolve_anaphora_and_context(session, "ferme le")
    assert eff_msg_2 == "Ferme Steam"
    assert session.last_app_action == "close"


def test_multiturn_steam_chat_then_close():
    """Test du scénario utilisateur : Parler de Steam puis 'ferme le'."""
    session = SessionManager.get_or_create("test_steam_chat")

    # Tour 1 : Discussion sur Steam
    eff_msg_1, _, _ = SessionManager.resolve_anaphora_and_context(session, "tu penses quoi de Steam ?")
    session.add_user_message("tu penses quoi de Steam ?")
    assert session.last_app == "Steam"

    # Tour 2 : 'ferme le'
    eff_msg_2, _, _ = SessionManager.resolve_anaphora_and_context(session, "ferme le")
    assert eff_msg_2 == "Ferme Steam"


def test_multiturn_file_explorer_synonyms():
    """Test du scénario : 'ouvre mes fichiers' puis 'ferme le'."""
    session = SessionManager.get_or_create("test_files_session")

    # Tour 1 : 'ouvre mes fichiers'
    eff_msg_1, _, _ = SessionManager.resolve_anaphora_and_context(session, "ouvre mes fichiers")
    assert eff_msg_1 == "Ouvre l'explorateur de fichiers"
    session.add_user_message("ouvre mes fichiers")
    assert session.last_app == "l'explorateur de fichiers"

    # Tour 2 : 'ferme le'
    eff_msg_2, _, _ = SessionManager.resolve_anaphora_and_context(session, "ferme le")
    assert eff_msg_2 == "Ferme l'explorateur de fichiers"


def test_multiturn_file_explorer_direct_close_synonym():
    """Test de fermeture directe avec synonyme : 'ferme mes fichiers'."""
    session = SessionManager.get_or_create("test_files_close_direct")
    eff_msg, _, _ = SessionManager.resolve_anaphora_and_context(session, "ferme mes fichiers")
    assert eff_msg == "Ferme l'explorateur de fichiers"
    assert session.last_app == "l'explorateur de fichiers"
    assert session.last_app_action == "close"


def test_multiturn_darija_pronouns():
    """Test des pronoms en Darija marocaine ('seddo', '7ello')."""
    session = SessionManager.get_or_create("test_darija_session")

    # Tour 1 : Ouvre Discord
    session.add_user_message("ouvre discord")
    assert session.last_app == "Discord"

    # Tour 2 : 'seddo' (ferme-le en Darija)
    eff_msg_2, _, _ = SessionManager.resolve_anaphora_and_context(session, "seddo")
    assert eff_msg_2 == "Ferme Discord"

    # Tour 3 : '7ello' (ouvre-le en Darija)
    eff_msg_3, _, _ = SessionManager.resolve_anaphora_and_context(session, "7ello")
    assert eff_msg_3 == "Ouvre Discord"


def test_app_launcher_explorer_safe_simulation():
    """Vérifie que l'Explorateur est simulé sans erreur et renvoie les bonnes informations."""
    res_open = AppLauncherService.launch_application("mes fichiers", simulate=True)
    assert res_open["display_name"] == "Explorateur de fichiers"
    assert res_open["status"] in ["launched", "opened"]

    res_close = AppLauncherService.close_application("mes fichiers", simulate=True)
    assert res_close["display_name"] == "Explorateur de fichiers"
    assert res_close["status"] == "closed"
    assert "fermé" in res_close["verbal_reply"]
