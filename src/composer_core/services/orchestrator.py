import asyncio
from datetime import datetime

from composer_core.services.agent_service import AgentService
from composer_core.services.tool_registry import ToolRegistry
from composer_core.services import task_manager
from composer_core.constants import PROJECT_ROOT

CONFIG_PATH = PROJECT_ROOT / "config.yaml"

class OrchestratorManager:
    """A singleton-like manager to hold active TaskOrchestrator instances."""
    _instances: dict[str, "TaskOrchestrator"] = {}

    @classmethod
    def get_orchestrator(cls, task_id: str, prompt: str | None = None) -> "TaskOrchestrator":
        if task_id not in cls._instances:
            if prompt is None:
                raise ValueError("Prompt must be provided to create a new orchestrator.")
            cls._instances[task_id] = TaskOrchestrator(task_id, prompt)
        return cls._instances[task_id]

    @classmethod
    def cleanup_orchestrator(cls, task_id: str):
        if task_id in cls._instances:
            del cls._instances[task_id]

class TaskOrchestrator:
    """
    Manages the entire lifecycle of a single task, from planning to execution.
    This ensures that the AgentService and its tools persist for the task's duration.
    """
    def __init__(self, task_id: str, prompt: str):
        self.task_id = task_id
        self.prompt = prompt
        self.agent_service: AgentService | None = None
        self.tool_registry = ToolRegistry()
        self.active_servers: list | None = None
        self.log_file = PROJECT_ROOT / f"task_{task_id}.log"
        self._log(f"Orchestrator initialized for task {task_id}.")

    def _log(self, message: str):
        """Logs a message to the task-specific log file."""
        with open(self.log_file, "a") as f:
            f.write(f"[{datetime.now()}] {message}\\n")

    async def initialize(self):
        """Starts the tool servers for the duration of the task."""
        if self.active_servers is None:
            self._log("Initializing tool servers...")
            self.active_servers = await self.tool_registry.start_servers()
            self.agent_service = AgentService(mcp_servers=self.active_servers)
            self._log("Tool servers initialized.")

    async def shutdown(self):
        """Shuts down the tool servers."""
        if self.active_servers is not None:
            self._log("Shutting down tool servers...")
            await self.tool_registry.shutdown_servers()
            self.active_servers = None
            self._log("Tool servers shut down.")

    async def create_plan(self):
        """Creates a plan for the task."""
        self._log(f"Beginning Plan Creation for prompt: '{self.prompt[:50]}...'")
        await self.initialize()
        plan = await self.agent_service.create_plan(task_prompt=self.prompt)
        task_manager.update_task_plan(self.task_id, plan)
        self._log("Plan Generation Finished.")
        self._log(f"Generated Plan:\\n{plan}")

    async def execute_plan(self):
        """Executes the approved plan for the task."""
        self._log("Beginning Plan Execution.")
        task = task_manager.get_task_status(self.task_id)
        if not task or not task.get("plan"):
            self._log("No plan found. Aborting execution.")
            await self.shutdown()
            OrchestratorManager.cleanup_orchestrator(self.task_id)
            return

        await self.initialize()

        plan = task["plan"]
        plan_steps = [
            line.strip()
            for line in plan.strip().split("\n")
            if line.strip() and line.strip()[0].isdigit()
        ]

        last_result = None
        for i, step in enumerate(plan_steps):
            self._log(f"Executing step {i+1}/{len(plan_steps)}: {step}")
            last_result = await self.agent_service.execute_step(
                task_prompt=self.prompt,
                plan=plan,
                step_index=i,
                previous_step_result=last_result,
            )
            self._log(f"Result from step {i+1}: {last_result}")

        task_manager.update_task_result(self.task_id, "completed", last_result)
        self._log("Plan Execution Finished.")
        await self.shutdown()
        OrchestratorManager.cleanup_orchestrator(self.task_id)

async def run_task_and_update_status(task_id: str, prompt: str):
    """
    A wrapper function for background execution. Creates a plan and waits for approval.
    """
    try:
        orchestrator = OrchestratorManager.get_orchestrator(task_id, prompt)
        await orchestrator.create_plan()
    except Exception as e:
        print(f"--- Orchestrator: Task failed for task_id {task_id} ---")
        print(f"Error: {e}")
        task_manager.update_task_result(task_id, "failed", str(e))

async def trigger_plan_execution(task_id: str):
    """
    A wrapper function to be called on approval to execute the plan.
    """
    task = task_manager.get_task_status(task_id)
    if task:
        orchestrator = OrchestratorManager.get_orchestrator(task_id, task["prompt"])
        await orchestrator.execute_plan() 