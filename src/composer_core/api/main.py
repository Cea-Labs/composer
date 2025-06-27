from fastapi import FastAPI
from pathlib import Path
import yaml
import uvicorn
import os

from agents import set_default_openai_key
from composer_core.api.endpoints import tasks
from composer_core.constants import PROJECT_ROOT
from composer_core.services.tool_manager import setup_tools

def create_app(config_path: Path | None = None) -> FastAPI:
    """Creates and configures the main FastAPI application."""
    
    # --- App and Config Setup ---
    app = FastAPI(
        title="MCP Agent Service",
        description="An asynchronous, task-based service for orchestrating AI agents.",
        version="3.0.0",
    )

    if config_path is None:
        config_env = os.environ.get("COMPOSER_CONFIG")
        if config_env:
            config_path = Path(config_env)
        else:
            config_path = PROJECT_ROOT / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found at '{config_path}'. "
            f"Please create it by copying 'config.template.yaml' to 'config.yaml' "
            f"and filling in your details."
        )

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    if not config:
        raise ValueError(f"Configuration file at '{config_path}' is empty or invalid.")

    api_key = config.get("openai", {}).get("api_key")
    if not api_key or api_key == "YOUR_OPENAI_API_KEY_HERE":
        raise ValueError("OpenAI API key is not configured in config.yaml")
    set_default_openai_key(api_key)

    # --- Include Routers ---
    app.include_router(tasks.router, prefix="/v1", tags=["Tasks"])

    return app

# --- Server Runner ---
def run_server():
    """A convenience function to run the Uvicorn server."""
    # First, ensure all necessary tools are set up.
    setup_tools()

    config_env = os.environ.get("COMPOSER_CONFIG")
    if config_env:
        config_path = Path(config_env)
    else:
        config_path = PROJECT_ROOT / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found at '{config_path}'. "
            f"Please create it by copying 'config.template.yaml' to 'config.yaml' "
            f"and filling in your details."
        )
        
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    if not config:
        raise ValueError(f"Configuration file at '{config_path}' is empty or invalid.")

    server_config = config.get("server", {})
    host = server_config.get("host", "0.0.0.0")
    port = server_config.get("port", 8000)
    
    app = create_app(config_path=config_path)
    uvicorn.run(app, host=host, port=port)

# This approach allows the app to be created with a specific config, making testing easier.
# We no longer define 'app' at the module level.

# To run this API server:
# uvicorn composer_core.api.main:run_server
