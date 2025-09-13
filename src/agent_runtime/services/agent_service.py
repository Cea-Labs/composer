import shutil
from pathlib import Path

from agents import Agent, Runner
from agents.mcp import MCPServer


class AgentService:
    """
    This service is the brain of the operation. It defines the agent's
    logic, instruction, and handles the core execution loop.
    """

    def __init__(self, mcp_servers: list[MCPServer]):
        self._mcp_servers = mcp_servers
        self._planner_agent = self._define_planner_agent()
        self._executor_agent = self._define_executor_agent()
        self._setup_environment()

    def _setup_environment(self):
        """Ensures necessary files and directories exist for the agent's tools."""
        print("\\n--- Setting up Execution Environment ---")
        if not shutil.which("npx"):
            raise RuntimeError("'npx' command not found. Please ensure Node.js and npm are installed.")
        print("-> 'npx' is available.")

        project_root = Path(__file__).parent.parent.parent
        sample_data_dir = project_root / "sample_data"
        sample_data_dir.mkdir(exist_ok=True)
        url_file = sample_data_dir / "url_to_fetch.txt"
        if not url_file.exists():
            url_file.write_text("https://v7t.space")
            print(f"-> File '{url_file}' created with default URL.")
        else:
            print(f"-> File '{url_file}' already exists.")

        mcp_fetch_downloads_dir = Path.home() / "Downloads" / "mcp-fetch"
        mcp_fetch_downloads_dir.mkdir(parents=True, exist_ok=True)
        print(f"-> Ensured MCP fetch download directory exists.")
        print("--------------------------------------\\n")

    def _define_planner_agent(self) -> Agent:
        """Defines the planning agent's properties."""
        return Agent(
            name="PlannerAgent",
            instructions=(
                "You are a master planner. Your job is to take a high-level user request "
                "and create a step-by-step plan to accomplish it using the tools available to you. "
                "Carefully inspect the tools you have been given and create a numbered plan that uses THEIR EXACT names. "
                "Do not make up tools. Do not execute the plan, only create it."
            ),
            mcp_servers=self._mcp_servers,
        )

    def _define_executor_agent(self) -> Agent:
        """Defines the executor agent's properties."""
        return Agent(
            name="ExecutorAgent",
            instructions=(
                "You are an executor. Your job is to receive a single step of a plan and execute it precisely. "
                "You will be given the original user request, the full plan, the result of the previous step, and the current step to execute. "
                "Use the available tools to perform the action described in the current step. "
                "If you are using the filesystem and get a path error, try again with a full, absolute path to the resource."
            ),
            mcp_servers=self._mcp_servers,
        )

    async def create_plan(self, task_prompt: str) -> str:
        """
        Runs the planner agent to generate a plan.
        """
        print(f"--- Agent Service: Creating Plan ---")
        print(f"Prompt: '{task_prompt}'")
        print("----------------------------------\\n")

        result = await Runner.run(self._planner_agent, task_prompt)

        plan = str(result.final_output)
        print("\\n--- Agent Service: Generated Plan ---")
        print(plan)
        print("-----------------------------------")

        return plan

    async def execute_step(
        self,
        task_prompt: str,
        plan: str,
        step_index: int,
        previous_step_result: str | None,
    ) -> str:
        """
        Runs the executor agent to perform a single step of the plan.
        """
        # More robustly parse the plan to extract only numbered steps.
        plan_steps = [
            line.strip()
            for line in plan.strip().split("\n")
            if line.strip() and line.strip()[0].isdigit()
        ]
        current_step = plan_steps[step_index]

        print(f"--- Agent Service: Executing Step {step_index + 1}/{len(plan_steps)} ---")
        print(f"Step Details: {current_step}")
        
        prompt_for_executor = (
            f"You are executing one step of a larger plan.\\n"
            f"The original user request was: '{task_prompt}'\\n"
            f"The full plan is:\\n{plan}\\n"
            f"The result of the previous step was: '{previous_step_result or 'None'}'\\n\\n"
            f"Your current task is to execute ONLY this step: '{current_step}'\\n"
            f"Focus only on this step. Do not repeat previous steps. Return only the direct output of this step."
        )

        print("\\n--- Executor Agent Prompt ---")
        print(prompt_for_executor)
        print("-----------------------------")

        result = await Runner.run(self._executor_agent, prompt_for_executor)
        step_output = str(result.final_output)

        print(f"\\n--- Raw Output from Step {step_index + 1} ---")
        print(step_output)
        print("------------------------------------")

        return step_output 