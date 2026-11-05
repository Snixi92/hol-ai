"""
Implémentation isolée des simulateurs pour les 6 agents spécialisés de HoL AI.
Chaque mock répond avec des données typées réalistes pour valider l'orchestrateur.
"""
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


class MockCanvasAgent(BaseAgent):
    def __init__(self, bus: StreamBus):
        super().__init__(AgentID.AGENT_1_CANVAS, bus)

    async def handle_message(self, message: A2AMessage) -> A2AResponse:
        action = message.target.action
        payload = message.payload

        if action == ActionType.CREATE_CANVAS_NODE:
            node_id = payload.get("node_id", "node_generated_101")
            result = {
                "created": True,
                "node": {
                    "id": node_id,
                    "type": payload.get("type", "note_card"),
                    "position": payload.get("position", {"x": 120, "y": 240}),
                    "content": payload.get("content", "Bloc synchronisé par HoL AI"),
                    "canvas_id": message.context.canvas_id or "default_workspace"
                }
            }
        else:
            result = {"action_executed": action.value, "status": "simulated_ok"}

        return A2AResponse(
            correlation_id=message.correlation_id,
            causation_id=message.message_id,
            source=SourceDescriptor(agent_id=self.agent_id, instance_id=self.instance_id),
            status=StatusEnum.SUCCESS,
            execution_metrics=ExecutionMetrics(duration_ms=0, tokens_consumed=0),
            result=result
        )


class MockIngestionAgent(BaseAgent):
    def __init__(self, bus: StreamBus):
        super().__init__(AgentID.AGENT_2_INGESTION, bus)

    async def handle_message(self, message: A2AMessage) -> A2AResponse:
        action = message.target.action
        payload = message.payload

        if action == ActionType.TRANSCRIBE_AUDIO:
            result = {
                "transcript": "Salam khoya, bghit nchouf fin wsal lcolis diali dyal la commande 9823",
                "detected_language": "darija_arabizi",
                "normalized_french": "Bonjour mon frère, je voudrais voir où en est mon colis pour la commande 9823",
                "confidence": 0.96
            }
        elif action == ActionType.OCR_DOCUMENT:
            result = {
                "extracted_text": "FACTURE F-2026-081\nMontant HT: 1500.00 EUR\nTVA 20%: 300.00 EUR\nTotal TTC: 1800.00 EUR",
                "document_type": "invoice",
                "vector_id": "vec_doc_8839"
            }
        else:
            result = {"matches_found": 3, "top_similarity": 0.89}

        return A2AResponse(
            correlation_id=message.correlation_id,
            causation_id=message.message_id,
            source=SourceDescriptor(agent_id=self.agent_id, instance_id=self.instance_id),
            status=StatusEnum.SUCCESS,
            execution_metrics=ExecutionMetrics(duration_ms=0, tokens_consumed=250),
            result=result
        )


class MockLogisticsAgent(BaseAgent):
    def __init__(self, bus: StreamBus):
        super().__init__(AgentID.AGENT_3_LOGISTICS, bus)

    async def handle_message(self, message: A2AMessage) -> A2AResponse:
        action = message.target.action
        payload = message.payload

        if action == ActionType.TRACK_SHIPMENT:
            tracking_number = payload.get("tracking_number", "1Z9999999999")
            result = {
                "tracking_number": tracking_number,
                "carrier": payload.get("carrier", "UPS"),
                "status": "EN_TRANSIT",
                "estimated_delivery": "2026-10-26T14:30:00Z",
                "last_location": "Hub Logistique Paris-Nord",
                "last_event": "Arrivé au centre de distribution régional"
            }
        else:
            result = {"price_scraped": 49.99, "currency": "EUR", "in_stock": True}

        return A2AResponse(
            correlation_id=message.correlation_id,
            causation_id=message.message_id,
            source=SourceDescriptor(agent_id=self.agent_id, instance_id=self.instance_id),
            status=StatusEnum.SUCCESS,
            execution_metrics=ExecutionMetrics(duration_ms=0, tokens_consumed=0),
            result=result
        )


class MockFinanceAgent(BaseAgent):
    def __init__(self, bus: StreamBus):
        super().__init__(AgentID.AGENT_4_FINANCE, bus)

    async def handle_message(self, message: A2AMessage) -> A2AResponse:
        action = message.target.action
        payload = message.payload

        if action == ActionType.AUDIT_MARGINS:
            selling_price = float(payload.get("selling_price", 100.0))
            cost_price = float(payload.get("cost_price", 40.0))
            platform_fee_percent = float(payload.get("platform_fee_percent", 0.15))
            vat_percent = float(payload.get("vat_percent", 0.20))

            vat_amount = selling_price * (vat_percent / (1 + vat_percent))
            revenue_ht = selling_price - vat_amount
            platform_fee = selling_price * platform_fee_percent
            net_margin = revenue_ht - cost_price - platform_fee
            margin_rate = (net_margin / revenue_ht) * 100 if revenue_ht > 0 else 0

            result = {
                "selling_price_ttc": selling_price,
                "revenue_ht": round(revenue_ht, 2),
                "cost_price": cost_price,
                "platform_fee": round(platform_fee, 2),
                "net_margin_eur": round(net_margin, 2),
                "margin_rate_percent": round(margin_rate, 2),
                "profitability_rating": "HEALTHY" if margin_rate >= 20 else "LOW"
            }
        else:
            result = {"reconciled": True, "discrepancies": 0}

        return A2AResponse(
            correlation_id=message.correlation_id,
            causation_id=message.message_id,
            source=SourceDescriptor(agent_id=self.agent_id, instance_id=self.instance_id),
            status=StatusEnum.SUCCESS,
            execution_metrics=ExecutionMetrics(duration_ms=0, tokens_consumed=0),
            result=result
        )


class MockContentAgent(BaseAgent):
    def __init__(self, bus: StreamBus):
        super().__init__(AgentID.AGENT_5_CONTENT, bus)

    async def handle_message(self, message: A2AMessage) -> A2AResponse:
        action = message.target.action
        payload = message.payload

        if action == ActionType.GENERATE_SCRIPT:
            topic = payload.get("topic", "E-commerce Automation")
            result = {
                "hook": "Arrête de vérifier tes colis et tes marges à la main !",
                "key_points": [
                    "1. Suivi autonome synchronisé sur ton canevas",
                    "2. Calcul instantané de la marge nette réelle déduite des taxes",
                    "3. Pilotage vocal direct en Darija et Français"
                ],
                "call_to_action": "Découvre comment configurer HoL AI en commentaire.",
                "multilingual_variants": {
                    "fr": "Arrête de vérifier tes colis à la main.",
                    "darija": "Baraka mat-tchecki les colis dialek b ydik kul nhar."
                }
            }
        else:
            result = {"telegram_sent": True, "message_id": 98421}

        return A2AResponse(
            correlation_id=message.correlation_id,
            causation_id=message.message_id,
            source=SourceDescriptor(agent_id=self.agent_id, instance_id=self.instance_id),
            status=StatusEnum.SUCCESS,
            execution_metrics=ExecutionMetrics(duration_ms=0, tokens_consumed=410),
            result=result
        )


class MockExecutionAgent(BaseAgent):
    def __init__(self, bus: StreamBus):
        super().__init__(AgentID.AGENT_6_EXECUTION, bus)

    async def handle_message(self, message: A2AMessage) -> A2AResponse:
        action = message.target.action
        payload = message.payload

        if action == ActionType.BREAKDOWN_GOAL:
            goal = payload.get("goal", "Lancer la nouvelle campagne produit")
            result = {
                "original_goal": goal,
                "friction_level": "ELEVATED",
                "micro_actions": [
                    {"step": 1, "action": "Ouvrir le canevas et déposer les 3 visuels produits", "estimated_mins": 2},
                    {"step": 2, "action": "Lancer le calcul de rentabilité avec l'Agent Finance", "estimated_mins": 3},
                    {"step": 3, "action": "Valider le script court généré", "estimated_mins": 2}
                ],
                "first_immediate_action": "Déposer les visuels sur le canevas (Règle des 2 minutes)"
            }
        else:
            result = {"scheduled": True, "next_run": "2026-10-24T08:00:00Z"}

        return A2AResponse(
            correlation_id=message.correlation_id,
            causation_id=message.message_id,
            source=SourceDescriptor(agent_id=self.agent_id, instance_id=self.instance_id),
            status=StatusEnum.SUCCESS,
            execution_metrics=ExecutionMetrics(duration_ms=0, tokens_consumed=180),
            result=result
        )
