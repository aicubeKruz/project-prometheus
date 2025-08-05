"""
Core domain entities and value objects for Project Prometheus.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Union
from uuid import UUID, uuid4

import structlog

logger = structlog.get_logger()


class AgentType(Enum):
    """Agent types in the hierarchical system."""
    PROMETHEUS = "prometheus"  # Master Control & Strategy
    DAEDALUS = "daedalus"     # Cognitive Architect
    LOGOS = "logos"           # Symbolic Reasoner & Verifier
    ODYSSEUS = "odysseus"     # Embodied Explorer & Tool User
    THEMIS = "themis"         # Safety & Alignment Overseer


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Priority(Enum):
    """Task priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass(frozen=True)
class AgentId:
    """Value object for agent identification."""
    value: UUID = field(default_factory=uuid4)

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class TaskId:
    """Value object for task identification."""
    value: UUID = field(default_factory=uuid4)

    def __str__(self) -> str:
        return str(self.value)


@dataclass
class Message:
    """Inter-agent communication message."""
    id: UUID = field(default_factory=uuid4)
    sender_id: AgentId = field(default_factory=AgentId)
    receiver_id: AgentId = field(default_factory=AgentId)
    content: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    message_type: str = "general"


@dataclass
class Task:
    """Task entity for agent execution."""
    id: TaskId = field(default_factory=TaskId)
    agent_id: AgentId = field(default_factory=AgentId)
    name: str = ""
    description: str = ""
    priority: Priority = Priority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def mark_in_progress(self) -> None:
        """Mark task as in progress."""
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.utcnow()

    def mark_completed(self, result: Dict[str, Any]) -> None:
        """Mark task as completed with result."""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_failed(self, error: str) -> None:
        """Mark task as failed with error."""
        self.status = TaskStatus.FAILED
        self.error = error
        self.updated_at = datetime.utcnow()


class AgentProtocol(Protocol):
    """Protocol defining agent interface."""
    
    def get_id(self) -> AgentId:
        """Get agent identifier."""
        ...

    def get_type(self) -> AgentType:
        """Get agent type."""
        ...

    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming message and optionally return response."""
        ...

    async def execute_task(self, task: Task) -> Task:
        """Execute assigned task."""
        ...


class SafetyViolation(Exception):
    """Exception raised when safety constraints are violated."""
    
    def __init__(self, message: str, severity: str = "medium"):
        super().__init__(message)
        self.severity = severity


@dataclass
class SafetyCheck:
    """Safety check result."""
    id: UUID = field(default_factory=uuid4)
    check_type: str = ""
    status: str = "passed"  # passed, warning, failed
    message: str = ""
    severity: str = "low"  # low, medium, high, critical
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class Repository(ABC):
    """Abstract repository interface."""
    
    @abstractmethod
    async def save(self, entity: Any) -> None:
        """Save entity to repository."""
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_id: Union[AgentId, TaskId, UUID]) -> Optional[Any]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    async def list_all(self) -> List[Any]:
        """List all entities."""
        pass
    
    @abstractmethod
    async def delete(self, entity_id: Union[AgentId, TaskId, UUID]) -> bool:
        """Delete entity by ID."""
        pass


class EventBus(ABC):
    """Abstract event bus for inter-agent communication."""
    
    @abstractmethod
    async def publish(self, message: Message) -> None:
        """Publish message to event bus."""
        pass
    
    @abstractmethod
    async def subscribe(self, agent_id: AgentId, callback) -> None:
        """Subscribe agent to receive messages."""
        pass
    
    @abstractmethod
    async def unsubscribe(self, agent_id: AgentId) -> None:
        """Unsubscribe agent from receiving messages."""
        pass