"""
Agent management API endpoints.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import structlog

from ..dependencies import (
    get_agent_manager, 
    check_rate_limit, 
    validate_agent_id,
    verify_api_key
)
from ...services.agent_manager import AgentManager
from ...core.domain import AgentType, Message

logger = structlog.get_logger()

router = APIRouter(dependencies=[Depends(check_rate_limit), Depends(verify_api_key)])


class AgentCreateRequest(BaseModel):
    """Request model for creating an agent."""
    agent_type: str
    config: Dict[str, Any] = {}


class AgentUpdateRequest(BaseModel):
    """Request model for updating an agent."""
    config: Dict[str, Any] = {}


class MessageRequest(BaseModel):
    """Request model for sending a message to an agent."""
    receiver_id: str
    content: Dict[str, Any]
    message_type: str = "general"


class AgentResponse(BaseModel):
    """Response model for agent information."""
    id: str
    type: str
    status: str
    active: bool
    subordinates: List[str]
    supervisor: Optional[str]


class AgentListResponse(BaseModel):
    """Response model for agent list."""
    agents: List[AgentResponse]
    total: int


@router.get("/", response_model=AgentListResponse)
async def list_agents(
    agent_type: Optional[str] = None,
    active_only: bool = False,
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    """List all agents or filter by type/status."""
    try:
        agents_info = await agent_manager.list_agents()
        
        # Apply filters
        if agent_type:
            agents_info = [
                agent for agent in agents_info 
                if agent.get("type") == agent_type
            ]
        
        if active_only:
            agents_info = [
                agent for agent in agents_info 
                if agent.get("active", False)
            ]
        
        agents = [
            AgentResponse(
                id=agent["id"],
                type=agent.get("type", "unknown"),
                status="active" if agent.get("active") else "inactive",
                active=agent.get("active", False),
                subordinates=agent.get("subordinates", []),
                supervisor=agent.get("supervisor")
            )
            for agent in agents_info
        ]
        
        return AgentListResponse(agents=agents, total=len(agents))
        
    except Exception as e:
        logger.error("Error listing agents", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list agents"
        )


@router.post("/", response_model=AgentResponse)
async def create_agent(
    request: AgentCreateRequest,
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    """Create a new agent."""
    try:
        # Validate agent type
        try:
            agent_type = AgentType(request.agent_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid agent type: {request.agent_type}"
            )
        
        # Create agent
        agent = await agent_manager.create_agent(agent_type, request.config)
        agent_status = await agent.get_status()
        
        return AgentResponse(
            id=agent_status["id"],
            type=agent_status.get("type", "unknown"),
            status="active" if agent_status.get("active") else "inactive",
            active=agent_status.get("active", False),
            subordinates=agent_status.get("subordinates", []),
            supervisor=agent_status.get("supervisor")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating agent", error=str(e), agent_type=request.agent_type)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent"
        )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str = Depends(validate_agent_id),
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    """Get agent information by ID."""
    try:
        agent = await agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        agent_status = await agent.get_status()
        
        return AgentResponse(
            id=agent_status["id"],
            type=agent_status.get("type", "unknown"),
            status="active" if agent_status.get("active") else "inactive",
            active=agent_status.get("active", False),
            subordinates=agent_status.get("subordinates", []),
            supervisor=agent_status.get("supervisor")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting agent", error=str(e), agent_id=agent_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get agent"
        )


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    request: AgentUpdateRequest,
    agent_id: str = Depends(validate_agent_id),
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    """Update agent configuration."""
    try:
        agent = await agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        # Update agent configuration
        success = await agent_manager.update_agent_config(agent_id, request.config)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update agent configuration"
            )
        
        agent_status = await agent.get_status()
        
        return AgentResponse(
            id=agent_status["id"],
            type=agent_status.get("type", "unknown"),
            status="active" if agent_status.get("active") else "inactive",
            active=agent_status.get("active", False),
            subordinates=agent_status.get("subordinates", []),
            supervisor=agent_status.get("supervisor")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating agent", error=str(e), agent_id=agent_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update agent"
        )


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str = Depends(validate_agent_id),
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    """Delete an agent."""
    try:
        success = await agent_manager.remove_agent(agent_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        return {"message": "Agent deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting agent", error=str(e), agent_id=agent_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete agent"
        )


@router.post("/{agent_id}/start")
async def start_agent(
    agent_id: str = Depends(validate_agent_id),
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    """Start an agent."""
    try:
        success = await agent_manager.start_agent(agent_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        return {"message": "Agent started successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error starting agent", error=str(e), agent_id=agent_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start agent"
        )


@router.post("/{agent_id}/stop")
async def stop_agent(
    agent_id: str = Depends(validate_agent_id),
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    """Stop an agent."""
    try:
        success = await agent_manager.stop_agent(agent_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        return {"message": "Agent stopped successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error stopping agent", error=str(e), agent_id=agent_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop agent"
        )


@router.post("/{agent_id}/message")
async def send_message(
    request: MessageRequest,
    agent_id: str = Depends(validate_agent_id),
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    """Send a message to an agent."""
    try:
        # Validate receiver ID
        try:
            UUID(request.receiver_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid receiver ID format"
            )
        
        success = await agent_manager.send_message(
            agent_id, 
            request.receiver_id, 
            request.content,
            request.message_type
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        return {"message": "Message sent successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error sending message", error=str(e), agent_id=agent_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message"
        )


@router.get("/{agent_id}/status")
async def get_agent_status(
    agent_id: str = Depends(validate_agent_id),
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    """Get detailed agent status."""
    try:
        agent = await agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        status = await agent.get_status()
        health = await agent.get_health()
        
        return {
            "status": status,
            "health": health,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting agent status", error=str(e), agent_id=agent_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get agent status"
        )


@router.get("/{agent_id}/subordinates")
async def get_agent_subordinates(
    agent_id: str = Depends(validate_agent_id),
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    """Get agent's subordinates."""
    try:
        agent = await agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        subordinates = agent.subordinates
        subordinate_info = []
        
        for sub_id in subordinates:
            sub_agent = await agent_manager.get_agent(str(sub_id))
            if sub_agent:
                sub_status = await sub_agent.get_status()
                subordinate_info.append({
                    "id": str(sub_id),
                    "type": sub_status.get("type"),
                    "active": sub_status.get("active", False),
                })
        
        return {
            "subordinates": subordinate_info,
            "total": len(subordinate_info),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting agent subordinates", error=str(e), agent_id=agent_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get agent subordinates"
        )