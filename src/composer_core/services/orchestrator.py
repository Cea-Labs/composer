from pathlib import Path
from composer_core.services.tool_registry import managed_tool_registry
from composer_core.services.agent_service import AgentService
from composer_core.services import task_manager
from composer_core.constants import PROJECT_ROOT

CONFIG_PATH = PROJECT_ROOT / "config.yaml"

async def _run_task_internal(prompt: str) -> str:
    """The core orchestration logic for creating a plan."""
    print(f"--- Orchestrator: Beginning Task Execution for prompt: '{prompt[:50]}...' ---")
    async with managed_tool_registry() as active_servers:
        agent_service = AgentService(mcp_servers=active_servers)
        plan = await agent_service.create_plan(task_prompt=prompt)
    print("--- Orchestrator: Plan Generation Finished ---")
    return plan

async def execute_plan(task_id: str):
    """
    The core orchestration logic for executing a plan.
    """
    print(f"--- Orchestrator: Beginning Plan Execution for task: {task_id} ---")
    task = task_manager.get_task_status(task_id)
    if not task or not task.get("plan"):
        print(f"Orchestrator: No plan found for task {task_id}. Aborting.")
        return

    prompt = task["prompt"]
    plan = task["plan"]
    plan_steps = [step for step in plan.strip().split("\\n") if step]

    async with managed_tool_registry() as active_servers:
        agent_service = AgentService(mcp_servers=active_servers)
        
        last_result = None
        for i, _ in enumerate(plan_steps):
            last_result = await agent_service.execute_step(
                task_prompt=prompt,
                plan=plan,
                step_index=i,
                previous_step_result=last_result,
            )

    task_manager.update_task_result(task_id, "completed", last_result)
    print(f"--- Orchestrator: Plan Execution Finished for task: {task_id} ---")

async def run_task_and_update_status(task_id: str, prompt: str):
    """
    A wrapper function for background execution. Creates a plan and waits for approval.
    """
    try:
        plan = await _run_task_internal(prompt)
        task_manager.update_task_plan(task_id, plan)
    except Exception as e:
        print(f"--- Orchestrator: Task failed for task_id {task_id} ---")
        print(f"Error: {e}") 