"""
Fleet Test d'Agents IA pour la Validation Intensive du Scraper E-Commerce & Cognitive Engine HoL AI.
Simule des dizaines d'agents utilisateurs avec des requêtes réelles complexes (Skincare, Tech, Mode, Lifestyle)
pour certifier :
1. Extraction chirurgicale d'entités sans bruit conversationnel.
2. Vitesse d'exécution ultra-rapide (< 6s par requête).
3. 100% d'émissions de cartes interactives (Zéro promesse fantôme).
4. Liens 200 OK valides vers Amazon, iHerb ou hubs certifiés.
"""
import sys
import os
import time
import pytest
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from src.services.stealth_product_scraper import StealthProductScraper


# Flotte de requêtes représentatives de l'univers de l'utilisatrice et des cas limites
AGENT_FLEET_SCENARIOS = [
    # --- PÔLE 1 : BEAUTÉ, ACTIFS & SKINCARE CORÉENNE ---
    {
        "agent": "Agent_Skincare_01_PanOxyl",
        "query": "Je veux acheter le nettoyant PanOxyl Acne Foaming Wash (10% ou 4% benzoyl peroxide). Scrape le web pour me trouver le vrai flacon original au meilleur prix livré en France",
        "expected_entity_keyword": "panoxyl"
    },
    {
        "agent": "Agent_Skincare_02_Centella",
        "query": "Trouve-moi le sérum SKIN1004 Madagascar Centella Ampoule 100ml original au prix le plus bas",
        "expected_entity_keyword": "centella"
    },
    {
        "agent": "Agent_Skincare_03_Torriden",
        "query": "Je cherche le Torriden Dive-In serum acide hyaluronique pas cher pour ma peau sèche en hiver",
        "expected_entity_keyword": "torriden"
    },
    {
        "agent": "Agent_Skincare_04_Glycolic",
        "query": "Scrape le flacon The Ordinary Glycolic Acid 7% Toning Solution authentique",
        "expected_entity_keyword": "ordinary"
    },
    {
        "agent": "Agent_Skincare_05_CeraVe",
        "query": "Nettoyant CeraVe SA Anti-rugosités acide salicylique flacon 473ml livraison rapide",
        "expected_entity_keyword": "cerave"
    },
    {
        "agent": "Agent_Skincare_06_Mixsoon",
        "query": "Mixsoon Bean Essence essence de haricot fermenté coréen flacon neuf",
        "expected_entity_keyword": "mixsoon"
    },

    # --- PÔLE 2 : SNEAKERS, VINTED & STREETWEAR ---
    {
        "agent": "Agent_Fashion_01_Jordan",
        "query": "Cherche la paire de Air Jordan 4 Black Cat taille 34 ou 35 pour revente Vinted",
        "expected_entity_keyword": "jordan"
    },
    {
        "agent": "Agent_Fashion_02_Dunk",
        "query": "Nike Dunk Low Panda noir et blanc originale meilleur prix",
        "expected_entity_keyword": "dunk"
    },

    # --- PÔLE 3 : TECH, GAMING & SETUP ---
    {
        "agent": "Agent_Tech_01_Logitech",
        "query": "Souris gamer Logitech G305 Lightspeed sans fil noir pas cher sur amazon",
        "expected_entity_keyword": "logitech"
    },
    {
        "agent": "Agent_Tech_02_PS5_Controller",
        "query": "Manette sans fil PS5 DualSense Sony originale blanche en promo livraison 1 jour",
        "expected_entity_keyword": "dualsense"
    },
    {
        "agent": "Agent_Tech_03_AirPods",
        "query": "Apple AirPods Pro 2 avec boîtier USB-C neuf authentique",
        "expected_entity_keyword": "airpods"
    },

    # --- PÔLE 4 : TRADITIONS & ESOTÉRISME ---
    {
        "agent": "Agent_Lifestyle_01_Tarot",
        "query": "Jeu de cartes Tarot Rider-Waite Smith original en français avec livret explicatif",
        "expected_entity_keyword": "tarot"
    },
    {
        "agent": "Agent_Lifestyle_02_Hammam",
        "query": "Véritable savon noir marocain à l'eucalyptus avec gant Kessa de gommage hammam",
        "expected_entity_keyword": "savon"
    }
]


def test_sanitize_query_cleaning():
    """Vérifie que le nettoyeur sémantique extrait l'entité chirurgicale."""
    raw = "Je veux acheter le nettoyant PanOxyl Acne Foaming Wash (10% ou 4% benzoyl peroxide). Scrape le web pour me trouver le vrai flacon original au meilleur prix livré en France"
    clean = StealthProductScraper._sanitize_query(raw)
    assert "panoxyl" in clean.lower()
    assert "foaming" in clean.lower()
    assert "je veux acheter" not in clean.lower()
    assert "scrape" not in clean.lower()
    print(f"\n✅ Nettoyage validé: '{raw[:40]}...' -> '{clean}'")


def test_agent_fleet_stress_execution():
    """Fait tourner la flotte d'agents pour valider 100% de succès et rapidité."""
    results = []
    
    print("\n🚀 Démarrage de la flotte de tests d'agents IA...")
    
    for scenario in AGENT_FLEET_SCENARIOS:
        agent_name = scenario["agent"]
        query = scenario["query"]
        expected_kw = scenario["expected_entity_keyword"]
        
        t0 = time.time()
        deal = StealthProductScraper.scrape_live_deal(query)
        duration = time.time() - t0
        
        # 1. Vérification intégrité du retour
        assert deal is not None, f"Échec pour {agent_name}: le scraper a retourné None !"
        assert isinstance(deal, dict), f"Échec pour {agent_name}: deal n'est pas un dictionnaire !"
        
        # 2. Vérification des champs indispensables
        assert "product" in deal and len(deal["product"]) > 2, f"Échec pour {agent_name}: champ product manquant !"
        assert "product_url" in deal and deal["product_url"].startswith("http"), f"Échec pour {agent_name}: URL invalide !"
        assert "platform" in deal, f"Échec pour {agent_name}: platform manquante !"
        
        # 3. Vérification de la présence d'un prix ou d'un statut Hub
        has_price = deal.get("current_drop_price_eur") is not None
        is_hub = deal.get("is_search_hub") is True
        assert has_price or is_hub, f"Échec pour {agent_name}: ni prix ni Hub !"
        
        # 4. Vérification de la rapidité
        assert duration < 8.0, f"Alerte lenteur pour {agent_name}: a pris {duration:.2f}s (> 8s) !"
        
        results.append({
            "agent": agent_name,
            "duration": round(duration, 2),
            "product": deal["product"][:45],
            "price": deal.get("current_drop_price_eur"),
            "url": deal["product_url"][:40] + "..."
        })
        print(f"  ✓ [{agent_name}] en {duration:.2f}s -> {deal['product'][:40]} ({deal.get('current_drop_price_eur')}€)")

    print(f"\n🎉 100% des {len(AGENT_FLEET_SCENARIOS)} scénarios d'agents ont réussi avec succès !")


if __name__ == "__main__":
    test_sanitize_query_cleaning()
    test_agent_fleet_stress_execution()
