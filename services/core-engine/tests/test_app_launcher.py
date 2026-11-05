import pytest
from src.services.app_launcher import AppLauncherService


def test_app_launcher_known_app():
    result = AppLauncherService.resolve_app_command("discord")
    assert result is not None
    assert "discord" in result.lower() or "http" in result.lower()


def test_app_launcher_custom_fallback():
    result = AppLauncherService.launch_application("calculatrice", target_screen="droite")
    assert result["status"] in ["launched", "simulated", "opened"]
    assert "calculatrice" in result["app"].lower()
    assert "droite" in result["screen"]


def test_app_launcher_web_fallback_for_socials():
    result = AppLauncherService.launch_application("instagram", target_screen="principal")
    assert result["status"] in ["launched", "simulated", "opened"]
    assert "instagram" in result["app"].lower()
    assert result["screen"] == "principal"


def test_universal_find_installed_app():
    # Should find Calculator, Notepad, or any app from Windows StartApps
    match = AppLauncherService.find_installed_app("bloc-notes") or AppLauncherService.find_installed_app("notepad")
    assert match is not None
    assert "notepad" in match["name"].lower() or "bloc" in match["name"].lower() or "app" in match["app_id"].lower()


def test_close_application_simulation():
    # Test closing an application gracefully
    res = AppLauncherService.close_application("notepad", simulate=True)
    assert res["status"] in ["closed", "not_running"]
    assert "notepad" in res["app"].lower()
    assert "fermé" in res["verbal_reply"] or "pas en cours" in res["verbal_reply"] or "fermee" in res["verbal_reply"]


def test_app_launcher_explorer_fichiers():
    res_open = AppLauncherService.launch_application("fichiers", simulate=True)
    assert res_open["status"] in ["launched", "opened"]
    assert "Explorateur de fichiers" in res_open["display_name"]

    res_close = AppLauncherService.close_application("mes fichiers", simulate=True)
    assert res_close["status"] in ["closed", "not_running"]
    assert "Explorateur de fichiers" in res_close["display_name"]
    assert "fermé" in res_close["verbal_reply"] or "ouverte" in res_close["verbal_reply"]
