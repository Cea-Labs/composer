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
        self._agent = self._define_agent()
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
            url_file.write_text("https://example.com")
            print(f"-> File '{url_file}' created with default URL.")
        else:
            print(f"-> File '{url_file}' already exists.")

        mcp_fetch_downloads_dir = Path.home() / "Downloads" / "mcp-fetch"
        mcp_fetch_downloads_dir.mkdir(parents=True, exist_ok=True)
        print(f"-> Ensured MCP fetch download directory exists.")
        print("--------------------------------------\\n")

    def _define_agent(self) -> Agent:
        """Defines the orchestrator agent's properties and tools."""
        return Agent(
            name="OrchestratorAgent",
            instructions=(
                "You have access to a sandboxed filesystem tool. "
                "To read the file you need, you MUST ask the tool to read the file at the exact path 'url_to_fetch.txt'. "
                "Do NOT add './' or any other directory path to the filename. Request the filename directly. "
                "After reading the file and getting the URL, use the 'imageFetch' tool to fetch the webpage content."
            ),
            mcp_servers=self._mcp_servers,
        )

    async def run_task(self, task_prompt: str) -> str:
        """
        Runs the agent with a specific task prompt and returns the final output.
        """
        print(f"--- Agent Service: Running Task ---")
        print(f"Prompt: '{task_prompt}'")
        print("-----------------------------------\\n")

        result = await Runner.run(self._agent, task_prompt)

        final_output = str(result.final_output)
        print("\\n--- Agent Service: Final Output ---")
        print(final_output)
        print("-----------------------------------")

        return final_output 