"""
Task management API endpoints.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import structlog

from ..dependencies import (
    get_task_service,
    check_rate_limit,
    validate_task_id,
    validate_agent_id,
    verify_api_key
)
from ...services.task_service import TaskService
from ...core.domain import Priority, TaskStatus

logger = structlog.get_logger()

router = APIRouter(dependencies=[Depends(check_rate_limit), Depends(verify_api_key)])


class TaskCreateRequest(BaseModel):
    """Request model for creating a task."""
    agent_id: str
    name: str
    description: str = ""
    priority: str = "medium"
    metadata: Dict[str, Any] = {}


class TaskUpdateRequest(BaseModel):
    """Request model for updating a task."""
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TaskResponse(BaseModel):
    """Response model for task information."""
    id: str
    agent_id: str
    name: str
    description: str
    priority: str
    status: str
    created_at: str
    updated_at: str
    completed_at: Optional[str]
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    metadata: Dict[str, Any]


class TaskListResponse(BaseModel):
    """Response model for task list."""
    tasks: List[TaskResponse]
    total: int


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    task_service: TaskService = Depends(get_task_service)
):
    """List tasks with optional filtering."""
    try:
        filters = {}
        
        if agent_id:
            # Validate agent ID format
            try:
                UUID(agent_id)
                filters["agent_id"] = agent_id
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid agent ID format"
                )
        
        if status:
            try:
                TaskStatus(status)
                filters["status"] = status
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status}"
                )
        
        if priority:
            try:
                Priority[priority.upper()]
                filters["priority"] = priority
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid priority: {priority}"
                )
        
        tasks = await task_service.list_tasks(filters, limit, offset)
        
        task_responses = [
            TaskResponse(
                id=str(task.id),
                agent_id=str(task.agent_id),
                name=task.name,
                description=task.description,
                priority=task.priority.name.lower(),
                status=task.status.value,
                created_at=task.created_at.isoformat(),
                updated_at=task.updated_at.isoformat(),
                completed_at=task.completed_at.isoformat() if task.completed_at else None,
                result=task.result,
                error=task.error,
                metadata=task.metadata,
            )
            for task in tasks
        ]
        
        return TaskListResponse(tasks=task_responses, total=len(task_responses))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error listing tasks", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list tasks"
        )


@router.post("/", response_model=TaskResponse)
async def create_task(
    request: TaskCreateRequest,
    task_service: TaskService = Depends(get_task_service)
):
    """Create a new task."""
    try:
        # Validate agent ID format
        try:
            UUID(request.agent_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid agent ID format"
            )
        
        # Validate priority
        try:
            priority = Priority[request.priority.upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid priority: {request.priority}"
            )
        
        task = await task_service.create_task(
            agent_id=request.agent_id,
            name=request.name,
            description=request.description,
            priority=priority,
            metadata=request.metadata
        )
        
        return TaskResponse(
            id=str(task.id),
            agent_id=str(task.agent_id),
            name=task.name,
            description=task.description,
            priority=task.priority.name.lower(),
            status=task.status.value,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
            completed_at=task.completed_at.isoformat() if task.completed_at else None,
            result=task.result,
            error=task.error,
            metadata=task.metadata,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating task", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task"
        )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str = Depends(validate_task_id),
    task_service: TaskService = Depends(get_task_service)
):
    """Get task by ID."""
    try:
        task = await task_service.get_task(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return TaskResponse(
            id=str(task.id),
            agent_id=str(task.agent_id),
            name=task.name,
            description=task.description,
            priority=task.priority.name.lower(),
            status=task.status.value,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
            completed_at=task.completed_at.isoformat() if task.completed_at else None,
            result=task.result,
            error=task.error,
            metadata=task.metadata,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting task", error=str(e), task_id=task_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get task"
        )


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    request: TaskUpdateRequest,
    task_id: str = Depends(validate_task_id),
    task_service: TaskService = Depends(get_task_service)
):
    """Update task."""
    try:
        # Validate priority if provided
        priority = None
        if request.priority:
            try:
                priority = Priority[request.priority.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid priority: {request.priority}"
                )
        
        task = await task_service.update_task(
            task_id=task_id,
            name=request.name,
            description=request.description,
            priority=priority,
            metadata=request.metadata
        )
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return TaskResponse(
            id=str(task.id),
            agent_id=str(task.agent_id),
            name=task.name,
            description=task.description,
            priority=task.priority.name.lower(),
            status=task.status.value,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
            completed_at=task.completed_at.isoformat() if task.completed_at else None,
            result=task.result,
            error=task.error,
            metadata=task.metadata,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating task", error=str(e), task_id=task_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update task"
        )


@router.delete("/{task_id}")
async def delete_task(
    task_id: str = Depends(validate_task_id),
    task_service: TaskService = Depends(get_task_service)
):
    """Delete task."""
    try:
        success = await task_service.delete_task(task_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return {"message": "Task deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting task", error=str(e), task_id=task_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete task"
        )


@router.post("/{task_id}/execute")
async def execute_task(
    task_id: str = Depends(validate_task_id),
    task_service: TaskService = Depends(get_task_service)
):
    """Execute task."""
    try:
        task = await task_service.execute_task(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return TaskResponse(
            id=str(task.id),
            agent_id=str(task.agent_id),
            name=task.name,
            description=task.description,
            priority=task.priority.name.lower(),
            status=task.status.value,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
            completed_at=task.completed_at.isoformat() if task.completed_at else None,
            result=task.result,
            error=task.error,
            metadata=task.metadata,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error executing task", error=str(e), task_id=task_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute task"
        )


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: str = Depends(validate_task_id),
    task_service: TaskService = Depends(get_task_service)
):
    """Cancel task."""
    try:
        success = await task_service.cancel_task(task_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found or cannot be cancelled"
            )
        
        return {"message": "Task cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error cancelling task", error=str(e), task_id=task_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel task"
        )


@router.get("/agent/{agent_id}/tasks", response_model=TaskListResponse)
async def get_agent_tasks(
    agent_id: str = Depends(validate_agent_id),
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    task_service: TaskService = Depends(get_task_service)
):
    """Get tasks for specific agent."""
    try:
        filters = {"agent_id": agent_id}
        
        if status:
            try:
                TaskStatus(status)
                filters["status"] = status
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status}"
                )
        
        tasks = await task_service.list_tasks(filters, limit, offset)
        
        task_responses = [
            TaskResponse(
                id=str(task.id),
                agent_id=str(task.agent_id),
                name=task.name,
                description=task.description,
                priority=task.priority.name.lower(),
                status=task.status.value,
                created_at=task.created_at.isoformat(),
                updated_at=task.updated_at.isoformat(),
                completed_at=task.completed_at.isoformat() if task.completed_at else None,
                result=task.result,
                error=task.error,
                metadata=task.metadata,
            )
            for task in tasks
        ]
        
        return TaskListResponse(tasks=task_responses, total=len(task_responses))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting agent tasks", error=str(e), agent_id=agent_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get agent tasks"
        )


@router.get("/stats/summary")
async def get_task_stats(
    task_service: TaskService = Depends(get_task_service)
):
    """Get task statistics summary."""
    try:
        stats = await task_service.get_task_statistics()
        return stats
        
    except Exception as e:
        logger.error("Error getting task stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get task statistics"
        )