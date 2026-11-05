"""
Tests de Stress Concurrence, Deadlock & Robustesse DAG pour Muse-X OS.
Valide la haute résilience du bus Redis Streams, l'orchestrateur multi-agents sous charge,
et la détection de cycles/dépendances orphelines dans les graphes d'exécution (DAG).
"""
import sys
import asyncio
from pathlib import Path
import pytest
import pytest_asyncio
import fakeredis.aioredis as fake_aioredis

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.core.contracts import (
    AgentID,
    ActionType,
    PriorityEnum,
    ContextModel
)
from src.orchestrator.planner import (
    IntentPlanner,
    SubTask,
    ExecutionPlan,
    CyclicDependencyError
)
from src.broker.stream_bus import StreamBus


# ============================================================================
# 1. DAG INTEGRITY & CYCLE DETECTION TESTS
# ============================================================================

def test_dag_direct_cycle_detection():
    """Détecte immédiatement un cycle direct A -> B -> A et lève CyclicDependencyError."""
    task_a = SubTask(
        task_id="task_A",
        target_agent=AgentID.AGENT_1_CANVAS,
        action=ActionType.CREATE_CANVAS_NODE,
        payload={"title": "Task A"},
        depends_on=["task_B"]
    )
    task_b = SubTask(
        task_id="task_B",
        target_agent=AgentID.AGENT_4_FINANCE,
        action=ActionType.AUDIT_MARGINS,
        payload={"price": 100},
        depends_on=["task_A"]
    )
    plan = ExecutionPlan(
        original_intent="Test direct cycle",
        context=ContextModel(user_id="test_user", session_id="sess_1"),
        tasks=[task_a, task_b],
        estimated_total_steps=2
    )

    with pytest.raises(CyclicDependencyError) as exc_info:
        IntentPlanner.validate_plan(plan)
    assert "Cycle" in str(exc_info.value)


def test_dag_self_referencing_loop():
    """Détecte une auto-dépendance réflexive A -> A."""
    task_self = SubTask(
        task_id="task_SELF",
        target_agent=AgentID.AGENT_3_LOGISTICS,
        action=ActionType.TRACK_SHIPMENT,
        payload={"tracking": "1Z999"},
        depends_on=["task_SELF"]
    )
    plan = ExecutionPlan(
        original_intent="Test self loop",
        context=ContextModel(user_id="test_user", session_id="sess_2"),
        tasks=[task_self],
        estimated_total_steps=1
    )

    with pytest.raises(CyclicDependencyError):
        IntentPlanner.validate_plan(plan)


def test_dag_three_node_transitive_cycle():
    """Détecte un cycle transitif à trois étapes A -> B -> C -> A."""
    t1 = SubTask(task_id="T1", target_agent=AgentID.AGENT_1_CANVAS, action=ActionType.CREATE_CANVAS_NODE, payload={}, depends_on=["T2"])
    t2 = SubTask(task_id="T2", target_agent=AgentID.AGENT_2_INGESTION, action=ActionType.INGEST_MULTIMODAL, payload={}, depends_on=["T3"])
    t3 = SubTask(task_id="T3", target_agent=AgentID.AGENT_5_CONTENT, action=ActionType.GENERATE_AFFILIATE_DROP, payload={}, depends_on=["T1"])

    plan = ExecutionPlan(
        original_intent="Test 3-cycle",
        context=ContextModel(user_id="test_user", session_id="sess_3"),
        tasks=[t1, t2, t3],
        estimated_total_steps=3
    )

    with pytest.raises(CyclicDependencyError):
        IntentPlanner.validate_plan(plan)


def test_dag_valid_diamond_dependency():
    """Vérifie qu'un DAG en diamant valide (A -> B, A -> C, B -> D, C -> D) est accepté sans faux positif."""
    t_a = SubTask(task_id="A", target_agent=AgentID.AGENT_1_CANVAS, action=ActionType.CREATE_CANVAS_NODE, payload={})
    t_b = SubTask(task_id="B", target_agent=AgentID.AGENT_2_INGESTION, action=ActionType.INGEST_MULTIMODAL, payload={}, depends_on=["A"])
    t_c = SubTask(task_id="C", target_agent=AgentID.AGENT_3_LOGISTICS, action=ActionType.TRACK_SHIPMENT, payload={}, depends_on=["A"])
    t_d = SubTask(task_id="D", target_agent=AgentID.AGENT_4_FINANCE, action=ActionType.AUDIT_MARGINS, payload={}, depends_on=["B", "C"])

    plan = ExecutionPlan(
        original_intent="Test Diamond DAG",
        context=ContextModel(user_id="test_user", session_id="sess_diamond"),
        tasks=[t_a, t_b, t_c, t_d],
        estimated_total_steps=4
    )

    # Doit valider sans lever d'exception
    IntentPlanner.validate_plan(plan)


# ============================================================================
# 2. STREAMBUS HIGH-FREQUENCY CONCURRENCY TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_streambus_high_throughput_burst():
    """Vérifie que le StreamBus encaisse 50 publications asynchrones quasi-instantanées sans perte."""
    fake_client = fake_aioredis.FakeRedis(decode_responses=True)
    bus = StreamBus(redis_client=fake_client)
    await bus.connect()

    stream_name = "stream:test:burst"
    group_name = "group_burst"
    await bus.ensure_consumer_group(stream_name, group_name)

    # 50 messages en parallèle
    async def publish_one(i: int):
        await bus.publish_raw(stream_name, {"message_index": i, "payload": f"burst_data_{i}"})

    await asyncio.gather(*[publish_one(i) for i in range(50)])

    # Lecture des messages
    messages = await bus.read_from_group(stream_name, group_name, "consumer_01", count=50, block_ms=500)
    assert len(messages) == 50

    # Acquittement en masse
    for msg_id, _ in messages:
        await bus.ack(stream_name, group_name, msg_id)

    await bus.close()


# ============================================================================
# 3. CONCURRENT ORCHESTRATION UNDER LOAD
# ============================================================================

@pytest.mark.asyncio
async def test_orchestrator_parallel_stress(running_hol_cluster):
    """
    Exécute 15 requêtes d'orchestration multi-agents simultanées.
    Vérifie l'absence de deadlock et l'isolation parfaite des sessions.
    """
    manager = running_hol_cluster["manager"]

    intents = [
        "Suis mon colis UPS 1Z001, calcule ma marge sur vente 100€ coût 40€",
        "Génère un script viral TikTok mode pour Hacoo hoodie 39€",
        "Ajoute une note urgente sur le canevas avec rappel 14h",
        "Analyse le reçu de 85€ déjeuner d'affaires brasserie",
        "Décompose mon projet de lancement e-commerce en micro-actions"
    ] * 3  # 15 requêtes en concurrence absolue

    async def execute_query(idx: int, query: str):
        ctx = ContextModel(user_id=f"user_load_{idx}", session_id=f"sess_load_{idx}")
        res = await manager.orchestrate(query, context=ctx)
        assert res is not None
        assert res.success is True
        assert len(res.results_by_agent) >= 1
        assert res.original_intent == query
        return res

    results = await asyncio.gather(*[execute_query(i, q) for i, q in enumerate(intents)])
    assert len(results) == 15
    for r in results:
        assert r.success is True
