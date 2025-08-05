"""
Base agent implementation for the Prometheus multi-agent system.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import structlog

from .domain import (
    AgentId,
    AgentProtocol,
    AgentType,
    EventBus,
    Message,
    Repository,
    SafetyCheck,
    Task,
    TaskStatus,
)

logger = structlog.get_logger()


class BaseAgent(ABC):
    """Base class for all agents in the Prometheus system."""

    def __init__(
        self,
        agent_id: Optional[AgentId] = None,
        agent_type: Optional[AgentType] = None,
        event_bus: Optional[EventBus] = None,
        task_repository: Optional[Repository] = None,
    ):
        self._id = agent_id or AgentId()
        self._type = agent_type
        self._event_bus = event_bus
        self._task_repository = task_repository
        self._is_active = False
        self._subordinates: List[AgentId] = []
        self._supervisor: Optional[AgentId] = None
        self._logger = logger.bind(agent_id=str(self._id), agent_type=str(self._type))

    @property
    def id(self) -> AgentId:
        """Get agent ID."""
        return self._id

    @property
    def type(self) -> Optional[AgentType]:
        """Get agent type."""
        return self._type

    @property
    def is_active(self) -> bool:
        """Check if agent is active."""
        return self._is_active

    @property
    def subordinates(self) -> List[AgentId]:
        """Get list of subordinate agents."""
        return self._subordinates.copy()

    @property
    def supervisor(self) -> Optional[AgentId]:
        """Get supervisor agent ID."""
        return self._supervisor

    def get_id(self) -> AgentId:
        """Get agent identifier."""
        return self._id

    def get_type(self) -> Optional[AgentType]:
        """Get agent type."""
        return self._type

    async def start(self) -> None:
        """Start the agent."""
        self._logger.info("Starting agent")
        self._is_active = True
        if self._event_bus:
            await self._event_bus.subscribe(self._id, self._handle_message)

    async def stop(self) -> None:
        """Stop the agent."""
        self._logger.info("Stopping agent")
        self._is_active = False
        if self._event_bus:
            await self._event_bus.unsubscribe(self._id)

    def add_subordinate(self, subordinate_id: AgentId) -> None:
        """Add a subordinate agent."""
        if subordinate_id not in self._subordinates:
            self._subordinates.append(subordinate_id)
            self._logger.info("Added subordinate", subordinate_id=str(subordinate_id))

    def remove_subordinate(self, subordinate_id: AgentId) -> None:
        """Remove a subordinate agent."""
        if subordinate_id in self._subordinates:
            self._subordinates.remove(subordinate_id)
            self._logger.info("Removed subordinate", subordinate_id=str(subordinate_id))

    def set_supervisor(self, supervisor_id: AgentId) -> None:
        """Set supervisor agent."""
        self._supervisor = supervisor_id
        self._logger.info("Set supervisor", supervisor_id=str(supervisor_id))

    async def send_message(self, receiver_id: AgentId, content: Dict[str, Any], message_type: str = "general") -> None:
        """Send message to another agent."""
        if not self._event_bus:
            self._logger.error("No event bus configured")
            return

        message = Message(
            sender_id=self._id,
            receiver_id=receiver_id,
            content=content,
            message_type=message_type,
        )
        await self._event_bus.publish(message)
        self._logger.debug("Sent message", receiver_id=str(receiver_id), message_type=message_type)

    async def broadcast_to_subordinates(self, content: Dict[str, Any], message_type: str = "broadcast") -> None:
        """Broadcast message to all subordinates."""
        for subordinate_id in self._subordinates:
            await self.send_message(subordinate_id, content, message_type)

    async def report_to_supervisor(self, content: Dict[str, Any], message_type: str = "report") -> None:
        """Send report to supervisor."""
        if self._supervisor:
            await self.send_message(self._supervisor, content, message_type)

    async def _handle_message(self, message: Message) -> None:
        """Handle incoming message."""
        try:
            self._logger.debug("Received message", sender_id=str(message.sender_id), message_type=message.message_type)
            response = await self.process_message(message)
            if response:
                await self._event_bus.publish(response)
        except Exception as e:
            self._logger.error("Error handling message", error=str(e))

    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming message. Override in subclasses."""
        self._logger.debug("Processing message", message_type=message.message_type)
        return await self._process_message_internal(message)

    @abstractmethod
    async def _process_message_internal(self, message: Message) -> Optional[Message]:
        """Internal message processing. Must be implemented by subclasses."""
        pass

    async def execute_task(self, task: Task) -> Task:
        """Execute assigned task."""
        try:
            self._logger.info("Starting task execution", task_id=str(task.id))
            task.mark_in_progress()
            
            if self._task_repository:
                await self._task_repository.save(task)

            # Perform safety checks before execution
            safety_results = await self._perform_safety_checks(task)
            if any(check.status == "failed" for check in safety_results):
                task.mark_failed("Safety check failed")
                return task

            # Execute the actual task
            result = await self._execute_task_internal(task)
            task.mark_completed(result)
            
            self._logger.info("Task completed successfully", task_id=str(task.id))
            
        except Exception as e:
            self._logger.error("Task execution failed", task_id=str(task.id), error=str(e))
            task.mark_failed(str(e))
        
        if self._task_repository:
            await self._task_repository.save(task)
        
        return task

    @abstractmethod
    async def _execute_task_internal(self, task: Task) -> Dict[str, Any]:
        """Internal task execution. Must be implemented by subclasses."""
        pass

    async def _perform_safety_checks(self, task: Task) -> List[SafetyCheck]:
        """Perform safety checks before task execution."""
        # Base implementation - override in subclasses for specific checks
        return []

    async def get_status(self) -> Dict[str, Any]:
        """Get agent status information."""
        return {
            "id": str(self._id),
            "type": str(self._type) if self._type else None,
            "active": self._is_active,
            "subordinates": [str(sub_id) for sub_id in self._subordinates],
            "supervisor": str(self._supervisor) if self._supervisor else None,
        }

    async def get_health(self) -> Dict[str, Any]:
        """Get agent health information."""
        return {
            "status": "healthy" if self._is_active else "inactive",
            "uptime": "N/A",  # TODO: Implement uptime tracking
        }

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self._id})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self._id}, type={self._type})"