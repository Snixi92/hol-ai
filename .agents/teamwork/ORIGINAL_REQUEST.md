# Original User Request

## Approved Task Prompt — 2026-11-03T19:38:04Z

Pour garantir une rigueur absolue et ne jamais mélanger les contextes ou le code, interdiction formelle de travailler dans un flux unique : déployer une architecture multi-agents orchestrée par un Agent Manager où chaque agent a un périmètre d'action strict. Exécuter pour un usage en production une refonte et un enrichissement massifs de HoL AI combinant fonctionnalités avancées de chatbots leaders, UI/UX Apple Liquid Glass et modules autonomes spécialisés.

Working directory: C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai
Integrity mode: development

## Requirements

### R1. Orchestration Multi-Agents et Rapport d'Exécution Final (Agent Manager)
L'Agent Manager supervise et séquence l'ensemble du projet, lance et valide les livrables des sous-agents un par un sans conflits de code, d'API ou de style, crée dynamiquement des sous-agents spécialisés supplémentaires si une tâche devient trop complexe, et rédige le Rapport d'Exécution Final Détaillé couvrant l'orchestration multi-agents, la revue fonctionnelle par module, le catalogue des sources et outils, l'analyse des défis techniques et le récapitulatif des fichiers modifiés et créés.

### R2. Persistance et Historique des Conversations (Agent 1)
Développer un système de stockage persistant des discussions (IndexedDB, LocalStorage ou base de données) avec une sidebar d'historique classé chronologiquement (Aujourd'hui, 7 derniers jours, 30 jours), génération automatique du titre du chat dès les premiers échanges, actions complètes (renommer, épingler, supprimer, archiver, exporter en Markdown et JSON) et reprise instantanée du contexte exact lors du clic sur un chat passé.

### R3. Benchmark Autonome et Intégration des Fonctionnalités IA (Agent 2)
Explorer et répertorier de manière autonome les fonctionnalités phares des chatbots leaders (ChatGPT, Claude, Gemini, Perplexity), sélectionner les outils et options à plus forte valeur ajoutée et les intégrer dans le moteur de HoL AI.

### R4. UI/UX Globale et Design System Apple Liquid Glass (Agent 3)
Concevoir l'interface selon les standards ergonomiques des chatbots modernes (Input Dock en pilule flottante centrée en bas, navigation fluide) avec un rendu Liquid Glass natif sur Mobile et Desktop (réfraction optique sur les arêtes, flou progressif multicouche `backdrop-filter: blur(24px) saturate(180%)`, bordures spéculaires fines de 1px, reflets lumineux internes `inset box-shadow`, animations spring physics) et une palette neutre luxueuse (gris titane, anthracite, noir obsidienne, verre transparent, blanc cassé, icônes vectorielles nettes, sans néon ni couleurs criardes).

### R5. Automatisation Matinale et Live News (Agent 4)
Mettre en place un système autonome de Morning Briefing connecté en direct au web (actualités réelles, météo locale, tendances) avec génération dynamique adaptant le ton, les angles et la structure chaque matin pour garantir une expérience sans répétition.

### R6. Moteur de Recherche Visuelle et Enrichissement Image (Agent 5)
Détecter les entités et sujets visuels (objets, monuments, lieux, produits, concepts visuels) dans la discussion et injecter automatiquement dans la réponse une vraie photo nette et contextuelle en haute résolution, intégrée dans une carte au style Liquid Glass avec titre/badge et agrandissement possible.

### R7. Optimiseur de Recherche et Décision E-commerce (Agent 6)
Pour toute intention d'achat ou recherche produit, arbitrer en coulisses et sélectionner dynamiquement un seul marchand de référence par requête (ex: Amazon OU Cdiscount, sans liste multi-sites confuse), tout en recommandant plusieurs alternatives d'objets pertinents issus de ce marchand sélectionné avec leurs caractéristiques distinctes.

## Acceptance Criteria

### Orchestration et Rapport Final
- [ ] L'Agent Manager orchestre les sous-agents (Agent 1 à 6 et éventuels sous-agents dynamiques) et valide leurs livrables sans conflit de code ni régression.
- [ ] Le Rapport d'Exécution Final Détaillé est rédigé et contient les 5 sections obligatoires : orchestration et rôles, revue fonctionnelle par module, catalogue des sources et outils, analyse des défis techniques et solutions, et récapitulatif des fichiers modifiés et créés.

### Sauvegarde et Historique
- [ ] Les conversations sont enregistrées de façon persistante et restaurées sans perte de contexte lors de la sélection dans la sidebar.
- [ ] La sidebar regroupe les discussions par sections chronologiques (Aujourd'hui, 7 derniers jours, 30 jours).
- [ ] Les fonctionnalités de renommage automatique au début de chat, renommage manuel, épinglage, suppression, archivage et export (Markdown et JSON) sont fonctionnelles et testées.

### Benchmark et Fonctionnalités IA
- [ ] Une sélection documentée de fonctionnalités inspirées des chatbots leaders est intégrée et utilisable au sein de HoL AI.

### Design System Apple Liquid Glass
- [ ] L'interface applique le matériau Liquid Glass (flou multicouche backdrop-filter: blur(24px) saturate(180%), bordures spéculaires 1px, reflets internes inset box-shadow) sur Mobile et Desktop sans altérer la lisibilité du texte.
- [ ] L'Input Dock flottant en pilule et la navigation respectent la palette monochrome neutre (titane, anthracite, obsidienne) sans dégradés néon ni couleurs criardes.

### Morning Briefing
- [ ] Le récapitulatif matinal récupère et affiche des données fraîches du web en direct (actualités réelles, météo).
- [ ] Deux exécutions successives du briefing présentent une formulation, une structure et un angle éditorial différents sans répétition textuelle.

### Recherche Visuelle et Sourcing E-commerce
- [ ] L'évocation d'un sujet visuel entraîne l'affichage d'une carte image haute résolution contextuelle dans la réponse avec option d'agrandissement.
- [ ] Une requête produit aboutit au choix d'un unique marchand de référence cohérent pour la requête, accompagné de plusieurs alternatives de produits provenant de ce marchand.

### Intégration Système et Tests
- [ ] Une suite de tests automatisés vérifie le bon fonctionnement des endpoints backend, de la persistance, du briefing et des connecteurs de recherche.
- [ ] Le serveur FastAPI services/core-engine démarre avec succès sur le port 8000 et sert la Single Page Application sans erreur console.
