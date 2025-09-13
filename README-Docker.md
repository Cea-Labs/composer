# Agent Runtime Service Docker Deployment

Agent Runtime Service is an independent Python FastAPI backend that provides tool orchestration and MCP server management.

## Quick Start

### Development Mode
```bash
# Build and run development container
docker-compose up --build

# Access API docs at: http://localhost:8000/docs
# Access API at: http://localhost:8000
```

### Production Mode
```bash
# Run production container (on port 8001 to avoid conflicts)
docker-compose --profile production up --build agent-runtime-prod

# Access API docs at: http://localhost:8001/docs
# Access API at: http://localhost:8001
```

## Configuration

### Environment Variables
- `AGENT_RUNTIME_CONFIG`: Path to config.yaml file
- `CORS_ORIGINS`: Comma-separated list of allowed origins for CORS
- `PYTHONPATH`: Python path for module imports

### Required Files
- `config.yaml`: Service configuration
- `tool_registry.yaml`: Tool definitions and MCP server mappings

## API Endpoints
The service exposes a clean REST API for TypeCell integration:

### Core Endpoints
- `GET /docs` - API documentation (Swagger UI)
- `GET /v1/tools` - List available tools
- `POST /v1/tasks` - Execute workflow tasks
- `GET /v1/tasks/{task_id}` - Get task status
- `GET /v1/status` - Service health check

### Integration with TypeCell
- TypeCell connects via HTTP REST API
- CORS configured for local development
- Production deployment supports custom domains

## Standalone Operation
Agent Runtime Service runs completely independently:
- Self-contained Python service with FastAPI
- Manages its own MCP server processes
- Provides REST API for external integration
- No dependencies on TypeCell or other services

## Docker Commands

### Development
```bash
docker-compose up -d                    # Run in background
docker-compose logs -f                  # View logs
docker-compose down                     # Stop service
docker-compose exec agent-runtime bash # Shell access
```

### Production
```bash
docker-compose --profile production up -d agent-runtime-prod
docker-compose --profile production logs -f agent-runtime-prod
docker-compose --profile production down
```

## Health Checks
- Development: `curl http://localhost:8000/docs`
- Production: `curl http://localhost:8001/docs`

## Volumes
- `logs/`: Service logs (persistent)
- `config.yaml`: Service configuration (read-only)
- `tool_registry.yaml`: Tool definitions (read-only)
- `sample_data/`: MCP server data (persistent)