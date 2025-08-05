"""
Repository implementations for data persistence.
"""
import json
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

import redis.asyncio as redis
import structlog

from ..core.domain import AgentId, Repository, Task, TaskId

logger = structlog.get_logger()


class InMemoryRepository(Repository):
    """In-memory repository for testing and development."""

    def __init__(self):
        self._storage: Dict[str, Any] = {}

    async def save(self, entity: Any) -> None:
        """Save entity to repository."""
        if hasattr(entity, 'id'):
            key = str(entity.id)
            self._storage[key] = entity
            logger.debug("Entity saved to in-memory repository", entity_id=key)
        else:
            raise ValueError("Entity must have an 'id' attribute")

    async def get_by_id(self, entity_id: Union[AgentId, TaskId, UUID]) -> Optional[Any]:
        """Get entity by ID."""
        key = str(entity_id)
        entity = self._storage.get(key)
        if entity:
            logger.debug("Entity retrieved from in-memory repository", entity_id=key)
        return entity

    async def list_all(self) -> List[Any]:
        """List all entities."""
        entities = list(self._storage.values())
        logger.debug("Listed all entities from in-memory repository", count=len(entities))
        return entities

    async def delete(self, entity_id: Union[AgentId, TaskId, UUID]) -> bool:
        """Delete entity by ID."""
        key = str(entity_id)
        if key in self._storage:
            del self._storage[key]
            logger.debug("Entity deleted from in-memory repository", entity_id=key)
            return True
        return False

    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List[Any]:
        """Find entities by criteria."""
        results = []
        for entity in self._storage.values():
            match = True
            for key, value in criteria.items():
                if not hasattr(entity, key) or getattr(entity, key) != value:
                    match = False
                    break
            if match:
                results.append(entity)
        
        logger.debug("Found entities by criteria", criteria=criteria, count=len(results))
        return results


class RedisRepository(Repository):
    """Redis-based repository for production use."""

    def __init__(self, redis_url: str = "redis://localhost:6379", key_prefix: str = "prometheus"):
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self._redis_client: Optional[redis.Redis] = None

    async def connect(self) -> None:
        """Connect to Redis."""
        self._redis_client = redis.from_url(self.redis_url)
        await self._redis_client.ping()
        logger.info("Connected to Redis repository")

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._redis_client:
            await self._redis_client.close()
        logger.info("Disconnected from Redis repository")

    async def save(self, entity: Any) -> None:
        """Save entity to Redis."""
        if not self._redis_client:
            await self.connect()

        if hasattr(entity, 'id'):
            key = f"{self.key_prefix}:{type(entity).__name__.lower()}:{entity.id}"
            
            # Serialize entity
            entity_data = await self._serialize_entity(entity)
            
            await self._redis_client.set(key, json.dumps(entity_data))
            logger.debug("Entity saved to Redis repository", entity_id=str(entity.id))
        else:
            raise ValueError("Entity must have an 'id' attribute")

    async def get_by_id(self, entity_id: Union[AgentId, TaskId, UUID]) -> Optional[Any]:
        """Get entity by ID from Redis."""
        if not self._redis_client:
            await self.connect()

        # Try different entity types
        for entity_type in ["task", "agent", "message"]:
            key = f"{self.key_prefix}:{entity_type}:{entity_id}"
            data = await self._redis_client.get(key)
            if data:
                entity_data = json.loads(data)
                entity = await self._deserialize_entity(entity_data, entity_type)
                logger.debug("Entity retrieved from Redis repository", entity_id=str(entity_id))
                return entity
        
        return None

    async def list_all(self) -> List[Any]:
        """List all entities from Redis."""
        if not self._redis_client:
            await self.connect()

        pattern = f"{self.key_prefix}:*"
        keys = await self._redis_client.keys(pattern)
        
        entities = []
        for key in keys:
            data = await self._redis_client.get(key)
            if data:
                entity_data = json.loads(data)
                # Extract entity type from key
                key_parts = key.decode("utf-8").split(":")
                if len(key_parts) >= 2:
                    entity_type = key_parts[1]
                    entity = await self._deserialize_entity(entity_data, entity_type)
                    if entity:
                        entities.append(entity)
        
        logger.debug("Listed all entities from Redis repository", count=len(entities))
        return entities

    async def delete(self, entity_id: Union[AgentId, TaskId, UUID]) -> bool:
        """Delete entity by ID from Redis."""
        if not self._redis_client:
            await self.connect()

        # Try different entity types
        for entity_type in ["task", "agent", "message"]:
            key = f"{self.key_prefix}:{entity_type}:{entity_id}"
            result = await self._redis_client.delete(key)
            if result:
                logger.debug("Entity deleted from Redis repository", entity_id=str(entity_id))
                return True
        
        return False

    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List[Any]:
        """Find entities by criteria in Redis."""
        # For simplicity, get all entities and filter
        # In production, consider using Redis search or secondary indexes
        all_entities = await self.list_all()
        
        results = []
        for entity in all_entities:
            match = True
            for key, value in criteria.items():
                if not hasattr(entity, key) or getattr(entity, key) != value:
                    match = False
                    break
            if match:
                results.append(entity)
        
        logger.debug("Found entities by criteria in Redis", criteria=criteria, count=len(results))
        return results

    async def _serialize_entity(self, entity: Any) -> Dict[str, Any]:
        """Serialize entity for storage."""
        if isinstance(entity, Task):
            return {
                "id": str(entity.id.value),
                "agent_id": str(entity.agent_id.value),
                "name": entity.name,
                "description": entity.description,
                "priority": entity.priority.value,
                "status": entity.status.value,
                "created_at": entity.created_at.isoformat(),
                "updated_at": entity.updated_at.isoformat(),
                "completed_at": entity.completed_at.isoformat() if entity.completed_at else None,
                "result": entity.result,
                "error": entity.error,
                "metadata": entity.metadata,
                "_type": "Task",
            }
        else:
            # Generic serialization for other entities
            return {
                "id": str(getattr(entity, 'id', '')),
                "_type": type(entity).__name__,
                "data": str(entity),  # Fallback serialization
            }

    async def _deserialize_entity(self, data: Dict[str, Any], entity_type: str) -> Optional[Any]:
        """Deserialize entity from storage."""
        try:
            if data.get("_type") == "Task":
                from ..core.domain import Task, TaskId, AgentId, Priority, TaskStatus
                from datetime import datetime
                
                task = Task(
                    id=TaskId(UUID(data["id"])),
                    agent_id=AgentId(UUID(data["agent_id"])),
                    name=data["name"],
                    description=data["description"],
                    priority=Priority(data["priority"]),
                    status=TaskStatus(data["status"]),
                    created_at=datetime.fromisoformat(data["created_at"]),
                    updated_at=datetime.fromisoformat(data["updated_at"]),
                    completed_at=datetime.fromisoformat(data["completed_at"]) if data["completed_at"] else None,
                    result=data["result"],
                    error=data["error"],
                    metadata=data["metadata"],
                )
                return task
            else:
                # Generic deserialization
                logger.warning("Unknown entity type for deserialization", entity_type=entity_type)
                return None
                
        except Exception as e:
            logger.error("Error deserializing entity", error=str(e), data=data)
            return None


class TaskRepository(RedisRepository):
    """Specialized repository for Task entities."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        super().__init__(redis_url, "prometheus:tasks")

    async def find_by_agent(self, agent_id: AgentId) -> List[Task]:
        """Find tasks by agent ID."""
        return await self.find_by_criteria({"agent_id": agent_id})

    async def find_by_status(self, status: str) -> List[Task]:
        """Find tasks by status."""
        return await self.find_by_criteria({"status": status})

    async def find_pending_tasks(self) -> List[Task]:
        """Find all pending tasks."""
        return await self.find_by_status("pending")

    async def find_active_tasks(self) -> List[Task]:
        """Find all active tasks."""
        return await self.find_by_status("in_progress")


class AgentRepository(RedisRepository):
    """Specialized repository for Agent entities."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        super().__init__(redis_url, "prometheus:agents")

    async def find_by_type(self, agent_type: str) -> List[Any]:
        """Find agents by type."""
        return await self.find_by_criteria({"type": agent_type})

    async def find_active_agents(self) -> List[Any]:
        """Find all active agents."""
        return await self.find_by_criteria({"is_active": True})