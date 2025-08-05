"""
Event bus implementation for inter-agent communication.
"""
import asyncio
import json
from typing import Any, Callable, Dict, Optional
from uuid import UUID

import redis.asyncio as redis
import structlog

from ..core.domain import AgentId, EventBus, Message

logger = structlog.get_logger()


class RedisEventBus(EventBus):
    """Redis-based event bus for inter-agent communication."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self._redis_client: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        self._subscribers: Dict[str, Callable] = {}
        self._running = False

    async def connect(self) -> None:
        """Connect to Redis."""
        self._redis_client = redis.from_url(self.redis_url)
        self._pubsub = self._redis_client.pubsub()
        await self._redis_client.ping()
        logger.info("Connected to Redis event bus")

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        self._running = False
        if self._pubsub:
            await self._pubsub.close()
        if self._redis_client:
            await self._redis_client.close()
        logger.info("Disconnected from Redis event bus")

    async def publish(self, message: Message) -> None:
        """Publish message to event bus."""
        if not self._redis_client:
            await self.connect()

        channel = f"agent:{message.receiver_id}"
        message_data = {
            "id": str(message.id),
            "sender_id": str(message.sender_id),
            "receiver_id": str(message.receiver_id),
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
            "message_type": message.message_type,
        }

        await self._redis_client.publish(channel, json.dumps(message_data))
        logger.debug("Message published", 
                    sender=str(message.sender_id),
                    receiver=str(message.receiver_id),
                    type=message.message_type)

    async def subscribe(self, agent_id: AgentId, callback: Callable[[Message], None]) -> None:
        """Subscribe agent to receive messages."""
        if not self._redis_client:
            await self.connect()

        channel = f"agent:{agent_id}"
        self._subscribers[str(agent_id)] = callback
        
        await self._pubsub.subscribe(channel)
        
        if not self._running:
            self._running = True
            asyncio.create_task(self._message_listener())
        
        logger.info("Agent subscribed to event bus", agent_id=str(agent_id))

    async def unsubscribe(self, agent_id: AgentId) -> None:
        """Unsubscribe agent from receiving messages."""
        if not self._pubsub:
            return

        channel = f"agent:{agent_id}"
        await self._pubsub.unsubscribe(channel)
        
        if str(agent_id) in self._subscribers:
            del self._subscribers[str(agent_id)]
        
        logger.info("Agent unsubscribed from event bus", agent_id=str(agent_id))

    async def _message_listener(self) -> None:
        """Listen for incoming messages and route to subscribers."""
        while self._running:
            try:
                message = await self._pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    await self._handle_message(message)
            except Exception as e:
                logger.error("Error in message listener", error=str(e))
                await asyncio.sleep(1)

    async def _handle_message(self, redis_message: Dict[str, Any]) -> None:
        """Handle incoming Redis message."""
        try:
            channel = redis_message["channel"].decode("utf-8")
            data = json.loads(redis_message["data"])
            
            # Parse message
            message = Message(
                id=UUID(data["id"]),
                sender_id=AgentId(UUID(data["sender_id"])),
                receiver_id=AgentId(UUID(data["receiver_id"])),
                content=data["content"],
                message_type=data["message_type"],
            )
            
            # Route to appropriate callback
            receiver_id = str(message.receiver_id)
            if receiver_id in self._subscribers:
                callback = self._subscribers[receiver_id]
                await callback(message)
                
        except Exception as e:
            logger.error("Error handling message", error=str(e))


class InMemoryEventBus(EventBus):
    """In-memory event bus for testing and development."""

    def __init__(self):
        self._subscribers: Dict[str, Callable] = {}
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._running = False

    async def publish(self, message: Message) -> None:
        """Publish message to event bus."""
        await self._message_queue.put(message)
        
        if not self._running:
            self._running = True
            asyncio.create_task(self._message_processor())

    async def subscribe(self, agent_id: AgentId, callback: Callable[[Message], None]) -> None:
        """Subscribe agent to receive messages."""
        self._subscribers[str(agent_id)] = callback
        logger.debug("Agent subscribed to in-memory event bus", agent_id=str(agent_id))

    async def unsubscribe(self, agent_id: AgentId) -> None:
        """Unsubscribe agent from receiving messages."""
        if str(agent_id) in self._subscribers:
            del self._subscribers[str(agent_id)]
        logger.debug("Agent unsubscribed from in-memory event bus", agent_id=str(agent_id))

    async def _message_processor(self) -> None:
        """Process messages from queue."""
        while self._running:
            try:
                # Wait for message with timeout
                message = await asyncio.wait_for(self._message_queue.get(), timeout=1.0)
                
                # Route to appropriate callback
                receiver_id = str(message.receiver_id)
                if receiver_id in self._subscribers:
                    callback = self._subscribers[receiver_id]
                    await callback(message)
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error("Error processing message", error=str(e))

    async def stop(self) -> None:
        """Stop the message processor."""
        self._running = False