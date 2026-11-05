"""
Script de Démonstration Interactive en direct de l'Orchestrateur HoL AI.
Exécute des requêtes multimodales et composites à travers les 6 agents simulés.
"""
import asyncio
import sys
from pathlib import Path

# Force UTF-8 stdout sur les consoles Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Inclusion du chemin source
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import fakeredis.aioredis as fake_aioredis
from src.broker.stream_bus import StreamBus
from src.orchestrator.manager import AgentManager
from src.agents.mocks import (
    MockCanvasAgent,
    MockIngestionAgent,
    MockLogisticsAgent,
    MockFinanceAgent,
    MockContentAgent,
    MockExecutionAgent
)


async def main():
    print("=" * 75)
    print("🚀 DÉMARRAGE DU CORE ENGINE 'HoL AI' (JALON 1 : SOCLE FONDATEUR)")
    print("=" * 75)

    # 1. Initialisation du Bus d'événements
    print("\n[1/3] Initialisation du bus d'événements Redis Streams...")
    fake_client = fake_aioredis.FakeRedis(decode_responses=True)
    bus = StreamBus(redis_client=fake_client)
    await bus.connect()

    # 2. Démarrage de l'Agent Manager et des 6 Mocks
    print("[2/3] Démarrage du Superviseur (Agent Manager) et des 6 Agents spécialisés...")
    manager = AgentManager(bus)
    agents = [
        MockCanvasAgent(bus),
        MockIngestionAgent(bus),
        MockLogisticsAgent(bus),
        MockFinanceAgent(bus),
        MockContentAgent(bus),
        MockExecutionAgent(bus),
    ]

    await manager.start()
    for agent in agents:
        await agent.start()

    print("      ✓ Agent Manager : ACTIF")
    for agent in agents:
        print(f"      ✓ {agent.agent_id.value:<22} : ACTIF (Écoute sur {agent.stream_name})")

    # 3. Exécution de scénarios de démonstration
    print("\n[3/3] Exécution de scénarios d'orchestration multi-agents réels :\n")

    test_scenarios = [
        (
            "Scénario 1 (Composite : Logistique + Finance + Canvas)",
            "Suis mon colis UPS 1Z9928, calcule la marge nette de mon produit vendu 120€ et affiche la synthèse sur mon canevas"
        ),
        (
            "Scénario 2 (Moteur Social & Contenu Viral)",
            "Génère-moi un script TikTok viral sur l'automatisation e-commerce avec hook percutant"
        ),
        (
            "Scénario 3 (Anti-Procrastination & Exécution)",
            "Je suis bloqué sur le lancement de ma nouvelle campagne produit, donne-moi les micro-actions immédiates"
        )
    ]

    for title, query in test_scenarios:
        print("-" * 75)
        print(f"🔹 {title}")
        print(f"   Requête utilisateur : \"{query}\"")
        print("-" * 75)

        result = await manager.orchestrate(query)

        print(f"⏱️  Durée totale d'exécution : {result.total_duration_ms} ms")
        print(f"🔗 Correlation ID          : {result.correlation_id}")
        print(f"📊 Étapes exécutées         : {result.steps_executed}")
        print(f"📋 Synthèse de l'Orchestrateur :\n{result.synthesized_summary}\n")

    # Nettoyage
    print("=" * 75)
    print("🛑 Arrêt gracieux du cluster HoL AI...")
    await manager.stop()
    for agent in agents:
        await agent.stop()
    await bus.close()
    print("✓ Tous les services sont arrêtés avec succès.\n")


if __name__ == "__main__":
    asyncio.run(main())
