# MCP Agent Service - Plan and Execute

This project provides a modular, asynchronous, task-based service for orchestrating sophisticated AI agents. It uses a **Plan and Execute** model with human-in-the-loop approval, allowing agents to tackle complex, multi-step tasks by first creating a plan, awaiting human consent, and then executing that plan step-by-step.

## Architecture

The application is built on a clear separation of concerns, featuring two distinct types of agents and a robust orchestration layer.

1.  **Input Service (`api/`)**: A FastAPI server exposing a versioned API for task management. It allows for task creation, status checking, and plan approval.

2.  **Core Agents (`services/agent_service.py`)**:
    *   **PlannerAgent**: A high-level agent responsible for taking a user's request and, based on a set of available tools, creating a logical, step-by-step plan.
    *   **ExecutorAgent**: A focused agent that receives a single step from an approved plan and executes it using the available tools. It operates with the context of the original request and the results of previous steps.

3.  **Orchestration (`services/orchestrator.py`)**:
    *   **TaskOrchestrator**: Manages the entire lifecycle of a single task, from planning to execution. It ensures that the necessary tools and agent services persist for the task's duration.
    *   **OrchestratorManager**: A singleton-like manager that holds and provides access to active `TaskOrchestrator` instances, ensuring state is maintained across different API calls.

4.  **Tooling (`services/tool_registry.py` & `config.yaml`)**:
    *   **ToolRegistry**: Manages the lifecycle of all MCP servers (local or remote) that provide tools to the agents.
    *   **Configuration (`config.yaml`)**: A single YAML file to define the OpenAI API key and the entire tool registry.

## Asynchronous Plan-Approve-Execute Workflow

This service operates on a sophisticated asynchronous workflow ideal for long-running, interactive agent tasks.

1.  **`POST /v1/tasks`**: You submit a task with a high-level prompt (e.g., "Read a file and fetch a URL"). The server immediately responds with a `task_id`. The `PlannerAgent` begins generating a plan in the background.

2.  **`GET /v1/tasks/{task_id}`**: You use the `task_id` to poll this endpoint. The status will initially be `pending`. Once the plan is ready, the status will change to `awaiting_approval`, and the response will contain the generated `plan`.

3.  **`POST /v1/tasks/{task_id}/approve`**: After reviewing the plan, you call this endpoint to give your consent. This triggers the `ExecutorAgent` to begin executing the plan step-by-step in the background.

4.  **`GET /v1/tasks/{task_id}` (Polling for Result)**: You continue to poll the task status endpoint. Once all steps are complete, the status will change to `completed`, and the `result` field will contain the final output of the last step in the plan.

For a detailed visual of the execution flow, see the [Execution Flow Diagram](./diagrams/execution_flow.md).

## Setup & Usage

1.  **Configure `config.yaml`**: Set your `openai.api_key`.
2.  **Install Dependencies**: `poetry install`
3.  **Run the Server**: `poetry run start`

### Interacting with the API

Here is an example workflow using `curl` and `jq`:

**1. Submit a task to generate a plan:**
```bash
TASK_ID=$(curl -s -X POST "http://127.0.0.1:8000/v1/tasks" \\
-H "Content-Type: application/json" \\
-d '{
  "prompt": "Read the URL from ''url_to_fetch.txt'' and then fetch the content of that website."
}' | jq -r .task_id)

echo "Task submitted with ID: $TASK_ID"
```

**2. Check status until awaiting approval (this may take a few moments):**
```bash
# Poll until the status is 'awaiting_approval'
while true; do
  STATUS_INFO=$(curl -s "http://127.0.0.1:8000/v1/tasks/$TASK_ID")
  STATUS=$(echo "$STATUS_INFO" | jq -r .status)
  echo "Current status: $STATUS"
  if [ "$STATUS" == "awaiting_approval" ]; then
    echo "Plan is ready for approval:"
    echo "$STATUS_INFO" | jq .plan
    break
  fi
  sleep 2
done
```

**3. Approve the plan:**
```bash
curl -s -X POST "http://127.0.0.1:8000/v1/tasks/$TASK_ID/approve"
```

**4. Check the final result:**
```bash
# Wait for the agent to execute...
echo "Waiting for execution to complete..."
sleep 15

curl -s "http://127.0.0.1:8000/v1/tasks/$TASK_ID" | jq .
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