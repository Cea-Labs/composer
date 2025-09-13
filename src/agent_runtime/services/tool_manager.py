import yaml
import subprocess
import sys
import json
from pathlib import Path

# Navigate up to the project root from the current file's location (src/agent_runtime/services)
PROJECT_ROOT = Path(__file__).parent.parent.parent
TOOL_REGISTRY_PATH = PROJECT_ROOT / "tool_registry.yaml"

def get_required_npm_packages():
    """
    Parses the tool_registry.yaml to find all required npm packages
    for local_stdio tools.
    """
    print(f"ToolManager: Reading tool registry from: {TOOL_REGISTRY_PATH}")
    if not TOOL_REGISTRY_PATH.exists():
        print(f"Warning: Tool registry not found at {TOOL_REGISTRY_PATH}. Skipping tool setup.")
        return []

    with open(TOOL_REGISTRY_PATH, "r") as f:
        config = yaml.safe_load(f)

    packages = []
    tool_registry = config.get("tool_registry", [])
    for tool in tool_registry:
        if tool.get("type") == "local_stdio":
            # The package name is expected to be the first argument after the command.
            # e.g., args: ["@kazuph/mcp-fetch"]
            # e.g., args: ["@modelcontextprotocol/server-filesystem", "path/to/data"]
            args = tool.get("config", {}).get("args", [])
            if args:
                package_name = args[0]
                # Simple check to see if it looks like an npm package.
                if "@" in package_name or "/" in package_name:
                    packages.append(package_name)

    print(f"ToolManager: Found required npm packages: {packages}")
    return list(set(packages)) # Return unique packages

def get_installed_npm_packages():
    """Returns a set of globally installed npm packages."""
    try:
        # npm ls -g --depth=0 gets the top-level global packages
        # The --json flag provides easy-to-parse output
        result = subprocess.run(
            ["npm", "ls", "-g", "--depth=0", "--json"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(result.stdout)
        return set(data.get("dependencies", {}).keys())
    except (FileNotFoundError, subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"Warning: Could not list installed npm packages: {e}. Assuming none are installed.")
        return set()

def setup_tools():
    """
    Checks for and installs required npm packages for local tools if they
    are not already installed.
    """
    print("\\n--- ToolManager: Setting up local tools ---")
    required_packages = get_required_npm_packages()
    
    if not required_packages:
        print("ToolManager: No local stdio tools with npm packages found to install.")
        print("------------------------------------------\\n")
        return

    installed_packages = get_installed_npm_packages()
    
    packages_to_install = [p for p in required_packages if p not in installed_packages]

    if not packages_to_install:
        print("ToolManager: All required npm packages are already installed.")
        print("------------------------------------------\\n")
        return

    print(f"ToolManager: Found {len(packages_to_install)} new package(s) to install: {', '.join(packages_to_install)}")

    # The -g flag installs the packages globally.
    command = ["npm", "install", "-g"] + packages_to_install
    
    try:
        # We use sys.executable to run npm via a python subprocess
        # This can be more reliable in some environments.
        # However, a direct call to npm is often simpler. Let's do that.
        print(f"Executing command: {' '.join(command)}")
        # Using capture_output=True to hide the npm output unless there's an error.
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        print("ToolManager: All required npm packages are installed successfully.")
        if result.stdout:
            print("NPM Output:\\n", result.stdout)

    except FileNotFoundError:
        print("Error: 'npm' command not found. Please ensure Node.js and npm are installed and in your PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error installing npm packages: {e}")
        print("NPM Stderr:\\n", e.stderr)
        print("NPM Stdout:\\n", e.stdout)
        sys.exit(1)
    
    print("------------------------------------------\\n")

if __name__ == '__main__':
    # Allow running this script directly for manual setup if needed.
    setup_tools() 