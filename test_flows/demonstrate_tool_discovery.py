import asyncio
import yaml
from pathlib import Path
import sys

# --- Setup Project Root ---
# This ensures the script can find the project's root directory to locate
# the tool_registry.yaml and the agents library correctly.
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Now we can import from the agents library and our local modules
from agents.mcp import MCPServerStdio, MCPServerStreamableHttp
from agent_runtime.services.tool_manager import setup_tools

# --- Main Demonstration Logic ---

async def demonstrate_tool_discovery():
    """
    Connects to all servers defined in tool_registry.yaml and prints the
    tools they expose via the list_tools() method.
    """
    print("--- Starting Tool Discovery Demonstration ---")
    
    config_path = PROJECT_ROOT / "tool_registry.yaml"
    if not config_path.exists():
        print(f"Error: Could not find '{config_path}'")
        return

    print(f"Loading tool registry from: {config_path}\\n")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f).get("tool_registry", [])

    servers = []
    for server_config in config:
        if not server_config.get("enabled", False):
            continue

        server_type = server_config.get("type")
        server_id = server_config.get("id", "N/A")
        server = None

        if server_type == "local_stdio":
            current_config = server_config.get("config", {}).copy()
            if server_id == "filesystem" and current_config.get("args"):
                relative_path = Path(current_config["args"][1])
                current_config["args"][1] = str(PROJECT_ROOT / "src" / relative_path)
            server = MCPServerStdio(current_config, cache_tools_list=False)
            print(f"-> Initialized LOCAL server: '{server_id}'")

        elif server_type == "remote_http":
            base_url = server_config.get("config", {}).get("base_url")
            if base_url:
                server = MCPServerStreamableHttp(params={"url": base_url}, cache_tools_list=False)
                print(f"-> Initialized REMOTE server: '{server_id}'")

        if server:
            servers.append((server_id, server))
    
    print("\\n--- Querying Servers for Available Tools ---")
    for server_id, server in servers:
        print(f"\\n=========================================")
        print(f"Server: {server_id}")
        print(f"=========================================")
        try:
            async with server:
                tools = await server.list_tools()
                
                if not tools:
                    print("No tools found on this server.")
                    continue

                for tool in tools:
                    print(f"\\n  - Tool: {tool.name}")
                    print(f"    Description: {tool.description}")
                    
                    # CORRECTED: Defensively check for the spec and parameters
                    if hasattr(tool, 'spec') and hasattr(tool.spec, 'parameters'):
                        print(f"    Arguments Schema:")
                        import json
                        print(f"      {json.dumps(tool.spec.parameters, indent=8)}")
                    else:
                        print(f"    Arguments Schema: Not provided in a structured format.")

        except Exception as e:
            print(f"\\nError connecting to or querying server '{server_id}': {e}")
            print("This can happen if a server is misconfigured, or a local tool's dependencies are not installed.")

    print("\\n--- Demonstration Complete ---")


if __name__ == "__main__":
    # Point the tool_manager to the correct path for this script
    from agent_runtime.services import tool_manager
    tool_manager.TOOL_REGISTRY_PATH = PROJECT_ROOT / "tool_registry.yaml"

    try:
        setup_tools()
    except Exception as e:
        print(f"An error occurred during tool setup: {e}")
        sys.exit(1)

    asyncio.run(demonstrate_tool_discovery()) 