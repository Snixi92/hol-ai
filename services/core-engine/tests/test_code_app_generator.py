import os
import pytest
from src.services.code_app_generator import CodeAppGeneratorService


def test_create_and_preview_morpion():
    html_code = "<!DOCTYPE html><html><body><h1>Morpion</h1></body></html>"
    css_code = "body { background: black; color: white; }"
    js_code = "console.log('Jeu de Morpion initialisé');"

    res = CodeAppGeneratorService.create_and_preview_app(
        app_name="morpion",
        description="Jeu de morpion interactif en HTML/CSS/JS",
        html_content=html_code,
        css_content=css_code,
        js_content=js_code,
        open_browser=False
    )

    assert res["status"] == "created"
    assert res["app_name"] == "morpion"
    assert os.path.exists(res["files"]["html"])
    assert res["preview_url"] == "/apps/morpion/index.html"
    assert "Morpion" in open(res["files"]["html"], encoding="utf-8").read()


def test_default_template_generation_if_empty():
    # If the user asks for a calculator or morpion without providing code, the generator generates a functional default template!
    res = CodeAppGeneratorService.generate_app_template("morpion", open_browser=False)
    assert res["status"] == "created"
    assert "Morpion" in res["description"] or "Tic-Tac-Toe" in res["description"]
    assert os.path.exists(res["files"]["html"])
