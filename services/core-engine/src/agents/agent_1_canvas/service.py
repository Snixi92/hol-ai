"""
Moteur spatial de l'Agent 1 (Canvas & Workspace).
Gère la géométrie spatiale, les types de formes, les liaisons logiques et l'auto-agencement.
"""
import math
from typing import Dict, Any, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator
from src.core.contracts import (
    AgentID,
    ActionType,
    A2AMessage,
    A2AResponse,
    SourceDescriptor,
    StatusEnum,
    ExecutionMetrics
)
from src.agents.base import BaseAgent
from src.broker.stream_bus import StreamBus


class Position(BaseModel):
    x: float
    y: float

    @field_validator("x", "y", mode="before")
    @classmethod
    def validate_finite(cls, v: Any) -> float:
        if v is None:
            raise ValueError("Coordinate cannot be null")
        try:
            val = float(v)
            if not math.isfinite(val):
                raise ValueError("Coordinate must be a finite number")
            return val
        except (ValueError, TypeError):
            raise ValueError("Coordinate must be a valid number")


class Dimensions(BaseModel):
    width: float = 320.0
    height: float = 200.0


class CanvasNode(BaseModel):
    id: str = Field(default_factory=lambda: f"node_{uuid4().hex[:8]}")
    type: str  # 'logistics', 'finance', 'content', 'execution', 'memory', 'note'
    title: str
    position: Position
    dimensions: Dimensions = Field(default_factory=Dimensions)
    data: Dict[str, Any] = Field(default_factory=dict)
    connected_to: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: "2026-10-24T01:00:00Z")


class CanvasAgent(BaseAgent):
    def __init__(self, bus: StreamBus):
        super().__init__(AgentID.AGENT_1_CANVAS, bus)
        self.workspace_nodes: Dict[str, CanvasNode] = {}
        self._init_default_workspace()

    def _init_default_workspace(self):
        """Initialise les 5 blocs interactifs de démonstration spatiale interconnectés."""
        node_welcome = CanvasNode(
            id="node_welcome",
            type="note",
            title="Bienvenue sur Muse-X Spatial OS",
            position=Position(x=60, y=80),
            dimensions=Dimensions(width=340, height=210),
            data={
                "content": "Canevas infini 2D ultra-fluide 60 FPS.\n"
                           "• Glissez pour faire un Pan, molette pour Zoomer.\n"
                           "• Déplacez les cartes en Drag & Drop (WS temps réel).\n"
                           "• Glissez-déposez n'importe quel fichier sur l'écran pour l'ingérer avec l'Agent 2 !",
                "badge": "ADN Spatial Muse x1000",
                "color": "#6366f1"
            },
            connected_to=["node_pkg", "node_deal"]
        )

        node_pkg = CanvasNode(
            id="node_pkg",
            type="logistics",
            title="Colis UPS Express • 1Z99283749281",
            position=Position(x=460, y=80),
            dimensions=Dimensions(width=360, height=240),
            data={
                "carrier": "UPS",
                "tracking_number": "1Z99283749281",
                "status": "EN_TRANSIT",
                "progress_percent": 75,
                "current_location": "Chilly-Mazarin, France",
                "estimated_delivery": "2026-10-26 14:00 (Créneau garanti)",
                "customs_cleared": True
            },
            connected_to=["node_cfo"]
        )

        node_cfo = CanvasNode(
            id="node_cfo",
            type="finance",
            title="Audit Marge CFO • Vente 140€",
            position=Position(x=880, y=80),
            dimensions=Dimensions(width=360, height=250),
            data={
                "selling_price_ttc": 140.0,
                "cost_price": 48.0,
                "gross_margin": 68.6,
                "vat_amount": 23.33,
                "stripe_fee": 2.35,
                "net_profit": 66.57,
                "status": "PROFITABLE"
            },
            connected_to=[]
        )

        node_deal = CanvasNode(
            id="node_deal",
            type="deal",
            title="Alerte Deal (-22%) • PS5 Slim",
            position=Position(x=460, y=380),
            dimensions=Dimensions(width=360, height=260),
            data={
                "product": "Sony PlayStation 5 Slim",
                "platform": "Amazon.fr",
                "current_drop_price_eur": 429.00,
                "historical_average_eur": 549.99,
                "savings_percent": 22.0,
                "deal_urgency": "⚡ Vente Flash Amazon",
                "stock_remaining": 8,
                "approval_action_id": "act_buy_ps5_direct"
            },
            connected_to=["node_act"]
        )

        node_act = CanvasNode(
            id="node_act",
            type="execution",
            title="Micro-Actions (Règle des 2 Min)",
            position=Position(x=880, y=380),
            dimensions=Dimensions(width=360, height=250),
            data={
                "micro_actions": [
                    {"step": 1, "action": "Vérifier l'arrivée du colis UPS", "duration_min": 1, "done": True},
                    {"step": 2, "action": "Valider la marge CFO de 66.57€", "duration_min": 2, "done": True},
                    {"step": 3, "action": "Confirmer l'achat flash PS5 à 429€", "duration_min": 2, "done": False}
                ]
            },
            connected_to=[]
        )

        self.workspace_nodes[node_welcome.id] = node_welcome
        self.workspace_nodes[node_pkg.id] = node_pkg
        self.workspace_nodes[node_cfo.id] = node_cfo
        self.workspace_nodes[node_deal.id] = node_deal
        self.workspace_nodes[node_act.id] = node_act

    def get_all_nodes(self) -> List[Dict[str, Any]]:
        return [node.model_dump() for node in self.workspace_nodes.values()]

    async def handle_message(self, message: A2AMessage) -> A2AResponse:
        action = message.target.action
        payload = message.payload

        if action == ActionType.CREATE_CANVAS_NODE:
            node_type = payload.get("type", "note")
            title = payload.get("title", "Nouveau Bloc")
            pos = payload.get("position", {"x": 200 + (len(self.workspace_nodes) * 50), "y": 150 + (len(self.workspace_nodes) * 40)})
            dims = payload.get("dimensions", {"width": 340, "height": 220})
            data = payload.get("data", payload.get("content", {}))
            if isinstance(data, str):
                data = {"content": data}

            node = CanvasNode(
                id=payload.get("node_id", f"node_{uuid4().hex[:8]}"),
                type=node_type,
                title=title,
                position=Position(**pos),
                dimensions=Dimensions(**dims),
                data=data,
                connected_to=payload.get("connected_to", [])
            )
            self.workspace_nodes[node.id] = node

            result = {
                "created": True,
                "node": node.model_dump(),
                "total_nodes": len(self.workspace_nodes)
            }

        elif action == ActionType.UPDATE_CANVAS_NODE:
            node_id = payload.get("node_id")
            if node_id in self.workspace_nodes:
                node = self.workspace_nodes[node_id]
                if "position" in payload:
                    node.position = Position(**payload["position"])
                if "data" in payload:
                    node.data.update(payload["data"])
                if "title" in payload:
                    node.title = payload["title"]
                result = {"updated": True, "node": node.model_dump()}
            else:
                result = {"updated": False, "error": "Node not found"}

        elif action == ActionType.CONNECT_NODES:
            source_id = payload.get("source_id")
            target_id = payload.get("target_id")
            if source_id in self.workspace_nodes and target_id in self.workspace_nodes:
                if target_id not in self.workspace_nodes[source_id].connected_to:
                    self.workspace_nodes[source_id].connected_to.append(target_id)
                result = {"connected": True, "source": source_id, "target": target_id}
            else:
                result = {"connected": False, "error": "Nodes not found"}

        elif action == ActionType.FETCH_WORKSPACE_STATE:
            result = {"nodes": self.get_all_nodes()}

        else:
            result = {"action": action.value, "status": "executed"}

        return A2AResponse(
            correlation_id=message.correlation_id,
            causation_id=message.message_id,
            source=SourceDescriptor(agent_id=self.agent_id, instance_id=self.instance_id),
            status=StatusEnum.SUCCESS,
            execution_metrics=ExecutionMetrics(duration_ms=5, tokens_consumed=0),
            result=result
        )
