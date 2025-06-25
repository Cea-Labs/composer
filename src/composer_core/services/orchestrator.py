from pathlib import Path
from composer_core.services.tool_registry import managed_tool_registry
from composer_core.services.agent_service import AgentService
from composer_core.services import task_manager
from composer_core.constants import PROJECT_ROOT

CONFIG_PATH = PROJECT_ROOT / "config.yaml"

async def _run_task_internal(prompt: str) -> str:
    """The core orchestration logic."""
    print(f"--- Orchestrator: Beginning Task Execution for prompt: '{prompt[:50]}...' ---")
    async with managed_tool_registry() as active_servers:
        agent_service = AgentService(mcp_servers=active_servers)
        final_output = await agent_service.run_task(task_prompt=prompt)
    print("--- Orchestrator: Task Execution Finished ---")
    return final_output

async def run_task_and_update_status(task_id: str, prompt: str):
    """
    A wrapper function for background execution. Runs the task and updates
    the task manager with the final status and result.
    """
    try:
        result = await _run_task_internal(prompt)
        task_manager.update_task_result(task_id, "completed", result)
    except Exception as e:
        print(f"--- Orchestrator: Task failed for task_id {task_id} ---")
        print(f"Error: {e}")
        task_manager.update_task_result(task_id, "failed", str(e)) 