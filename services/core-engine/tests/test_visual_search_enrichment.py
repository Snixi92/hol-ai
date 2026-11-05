"""
Suite de tests complète pour le Moteur de Recherche Visuelle & Enrichissement Image (Requirement R6).

Vérifie :
1. Extraction et détection d'entités visuelles (Monuments, Merveilles naturelles, Art, Faune, Sciences).
2. Résolveur multi-paliers Wikipedia REST API (Haute résolution 4K/HD, dimensions, métadonnées).
3. Tolérance aux pannes et requêtes inconnues (Zéro crash, retours gracieux).
4. Conformité du schéma de payload des cartes Liquid Glass (visual_card).
5. Endpoints REST FastAPI GET et POST /api/visual/search.
6. Intégration du composant Lightbox modal (#liquid-image-lightbox) et rendu frontend index.html.
7. Enregistrement de l'outil search_visual_enrichment dans le Cerveau Cognitif (CognitiveAgentEngine).
"""

import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from src.services.visual_search import VisualSearchEngine
from src.api.server import app
from src.services.cognitive_engine import CognitiveAgentEngine, search_visual_enrichment


client = TestClient(app)


# ============================================================================
# 1. TESTS D'EXTRACTION D'ENTITÉS VISUELLES (PATTERNS & DICTIONNAIRES)
# ============================================================================

def test_visual_entity_extraction_monuments():
    """Vérifie l'extraction précise des monuments internationaux majeurs."""
    queries = [
        ("Montre-moi la Tour Eiffel", ["Tour Eiffel"]),
        ("Quelle est l'histoire du Colisée de Rome ?", ["Colisée"]),
        ("Je prépare un voyage pour voir Big Ben et le Taj Mahal", ["Big Ben", "Taj Mahal"]),
        ("Parle-moi de la Statue de la Liberté", ["Statue de la Liberté"]),
        ("La Sagrada Família est-elle terminée ?", ["Sagrada Família"]),
        ("Photo des Pyramides de Gizeh", ["Pyramides de Gizeh"]),
        ("Vue sur Le Mont-Saint-Michel à marée haute", ["Le Mont-Saint-Michel"]),
    ]
    for q, expected in queries:
        detected = VisualSearchEngine.extract_visual_entities(q)
        for exp in expected:
            assert exp in detected, f"Entité '{exp}' non trouvée dans la requête '{q}' (trouvé: {detected})"


def test_visual_entity_extraction_natural_wonders_and_art():
    """Vérifie l'extraction des merveilles naturelles et chefs-d'œuvre artistiques."""
    queries = [
        ("Parle-moi du Grand Canyon et du Mont Fuji", ["Grand Canyon", "Mont Fuji"]),
        ("Une expédition sur le Mont Blanc", ["Mont Blanc"]),
        ("J'aimerais admirer une aurore boréale", ["Aurore polaire"]),
        ("Où est exposée La Joconde au musée du Louvre ?", ["La Joconde", "Musée du Louvre"]),
        ("L'analyse du tableau Guernica de Picasso", ["Guernica (Picasso)"]),
        ("La Nuit étoilée de Van Gogh", ["La Nuit étoilée"]),
    ]
    for q, expected in queries:
        detected = VisualSearchEngine.extract_visual_entities(q)
        for exp in expected:
            assert exp in detected, f"Entité '{exp}' non trouvée dans la requête '{q}' (trouvé: {detected})"


def test_visual_entity_extraction_intent_regex_and_cleanup():
    """Vérifie l'extraction par expressions régulières d'intention avec nettoyage des stop words."""
    test_cases = [
        ("photo de Séquoia géant s'il te plaît", ["Séquoia géant"]),
        ("montre-moi le Télescope James Webb", ["James Webb (télescope spatial)"]),
        ("affiche une image de la Station spatiale internationale", ["Station spatiale internationale"]),
    ]
    for q, expected in test_cases:
        detected = VisualSearchEngine.extract_visual_entities(q)
        for exp in expected:
            assert exp in detected, f"Entité '{exp}' attendue pour '{q}', trouvé: {detected}"


def test_non_visual_queries_produce_no_false_positives():
    """Vérifie que les requêtes usuelles non-visuelles ne déclenchent pas d'entités imaginaires."""
    non_visual = [
        "Bonjour comment ça va ?",
        "Fais-moi le point sur ma journée",
        "Calcule la TVA pour 120 euros",
        "Quels sont les raccourcis clavier sous Windows ?",
        "Rédige un e-mail professionnel",
    ]
    for q in non_visual:
        detected = VisualSearchEngine.extract_visual_entities(q)
        assert len(detected) == 0, f"Faux positif inattendu pour '{q}' : {detected}"


# ============================================================================
# 2. TESTS DU RÉSOLVEUR WIKIPEDIA REST API & HAUTE RÉSOLUTION
# ============================================================================

def test_wikipedia_rest_api_high_res_monument():
    """Vérifie la récupération réelle de photo haute résolution pour un monument vérifié."""
    res = VisualSearchEngine.search_visual_entity_sync("Tour Eiffel", lang="fr")
    assert res is not None, "Aucun résultat retourné pour Tour Eiffel"
    assert res["type"] == "visual_card"
    assert "Tour Eiffel" in res["title"]
    assert res["image_url"].startswith("http")
    assert res["thumbnail_url"].startswith("http")
    assert res["dimensions"]["width"] >= 1920, f"Résolution largeur insuffisante: {res['dimensions']['width']}"
    assert res["dimensions"]["height"] >= 1080, f"Résolution hauteur insuffisante: {res['dimensions']['height']}"
    assert "Wikipedia" in res["source"]
    assert "fr.wikipedia.org" in res["source_url"] or "wikimedia.org" in res["source_url"]
    assert "Haute Résolution" in res["badge"] or "4K" in res["badge"] or "2K" in res["badge"]


def test_wikipedia_rest_api_natural_wonder_dimensions():
    """Vérifie la récupération pour une merveille naturelle (Grand Canyon)."""
    res = VisualSearchEngine.search_visual_entity_sync("Grand Canyon", lang="fr")
    assert res is not None
    assert "Grand Canyon" in res["title"]
    assert res["dimensions"]["width"] >= 1920
    assert len(res["description"]) > 10


def test_visual_search_unknown_entity_graceful_none():
    """Vérifie la robustesse et l'absence de crash face à une entité imaginaire ou inexistante."""
    res = VisualSearchEngine.search_visual_entity_sync("xyznonexistentfakeentity9999", lang="fr")
    assert res is None, "Une entité imaginaire devrait retourner None sans lever d'exception"


def test_enrich_with_visuals_sync_full_flow():
    """Vérifie le flux complet d'enrichissement synchrone sur une phrase utilisateur."""
    cards = VisualSearchEngine.enrich_with_visuals_sync("Montre-moi une vue de la Tour Eiffel")
    assert isinstance(cards, list)
    assert len(cards) >= 1
    first_card = cards[0]
    assert first_card["type"] == "visual_card"
    assert first_card["title"] == "Tour Eiffel"
    assert first_card["image_url"] != ""
    assert first_card["dimensions"]["width"] > 0


# ============================================================================
# 3. CONFORMITÉ DU SCHÉMA DE PAYLOAD DE LA CARTE LIQUID GLASS
# ============================================================================

def test_visual_card_payload_schema_compliance():
    """Valide les types et attributs obligatoires du contrat de carte visuelle."""
    res = VisualSearchEngine.search_visual_entity_sync("La Joconde", lang="fr")
    assert res is not None

    mandatory_keys = [
        "type", "title", "description", "image_url", "thumbnail_url",
        "source", "source_url", "dimensions", "badge"
    ]
    for key in mandatory_keys:
        assert key in res, f"Clé obligatoire manquante : '{key}'"

    assert res["type"] == "visual_card"
    assert isinstance(res["title"], str) and len(res["title"]) > 0
    assert isinstance(res["description"], str)
    assert isinstance(res["image_url"], str) and res["image_url"].startswith("http")
    assert isinstance(res["thumbnail_url"], str) and res["thumbnail_url"].startswith("http")
    assert isinstance(res["source"], str) and len(res["source"]) > 0
    assert isinstance(res["source_url"], str) and res["source_url"].startswith("http")
    assert isinstance(res["dimensions"], dict)
    assert isinstance(res["dimensions"]["width"], int) and res["dimensions"]["width"] > 0
    assert isinstance(res["dimensions"]["height"], int) and res["dimensions"]["height"] > 0
    assert isinstance(res["badge"], str) and len(res["badge"]) > 0


# ============================================================================
# 4. TESTS DES ENDPOINTS REST FASTAPI (/api/visual/search)
# ============================================================================

def test_api_visual_search_get_success():
    """Vérifie le endpoint GET /api/visual/search avec query param q."""
    response = client.get("/api/visual/search?q=Tour+Eiffel&lang=fr")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
    assert data.get("query") == "Tour Eiffel"
    assert isinstance(data.get("results"), list)
    assert len(data["results"]) >= 1
    assert data["results"][0]["type"] == "visual_card"
    assert "Tour Eiffel" in data["results"][0]["title"]


def test_api_visual_search_get_unknown_query():
    """Vérifie que GET /api/visual/search avec requête inconnue renvoie une liste vide sans erreur 500."""
    response = client.get("/api/visual/search?q=xyzfakeimaginaryunknown999&lang=fr")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
    assert data.get("results") == []


def test_api_visual_search_post_success():
    """Vérifie le endpoint POST /api/visual/search avec payload JSON."""
    response = client.post("/api/visual/search", json={"query": "Grand Canyon", "lang": "fr"})
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
    assert data.get("query") == "Grand Canyon"
    assert len(data.get("results", [])) >= 1
    assert data["results"][0]["type"] == "visual_card"
    assert "Grand Canyon" in data["results"][0]["title"]


# ============================================================================
# 5. TESTS DU FRONTEND & DU COMPOSANT LIGHTBOX (#liquid-image-lightbox)
# ============================================================================

def test_frontend_contains_liquid_image_lightbox_and_handlers():
    """Vérifie la présence du modal Liquid Glass Lightbox et des fonctions UI dans index.html."""
    html_path = Path(__file__).resolve().parent.parent / "src" / "api" / "static" / "index.html"
    assert html_path.exists(), f"Fichier {html_path} introuvable"

    content = html_path.read_text(encoding="utf-8")

    # 1. Vérification du markup HTML du modal Lightbox
    assert 'id="liquid-image-lightbox"' in content, "Composant modal #liquid-image-lightbox manquant"
    assert 'id="lightbox-img"' in content, "Élément #lightbox-img manquant dans le Lightbox"
    assert 'id="lightbox-title"' in content, "Élément #lightbox-title manquant dans le Lightbox"
    assert 'id="lightbox-dimensions"' in content, "Élément #lightbox-dimensions manquant dans le Lightbox"
    assert 'id="lightbox-source-link"' in content, "Élément #lightbox-source-link manquant dans le Lightbox"
    assert 'closeLiquidImageLightbox()' in content, "Appel de fermeture du Lightbox manquant"

    # 2. Vérification du rendu de la carte visual_card dans renderChatCard
    assert "type === 'visual_card'" in content, "Branche de rendu visual_card manquante dans renderChatCard"
    assert "openLiquidImageLightbox" in content, "Liaison d'ouverture Lightbox manquante dans visual_card"
    assert "visual-card" in content, "Classe CSS visual-card manquante"

    # 3. Vérification des fonctions JavaScript de contrôle et de la gestion de la touche Échap
    assert "function openLiquidImageLightbox(" in content, "Fonction JavaScript openLiquidImageLightbox manquante"
    assert "function closeLiquidImageLightbox(" in content, "Fonction JavaScript closeLiquidImageLightbox manquante"
    assert "e.key === 'Escape'" in content, "Écouteur clavier de fermeture Échap manquant"


# ============================================================================
# 6. TESTS D'INTÉGRATION DU CERVEAU COGNITIF (COGNITIVE AGENT ENGINE)
# ============================================================================

def test_cognitive_engine_has_visual_search_tool_registered():
    """Vérifie que search_visual_enrichment est dûment enregistré comme outil LLM."""
    tools = CognitiveAgentEngine.get_registered_tools()
    tool_names = [getattr(t, "__name__", str(t)) for t in tools]
    assert "search_visual_enrichment" in tool_names, (
        f"L'outil search_visual_enrichment doit être dans CognitiveAgentEngine.get_registered_tools(). "
        f"Outils actuels: {tool_names}"
    )


def test_search_visual_enrichment_tool_execution():
    """Vérifie l'exécution directe de l'outil search_visual_enrichment."""
    result_str = search_visual_enrichment("Tour Eiffel", lang="fr")
    assert isinstance(result_str, str)
    assert "Tour Eiffel" in result_str or "Photographie" in result_str
    assert "Carte Liquid Glass" in result_str
