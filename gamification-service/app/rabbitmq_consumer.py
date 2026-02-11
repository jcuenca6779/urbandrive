import os
import json
import asyncio
import logging
from typing import Optional

import aio_pika

from app.gamification_logic import GamificationService
from app.redis_client import RedisGamificationClient

logger = logging.getLogger(__name__)


class RabbitMQGamificationConsumer:
    """
    Consumer de RabbitMQ para eventos del traffic-service.

    Escucha en un intercambio / cola de eventos de tráfico y procesa
    eventos de tipo 'reporte_validado'.
    """

    EXCHANGE_NAME = "traffic.events"
    QUEUE_NAME = "gamification.reports"
    ROUTING_KEYS = ["reporte_creado", "reporte_validado"]  # Múltiples routing keys

    def __init__(self, gamification_service: GamificationService) -> None:
        self.gamification_service = gamification_service
        self._connection: Optional[aio_pika.RobustConnection] = None
        self._channel: Optional[aio_pika.Channel] = None
        self._task: Optional[asyncio.Task] = None
        self._stopping: bool = False

    async def _connect(self) -> None:
        rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

        logger.info("Conectando a RabbitMQ en %s", rabbitmq_url)
        self._connection = await aio_pika.connect_robust(rabbitmq_url)
        self._channel = await self._connection.channel()

        # Declarar exchange tipo topic
        exchange = await self._channel.declare_exchange(
            self.EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
        )

        # Declarar cola para gamificación
        queue = await self._channel.declare_queue(
            self.QUEUE_NAME, durable=True
        )

        # Enlazar cola al exchange con múltiples routing keys
        for routing_key in self.ROUTING_KEYS:
            await queue.bind(exchange, routing_key=routing_key)
            logger.info(
                "Cola '%s' enlazada a exchange '%s' con routing_key '%s'",
                self.QUEUE_NAME,
                self.EXCHANGE_NAME,
                routing_key,
            )

        # Consumir mensajes
        await queue.consume(self._on_message, no_ack=False)

    async def _on_message(self, message: aio_pika.IncomingMessage) -> None:
        async with message.process(requeue=False):
            try:
                payload = json.loads(message.body.decode("utf-8"))
                event_type = payload.get("type")

                if event_type == "reporte_validado":
                    result = self.gamification_service.process_validated_report(payload)
                    logger.info("Evento reporte_validado procesado: %s", result)
                elif event_type == "reporte_creado":
                    result = self.gamification_service.process_created_report(payload)
                    logger.info("Evento reporte_creado procesado: %s", result)
                else:
                    logger.debug("Evento ignorado: %s", payload)

            except json.JSONDecodeError:
                logger.error("No se pudo decodificar mensaje de RabbitMQ: %s", message.body)
            except Exception as e:
                logger.exception("Error procesando mensaje de RabbitMQ: %s", e)

    async def start(self) -> None:
        """
        Inicia la conexión y el consumo en segundo plano.
        """
        if self._task and not self._task.done():
            return

        async def _runner():
            while not self._stopping:
                try:
                    await self._connect()
                    # Mantener la conexión activa
                    while not self._stopping:
                        await asyncio.sleep(1)
                except Exception as e:
                    logger.error("Error en consumidor de RabbitMQ: %s", e)
                    await asyncio.sleep(5)  # backoff antes de reintentar

        self._task = asyncio.create_task(_runner())

    async def stop(self) -> None:
        """
        Detiene el consumidor y cierra la conexión.
        """
        self._stopping = True
        if self._task:
            await asyncio.wait([self._task], timeout=5)

        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        if self._connection and not self._connection.is_closed:
            await self._connection.close()

