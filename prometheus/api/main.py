"""
FastAPI application for Project Prometheus.
"""
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from .routers import agents, tasks, system
from .dependencies import get_agent_manager, get_task_service
from ..services.agent_manager import AgentManager
from ..config.settings import get_settings

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Project Prometheus API")
    
    # Initialize services
    settings = get_settings()
    agent_manager = AgentManager()
    
    # Start agent manager
    await agent_manager.start()
    
    # Store in app state
    app.state.agent_manager = agent_manager
    app.state.settings = settings
    
    yield
    
    # Cleanup
    logger.info("Shutting down Project Prometheus API")
    await agent_manager.stop()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="Project Prometheus",
        description="Multi-Agent AGI System API",
        version="0.1.0",
        lifespan=lifespan,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
    app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
    app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "name": "Project Prometheus",
            "description": "Multi-Agent AGI System",
            "version": "0.1.0",
            "status": "active",
        }
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error("Unhandled exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )
    
    return app


# Create app instance
app = create_app()