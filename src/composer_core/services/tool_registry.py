import asyncio
from pathlib import Path
import yaml
from contextlib import asynccontextmanager

from agents.mcp import MCPServer, MCPServerStdio, MCPServerStreamableHttp
from composer_core.constants import PROJECT_ROOT
# In the future, we would add MCPServerSse and MCPServerStreamableHttp here

class ToolRegistry:
    """
    Manages the lifecycle of all MCP servers based on the application configuration.
    """

    def __init__(self):
        self._config_path = PROJECT_ROOT / "tool_registry.yaml"
        self._config = self._load_config()
        self._server_contexts: list[MCPServer] = []

    def _load_config(self) -> dict:
        """Loads and validates the tool registry configuration."""
        print(f"ToolRegistry: Loading configuration from: {self._config_path}")
        with open(self._config_path, "r") as f:
            full_config = yaml.safe_load(f)
        
        # We could add validation logic here (e.g., using Pydantic)
        return full_config.get("tool_registry", [])

    async def start_servers(self) -> list[MCPServer]:
        """
        Starts all enabled MCP servers based on the configuration.
        Returns a list of active server instances.
        """
        print("\\n--- Starting MCP Servers ---")
        active_servers = []
        for server_config in self._config:
            if not server_config.get("enabled", False):
                continue

            server_type = server_config.get("type")
            server_id = server_config.get("id", "N/A")
            print(f"Initializing '{server_id}' server of type '{server_type}'...")

            server = None
            if server_type == "local_stdio":
                command_params = server_config.get("config", {}).copy()
                kwargs = {}
                if "client_session_timeout_seconds" in server_config:
                    kwargs["client_session_timeout_seconds"] = server_config["client_session_timeout_seconds"]
                
                server = MCPServerStdio(command_params, cache_tools_list=True, **kwargs)
            
            # Future server types would be handled here
            elif server_type == "remote_http":
                config = server_config.get("config", {})
                base_url = config.get("base_url")
                if not base_url:
                    print(f"Warning: 'base_url' not configured for remote_http server '{server_id}'. Skipping.")
                    continue
                server = MCPServerStreamableHttp(params={"url": base_url}, cache_tools_list=True)
            # elif server_type == "remote_sse":
            #     ...

            else:
                print(f"Warning: Server type '{server_type}' is not currently supported.")
                continue

            if server:
                server.server_id = server_id  # For better logging
                await server.__aenter__()
                self._server_contexts.append(server)
                active_servers.append(server)
                print(f"-> '{server_id}' server started successfully.")
        
        print("----------------------------\\n")
        return active_servers

    async def shutdown_servers(self):
        """Shuts down all managed MCP servers."""
        print("\\n--- Shutting Down MCP Servers ---")
        for server in reversed(self._server_contexts):
            server_id = getattr(server, 'server_id', 'N/A')
            print(f"Shutting down '{server_id}' server...")
            await server.__aexit__(None, None, None)
            print(f"-> '{server_id}' server shut down.")
        print("-------------------------------\\n")
