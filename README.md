# MCP Agent Service - Plan and Execute

This project provides a modular, asynchronous, task-based service for orchestrating sophisticated AI agents. It uses a **Plan and Execute** model with human-in-the-loop approval, allowing agents to tackle complex, multi-step tasks by first creating a plan, awaiting human consent, and then executing that plan step-by-step.

## Architecture

The application is built on a clear separation of concerns, featuring two distinct types of agents, a robust orchestration layer, and a dynamic tool management system.

```mermaid
graph TD
    subgraph User Interaction
        User -- "1. Submits Prompt via API" --> APIService["FastAPI Service (/v1/tasks)"];
    end

    subgraph Core Orchestration
        APIService -- "2. Creates Task" --> OrchestratorManager["Orchestrator Manager"];
        OrchestratorManager -- "3. Manages" --> TaskOrchestrator["Task Orchestrator"];
        TaskOrchestrator -- "4. Uses" --> AgentService["Agent Service (Planner & Executor)"];
        AgentService -- "5. Gets Tools From" --> ToolRegistry["Tool Registry"];
    end

    subgraph Tool Ecosystem
        ToolRegistry -- "6. Manages Lifecycle of" --> LocalTools["Local Tools (Stdio)<br/>e.g., Filesystem, Fetch"];
        ToolRegistry -- "7. Manages Lifecycle of" --> RemoteTools["Remote Tools (HTTP)<br/>e.g., Notion, Gmail"];
    end

    subgraph AI Core
        AgentService -- "8. Sends Prompt + Tool Schemas to" --> LLM["LLM (e.g., OpenAI)"];
        LLM -- "9. Returns Plan / Action" --> AgentService;
    end

    style User fill:#c9d,stroke:#333,stroke-width:2px
    style APIService fill:#bdf,stroke:#333,stroke-width:2px
    style LLM fill:#f96,stroke:#333,stroke-width:2px
```

## Core Components

1.  **API Service (`api/`)**: A FastAPI server that exposes a versioned API for task management.
2.  **Orchestration (`services/orchestrator.py`)**: Manages the entire lifecycle of a single task, from planning to execution.
3.  **Agent Service (`services/agent_service.py`)**: Defines the `PlannerAgent` (creates the plan) and the `ExecutorAgent` (executes the plan).
4.  **Tool Registry (`services/tool_registry.py`)**: Manages the lifecycle of all MCP servers (local or remote) that provide tools to the agents.
5.  **Tool Manager (`services/tool_manager.py`)**: Automatically discovers and installs dependencies for local tools defined in the tool registry.

## Setup & Usage

This project uses Poetry for dependency management.

**1. Create Your Local Configurations:**

You need to create two local configuration files from the provided templates. These files are gitignored, so your private keys and tool configurations will not be committed.

-   **Copy `config.template.yaml` to `config.yaml`:**
    ```bash
    cp config.template.yaml config.yaml
    ```
    -   Edit `config.yaml` and add your OpenAI API key.

-   **Copy `tool_registry.template.yaml` to `tool_registry.yaml`:**
    ```bash
    cp tool_registry.template.yaml tool_registry.yaml
    ```
    -   Edit `tool_registry.yaml` to add your private remote tools (e.g., Notion, Gmail). The public `filesystem` and `fetch` tools are already included.

**2. Install Python Dependencies:**
```bash
poetry install
```

**3. Run the Server:**
```bash
poetry run start
```
When you run the server, the `ToolManager` will automatically inspect your `tool_registry.yaml` and install any required `npm` packages for the local tools.

## Interacting with the API

The API workflow remains the same. You can use `curl` or any other HTTP client to interact with the service.

**1. Submit a task:**
```bash
# ... (curl command to submit task)
```

**2. Check status until awaiting approval:**
```bash
# ... (curl command to check status)
```

**3. Approve the plan:**
```bash
# ... (curl command to approve plan)
```

**4. Check the final result:**
```bash
# ... (curl command to get final result)
```

## Testing

To run a full, end-to-end test that starts the server and makes a real request, use the test script in the `MCPschema_check` directory.

```bash
poetry run python MCPschema_check/comprehensive_e2e_test.py
```
This script now serves as the primary end-to-end test. 