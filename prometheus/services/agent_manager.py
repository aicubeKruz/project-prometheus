"""
Agent Manager Service for Project Prometheus.
Manages the lifecycle and coordination of all agents in the system.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog

from ..core.domain import AgentId, AgentType, EventBus, Repository
from ..core.base_agent import BaseAgent
from ..agents import (
    AgentPrometheus,
    AgentDaedalus,
    AgentLogos,
    AgentOdysseus,
    AgentThemis,
)
from ..infrastructure.event_bus import InMemoryEventBus, RedisEventBus
from ..infrastructure.repositories import InMemoryRepository, TaskRepository

logger = structlog.get_logger()


class AgentManager:
    """
    Central manager for all agents in the Project Prometheus system.
    
    Responsibilities:
    - Create and manage agent lifecycle
    - Setup and maintain agent hierarchy
    - Coordinate inter-agent communication
    - Monitor agent health and status
    - Handle emergency operations
    """

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        task_repository: Optional[Repository] = None,
        use_redis: bool = False,
    ):
        self._agents: Dict[str, BaseAgent] = {}
        self._event_bus = event_bus or (
            RedisEventBus() if use_redis else InMemoryEventBus()
        )
        self._task_repository = task_repository or (
            TaskRepository() if use_redis else InMemoryRepository()
        )
        self._agent_hierarchy: Dict[str, List[str]] = {}
        self._running = False

    async def start(self) -> None:
        """Start the agent manager."""
        self._running = True
        
        # Connect event bus if needed
        if hasattr(self._event_bus, 'connect'):
            await self._event_bus.connect()
        
        # Connect repository if needed
        if hasattr(self._task_repository, 'connect'):
            await self._task_repository.connect()
        
        logger.info("Agent manager started")

    async def stop(self) -> None:
        """Stop the agent manager and all agents."""
        self._running = False
        
        # Stop all agents
        for agent in self._agents.values():
            await agent.stop()
        
        # Disconnect infrastructure
        if hasattr(self._event_bus, 'disconnect'):
            await self._event_bus.disconnect()
        
        if hasattr(self._task_repository, 'disconnect'):
            await self._task_repository.disconnect()
        
        logger.info("Agent manager stopped")

    async def create_agent(
        self, 
        agent_type: AgentType, 
        config: Dict[str, Any] = None
    ) -> BaseAgent:
        """Create a new agent of the specified type."""
        config = config or {}
        
        # Create agent based on type
        agent_classes = {
            AgentType.PROMETHEUS: AgentPrometheus,
            AgentType.DAEDALUS: AgentDaedalus,
            AgentType.LOGOS: AgentLogos,
            AgentType.ODYSSEUS: AgentOdysseus,
            AgentType.THEMIS: AgentThemis,
        }
        
        if agent_type not in agent_classes:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        agent_class = agent_classes[agent_type]
        agent = agent_class(
            event_bus=self._event_bus,
            task_repository=self._task_repository,
        )
        
        # Store agent
        self._agents[str(agent.id)] = agent
        
        # Start agent
        await agent.start()
        
        logger.info("Agent created", agent_id=str(agent.id), agent_type=str(agent_type))
        return agent

    async def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID."""
        return self._agents.get(agent_id)

    async def get_agent_by_type(self, agent_type: str) -> Optional[BaseAgent]:
        """Get first agent of specified type."""
        for agent in self._agents.values():
            if str(agent.type).lower() == agent_type.lower():
                return agent
        return None

    async def remove_agent(self, agent_id: str) -> bool:
        """Remove agent from the system."""
        if agent_id not in self._agents:
            return False
        
        agent = self._agents[agent_id]
        await agent.stop()
        del self._agents[agent_id]
        
        # Remove from hierarchy
        self._remove_from_hierarchy(agent_id)
        
        logger.info("Agent removed", agent_id=agent_id)
        return True

    async def start_agent(self, agent_id: str) -> bool:
        """Start a specific agent."""
        agent = self._agents.get(agent_id)
        if not agent:
            return False
        
        await agent.start()
        logger.info("Agent started", agent_id=agent_id)
        return True

    async def stop_agent(self, agent_id: str) -> bool:
        """Stop a specific agent."""
        agent = self._agents.get(agent_id)
        if not agent:
            return False
        
        await agent.stop()
        logger.info("Agent stopped", agent_id=agent_id)
        return True

    async def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents with their status."""
        agents_info = []
        
        for agent in self._agents.values():
            status = await agent.get_status()
            agents_info.append(status)
        
        return agents_info

    async def setup_agent_hierarchy(self) -> Dict[str, Any]:
        """Setup the standard Project Prometheus agent hierarchy."""
        hierarchy_info = {"created_agents": [], "relationships": {}}
        
        # Create Prometheus (master) if not exists
        prometheus_agent = await self.get_agent_by_type("prometheus")
        if not prometheus_agent:
            prometheus_agent = await self.create_agent(AgentType.PROMETHEUS)
            hierarchy_info["created_agents"].append({
                "id": str(prometheus_agent.id),
                "type": "prometheus",
                "role": "master"
            })
        
        # Create subordinate agents
        subordinate_types = [
            (AgentType.DAEDALUS, "cognitive_architect"),
            (AgentType.ODYSSEUS, "embodied_explorer"),
            (AgentType.THEMIS, "safety_overseer"),
        ]
        
        for agent_type, role in subordinate_types:
            existing_agent = await self.get_agent_by_type(agent_type.value)
            if not existing_agent:
                agent = await self.create_agent(agent_type)
                hierarchy_info["created_agents"].append({
                    "id": str(agent.id),
                    "type": agent_type.value,
                    "role": role
                })
                
                # Set hierarchy relationships
                prometheus_agent.add_subordinate(agent.id)
                agent.set_supervisor(prometheus_agent.id)
                
                if str(prometheus_agent.id) not in hierarchy_info["relationships"]:
                    hierarchy_info["relationships"][str(prometheus_agent.id)] = []
                hierarchy_info["relationships"][str(prometheus_agent.id)].append(str(agent.id))
        
        # Create Logos as subordinate to Daedalus
        logos_agent = await self.get_agent_by_type("logos")
        daedalus_agent = await self.get_agent_by_type("daedalus")
        
        if not logos_agent and daedalus_agent:
            logos_agent = await self.create_agent(AgentType.LOGOS)
            hierarchy_info["created_agents"].append({
                "id": str(logos_agent.id),
                "type": "logos",
                "role": "symbolic_reasoner"
            })
            
            # Set hierarchy relationships
            daedalus_agent.add_subordinate(logos_agent.id)
            logos_agent.set_supervisor(daedalus_agent.id)
            
            if str(daedalus_agent.id) not in hierarchy_info["relationships"]:
                hierarchy_info["relationships"][str(daedalus_agent.id)] = []
            hierarchy_info["relationships"][str(daedalus_agent.id)].append(str(logos_agent.id))
        
        self._build_hierarchy_cache()
        
        logger.info("Agent hierarchy setup completed", 
                   created_agents=len(hierarchy_info["created_agents"]))
        
        return hierarchy_info

    async def get_prometheus_agent(self) -> Optional[BaseAgent]:
        """Get the Prometheus master agent."""
        return await self.get_agent_by_type("prometheus")

    async def get_hierarchy_structure(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get the current agent hierarchy structure."""
        hierarchy = {
            "master": [],
            "subordinates": [],
            "sub_subordinates": [],
        }
        
        for agent in self._agents.values():
            agent_info = {
                "id": str(agent.id),
                "type": str(agent.type).lower() if agent.type else "unknown",
                "active": agent.is_active,
                "subordinates": [str(sub_id) for sub_id in agent.subordinates],
                "supervisor": str(agent.supervisor) if agent.supervisor else None,
            }
            
            if not agent.supervisor:  # Master level
                hierarchy["master"].append(agent_info)
            elif agent.subordinates:  # Has subordinates
                hierarchy["subordinates"].append(agent_info)
            else:  # Leaf node
                hierarchy["sub_subordinates"].append(agent_info)
        
        return hierarchy

    async def send_message(
        self, 
        sender_id: str, 
        receiver_id: str, 
        content: Dict[str, Any],
        message_type: str = "general"
    ) -> bool:
        """Send message between agents."""
        sender = self._agents.get(sender_id)
        if not sender:
            return False
        
        try:
            receiver_agent_id = AgentId(UUID(receiver_id))
            await sender.send_message(receiver_agent_id, content, message_type)
            return True
        except Exception as e:
            logger.error("Error sending message", error=str(e), 
                        sender=sender_id, receiver=receiver_id)
            return False

    async def broadcast_message(
        self, 
        sender_id: str, 
        content: Dict[str, Any],
        message_type: str = "broadcast"
    ) -> int:
        """Broadcast message to all agents."""
        sender = self._agents.get(sender_id)
        if not sender:
            return 0
        
        success_count = 0
        for agent_id in self._agents.keys():
            if agent_id != sender_id:
                success = await self.send_message(sender_id, agent_id, content, message_type)
                if success:
                    success_count += 1
        
        return success_count

    async def emergency_halt(self, reason: str = "Emergency halt") -> None:
        """Emergency halt all system operations."""
        logger.critical("EMERGENCY HALT INITIATED", reason=reason)
        
        # Stop all agents immediately
        for agent in self._agents.values():
            try:
                await agent.stop()
            except Exception as e:
                logger.error("Error stopping agent during emergency halt", 
                           agent_id=str(agent.id), error=str(e))
        
        # Notify all agents of emergency halt
        halt_message = {
            "type": "emergency_halt",
            "reason": reason,
            "timestamp": "2024-01-01T00:00:00Z",
        }
        
        # Send via event bus if available
        try:
            if hasattr(self._event_bus, 'publish'):
                from ..core.domain import Message, AgentId
                for agent_id in self._agents.keys():
                    emergency_msg = Message(
                        sender_id=AgentId(),  # System message
                        receiver_id=AgentId(UUID(agent_id)),
                        content=halt_message,
                        message_type="emergency_halt"
                    )
                    await self._event_bus.publish(emergency_msg)
        except Exception as e:
            logger.error("Error broadcasting emergency halt", error=str(e))

    async def update_agent_config(self, agent_id: str, config: Dict[str, Any]) -> bool:
        """Update agent configuration."""
        agent = self._agents.get(agent_id)
        if not agent:
            return False
        
        # This is a simplified implementation
        # In a real system, you'd have a more sophisticated config update mechanism
        logger.info("Agent configuration update requested", 
                   agent_id=agent_id, config=config)
        return True

    async def get_task_statistics(self) -> Dict[str, int]:
        """Get task statistics across all agents."""
        stats = {
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
        }
        
        # This is a simplified implementation
        # In production, you'd query the task repository
        try:
            if hasattr(self._task_repository, 'find_by_criteria'):
                all_tasks = await self._task_repository.list_all()
                for task in all_tasks:
                    status = getattr(task, 'status', None)
                    if status:
                        status_value = status.value if hasattr(status, 'value') else str(status)
                        if status_value in stats:
                            stats[status_value] += 1
        except Exception as e:
            logger.error("Error getting task statistics", error=str(e))
        
        return stats

    def _build_hierarchy_cache(self) -> None:
        """Build internal hierarchy cache for efficient lookups."""
        self._agent_hierarchy = {}
        
        for agent in self._agents.values():
            agent_id = str(agent.id)
            subordinates = [str(sub_id) for sub_id in agent.subordinates]
            self._agent_hierarchy[agent_id] = subordinates

    def _remove_from_hierarchy(self, agent_id: str) -> None:
        """Remove agent from hierarchy relationships."""
        # Remove as subordinate from other agents
        for agent in self._agents.values():
            if agent_id in [str(sub_id) for sub_id in agent.subordinates]:
                agent.remove_subordinate(AgentId(UUID(agent_id)))
        
        # Remove from hierarchy cache
        if agent_id in self._agent_hierarchy:
            del self._agent_hierarchy[agent_id]