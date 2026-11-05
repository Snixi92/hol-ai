"""
Bus d'événements asynchrone basé sur Redis Streams (ou fakeredis en fallback de développement).
Gère la persistance at-least-once, les consumer groups, l'acquittement XACK et la DLQ.
"""
import asyncio
import logging
from typing import Optional, List, Tuple, Dict, Any
from uuid import uuid4
import redis.asyncio as aioredis
from src.core.config import settings
from src.core.contracts import A2AMessage, A2AResponse
from src.broker.topics import STREAM_DEAD_LETTER_QUEUE

logger = logging.getLogger("hol_ai.broker")


class StreamBus:
    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        self.redis: Optional[aioredis.Redis] = redis_client
        self._is_fake: bool = False
        self._connect_lock: Optional[asyncio.Lock] = None

    @property
    def connect_lock(self) -> asyncio.Lock:
        if self._connect_lock is None:
            self._connect_lock = asyncio.Lock()
        return self._connect_lock

    async def connect(self):
        """Initialise la connexion à Redis ou bascule en fakeredis si nécessaire."""
        if self.redis is not None:
            return

        async with self.connect_lock:
            if self.redis is not None:
                return

            try:
                client = aioredis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD or None,
                    decode_responses=True,
                    socket_timeout=1.5,
                    socket_connect_timeout=1.5
                )
                await client.ping()
                self.redis = client
                logger.info(f"Connecté avec succès au serveur Redis physique ({settings.REDIS_HOST}:{settings.REDIS_PORT})")
            except Exception as e:
                if settings.USE_FAKEREDIS:
                    logger.warning(f"Impossible de joindre Redis local ({e}). Activation automatique du mode FakeRedis en mémoire.")
                    import fakeredis.aioredis as fake_aioredis
                    self.redis = fake_aioredis.FakeRedis(decode_responses=True)
                    self._is_fake = True
                else:
                    raise ConnectionError(f"Échec de connexion Redis : {e}")

    async def close(self):
        """Ferme proprement la connexion Redis."""
        if self.redis:
            if hasattr(self.redis, "aclose"):
                await self.redis.aclose()
            else:
                await self.redis.close()
            self.redis = None

    async def ensure_consumer_group(self, stream: str, group_name: str):
        """Crée le consumer group de manière idempotente (tolère BUSYGROUP)."""
        await self.connect()
        try:
            # MKSTREAM crée le stream s'il n'existe pas encore
            await self.redis.xgroup_create(stream, group_name, id="$", mkstream=True)
            logger.debug(f"Consumer group '{group_name}' créé sur le stream '{stream}'")
        except Exception as e:
            err_msg = str(e).upper()
            if "BUSYGROUP" in err_msg or "ALREADY EXISTS" in err_msg:
                logger.debug(f"Consumer group '{group_name}' existe déjà sur '{stream}'")
            else:
                raise e

    async def publish(self, stream: str, message: A2AMessage | A2AResponse) -> str:
        """Publie un message typé sur un stream Redis."""
        await self.connect()
        try:
            raw_json = message.to_json() if hasattr(message, "to_json") else str(message)
            correlation_id = str(getattr(message, "correlation_id", uuid4()))
            priority_val = getattr(message, "priority", "MEDIUM")
            if hasattr(priority_val, "value"):
                priority_val = priority_val.value
        except Exception as e:
            logger.error(f"Erreur de sérialisation pour '{stream}': {e}")
            raise ValueError(f"Sérialisation impossible du message: {e}") from e

        payload_data = {
            "type": "A2AMessage" if isinstance(message, A2AMessage) else "A2AResponse",
            "json": raw_json,
            "correlation_id": correlation_id,
            "priority": str(priority_val)
        }
        msg_id = await self.redis.xadd(stream, payload_data)
        logger.debug(f"Message publié sur '{stream}' (ID Redis: {msg_id}, Correlation: {correlation_id})")
        return msg_id

    async def publish_raw(self, stream: str, payload_data: Dict[str, Any]) -> str:
        """Publie une charge brute (ex: stress-test ou injection de payload non formatée)."""
        await self.connect()
        msg_id = await self.redis.xadd(stream, payload_data)
        return msg_id

    async def read_from_group(
        self,
        stream: str,
        group_name: str,
        consumer_name: str,
        count: int = 1,
        block_ms: int = 1000
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """Lit les nouveaux messages assignés au groupe de consommateurs."""
        await self.connect()
        try:
            # ">" signifie : seulement les nouveaux messages non encore délivrés à un autre consommateur du groupe
            response = await self.redis.xreadgroup(
                groupname=group_name,
                consumername=consumer_name,
                streams={stream: ">"},
                count=count,
                block=block_ms
            )
            if not response:
                if self._is_fake:
                    await asyncio.sleep(min(block_ms / 1000.0 if block_ms else 0.05, 0.05))
                return []

            results = []
            for stream_name, messages in response:
                for msg_id, fields in messages:
                    results.append((msg_id, fields))
            return results
        except Exception as e:
            err_msg = str(e)
            if "NOGROUP" in err_msg:
                logger.warning(f"Consumer group '{group_name}' manquant sur {stream}, recréation automatique.")
                try:
                    await self.ensure_consumer_group(stream, group_name)
                    response = await self.redis.xreadgroup(
                        groupname=group_name,
                        consumername=consumer_name,
                        streams={stream: ">"},
                        count=count,
                        block=block_ms
                    )
                    if not response:
                        return []
                    results = []
                    for stream_name, messages in response:
                        for msg_id, fields in messages:
                            results.append((msg_id, fields))
                    return results
                except Exception as retry_err:
                    logger.error(f"Échec de lecture après recréation de groupe sur {stream}: {retry_err}")
                    return []
            logger.error(f"Erreur lors de la lecture sur {stream} (groupe {group_name}): {e}")
            return []

    async def ack(self, stream: str, group_name: str, redis_msg_id: str):
        """Acquitte le message traité avec succès."""
        await self.connect()
        await self.redis.xack(stream, group_name, redis_msg_id)
        logger.debug(f"Message {redis_msg_id} acquitté sur {stream}")

    async def send_to_dlq(self, original_stream: str, redis_msg_id: str, raw_fields: dict, error_reason: str):
        """Transfère un message en échec vers la Dead-Letter Queue pour audit."""
        await self.connect()
        dlq_payload = {
            "original_stream": original_stream,
            "original_redis_id": redis_msg_id,
            "error_reason": error_reason,
            "raw_payload": str(raw_fields)
        }
        await self.redis.xadd(STREAM_DEAD_LETTER_QUEUE, dlq_payload)
        logger.warning(f"Message {redis_msg_id} transféré vers la Dead-Letter Queue : {error_reason}")

