# Project Prometheus - Deployment Guide

## Quick Start

### Local Development

1. **Clone the repository:**
```bash
git clone https://github.com/aicubeKruz/project-prometheus.git
cd project-prometheus
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run demo:**
```bash
python scripts/run_demo.py
```

4. **Start API server:**
```bash
python main.py
```

Visit `http://localhost:8000/docs` for interactive API documentation.

### Docker Deployment

1. **Using Docker Compose (Recommended):**
```bash
docker-compose up -d
```

This will start:
- Project Prometheus API on port 8000
- Redis server on port 6379
- Prometheus metrics on port 9090 (optional)
- Grafana dashboard on port 3000 (optional)

2. **Build and run manually:**
```bash
# Build image
docker build -t project-prometheus .

# Run with Redis
docker run -d --name redis redis:7-alpine
docker run -d --name prometheus-api \
  --link redis:redis \
  -e REDIS_URL=redis://redis:6379 \
  -p 8000:8000 \
  project-prometheus
```

### Production Deployment

#### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Key production settings:
```env
ENVIRONMENT=production
DEBUG=false
API_KEY_REQUIRED=true
API_KEY=your-secure-api-key-here
REDIS_URL=redis://your-redis-server:6379
LOG_LEVEL=INFO
SAFETY_CHECKS_ENABLED=true
EMERGENCY_HALT_ON_CRITICAL=true
```

#### Security Considerations

- **API Key**: Always set `API_KEY_REQUIRED=true` in production
- **CORS Origins**: Configure `CORS_ORIGINS` to specific domains
- **Rate Limiting**: Adjust `RATE_LIMIT_RPM` based on your needs
- **SSL/TLS**: Use a reverse proxy (nginx, traefik) for HTTPS
- **Firewall**: Restrict access to Redis and internal services

#### Scaling

**Horizontal Scaling:**
- Run multiple API instances behind a load balancer
- Use Redis Cluster for high availability
- Consider container orchestration (Kubernetes, Docker Swarm)

**Monitoring:**
- Enable Prometheus metrics (`METRICS_ENABLED=true`)
- Use Grafana for visualization
- Set up alerting for critical safety violations

#### Health Checks

The application provides several health endpoints:
- `/health` - Basic health check
- `/api/v1/system/status` - Detailed system status
- `/api/v1/system/metrics` - System metrics

## API Usage Examples

### Initialize the System

```bash
# Setup agent hierarchy
curl -X POST "http://localhost:8000/api/v1/system/hierarchy/setup" \
  -H "X-API-Key: your-api-key"

# Initialize project
curl -X POST "http://localhost:8000/api/v1/system/initialize" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "mission": "Develop safe and aligned artificial general intelligence",
    "research_phases": ["architecture_design", "safety_validation"]
  }'
```

### Create and Execute Tasks

```bash
# Get agent list
curl "http://localhost:8000/api/v1/agents/" \
  -H "X-API-Key: your-api-key"

# Create task
curl -X POST "http://localhost:8000/api/v1/tasks/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "agent_id": "agent-uuid-here",
    "name": "Research Task",
    "description": "Conduct AGI research",
    "priority": "high"
  }'

# Execute task
curl -X POST "http://localhost:8000/api/v1/tasks/{task-id}/execute" \
  -H "X-API-Key: your-api-key"
```

### Safety and Monitoring

```bash
# Trigger safety audit
curl -X POST "http://localhost:8000/api/v1/system/safety/audit" \
  -H "X-API-Key: your-api-key"

# Get system metrics
curl "http://localhost:8000/api/v1/system/metrics" \
  -H "X-API-Key: your-api-key"

# Emergency halt (if needed)
curl -X POST "http://localhost:8000/api/v1/system/emergency/halt" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"reason": "Safety concern detected"}'
```

## Troubleshooting

### Common Issues

1. **Redis Connection Error:**
   - Ensure Redis is running and accessible
   - Check `REDIS_URL` environment variable
   - Verify network connectivity

2. **Agent Not Responding:**
   - Check agent status via `/api/v1/agents/{agent-id}/status`
   - Review logs for error messages
   - Restart specific agent if needed

3. **Task Execution Failures:**
   - Verify agent is active and available
   - Check task parameters and requirements
   - Review safety check results

4. **API Authentication Issues:**
   - Ensure `X-API-Key` header is set correctly
   - Verify API key in environment variables
   - Check CORS settings for browser requests

### Logging

Logs are structured JSON format by default. Key log fields:
- `timestamp`: Event timestamp
- `level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `agent_id`: Related agent identifier
- `message`: Log message
- `error`: Error details (if applicable)

To access logs:
```bash
# Docker logs
docker logs prometheus-api

# Or if using docker-compose
docker-compose logs -f prometheus-api
```

### Performance Tuning

- **Memory**: Adjust based on number of agents and tasks
- **CPU**: Multi-core beneficial for concurrent task execution
- **Redis**: Configure max memory and eviction policies
- **API Workers**: Scale uvicorn workers based on load

## Support

- **Documentation**: Check `/docs` endpoint for API reference
- **Issues**: Report bugs and feature requests on GitHub
- **Safety Concerns**: Immediately report any safety-related issues

---

**⚠️ Safety Notice**: This system is designed for research purposes. Always ensure proper safety measures and monitoring are in place before deploying in production environments.