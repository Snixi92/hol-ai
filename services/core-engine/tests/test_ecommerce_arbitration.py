"""
Suite de tests complète pour le Moteur d'Arbitrage E-Commerce & Sourcing Décisionnel (Requirement R7).

Vérifie :
1. L'arbitrage automatique et déterministe d'un SEUL marchand de référence (Fnac, Cdiscount, Amazon)
   selon l'affinité de catégorie (Audio/Photo/Culture -> Fnac, Électroménager/Maison/Bricolage -> Cdiscount,
   Informatique/Composants/Périphériques -> Amazon).
2. La prise en compte prioritaire de la préférence utilisateur explicite.
3. L'intégrité intra-marchand absolue : 100% des URL (produit principal et alternatives)
   doivent pointer strictement vers le domaine du marchand arbitré, sans aucune dispersion multi-sites.
4. Le nombre d'alternatives : exactement entre 3 et 4 alternatives pertinentes et différenciées par fiche.
5. La conformité du schéma de payload de la carte Liquid Glass (`ecommerce_arbitration_card`).
6. Le pont synchrone non-bloquant et le système de cache TTL.
7. Les endpoints REST FastAPI : GET /api/sourcing/arbitrate, POST /api/sourcing/arbitrate et POST /api/ecommerce/arbitrate.
8. La présence de la logique de rendu Liquid Glass dans le frontend `index.html`.
9. L'enregistrement et l'exécution de l'outil `ecommerce_sourcing_arbitration` dans le Cerveau Cognitif.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from src.services.ecommerce_arbitration import EcommerceArbitrationService, MERCHANT_PROFILES
from src.api.server import app
from src.services.cognitive_engine import CognitiveAgentEngine, ecommerce_sourcing_arbitration

client = TestClient(app)


# ============================================================================
# 1. TESTS D'ARBITRAGE DU MARCHAND UNIQUE PAR CATÉGORIE
# ============================================================================

def test_merchant_arbitration_audio_and_hifi_selects_fnac():
    """Vérifie que les produits audio haute-fidélité et casques antibruit arbitrent vers la Fnac."""
    queries = [
        "casque bluetooth antibruit",
        "écouteurs sans fil sony wh-1000xm5",
        "enceinte bluetooth hifi pour salon",
        "barre de son dolby atmos",
        "platine vinyle audiophile"
    ]
    for q in queries:
        merchant = EcommerceArbitrationService.arbitrate_merchant(q)
        assert merchant.name == "Fnac", f"Pour '{q}', attendu Fnac, obtenu {merchant.name}"
        assert merchant.domain == "fnac.com"


def test_merchant_arbitration_photo_and_gaming_selects_fnac():
    """Vérifie que la photo pro et les consoles de jeux arbitrent vers la Fnac."""
    queries = [
        "appareil photo hybride plein format",
        "boîtier sony alpha 7 iv",
        "console ps5 slim avec lecteur",
        "jeux nintendo switch oled",
        "manga one piece tome 108"
    ]
    for q in queries:
        merchant = EcommerceArbitrationService.arbitrate_merchant(q)
        assert merchant.name == "Fnac", f"Pour '{q}', attendu Fnac, obtenu {merchant.name}"
        assert merchant.domain == "fnac.com"


def test_merchant_arbitration_electromenager_selects_cdiscount():
    """Vérifie que le gros électroménager et l'équipement maison arbitrent vers Cdiscount."""
    queries = [
        "machine a laver 9kg hublot",
        "lave vaisselle encastrable 14 couverts",
        "refrigerateur combine no frost",
        "aspirateur robot laveur",
        "four pyrolyse encastrable"
    ]
    for q in queries:
        merchant = EcommerceArbitrationService.arbitrate_merchant(q)
        assert merchant.name == "Cdiscount", f"Pour '{q}', attendu Cdiscount, obtenu {merchant.name}"
        assert merchant.domain == "cdiscount.com"


def test_merchant_arbitration_maison_and_bricolage_selects_cdiscount():
    """Vérifie que la literie, le mobilier et le bricolage arbitrent vers Cdiscount."""
    queries = [
        "matelas memoire de forme 140x190",
        "canape d'angle convertible",
        "perceuse a percussion sans fil 18v",
        "tondeuse a gazon thermique",
        "meuleuse d'angle bosch"
    ]
    for q in queries:
        merchant = EcommerceArbitrationService.arbitrate_merchant(q)
        assert merchant.name == "Cdiscount", f"Pour '{q}', attendu Cdiscount, obtenu {merchant.name}"
        assert merchant.domain == "cdiscount.com"


def test_merchant_arbitration_hardware_and_peripherals_selects_amazon():
    """Vérifie que les composants PC, hardware et périphériques arbitrent vers Amazon."""
    queries = [
        "carte graphique rtx 4070 super",
        "processeur intel core i7 14700k",
        "ssd nvme 2to pcie 4.0",
        "souris gamer sans fil ultra legere",
        "clavier mecanique switch red",
        "ecran pc gamer 144hz qhd 27 pouces"
    ]
    for q in queries:
        merchant = EcommerceArbitrationService.arbitrate_merchant(q)
        assert merchant.name == "Amazon", f"Pour '{q}', attendu Amazon, obtenu {merchant.name}"
        assert merchant.domain == "amazon.fr"


# ============================================================================
# 2. TESTS DE LA PRÉFÉRENCE UTILISATEUR EXPLICITE (OVERRIDE)
# ============================================================================

def test_user_explicit_merchant_in_query_overrides_category():
    """Vérifie qu'une mention explicite dans la requête force le marchand demandé."""
    # Casque sur Cdiscount -> doit forcer Cdiscount
    m1 = EcommerceArbitrationService.arbitrate_merchant("quel casque bluetooth acheter sur cdiscount ?")
    assert m1.name == "Cdiscount"
    assert m1.domain == "cdiscount.com"

    # Lave-linge sur Amazon -> doit forcer Amazon
    m2 = EcommerceArbitrationService.arbitrate_merchant("lave linge bosch chez amazon")
    assert m2.name == "Amazon"
    assert m2.domain == "amazon.fr"

    # Carte graphique à la Fnac -> doit forcer Fnac
    m3 = EcommerceArbitrationService.arbitrate_merchant("carte graphique rtx 4060 a la fnac")
    assert m3.name == "Fnac"
    assert m3.domain == "fnac.com"


def test_user_preferred_merchant_parameter_overrides_category():
    """Vérifie que le paramètre preferred_merchant a la priorité."""
    m_param = EcommerceArbitrationService.arbitrate_merchant("machine a laver", preferred_merchant="Amazon")
    assert m_param.name == "Amazon"
    assert m_param.domain == "amazon.fr"

    m_param_fnac = EcommerceArbitrationService.arbitrate_merchant("pc portable gamer", preferred_merchant="Fnac")
    assert m_param_fnac.name == "Fnac"
    assert m_param_fnac.domain == "fnac.com"


# ============================================================================
# 3. TESTS D'INTÉGRITÉ INTRA-MARCHAND & NOMBRE D'ALTERNATIVES (REQUIREMENT R7)
# ============================================================================

@pytest.mark.asyncio
async def test_same_merchant_integrity_all_urls_match_arbitrated_domain():
    """
    Test capital d'intégrité R7 :
    Pour toute décision, 100% des URL du produit phare ET des alternatives
    doivent pointer strictement vers le domaine du marchand arbitré.
    Aucune dispersion multi-sites n'est tolérée.
    """
    test_queries = [
        "casque bluetooth",
        "lave linge",
        "carte graphique",
        "pc portable gamer",
        "appareil photo",
        "matelas 140x190",
        "souris gamer"
    ]
    for q in test_queries:
        card = await EcommerceArbitrationService.generate_decision_card(q)
        chosen_merchant_name = card["merchant"]["name"]
        chosen_merchant_domain = card["merchant"]["domain"]

        # 1. Vérification URL de l'offre principale
        primary_url = card["primary_recommendation"]["url"]
        assert chosen_merchant_domain in primary_url, (
            f"L'URL principale '{primary_url}' ne contient pas le domaine '{chosen_merchant_domain}'"
        )

        # 2. Vérification de chaque alternative
        alts = card["alternatives"]
        assert 3 <= len(alts) <= 4, f"Pour '{q}', attendu 3 ou 4 alternatives, obtenu {len(alts)}"

        for i, alt in enumerate(alts):
            alt_url = alt["url"]
            assert chosen_merchant_domain in alt_url, (
                f"L'alternative [{i}] '{alt['title']}' pointe sur '{alt_url}' au lieu de '{chosen_merchant_domain}'"
            )

        # 3. Vérification de l'absence totale des domaines concurrents
        competitor_domains = [p.domain for p in MERCHANT_PROFILES.values() if p.domain != chosen_merchant_domain]
        all_card_urls = [primary_url] + [a["url"] for a in alts]
        for url in all_card_urls:
            for c_dom in competitor_domains:
                assert c_dom not in url, f"Pollution multi-sites détectée : '{c_dom}' trouvé dans '{url}' !"


@pytest.mark.asyncio
async def test_alternatives_count_and_tier_differentiation():
    """Vérifie que chaque fiche propose des paliers différenciés (Économique, Qualité/Prix, Premium)."""
    card = await EcommerceArbitrationService.generate_decision_card("casque bluetooth")
    alts = card["alternatives"]
    assert len(alts) in [3, 4]

    tiers = [a["tier"] for a in alts]
    # Vérifie la présence d'au moins une alternative économique et une alternative de qualité/prix ou premium
    assert any("économique" in t.lower() or "budget" in t.lower() for t in tiers)
    assert any("qualité/prix" in t.lower() or "premium" in t.lower() for t in tiers)

    # Vérifie que les prix sont bien distincts et positifs
    prices = [a["price"] for a in alts]
    assert all(p > 0 for p in prices)
    assert len(set(prices)) >= len(prices) - 1, "Les prix des alternatives doivent être différenciés"


# ============================================================================
# 4. TESTS DU SCHÉMA DE PAYLOAD ET SYNCHRONISATION
# ============================================================================

@pytest.mark.asyncio
async def test_decision_card_payload_schema_compliance():
    """Vérifie la conformité structurelle stricte du dictionnaire payload émis."""
    card = await EcommerceArbitrationService.generate_decision_card("pc portable gamer")

    assert card["type"] == "ecommerce_arbitration_card"
    assert "merchant" in card
    assert "query" in card
    assert "primary_recommendation" in card
    assert "alternatives" in card

    m = card["merchant"]
    assert "name" in m and m["name"] in ["Amazon", "Cdiscount", "Fnac"]
    assert "domain" in m and ("amazon.fr" in m["domain"] or "cdiscount.com" in m["domain"] or "fnac.com" in m["domain"])
    assert "badge" in m and len(m["badge"]) > 0
    assert "rationale" in m and len(m["rationale"]) > 10

    p = card["primary_recommendation"]
    assert isinstance(p["title"], str) and len(p["title"]) > 0
    assert isinstance(p["price"], (int, float)) and p["price"] > 0
    assert p["currency"] == "EUR"
    assert isinstance(p["specs"], list) and len(p["specs"]) >= 2
    assert "url" in p and p["url"].startswith("http")


def test_sync_bridge_generate_decision_card_sync():
    """Vérifie que le pont synchrone fonctionne sans blocage d'Event Loop."""
    card = EcommerceArbitrationService.generate_decision_card_sync("lave linge")
    assert card["type"] == "ecommerce_arbitration_card"
    assert card["merchant"]["name"] == "Cdiscount"
    assert len(card["alternatives"]) >= 3


def test_shopping_intent_detection():
    """Vérifie le filtre de détection d'intention d'achat."""
    assert EcommerceArbitrationService.is_shopping_intent("Je veux acheter un casque bluetooth") is True
    assert EcommerceArbitrationService.is_shopping_intent("Quel est le meilleur pc portable gamer sous 1000€ ?") is True
    assert EcommerceArbitrationService.is_shopping_intent("machine a laver pas cher") is True
    assert EcommerceArbitrationService.is_shopping_intent("Quelle est la capitale de l'Australie ?") is False
    assert EcommerceArbitrationService.is_shopping_intent("Bonjour, comment vas-tu aujourd'hui ?") is False


# ============================================================================
# 5. TESTS DES ENDPOINTS REST FASTAPI
# ============================================================================

def test_api_sourcing_arbitrate_get_endpoint():
    """Vérifie l'endpoint GET /api/sourcing/arbitrate."""
    response = client.get("/api/sourcing/arbitrate?q=casque+bluetooth")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "ecommerce_arbitration_card"
    assert data["merchant"]["name"] == "Fnac"
    assert "fnac.com" in data["primary_recommendation"]["url"]
    assert len(data["alternatives"]) >= 3


def test_api_sourcing_arbitrate_post_endpoint():
    """Vérifie l'endpoint POST /api/sourcing/arbitrate."""
    response = client.post("/api/sourcing/arbitrate", json={"query": "machine a laver 9kg"})
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "ecommerce_arbitration_card"
    assert data["merchant"]["name"] == "Cdiscount"
    assert "cdiscount.com" in data["primary_recommendation"]["url"]


def test_api_sourcing_arbitrate_with_forced_merchant():
    """Vérifie l'endpoint POST avec marchand forcé."""
    response = client.post("/api/sourcing/arbitrate", json={"query": "casque audio", "merchant": "Amazon"})
    assert response.status_code == 200
    data = response.json()
    assert data["merchant"]["name"] == "Amazon"
    assert "amazon.fr" in data["primary_recommendation"]["url"]


def test_api_ecommerce_arbitrate_alias_endpoint():
    """Vérifie l'alias POST /api/ecommerce/arbitrate."""
    response = client.post("/api/ecommerce/arbitrate", json={"query": "carte graphique rtx 4070"})
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "ecommerce_arbitration_card"
    assert data["merchant"]["name"] == "Amazon"


# ============================================================================
# 6. TESTS DE RENDU FRONTEND DANS INDEX.HTML
# ============================================================================

def test_frontend_html_contains_ecommerce_arbitration_card_rendering():
    """Vérifie que index.html intègre bien le composant de carte décisionnelle Liquid Glass."""
    html_path = Path(__file__).resolve().parent.parent / "src" / "api" / "static" / "index.html"
    assert html_path.exists(), "Fichier static/index.html introuvable"
    content = html_path.read_text(encoding="utf-8")

    assert "ecommerce_arbitration_card" in content, "Type de carte ecommerce_arbitration_card manquant dans index.html"
    assert "ecommerce-arbitration-card" in content, "Classe CSS ecommerce-arbitration-card manquante"
    assert "Marchand de Référence" in content, "Libellé 'Marchand de Référence' manquant dans index.html"
    assert "Choix de Référence" in content, "Badge 'Choix de Référence' manquant dans index.html"
    assert "Alternatives disponibles sur" in content, "Section des alternatives intra-marchand manquante"


# ============================================================================
# 7. TESTS D'INTÉGRATION DU CERVEAU COGNITIF (TOOL CALLING)
# ============================================================================

def test_cognitive_engine_has_ecommerce_arbitration_tool_registered():
    """Vérifie que ecommerce_sourcing_arbitration est bien enregistré dans les outils du CognitiveAgentEngine."""
    tools = CognitiveAgentEngine.get_registered_tools()
    tool_names = [t.__name__ for t in tools if hasattr(t, "__name__")]
    assert "ecommerce_sourcing_arbitration" in tool_names, (
        f"'ecommerce_sourcing_arbitration' non trouvé parmi {tool_names}"
    )


def test_ecommerce_sourcing_arbitration_tool_execution():
    """Vérifie l'exécution directe de l'outil d'arbitrage e-commerce du CognitiveAgentEngine."""
    res = ecommerce_sourcing_arbitration(query="casque bluetooth antibruit")
    assert isinstance(res, str)
    assert "Fnac" in res
    assert "Arbitrage e-commerce réussi" in res
    assert "Carte décisionnelle générée" in res
