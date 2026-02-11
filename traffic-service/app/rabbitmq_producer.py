import os
import json
import asyncio
import logging
from typing import Optional

import aio_pika

logger = logging.getLogger(__name__)


class RabbitMQProducer:
    """
    Producer de RabbitMQ para publicar eventos del traffic-service.
    
    Maneja reconexiones automáticas usando aio_pika.connect_robust.
    Publica mensajes en el exchange 'urban_drive_events'.
    """

    EXCHANGE_NAME = "urban_drive_events"
    EXCHANGE_TYPE = aio_pika.ExchangeType.TOPIC

    def __init__(self):
        self._connection: Optional[aio_pika.RobustConnection] = None
        self._channel: Optional[aio_pika.Channel] = None
        self._exchange: Optional[aio_pika.Exchange] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        self._is_connected: bool = False
        self._lock = asyncio.Lock()

    async def _connect(self) -> None:
        """
        Establece conexión robusta con RabbitMQ y declara el exchange.
        """
        rabbitmq_url = os.getenv(
            "RABBITMQ_URL", 
            "amqp://guest:guest@rabbitmq:5672/"
        )

        try:
            logger.info("Conectando a RabbitMQ en %s", rabbitmq_url)
            self._connection = await aio_pika.connect_robust(
                rabbitmq_url,
                client_properties={
                    "connection_name": "traffic-service-producer",
                }
            )
            
            # Configurar callbacks de reconexión
            self._connection.add_close_callback(self._on_connection_closed)
            
            self._channel = await self._connection.channel()
            
            # Declarar exchange tipo topic (durable para persistencia)
            self._exchange = await self._channel.declare_exchange(
                self.EXCHANGE_NAME,
                self.EXCHANGE_TYPE,
                durable=True,
            )
            
            self._is_connected = True
            logger.info(
                "Conectado exitosamente a RabbitMQ. Exchange '%s' declarado.",
                self.EXCHANGE_NAME
            )
            
        except Exception as e:
            self._is_connected = False
            logger.error("Error conectando a RabbitMQ: %s", e)
            raise

    def _on_connection_closed(self, connection: aio_pika.RobustConnection, reason: Exception) -> None:
        """
        Callback cuando la conexión se cierra inesperadamente.
        """
        logger.warning(
            "Conexión a RabbitMQ cerrada: %s. Se intentará reconectar automáticamente.",
            reason
        )
        self._is_connected = False
        
        # Iniciar tarea de reconexión en segundo plano
        if self._reconnect_task is None or self._reconnect_task.done():
            self._reconnect_task = asyncio.create_task(self._reconnect_loop())

    async def _reconnect_loop(self) -> None:
        """
        Loop de reconexión automática con backoff exponencial.
        """
        max_delay = 60  # máximo 60 segundos entre intentos
        delay = 2  # empezar con 2 segundos
        
        while not self._is_connected:
            try:
                await asyncio.sleep(delay)
                logger.info("Intentando reconectar a RabbitMQ...")
                await self._connect()
                delay = 2  # resetear delay en caso de éxito
            except Exception as e:
                logger.error("Error en reconexión: %s. Reintentando en %s segundos...", e, delay)
                delay = min(delay * 2, max_delay)  # backoff exponencial

    async def ensure_connected(self) -> None:
        """
        Asegura que la conexión esté establecida antes de publicar.
        """
        async with self._lock:
            if not self._is_connected or self._connection.is_closed:
                await self._connect()

    async def publish_event(
        self,
        event_type: str,
        user_id: int,
        puntos_base: int = 10,
        routing_key: Optional[str] = None,
        **extra_data
    ) -> bool:
        """
        Publica un evento en el exchange de RabbitMQ.
        
        Args:
            event_type: Tipo de evento (ej: 'reporte_creado')
            user_id: ID del usuario que generó el evento
            puntos_base: Puntos base otorgados (default: 10)
            routing_key: Routing key opcional (default: event_type)
            **extra_data: Datos adicionales para incluir en el mensaje
            
        Returns:
            True si el mensaje se publicó exitosamente, False en caso contrario
        """
        try:
            # Asegurar conexión antes de publicar
            await self.ensure_connected()
            
            # Construir payload del mensaje
            message_data = {
                "event_type": event_type,
                "user_id": user_id,
                "puntos_base": puntos_base,
                **extra_data
            }
            
            # Usar event_type como routing_key si no se especifica uno
            if routing_key is None:
                routing_key = event_type
            
            # Serializar mensaje a JSON
            message_body = json.dumps(message_data).encode("utf-8")
            
            # Crear mensaje con propiedades de persistencia
            message = aio_pika.Message(
                message_body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,  # Mensaje persistente
                content_type="application/json",
            )
            
            # Publicar en el exchange
            await self._exchange.publish(
                message,
                routing_key=routing_key,
            )
            
            logger.info(
                "Evento publicado exitosamente: event_type=%s, user_id=%s, routing_key=%s",
                event_type,
                user_id,
                routing_key,
            )
            return True
            
        except Exception as e:
            logger.error(
                "Error publicando evento a RabbitMQ: %s. Datos: %s",
                e,
                message_data if 'message_data' in locals() else None,
            )
            # Intentar reconectar para el próximo mensaje
            self._is_connected = False
            return False

    async def close(self) -> None:
        """
        Cierra la conexión de forma ordenada.
        """
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
        
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        
        self._is_connected = False
        logger.info("Conexión a RabbitMQ cerrada")


# Instancia singleton del producer
_producer_instance: Optional[RabbitMQProducer] = None


async def get_producer() -> RabbitMQProducer:
    """
    Obtiene la instancia singleton del producer de RabbitMQ.
    """
    global _producer_instance
    
    if _producer_instance is None:
        _producer_instance = RabbitMQProducer()
        await _producer_instance.ensure_connected()
    
    return _producer_instance


async def close_producer() -> None:
    """
    Cierra la instancia singleton del producer.
    """
    global _producer_instance
    
    if _producer_instance:
        await _producer_instance.close()
        _producer_instance = None
