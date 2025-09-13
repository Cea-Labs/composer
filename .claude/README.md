# Agent Runtime Service - Development Context

This is the **Agent Runtime Service**, part of the larger **Cellery** platform ecosystem.

## Service Purpose

This service provides LLM-powered orchestration for converting natural language prompts into executable workflows through MCP (Model Context Protocol) servers.

## Current Focus

- **Runtime Orchestration**: Plan & Execute model with PlannerAgent + ExecutorAgent
- **MCP Integration**: Universal tool access through standardized protocol  
- **Task Management**: Background processing with streaming status updates
- **Tool Registry**: Dynamic discovery and lifecycle management of MCP servers

## Key Architecture

```
FastAPI Server → Orchestrator → Agent Service → Tool Registry → MCP Servers
                     ↓
               Task Manager (in-memory storage)
```

## Recent Changes

- ✅ Renamed from `composer_core` to `agent_runtime` 
- ✅ Updated all import paths and environment variables
- ✅ Focused README on runtime-specific functionality
- ✅ Removed high-level product docs (moved to Cellery root)
- ✅ Fixed test files and configuration references

## Environment

- **Config**: `AGENT_RUNTIME_CONFIG` (default: `config.yaml`)
- **Start Command**: `poetry run start`
- **API**: `http://127.0.0.1:8000` (FastAPI with OpenAPI docs)

## Integration with Cellery

This service will serve as the execution backend when the Cellery frontend is complete:
1. Cellery sends natural language blocks via API
2. Agent Runtime converts to executable plans  
3. MCP Tools execute the operations
4. Results stream back for inline display

## Next Steps

1. **Service Stability**: Ensure robust error handling and recovery
2. **Tool Expansion**: Add more MCP server integrations
3. **Performance**: Optimize for concurrent task execution
4. **API Evolution**: Prepare for Cellery frontend integration