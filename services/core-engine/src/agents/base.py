"""
Classe de base abstraite pour tous les agents spécialisés de HoL AI.
Gère le cycle de vie asynchrone, la consommation sur Redis Streams et le contrat I/O.
"""
import abc
import asyncio
import logging
import time
from typing import Optional
from src.core.contracts import (
    AgentID,
    A2AMessage,
    A2AResponse,
    SourceDescriptor,
    StatusEnum,
    ExecutionMetrics
)
from src.broker.stream_bus import StreamBus
from src.broker.topics import (
    get_stream_for_agent,
    get_consumer_group,
    STREAM_MANAGER_INBOUND
)

logger = logging.getLogger("hol_ai.agent")


class BaseAgent(abc.ABC):
    def __init__(self, agent_id: AgentID, bus: StreamBus, instance_id: Optional[str] = None):
        self.agent_id: AgentID = agent_id
        self.bus: StreamBus = bus
        self.instance_id: str = instance_id or f"{agent_id.value}-worker-01"
        self.stream_name: str = get_stream_for_agent(agent_id)
        self.consumer_group: str = get_consumer_group(agent_id)
        self._is_running: bool = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Initialise le groupe de consommateurs et lance la boucle d'écoute."""
        await self.bus.ensure_consumer_group(self.stream_name, self.consumer_group)
        self._is_running = True
        self._task = asyncio.create_task(self._listen_loop())
        logger.info(f"Agent [{self.agent_id.value}] démarré et en écoute sur '{self.stream_name}'")

    async def stop(self):
        """Arrêt gracieux de l'agent."""
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"Agent [{self.agent_id.value}] arrêté.")

    async def _listen_loop(self):
        """Boucle de consommation en tâche de fond."""
        while self._is_running:
            try:
                messages = await self.bus.read_from_group(
                    stream=self.stream_name,
                    group_name=self.consumer_group,
                    consumer_name=self.instance_id,
                    count=20,
                    block_ms=200
                )

                if messages:
                    tasks = [self._process_incoming(redis_msg_id, fields) for redis_msg_id, fields in messages]
                    await asyncio.gather(*tasks, return_exceptions=True)
                else:
                    await asyncio.sleep(0.05)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erreur inattendue dans la boucle de l'agent [{self.agent_id.value}]: {e}")
                await asyncio.sleep(0.1)

    async def _process_incoming(self, redis_msg_id: str, fields: dict):
        """Traite et valide un message individuel."""
        start_time = time.perf_counter()
        raw_json = fields.get("json", "{}")

        try:
            message = A2AMessage.from_json(raw_json)
        except Exception as parse_err:
            logger.error(f"Format de message invalide reçu par [{self.agent_id.value}]: {parse_err}")
            await self.bus.send_to_dlq(self.stream_name, redis_msg_id, fields, str(parse_err))
            await self.bus.ack(self.stream_name, self.consumer_group, redis_msg_id)
            return

        try:
            # Délégation à la logique métier de l'agent spécialisé
            response = await self.handle_message(message)
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            response.execution_metrics.duration_ms = duration_ms

            # Envoi de la réponse au Superviseur (Manager)
            await self.bus.publish(STREAM_MANAGER_INBOUND, response)

            # Acquittement du message
            await self.bus.ack(self.stream_name, self.consumer_group, redis_msg_id)

        except Exception as exec_err:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"Échec d'exécution dans [{self.agent_id.value}]: {exec_err}", exc_info=True)

            error_response = A2AResponse(
                correlation_id=message.correlation_id,
                causation_id=message.message_id,
                source=SourceDescriptor(agent_id=self.agent_id, instance_id=self.instance_id),
                status=StatusEnum.FAILED,
                execution_metrics=ExecutionMetrics(duration_ms=duration_ms),
                error=str(exec_err)
            )
            await self.bus.publish(STREAM_MANAGER_INBOUND, error_response)
            await self.bus.ack(self.stream_name, self.consumer_group, redis_msg_id)

    @abc.abstractmethod
    async def handle_message(self, message: A2AMessage) -> A2AResponse:
        """
        Logique métier spécifique implémentée par chaque agent.
        Doit retourner une enveloppe A2AResponse.
        """
        pass
