import asyncio
import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.app.core.config import settings

class RabbitMQClient:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.handlers = {}
        self._is_connecting = False

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, max=10))
    async def connect(self):
        if self._is_connecting:
            return
        self._is_connecting = True
        try:
            self.connection = await aio_pika.connect_robust(
                settings.RABBITMQ_URL,
                timeout=10
            )
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)
            print("Connected to RabbitMQ")
        finally:
            self._is_connecting = False

    async def close(self):
        if self.connection:
            await self.connection.close()

    def register_handler(self, queue_name: str, handler: callable):
        self.handlers[queue_name] = handler

    async def consume(self, queue_name: str):
        if not self.connection or self.connection.is_closed:
            await self.connect()

        queue = await self.channel.declare_queue(queue_name, durable=True)
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    if queue_name in self.handlers:
                        await self.handlers[queue_name](message)
                    else:
                        print(f"No handler for queue {queue_name}")

    async def start_consumers(self):
        for queue_name in self.handlers.keys():
            asyncio.create_task(self.consume(queue_name))