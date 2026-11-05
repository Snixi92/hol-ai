"""
Suite de tests de validation d'orchestration pour le Jalon 1 de HoL AI.
Vérifie le contrat de communication A2A, le bus Redis Streams,
la coordination multi-agents et la synthèse du Manager.
"""
import pytest
from uuid import uuid4
from src.core.contracts import (
    A2AMessage,
    A2AResponse,
    SourceDescriptor,
    TargetDescriptor,
    AgentID,
    ActionType,
    PriorityEnum,
    StatusEnum,
    ContextModel,
    ExecutionMetrics
)
from src.orchestrator.planner import IntentPlanner, SubTask


def test_contracts_serialization_and_validation():
    """Valide l'intégrité de la sérialisation Pydantic v2 de l'enveloppe universelle."""
    correlation_id = uuid4()
    msg = A2AMessage(
        correlation_id=correlation_id,
        source=SourceDescriptor(agent_id=AgentID.MANAGER, instance_id="mgr-test", role="supervisor"),
        target=TargetDescriptor(agent_id=AgentID.AGENT_4_FINANCE, action=ActionType.AUDIT_MARGINS),
        priority=PriorityEnum.HIGH,
        context=ContextModel(user_id="user_test_42", session_id="ses_abc123"),
        payload={"selling_price": 100.0, "cost_price": 40.0}
    )

    json_str = msg.to_json()
    assert isinstance(json_str, str)
    assert str(correlation_id) in json_str

    deserialized = A2AMessage.from_json(json_str)
    assert deserialized.correlation_id == correlation_id
    assert deserialized.target.action == ActionType.AUDIT_MARGINS
    assert deserialized.payload["selling_price"] == 100.0


def test_intent_planner_dag_generation():
    """Vérifie que le planificateur détecte les intentions composites et ordonnance les dépendances."""
    context = ContextModel(user_id="usr_1", session_id="ses_1")
    intent = "Suis mon colis UPS, calcule ma marge sur la vente et affiche un bloc sur le canevas"

    plan = IntentPlanner.create_plan_from_intent(intent, context)

    assert len(plan.tasks) == 3
    agents = [t.target_agent for t in plan.tasks]
    assert AgentID.AGENT_3_LOGISTICS in agents
    assert AgentID.AGENT_4_FINANCE in agents
    assert AgentID.AGENT_1_CANVAS in agents

    # Vérification que le canvas dépend des étapes précédentes
    canvas_task = next(t for t in plan.tasks if t.target_agent == AgentID.AGENT_1_CANVAS)
    assert len(canvas_task.depends_on) > 0


@pytest.mark.asyncio
async def test_single_agent_dispatch(running_hol_cluster):
    """Vérifie la délégation directe à un sous-agent et la réception de sa réponse typée."""
    cluster = running_hol_cluster
    manager = cluster["manager"]

    context = ContextModel(user_id="usr_01", session_id="ses_01")
    task = SubTask(
        target_agent=AgentID.AGENT_3_LOGISTICS,
        action=ActionType.TRACK_SHIPMENT,
        payload={"tracking_number": "1Z99999999", "carrier": "UPS"}
    )

    correlation_id = uuid4()
    response: A2AResponse = await manager.execute_task(
        task=task,
        correlation_id=correlation_id,
        context=context,
        injected_context={}
    )

    assert response.status == StatusEnum.SUCCESS
    assert response.source.agent_id == AgentID.AGENT_3_LOGISTICS
    assert response.result["tracking_number"] == "1Z99999999"
    assert response.result["status"] == "EN_TRANSIT"


@pytest.mark.asyncio
async def test_composite_multi_agent_orchestration(running_hol_cluster):
    """
    Test E2E Majeur :
    Une requête utilisateur composite implique successivement l'Agent 3 (Logistique),
    l'Agent 4 (Finance) et l'Agent 1 (Canvas).
    """
    cluster = running_hol_cluster
    manager = cluster["manager"]

    query = "Suis mon colis UPS 1Z99, calcule ma marge sur le produit vendu à 120€ et ajoute un bloc sur le canevas"

    res = await manager.orchestrate(query)

    assert res.success is True
    assert res.steps_executed == 3
    assert len(res.errors) == 0

    # Vérification des résultats agrégés
    assert AgentID.AGENT_3_LOGISTICS.value in res.results_by_agent
    assert AgentID.AGENT_4_FINANCE.value in res.results_by_agent
    assert AgentID.AGENT_1_CANVAS.value in res.results_by_agent

    # Vérification de la logique financière calculée
    finance_res = res.results_by_agent[AgentID.AGENT_4_FINANCE.value]
    assert finance_res["selling_price_ttc"] == 120.0
    assert finance_res["net_margin_eur"] > 0
    assert finance_res["profitability_rating"] in ["HEALTHY", "LOW"]

    # Vérification de la synthèse générée
    assert "Logistique" in res.synthesized_summary
    assert "Finance & Audit" in res.synthesized_summary
    assert "Canvas" in res.synthesized_summary
