"""
Main entry point for Project Prometheus API server.
"""
import uvicorn
from prometheus.config.settings import get_settings


def main():
    """Run the API server."""
    settings = get_settings()
    
    uvicorn.run(
        "prometheus.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True,
    )


if __name__ == "__main__":
    main()