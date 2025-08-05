# Project Prometheus

[![GitHub release](https://img.shields.io/github/v/release/aicubeKruz/project-prometheus)](https://github.com/aicubeKruz/project-prometheus/releases)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub issues](https://img.shields.io/github/issues/aicubeKruz/project-prometheus)](https://github.com/aicubeKruz/project-prometheus/issues)
[![Docker](https://img.shields.io/badge/docker-supported-blue)](https://docs.docker.com/)
[![Safety: Themis](https://img.shields.io/badge/safety-Themis%20monitored-green)](https://github.com/aicubeKruz/project-prometheus)

A hierarchical multi-agent system for AGI research and development, implementing a "society of minds" architecture with specialized AI agents collaborating in a structured yet adversarial ecosystem.

## Architecture Overview

Project Prometheus is executed by a hierarchical, multi-agent system composed of specialized AI agents, each with distinct roles and responsibilities:

### Agent Hierarchy

- **Agent Prometheus (Master Control & Strategy)**: The highest-level agent serving as project director
  - Interprets constitutional mission and decomposes into strategic research phases
  - Allocates computational resources and synthesizes findings from subordinate agents
  - Responsible for overall project planning and coordination

- **Agent Daedalus (Cognitive Architect)**: Lead R&D agent responsible for core AGI architecture design
  - Explores and integrates architectural pathways
  - Develops hybrid neuro-symbolic core with interplay between sub-symbolic learning and formal reasoning
  - Designs robust, generalizable intelligence systems

- **Agent Logos (Symbolic Reasoner & Verifier)**: Specialized sub-agent reporting to Daedalus
  - Focuses on "System 2" components of hybrid brain
  - Develops formal logic systems, knowledge graphs, and program synthesis capabilities
  - Serves as verifier for logical consistency of reasoning traces and plans

- **Agent Odysseus (Embodied Explorer & Tool User)**: Responsible for grounding knowledge in reality
  - Operates within complex, high-fidelity simulations
  - Interacts with external tools (databases, APIs, code execution environments)
  - Generates rich, multimodal, experiential data to bridge abstract knowledge and real-world application

- **Agent Themis (Safety & Alignment Overseer)**: Most critical agent with highest priority and veto power
  - Serves as internal perpetual red team
  - Continuously audits, stress-tests, and evaluates all architectures and behaviors
  - Monitors for emergent undesirable behaviors and specification gaming
  - Uses interpretability tools to ensure alignment with project constitution

## Key Features

- **Hierarchical Multi-Agent Architecture**: Structured communication and coordination between specialized agents
- **Safety-First Design**: Integrated safety monitoring and veto mechanisms
- **Hybrid Intelligence**: Combining neural networks with symbolic reasoning
- **Embodied Learning**: Real-world grounding through simulation and tool interaction
- **Formal Verification**: Logical consistency checking and program synthesis
- **RESTful API**: Complete REST API for system interaction and monitoring
- **Real-time Monitoring**: Comprehensive system status and metrics
- **Scalable Infrastructure**: Redis-based event bus and distributed task execution

## Quick Start

### Prerequisites

- Python 3.10+
- Redis server
- Docker (optional)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/aicubeKruz/project-prometheus.git
cd project-prometheus
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Start Redis server:
```bash
# Using Docker
docker run -d -p 6379:6379 redis:latest

# Or install locally and start
redis-server
```

5. Run the API server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### API Documentation

Once running, visit:
- Interactive API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

## Usage Examples

### Initialize the System

```bash
# Setup agent hierarchy
curl -X POST "http://localhost:8000/api/v1/system/hierarchy/setup"

# Initialize project with mission
curl -X POST "http://localhost:8000/api/v1/system/initialize" \
  -H "Content-Type: application/json" \
  -d '{
    "mission": "Develop safe and aligned artificial general intelligence",
    "research_phases": [
      "architecture_design",
      "symbolic_reasoning_development", 
      "embodied_learning",
      "safety_validation"
    ]
  }'
```

### Create and Execute Tasks

```bash
# Create a task
curl -X POST "http://localhost:8000/api/v1/tasks/" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "<agent-id>",
    "name": "Design Hybrid Architecture",
    "description": "Develop the neuro-symbolic hybrid core",
    "priority": "high"
  }'

# Execute task
curl -X POST "http://localhost:8000/api/v1/tasks/<task-id>/execute"
```

### Monitor System Status

```bash
# Get system status
curl "http://localhost:8000/api/v1/system/status"

# Get agent hierarchy
curl "http://localhost:8000/api/v1/system/hierarchy"

# Trigger safety audit
curl -X POST "http://localhost:8000/api/v1/system/safety/audit"
```

## Development

### Project Structure

```
project_prometheus/
├── prometheus/
│   ├── core/                 # Core domain models and base classes
│   ├── agents/              # Specialized agent implementations
│   ├── api/                 # FastAPI routes and dependencies
│   ├── services/            # Business logic services
│   ├── infrastructure/      # External integrations (Redis, etc.)
│   └── config/              # Configuration management
├── tests/                   # Test suites
├── docs/                    # Documentation
└── scripts/                 # Utility scripts
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=prometheus tests/

# Run specific test category
pytest tests/unit/
pytest tests/integration/
```

### Code Quality

```bash
# Format code
black prometheus/
isort prometheus/

# Type checking
mypy prometheus/

# Linting
flake8 prometheus/
```

## Configuration

Key configuration options in `.env`:

- `API_KEY_REQUIRED`: Enable API key authentication
- `SAFETY_CHECKS_ENABLED`: Enable safety monitoring
- `MAX_AGENTS`: Maximum number of agents
- `SIMULATION_ENABLED`: Enable simulation environments
- `LOG_LEVEL`: Logging verbosity

## Safety Considerations

Project Prometheus implements multiple safety layers:

1. **Themis Agent**: Continuous safety monitoring and veto power
2. **Hierarchical Control**: Structured oversight and coordination
3. **Formal Verification**: Logical consistency checking
4. **Emergency Halt**: System-wide shutdown capability
5. **Rate Limiting**: API request throttling
6. **Input Validation**: Comprehensive parameter validation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run code quality checks
5. Submit pull request

## License

This project is licensed under the MIT License with additional safety considerations - see the [LICENSE](LICENSE) file for details.

**Safety Notice**: This system is designed for AGI research. Always ensure proper safety measures and monitoring are in place.

## Support

For questions and support:
- **Repository**: [https://github.com/aicubeKruz/project-prometheus](https://github.com/aicubeKruz/project-prometheus)
- **Documentation**: See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment guide
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- **Issues**: Use [GitHub issues](https://github.com/aicubeKruz/project-prometheus/issues)
- **API Reference**: Available at `/docs` endpoint when running

## Roadmap

- [ ] Advanced neural architecture implementation
- [ ] Enhanced simulation environments
- [ ] Distributed agent deployment
- [ ] Advanced safety mechanisms
- [ ] Integration with external AI models
- [ ] Performance optimization
- [ ] Comprehensive monitoring dashboard

---

**Note**: This is a research system for AGI development. Use responsibly and ensure proper safety measures are in place.