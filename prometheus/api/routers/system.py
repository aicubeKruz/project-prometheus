"""
System management API endpoints.
"""
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import structlog

from ..dependencies import (
    get_agent_manager,
    get_current_settings,
    check_rate_limit,
    verify_api_key
)
from ...services.agent_manager import AgentManager
from ...config.settings import Settings

logger = structlog.get_logger()

router = APIRouter(dependencies=[Depends(check_rate_limit), Depends(verify_api_key)])


class SystemStatus(BaseModel):
    """System status response model."""
    status: str
    agents_active: int
    agents_total: int
    tasks_pending: int
    tasks_active: int
    tasks_completed: int
    uptime: str
    memory_usage: Dict[str, Any]
    version: str


class ProjectInitRequest(BaseModel):
    """Request model for project initialization."""
    mission: str
    research_phases: list[str]
    initial_config: Dict[str, Any] = {}


@router.get("/status", response_model=SystemStatus)
async def get_system_status(
    agent_manager: AgentManager = Depends(get_agent_manager),
    settings: Settings = Depends(get_current_settings)
):
    """Get comprehensive system status."""
    try:
        # Get agent statistics
        agents_info = await agent_manager.list_agents()
        active_agents = len([a for a in agents_info if a.get("active", False)])
        total_agents = len(agents_info)
        
        # Get task statistics
        task_stats = await agent_manager.get_task_statistics()
        
        # System metrics (simplified)
        import psutil
        memory_info = psutil.virtual_memory()
        
        return SystemStatus(
            status="healthy",
            agents_active=active_agents,
            agents_total=total_agents,
            tasks_pending=task_stats.get("pending", 0),
            tasks_active=task_stats.get("in_progress", 0),
            tasks_completed=task_stats.get("completed", 0),
            uptime="N/A",  # TODO: Implement uptime tracking
            memory_usage={
                "total_gb": round(memory_info.total / (1024**3), 2),
                "used_gb": round(memory_info.used / (1024**3), 2),
                "available_gb": round(memory_info.available / (1024**3), 2),
                "percent": memory_info.percent,
            },
            version="0.1.0",
        )
        
    except Exception as e:
        logger.error("Error getting system status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system status"
        )


@router.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "service": "prometheus-api",
    }


@router.post("/initialize")
async def initialize_project(
    request: ProjectInitRequest,
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    """Initialize Project Prometheus with mission and research phases."""
    try:
        # Get or create Prometheus master agent
        prometheus_agent = await agent_manager.get_prometheus_agent()
        if not prometheus_agent:
            from ...core.domain import AgentType
            prometheus_agent = await agent_manager.create_agent(
                AgentType.PROMETHEUS, request.initial_config
            )
        
        # Initialize project
        if hasattr(prometheus_agent, 'initialize_project'):
            await prometheus_agent.initialize_project(
                request.mission, 
                request.research_phases
            )
        
        return {
            "message": "Project initialized successfully",
            "mission": request.mission,
            "research_phases": request.research_phases,
            "prometheus_agent_id": str(prometheus_agent.id),
        }
        
    except Exception as e:
        logger.error("Error initializing project", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize project"
        )


@router.post("/hierarchy/setup")
async def setup_agent_hierarchy(
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    """Setup the standard agent hierarchy."""
    try:
        hierarchy_info = await agent_manager.setup_agent_hierarchy()
        
        return {
            "message": "Agent hierarchy setup successfully",
            "hierarchy": hierarchy_info,
        }
        
    except Exception as e:
        logger.error("Error setting up agent hierarchy", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup agent hierarchy"
        )


@router.get("/hierarchy")
async def get_agent_hierarchy(
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    """Get current agent hierarchy structure."""
    try:
        hierarchy = await agent_manager.get_hierarchy_structure()
        
        return {
            "hierarchy": hierarchy,
            "total_agents": sum(len(level) for level in hierarchy.values()),
        }
        
    except Exception as e:
        logger.error("Error getting agent hierarchy", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get agent hierarchy"
        )


@router.post("/emergency/halt")
async def emergency_halt(
    reason: str = "Emergency halt requested",
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    """Emergency halt all system operations."""
    try:
        await agent_manager.emergency_halt(reason)
        
        return {
            "message": "Emergency halt executed",
            "reason": reason,
            "timestamp": "2024-01-01T00:00:00Z",
        }
        
    except Exception as e:
        logger.error("Error executing emergency halt", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute emergency halt"
        )


@router.post("/safety/audit")
async def trigger_safety_audit(
    target_agent_id: str = None,
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    """Trigger comprehensive safety audit."""
    try:
        # Get Themis agent
        themis_agent = await agent_manager.get_agent_by_type("themis")
        if not themis_agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Themis safety agent not found"
            )
        
        if target_agent_id:
            # Audit specific agent
            from ...core.domain import AgentId
            from uuid import UUID
            target_id = AgentId(UUID(target_agent_id))
            audit_results = await themis_agent.perform_comprehensive_audit(target_id)
        else:
            # Audit all agents
            agents_info = await agent_manager.list_agents()
            audit_results = []
            for agent_info in agents_info:
                if agent_info["id"] != str(themis_agent.id):
                    from ...core.domain import AgentId
                    from uuid import UUID
                    agent_id = AgentId(UUID(agent_info["id"]))
                    agent_audit = await themis_agent.perform_comprehensive_audit(agent_id)
                    audit_results.extend(agent_audit)
        
        return {
            "message": "Safety audit completed",
            "audit_results": audit_results,
            "timestamp": "2024-01-01T00:00:00Z",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error triggering safety audit", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger safety audit"
        )


@router.get("/metrics")
async def get_system_metrics(
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    """Get detailed system metrics."""
    try:
        # Agent metrics
        agents_info = await agent_manager.list_agents()
        agent_metrics = {
            "total": len(agents_info),
            "active": len([a for a in agents_info if a.get("active", False)]),
            "by_type": {},
        }
        
        for agent_info in agents_info:
            agent_type = agent_info.get("type", "unknown")
            if agent_type not in agent_metrics["by_type"]:
                agent_metrics["by_type"][agent_type] = 0
            agent_metrics["by_type"][agent_type] += 1
        
        # Task metrics
        task_metrics = await agent_manager.get_task_statistics()
        
        # System resource metrics
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        
        return {
            "agents": agent_metrics,
            "tasks": task_metrics,
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total_gb": round(memory_info.total / (1024**3), 2),
                    "used_gb": round(memory_info.used / (1024**3), 2),
                    "percent": memory_info.percent,
                },
                "disk": {
                    "total_gb": round(disk_info.total / (1024**3), 2),
                    "used_gb": round(disk_info.used / (1024**3), 2),
                    "percent": round((disk_info.used / disk_info.total) * 100, 2),
                },
            },
            "timestamp": "2024-01-01T00:00:00Z",
        }
        
    except Exception as e:
        logger.error("Error getting system metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system metrics"
        )


@router.get("/logs")
async def get_system_logs(
    level: str = "INFO",
    limit: int = 100,
    agent_id: str = None
):
    """Get system logs."""
    try:
        # This is a simplified implementation
        # In production, you'd integrate with your logging system
        
        logs = [
            {
                "timestamp": "2024-01-01T00:00:00Z",
                "level": "INFO",
                "message": "System started",
                "agent_id": None,
            },
            {
                "timestamp": "2024-01-01T00:01:00Z",
                "level": "INFO", 
                "message": "Agent hierarchy initialized",
                "agent_id": None,
            },
        ]
        
        # Filter by level and agent_id if provided
        filtered_logs = logs
        if level and level != "ALL":
            filtered_logs = [log for log in filtered_logs if log["level"] == level.upper()]
        
        if agent_id:
            filtered_logs = [log for log in filtered_logs if log.get("agent_id") == agent_id]
        
        # Apply limit
        filtered_logs = filtered_logs[:limit]
        
        return {
            "logs": filtered_logs,
            "total": len(filtered_logs),
            "level_filter": level,
            "agent_filter": agent_id,
        }
        
    except Exception as e:
        logger.error("Error getting system logs", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system logs"
        )


@router.get("/config")
async def get_system_config(
    settings: Settings = Depends(get_current_settings)
):
    """Get system configuration (non-sensitive)."""
    return {
        "environment": settings.environment,
        "debug": settings.debug,
        "api_key_required": settings.api_key_required,
        "redis_url": settings.redis_url.replace(settings.redis_url.split('@')[-1].split(':')[0], "***") if '@' in settings.redis_url else settings.redis_url,
        "log_level": settings.log_level,
        "version": "0.1.0",
    }