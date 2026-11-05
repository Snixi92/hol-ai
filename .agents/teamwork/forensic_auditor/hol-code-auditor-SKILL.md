---
name: hol-code-auditor
description: Skill d'analyse statique, d'inspection de flux d'architecture et de revue de code exhaustive pour HoL AI (services, agents, orchestrateur, scrapers).
---

# HoL Code Auditor

Ce skill fournit un protocole d'analyse statique et de vérification d'architecture pour le moteur HoL AI (`services/core-engine`).

## 1. Objectifs d'Audit
- Cartographier 100% des composants : `src/services`, `src/agents`, `src/orchestrator`, `src/api`, `src/broker`, `src/core`.
- Vérifier les contrats d'échange (`src/core/contracts.py`) et la cohérence des messages `StreamBus`.
- Inspecter les regex de parsing d'entités, de détection de marque et de budget.
- Repérer les hard-codages, les fausses promesses ou contournements de requêtes (ex: substitution d'un smartphone complet au lieu de pièces détachées, biais vers Amazon exclusif).
- Analyser la gestion des erreurs, les timeouts, et la résilience aux pannes réseau ou d'API.

## 2. Checklist d'Inspection
1. **Pôle E-Commerce & Sourcing :**
   - Neutralité des marchands : support de Cdiscount, Fnac, Darty, BackMarket, AliExpress, etc. sans forcer Amazon.
   - Cohérence sémantique : différenciation stricte entre appareil complet vs pièce détachée (écran, batterie, vitre).
   - Cohérence matérielle : vérification de faisabilité réaliste (ex: pas de promesse de faire tourner RDR2 nativement sur un PC de bureautique à 150€).
2. **Pôle Parsing & Langage Naturel :**
   - Gestion des fautes de frappe et phonétique ("souris bleuthooth < 30eur", "ecran ifone").
   - Gestion stricte des budgets ("< 30eur", "moins de 50€").
   - Anaphores et contextes multi-tours ("le premier", "en rouge", "ouvre-le").
3. **Pôle Système & Automatisation :**
   - Contrôle d'applications Windows : lancement, listage, fermeture et bascule de fenêtres sans blocage de boucle d'événements.
