"""
FastAPI dependencies for Project Prometheus.
"""
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
import structlog

from ..services.agent_manager import AgentManager
from ..services.task_service import TaskService
from ..config.settings import Settings, get_settings

logger = structlog.get_logger()


async def get_agent_manager(request: Request) -> AgentManager:
    """Get agent manager from application state."""
    agent_manager = getattr(request.app.state, "agent_manager", None)
    if not agent_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent manager not available"
        )
    return agent_manager


async def get_task_service(agent_manager: AgentManager = Depends(get_agent_manager)) -> TaskService:
    """Get task service."""
    return TaskService(agent_manager)


async def get_current_settings(request: Request) -> Settings:
    """Get current application settings."""
    settings = getattr(request.app.state, "settings", None)
    if not settings:
        settings = get_settings()
    return settings


async def verify_api_key(request: Request) -> Optional[str]:
    """Verify API key if authentication is enabled."""
    settings = await get_current_settings(request)
    
    if not settings.api_key_required:
        return None
    
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return api_key


class RateLimiter:
    """Simple rate limiter for API endpoints."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests = {}
    
    async def check_rate_limit(self, client_ip: str) -> bool:
        """Check if client has exceeded rate limit."""
        import time
        
        current_time = time.time()
        window_start = current_time - self.window_seconds
        
        # Clean old requests
        if client_ip in self._requests:
            self._requests[client_ip] = [
                req_time for req_time in self._requests[client_ip] 
                if req_time > window_start
            ]
        else:
            self._requests[client_ip] = []
        
        # Check rate limit
        if len(self._requests[client_ip]) >= self.max_requests:
            return False
        
        # Add current request
        self._requests[client_ip].append(current_time)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter()


async def check_rate_limit(request: Request) -> None:
    """Check rate limit for incoming requests."""
    client_ip = request.client.host
    
    if not await rate_limiter.check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )


async def validate_agent_id(agent_id: str) -> str:
    """Validate agent ID format."""
    try:
        from uuid import UUID
        UUID(agent_id)
        return agent_id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid agent ID format"
        )


async def validate_task_id(task_id: str) -> str:
    """Validate task ID format."""
    try:
        from uuid import UUID
        UUID(task_id)
        return task_id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task ID format"
        )