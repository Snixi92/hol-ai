"""
Configuration et fixtures pytest pour la suite de tests de HoL AI.
"""
import sys
import os
from pathlib import Path
import pytest
import pytest_asyncio
import fakeredis.aioredis as fake_aioredis

# Assure que le dossier 'services/core-engine' est dans le sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

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


@pytest_asyncio.fixture
async def shared_stream_bus():
    """Crée un bus de test isolé en mémoire avec fakeredis."""
    fake_client = fake_aioredis.FakeRedis(decode_responses=True)
    bus = StreamBus(redis_client=fake_client)
    await bus.connect()
    yield bus
    await bus.close()


@pytest_asyncio.fixture
async def running_hol_cluster(shared_stream_bus):
    """
    Démarre l'écosystème complet pour les tests :
    - L'Agent Manager (Superviseur)
    - Les 6 agents spécialisés simulés (Mocks)
    """
    bus = shared_stream_bus

    # Instanciation des agents
    canvas_agent = MockCanvasAgent(bus)
    ingestion_agent = MockIngestionAgent(bus)
    logistics_agent = MockLogisticsAgent(bus)
    finance_agent = MockFinanceAgent(bus)
    content_agent = MockContentAgent(bus)
    execution_agent = MockExecutionAgent(bus)

    manager = AgentManager(bus)

    # Démarrage
    await manager.start()
    await canvas_agent.start()
    await ingestion_agent.start()
    await logistics_agent.start()
    await finance_agent.start()
    await content_agent.start()
    await execution_agent.start()

    yield {
        "manager": manager,
        "bus": bus,
        "agents": {
            "canvas": canvas_agent,
            "ingestion": ingestion_agent,
            "logistics": logistics_agent,
            "finance": finance_agent,
            "content": content_agent,
            "execution": execution_agent
        }
    }

    # Nettoyage et arrêt
    await manager.stop()
    await canvas_agent.stop()
    await ingestion_agent.stop()
    await logistics_agent.stop()
    await finance_agent.stop()
    await content_agent.stop()
    await execution_agent.stop()
