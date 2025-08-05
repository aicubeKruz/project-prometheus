# Contributing to Project Prometheus

Thank you for your interest in contributing to Project Prometheus! This document provides guidelines for contributing to this multi-agent AGI research system.

## Code of Conduct

- **Safety First**: Always prioritize safety in AGI research and development
- **Respect**: Treat all contributors with respect and professionalism
- **Collaboration**: Work together towards the common goal of safe AGI
- **Quality**: Maintain high code quality and comprehensive testing
- **Documentation**: Document all changes and new features thoroughly

## Getting Started

### Development Setup

1. **Fork the repository** on GitHub
2. **Clone your fork:**
```bash
git clone https://github.com/your-username/project-prometheus.git
cd project-prometheus
```

3. **Create a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

4. **Install dependencies:**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

5. **Run tests:**
```bash
pytest
```

6. **Run the demo:**
```bash
python scripts/run_demo.py
```

### Development Environment

- **Python 3.10+** required
- **Redis** for testing event bus functionality
- **Docker** (optional) for containerized testing
- **IDE**: VS Code, PyCharm, or similar with Python support

## Making Changes

### Branch Naming

- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `safety/description` - Safety-related improvements
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Commit Messages

Use conventional commit format:
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `safety`: Safety improvement
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

Example:
```
feat(agents): add new reasoning capability to Logos agent

- Implement temporal logic reasoning
- Add validation for time-based constraints
- Update safety checks for temporal operations

Closes #123
```

### Code Standards

#### Python Style

- **PEP 8** compliance
- **Type hints** for all function parameters and return types
- **Docstrings** for all classes and public methods
- **Black** formatting with 88 character line length
- **isort** for import organization

#### Architecture Principles

- **Domain-Driven Design**: Keep domain logic separate from infrastructure
- **SOLID Principles**: Follow single responsibility, open-closed, etc.
- **Async/Await**: Use async patterns for I/O operations
- **Error Handling**: Comprehensive exception handling with logging
- **Testing**: Unit tests for all new functionality

#### Safety Requirements

- **Safety Checks**: All agent modifications must include safety validation
- **Themis Integration**: New features must be compatible with safety monitoring
- **Emergency Controls**: Ensure emergency halt mechanisms work with changes
- **Documentation**: Safety implications must be documented

### Testing

#### Test Structure
```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── safety/         # Safety-specific tests
└── fixtures/       # Test fixtures and utilities
```

#### Running Tests
```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_agents.py

# With coverage
pytest --cov=prometheus tests/

# Safety tests only
pytest tests/safety/
```

#### Test Requirements

- **Unit tests** for all new functions and methods
- **Integration tests** for agent interactions
- **Safety tests** for safety-critical functionality
- **Mock external dependencies** (Redis, APIs, etc.)
- **Edge case coverage** including error conditions

### Agent Development

When adding new agents or modifying existing ones:

1. **Inherit from BaseAgent**
2. **Implement required abstract methods**
3. **Add safety checks** and monitoring
4. **Update agent hierarchy** if needed
5. **Add comprehensive tests**
6. **Document agent capabilities** and limitations

Example agent structure:
```python
class AgentNew(BaseAgent):
    """New specialized agent for specific functionality."""
    
    def __init__(self, ...):
        super().__init__(agent_type=AgentType.NEW, ...)
        
    async def _process_message_internal(self, message: Message) -> Optional[Message]:
        """Process agent-specific messages."""
        pass
        
    async def _execute_task_internal(self, task: Task) -> Dict[str, Any]:
        """Execute agent-specific tasks."""
        pass
        
    async def _perform_safety_checks(self, task: Task) -> List[SafetyCheck]:
        """Perform safety checks before task execution."""
        pass
```

### API Development

For API changes:

1. **Follow REST conventions**
2. **Add proper error handling**
3. **Include input validation**
4. **Update OpenAPI documentation**
5. **Add authentication/authorization**
6. **Test all endpoints**

### Documentation

- **README.md**: Update for new features
- **DEPLOYMENT.md**: Add deployment considerations
- **API docs**: Auto-generated from code
- **Code comments**: Explain complex logic
- **Safety documentation**: Document safety implications

## Pull Request Process

### Before Submitting

1. **Run all tests** and ensure they pass
2. **Check code formatting** with black and isort
3. **Verify type hints** with mypy
4. **Update documentation** as needed
5. **Test safety features** if applicable

### PR Requirements

- **Clear description** of changes
- **Link to related issues**
- **Test coverage** for new code
- **Documentation updates**
- **Safety review** for agent modifications
- **Backward compatibility** considerations

### Review Process

1. **Automated checks** must pass
2. **Code review** by maintainers
3. **Safety review** for safety-critical changes
4. **Testing** in development environment
5. **Approval** from project maintainers

## Issue Reporting

### Bug Reports

Include:
- **Python version** and environment details
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Error messages** and stack traces
- **System configuration** (OS, dependencies, etc.)

### Feature Requests

Include:
- **Use case** description
- **Proposed solution** or approach
- **Safety considerations**
- **Integration points** with existing agents
- **Testing strategy**

### Safety Issues

**Critical safety issues** should be reported immediately:
- Use "SAFETY" label
- Provide detailed description
- Include potential impact assessment
- Suggest mitigation strategies

## Release Process

### Version Numbers

Semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Release Checklist

- [ ] All tests passing
- [ ] Documentation updated
- [ ] Safety review completed
- [ ] Version number bumped
- [ ] Changelog updated
- [ ] Tag created and pushed

## Community

### Communication

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Pull Requests**: Code contributions

### Recognition

Contributors will be recognized:
- **Contributors list** in README
- **Release notes** acknowledgments
- **Special recognition** for safety improvements

## Safety Considerations

### Responsible Development

- Always consider **safety implications** of changes
- Follow **AI safety best practices**
- Implement **monitoring and oversight**
- Design with **fail-safe mechanisms**
- Document **safety trade-offs**

### Research Ethics

- Ensure **ethical use** of AGI research
- Consider **societal impact** of developments
- Maintain **transparency** in safety measures
- Follow **responsible disclosure** for vulnerabilities

---

Thank you for contributing to Project Prometheus! Together, we can advance AGI research while maintaining the highest safety standards.