# MCP Agent Service

This project provides a modular, asynchronous, task-based service for orchestrating `openai-agents` with various MCP (Model Context Protocol) servers. It is designed with a clear separation of concerns to be extensible, robust, and ready for long-running agent tasks.

## Architecture

The application is composed of clearly defined services:

1.  **Input Service (`api/`)**: A FastAPI server that exposes a `/v1/tasks` endpoint. It accepts tasks, starts them in the background, and provides an endpoint to check their status.

2.  **Core Services (`services/`)**:
    *   **Orchestrator (`orchestrator.py`)**: The central coordinator that ties all other services together to execute a task from start to finish.
    *   **Agent Service (`agent_service.py`)**: The "brain" of the operation. It defines the agent's instructions and manages the core execution loop.
    *   **Tool Registry (`tool_registry.py`)**: Manages the lifecycle of all MCP servers (local or remote) defined in the configuration.
    *   **Task Manager (`task_manager.py`)**: A simple in-memory store for tracking the status and results of submitted tasks.

3.  **Configuration (`config.yaml`)**: A single YAML file to define the OpenAI API key and the entire tool registry.

## Asynchronous Task-Based API

This service operates asynchronously, which is ideal for potentially long-running agent tasks.

1.  **POST `/v1/tasks`**: You submit a task with a prompt. The server immediately responds with a `task_id`.
2.  **GET `/v1/tasks/{task_id}`**: You use the `task_id` to poll this endpoint for the status of the task. The status will be `pending`, `completed`, or `failed`. Once completed, the response will contain the final result.

## Setup & Usage

1.  **Configure `config.yaml`**: Set your `openai.api_key`.
2.  **Install Dependencies**: `poetry install`
3.  **Run the Server**: `poetry run start`

### Interacting with the API

Here is an example workflow using `curl`:

**1. Submit a task:**
```bash
TASK_ID=$(curl -s -X POST "http://127.0.0.1:8000/v1/tasks" \\
-H "Content-Type: application/json" \\
-d '{
  "prompt": "Use the filesystem tool to read 'url_to_fetch.txt' and fetch the webpage."
}' | python -c "import sys, json; print(json.load(sys.stdin)['task_id'])")

echo "Task submitted with ID: $TASK_ID"
```

**2. Check the task status:**
```bash
# Wait a few seconds for the agent to work...
sleep 15

curl -s "http://127.0.0.1:8000/v1/tasks/$TASK_ID" | python -m json.tool
```

## Testing

Run the unit and integration tests with: `poetry run pytest`

### End-to-End Test

To run a full, end-to-end test that starts the server and makes a real request, run the following script from the `mcp-agent-orchestrator` directory:

```bash
poetry run python scripts/run_e2e_test.py
```

**Note:** If you get an "address already in use" error, it means a server process from a previous run was not shut down correctly. You can find and stop the process using the following commands:

1.  **Find the process ID (PID)**:
    ```bash
    lsof -i :8000
    ```
2.  **Stop the process**:
    ```bash
    kill -9 <PID>
    ``` 