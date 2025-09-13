# Agent Runtime Service

A production-ready, containerized orchestration engine for LLM agents with MCP (Model Context Protocol) server integration. Built with `uv` for fast dependency management and optimized for cloud deployment.

## Overview

The Agent Runtime Service is the core orchestration layer that powers the Cellery platform. It provides:

- **Plan & Execute Architecture**: LLM-powered planning with reliable execution
- **MCP Server Integration**: Universal tool access through Model Context Protocol
- **Containerized Deployment**: Docker-ready with health checks and production optimizations
- **Cloud-Native Design**: Built for scalability, monitoring, and resilience

## Quick Start (Docker-first)

Discipline: start the runtime via Docker for consistency.

### Container Deployment

```bash
# Build and test container
./test_container.sh

# Or run with Docker Compose
docker-compose up -d

# Access API docs
open http://localhost:8000/docs
```

### Local Development (uv) — optional

If you need to run locally outside containers for debugging:

```bash
# Install dependencies
uv sync

# Run service
uv run agent-runtime

# Run comprehensive tests
./test_uv_setup.sh
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Layer    │───▶│  Orchestrator    │───▶│  Agent Service  │
│   (FastAPI)    │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │  Task Manager    │    │  Tool Registry  │
                       │                  │    │                 │
                       └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                                ┌─────────────────┐
                                                │  MCP Servers    │
                                                │  (filesystem,   │
                                                │   fetch, etc.)  │
                                                └─────────────────┘
```

## Key Components

### 1. Orchestrator (`services/orchestrator.py`)
- Manages complete task lifecycle from planning to execution
- Handles MCP server startup/shutdown
- Provides task-scoped resource management
- Streams execution logs and status updates

### 2. Agent Service (`services/agent_service.py`)
- **PlannerAgent**: Converts natural language prompts into executable plans
- **ExecutorAgent**: Executes individual plan steps with tool integration
- Manages agent instructions and context

### 3. Tool Registry (`services/tool_registry.py`)
- Discovers and manages MCP servers based on configuration
- Supports local (stdio) and remote (HTTP) MCP servers
- Handles server lifecycle and connection pooling

### 4. Task Manager (`services/task_manager.py`)
- In-memory task storage and status tracking
- Task creation, approval, and result management
- Thread-safe operations for concurrent access

## API Endpoints

### Core Task Management

**POST** `/v1/tasks`
- Submit natural language prompts for execution
- Returns task ID for tracking
- Processes in background

**GET** `/v1/tasks/{task_id}`
- Retrieve task status, plan, and results
- Real-time status updates

**POST** `/v1/tasks/{task_id}/approve`
- Approve generated plan for execution
- Triggers background execution

**GET** `/v1/tasks/{task_id}/stream`
- Server-sent events for real-time task updates
- WebSocket-style streaming over HTTP

## Container Deployment

### Docker Build

```bash
# Development build
docker build -t agent-runtime-service:dev --target development .

# Production build  
docker build -t agent-runtime-service:prod --target production .
```

### Docker Compose

```bash
# Development environment
docker-compose up -d

# Production environment (modify compose file)
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables

- `AGENT_RUNTIME_CONFIG`: Path to config file (default: `/app/config.yaml`)
- `PYTHONPATH`: Python path (default: `/app/src`)
- `OPENAI_API_KEY`: OpenAI API key (alternative to config file)

### Health Checks

The container includes health checks via:
- HTTP endpoint: `GET /docs`
- Container healthcheck: `curl -f http://localhost:8000/docs`
- Docker Compose healthcheck: Built-in monitoring

## Configuration

### Server Configuration (`config.yaml`)
```yaml
openai:
  api_key: "your-openai-api-key-here"

server:
  host: "0.0.0.0"   # For container deployment
  port: 8000
```

### Tool Registry (`tool_registry.yaml`)
```yaml
tool_registry:
  - id: "filesystem"
    enabled: true
    type: "local_stdio"
    config:
      command: "npx"
      args: ["@modelcontextprotocol/server-filesystem", "src/agent_runtime/sample_data"]

  - id: "fetch"
    enabled: true
    type: "local_stdio"
    config:
      command: "npx"
      args: ["@kazuph/mcp-fetch"]
```

## Development

### uv Commands

```bash
# Install dependencies
uv sync

# Add new dependency
uv add package-name

# Add dev dependency
uv add --dev package-name

# Run application
uv run agent-runtime

# Run tests
uv run pytest

# Run linting
uv run ruff check
uv run ruff format

# Run type checking
uv run mypy src/
```

### Testing

```bash
# Full uv setup verification
./test_uv_setup.sh

# Container deployment test
./test_container.sh

# Manual API testing
curl -X POST "http://localhost:8000/v1/tasks" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Read a file and summarize its contents"}'
```

## Cloud Deployment

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-runtime-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agent-runtime-service
  template:
    metadata:
      labels:
        app: agent-runtime-service
    spec:
      containers:
      - name: agent-runtime
        image: agent-runtime-service:prod
        ports:
        - containerPort: 8000
        env:
        - name: AGENT_RUNTIME_CONFIG
          value: "/app/config.yaml"
        livenessProbe:
          httpGet:
            path: /docs
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /docs  
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### AWS ECS / Google Cloud Run / Azure Container Instances

The service is designed to run in any container orchestration platform:

1. **Stateless**: No local state dependencies
2. **Health Checks**: Built-in health monitoring
3. **Configuration**: Environment variable based
4. **Logging**: Structured JSON logging for cloud platforms
5. **Graceful Shutdown**: Proper signal handling

## Performance & Scaling

- **Concurrent Tasks**: Supports multiple simultaneous task execution
- **Resource Management**: Task-scoped MCP server lifecycles  
- **Memory Usage**: Optimized container with minimal footprint
- **Network**: Async HTTP with connection pooling
- **Horizontal Scaling**: Stateless design allows multiple replicas

## Production Considerations

### Security
- Non-root container user
- Minimal base image (Python slim)
- No secrets in image layers
- Input validation and sanitization

### Monitoring
- Health check endpoints
- Structured logging
- Prometheus metrics (planned)
- OpenTelemetry tracing (planned)

### Reliability
- Graceful error handling
- Circuit breakers for external services
- Retry mechanisms with exponential backoff
- Resource limits and cleanup

## Integration with Cellery Platform

This agent runtime serves as the execution backend for the Cellery platform:

1. **Cellery Frontend** sends natural language blocks via API
2. **Agent Runtime** converts to executable plans  
3. **MCP Tools** execute the actual operations
4. **Results** stream back to Cellery for inline display

See the parent Cellery project for the complete platform documentation.

## Troubleshooting

### Common Issues

1. **Container Build Failures**: Check Docker daemon and build context
2. **Service Startup Issues**: Verify config.yaml and environment variables
3. **MCP Server Failures**: Ensure Node.js and npm packages are available
4. **API Connection Issues**: Check network policies and firewall rules

### Debug Mode

```bash
# Run with debug logging
docker run -e LOG_LEVEL=DEBUG agent-runtime-service:dev

# Access container shell
docker exec -it container_name /bin/bash

# Check logs
docker logs container_name
```

### Health Check Endpoints

- `GET /docs` - API documentation (also health check)
- `GET /openapi.json` - OpenAPI specification
- Container healthcheck automatically monitors service availability

## License

Part of the Cellery platform. See main project for license details.

---

**Agent Runtime Service is production-ready and container-optimized for cloud deployment.**
