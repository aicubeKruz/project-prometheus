"""
Task Service for Project Prometheus.
Manages task creation, execution, and lifecycle.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog

from ..core.domain import AgentId, Priority, Task, TaskId, TaskStatus
from ..services.agent_manager import AgentManager

logger = structlog.get_logger()


class TaskService:
    """
    Service for managing tasks in the Project Prometheus system.
    
    Responsibilities:
    - Create and manage task lifecycle
    - Assign tasks to appropriate agents
    - Monitor task execution
    - Provide task statistics and reporting
    """

    def __init__(self, agent_manager: AgentManager):
        self._agent_manager = agent_manager
        self._task_repository = agent_manager._task_repository

    async def create_task(
        self,
        agent_id: str,
        name: str,
        description: str = "",
        priority: Priority = Priority.MEDIUM,
        metadata: Dict[str, Any] = None
    ) -> Task:
        """Create a new task."""
        try:
            # Validate agent exists
            agent = await self._agent_manager.get_agent(agent_id)
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            # Create task
            task = Task(
                agent_id=AgentId(UUID(agent_id)),
                name=name,
                description=description,
                priority=priority,
                metadata=metadata or {},
            )
            
            # Save task
            await self._task_repository.save(task)
            
            logger.info("Task created", 
                       task_id=str(task.id), 
                       agent_id=agent_id, 
                       name=name)
            
            return task
            
        except Exception as e:
            logger.error("Error creating task", error=str(e), agent_id=agent_id, name=name)
            raise

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        try:
            task_uuid = TaskId(UUID(task_id))
            return await self._task_repository.get_by_id(task_uuid)
        except Exception as e:
            logger.error("Error getting task", error=str(e), task_id=task_id)
            return None

    async def update_task(
        self,
        task_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[Priority] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Task]:
        """Update task."""
        try:
            task = await self.get_task(task_id)
            if not task:
                return None
            
            # Update fields
            if name is not None:
                task.name = name
            if description is not None:
                task.description = description
            if priority is not None:
                task.priority = priority
            if metadata is not None:
                task.metadata.update(metadata)
            
            task.updated_at = task.updated_at  # This would be set automatically in real implementation
            
            # Save updated task
            await self._task_repository.save(task)
            
            logger.info("Task updated", task_id=task_id)
            return task
            
        except Exception as e:
            logger.error("Error updating task", error=str(e), task_id=task_id)
            return None

    async def delete_task(self, task_id: str) -> bool:
        """Delete task."""
        try:
            task_uuid = TaskId(UUID(task_id))
            success = await self._task_repository.delete(task_uuid)
            
            if success:
                logger.info("Task deleted", task_id=task_id)
            
            return success
            
        except Exception as e:
            logger.error("Error deleting task", error=str(e), task_id=task_id)
            return False

    async def execute_task(self, task_id: str) -> Optional[Task]:
        """Execute task by assigning it to the appropriate agent."""
        try:
            task = await self.get_task(task_id)
            if not task:
                return None
            
            # Get agent
            agent = await self._agent_manager.get_agent(str(task.agent_id))
            if not agent:
                task.mark_failed("Agent not found")
                await self._task_repository.save(task)
                return task
            
            # Execute task
            executed_task = await agent.execute_task(task)
            
            # Save updated task
            await self._task_repository.save(executed_task)
            
            logger.info("Task executed", 
                       task_id=task_id, 
                       status=executed_task.status.value)
            
            return executed_task
            
        except Exception as e:
            logger.error("Error executing task", error=str(e), task_id=task_id)
            
            # Mark task as failed
            task = await self.get_task(task_id)
            if task:
                task.mark_failed(str(e))
                await self._task_repository.save(task)
            
            return task

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel task."""
        try:
            task = await self.get_task(task_id)
            if not task:
                return False
            
            # Can only cancel pending or in-progress tasks
            if task.status not in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
                return False
            
            task.status = TaskStatus.CANCELLED
            task.updated_at = task.updated_at  # Would be set automatically
            
            await self._task_repository.save(task)
            
            logger.info("Task cancelled", task_id=task_id)
            return True
            
        except Exception as e:
            logger.error("Error cancelling task", error=str(e), task_id=task_id)
            return False

    async def list_tasks(
        self, 
        filters: Dict[str, Any] = None, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[Task]:
        """List tasks with optional filtering."""
        try:
            if filters:
                # Use repository's find_by_criteria if available
                if hasattr(self._task_repository, 'find_by_criteria'):
                    tasks = await self._task_repository.find_by_criteria(filters)
                else:
                    # Fallback: get all and filter manually
                    all_tasks = await self._task_repository.list_all()
                    tasks = []
                    for task in all_tasks:
                        match = True
                        for key, value in filters.items():
                            task_value = getattr(task, key, None)
                            if task_value != value:
                                # Handle special cases
                                if key == "agent_id" and str(task_value) != value:
                                    match = False
                                    break
                                elif key == "status" and (
                                    hasattr(task_value, 'value') and task_value.value != value
                                ):
                                    match = False
                                    break
                                elif key == "priority" and (
                                    hasattr(task_value, 'name') and task_value.name.lower() != value.lower()
                                ):
                                    match = False
                                    break
                        if match:
                            tasks.append(task)
            else:
                tasks = await self._task_repository.list_all()
            
            # Apply pagination
            end_index = min(offset + limit, len(tasks))
            paginated_tasks = tasks[offset:end_index]
            
            return paginated_tasks
            
        except Exception as e:
            logger.error("Error listing tasks", error=str(e), filters=filters)
            return []

    async def get_tasks_by_agent(self, agent_id: str) -> List[Task]:
        """Get all tasks for a specific agent."""
        return await self.list_tasks({"agent_id": agent_id})

    async def get_pending_tasks(self) -> List[Task]:
        """Get all pending tasks."""
        return await self.list_tasks({"status": TaskStatus.PENDING.value})

    async def get_active_tasks(self) -> List[Task]:
        """Get all active (in-progress) tasks."""
        return await self.list_tasks({"status": TaskStatus.IN_PROGRESS.value})

    async def get_completed_tasks(self) -> List[Task]:
        """Get all completed tasks."""
        return await self.list_tasks({"status": TaskStatus.COMPLETED.value})

    async def get_task_statistics(self) -> Dict[str, Any]:
        """Get comprehensive task statistics."""
        try:
            all_tasks = await self._task_repository.list_all()
            
            stats = {
                "total": len(all_tasks),
                "by_status": {},
                "by_priority": {},
                "by_agent": {},
                "completion_rate": 0.0,
                "failure_rate": 0.0,
            }
            
            completed_count = 0
            failed_count = 0
            
            for task in all_tasks:
                # Status statistics
                status = task.status.value if hasattr(task.status, 'value') else str(task.status)
                stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
                
                # Priority statistics
                priority = task.priority.name if hasattr(task.priority, 'name') else str(task.priority)
                stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1
                
                # Agent statistics
                agent_id = str(task.agent_id)
                stats["by_agent"][agent_id] = stats["by_agent"].get(agent_id, 0) + 1
                
                # Count completed and failed
                if task.status == TaskStatus.COMPLETED:
                    completed_count += 1
                elif task.status == TaskStatus.FAILED:
                    failed_count += 1
            
            # Calculate rates
            if len(all_tasks) > 0:
                stats["completion_rate"] = completed_count / len(all_tasks)
                stats["failure_rate"] = failed_count / len(all_tasks)
            
            return stats
            
        except Exception as e:
            logger.error("Error getting task statistics", error=str(e))
            return {
                "total": 0,
                "by_status": {},
                "by_priority": {},
                "by_agent": {},
                "completion_rate": 0.0,
                "failure_rate": 0.0,
            }

    async def assign_task_to_agent(self, task_id: str, agent_id: str) -> bool:
        """Assign existing task to a different agent."""
        try:
            task = await self.get_task(task_id)
            if not task:
                return False
            
            # Validate new agent exists
            agent = await self._agent_manager.get_agent(agent_id)
            if not agent:
                return False
            
            # Update task assignment
            task.agent_id = AgentId(UUID(agent_id))
            task.updated_at = task.updated_at  # Would be set automatically
            
            await self._task_repository.save(task)
            
            logger.info("Task reassigned", task_id=task_id, new_agent_id=agent_id)
            return True
            
        except Exception as e:
            logger.error("Error reassigning task", error=str(e), task_id=task_id, agent_id=agent_id)
            return False

    async def create_research_phase_tasks(
        self, 
        phase: str, 
        phase_config: Dict[str, Any]
    ) -> List[Task]:
        """Create tasks for a specific research phase."""
        try:
            tasks = []
            
            # Get Prometheus agent to coordinate task creation
            prometheus_agent = await self._agent_manager.get_prometheus_agent()
            if not prometheus_agent and hasattr(prometheus_agent, 'decompose_research_phase'):
                phase_tasks = await prometheus_agent.decompose_research_phase(phase)
                
                for task_def in phase_tasks:
                    target_agent_type = task_def.metadata.get("target_agent")
                    target_agent = await self._agent_manager.get_agent_by_type(target_agent_type)
                    
                    if target_agent:
                        task = await self.create_task(
                            agent_id=str(target_agent.id),
                            name=task_def.name,
                            description=task_def.description,
                            priority=task_def.priority,
                            metadata=task_def.metadata
                        )
                        tasks.append(task)
            
            logger.info("Research phase tasks created", 
                       phase=phase, 
                       tasks_created=len(tasks))
            
            return tasks
            
        except Exception as e:
            logger.error("Error creating research phase tasks", error=str(e), phase=phase)
            return []

    async def monitor_task_execution(self) -> Dict[str, Any]:
        """Monitor ongoing task execution across all agents."""
        try:
            active_tasks = await self.get_active_tasks()
            
            monitoring_data = {
                "active_tasks": len(active_tasks),
                "task_details": [],
                "agent_workload": {},
                "stuck_tasks": [],
                "estimated_completion": {},
            }
            
            for task in active_tasks:
                agent_id = str(task.agent_id)
                
                # Count tasks per agent
                monitoring_data["agent_workload"][agent_id] = (
                    monitoring_data["agent_workload"].get(agent_id, 0) + 1
                )
                
                # Task details
                task_detail = {
                    "id": str(task.id),
                    "name": task.name,
                    "agent_id": agent_id,
                    "started_at": task.updated_at.isoformat(),
                    "priority": task.priority.name if hasattr(task.priority, 'name') else str(task.priority),
                }
                monitoring_data["task_details"].append(task_detail)
                
                # Check for stuck tasks (simplified logic)
                from datetime import datetime, timedelta
                if task.updated_at < datetime.utcnow() - timedelta(hours=1):
                    monitoring_data["stuck_tasks"].append({
                        "id": str(task.id),
                        "name": task.name,
                        "stuck_duration_hours": (datetime.utcnow() - task.updated_at).total_seconds() / 3600,
                    })
            
            return monitoring_data
            
        except Exception as e:
            logger.error("Error monitoring task execution", error=str(e))
            return {
                "active_tasks": 0,
                "task_details": [],
                "agent_workload": {},
                "stuck_tasks": [],
                "estimated_completion": {},
            }