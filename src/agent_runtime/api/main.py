from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import yaml
import uvicorn
import os

from agents import set_default_openai_key
from agent_runtime.api.endpoints import tasks
from agent_runtime.api.endpoints import tools
from agent_runtime.api import web_interface
from agent_runtime.constants import PROJECT_ROOT
from agent_runtime.services.tool_manager import setup_tools

def create_app(config_path: Path | None = None) -> FastAPI:
    """Creates and configures the main FastAPI application."""
    
    # --- App and Config Setup ---
    app = FastAPI(
        title="Agent Runtime Service",
        description="An asynchronous, task-based service for orchestrating AI agents with integrated web console.",
        version="3.0.0",
    )

    # --- Add CORS middleware ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",   # React dev server default
            "http://localhost:5173",   # Vite dev server default  
            "http://localhost:5174",   # Alternative Vite port
            "http://localhost:8080",   # Vue dev server default
            "http://127.0.0.1:5173",   # Alternative localhost format
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if config_path is None:
        config_env = os.environ.get("AGENT_RUNTIME_CONFIG")
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

    # --- Mount Static Files ---
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # --- Include Routers ---
    app.include_router(tasks.router, prefix="/v1", tags=["Tasks"])
    app.include_router(tools.router, prefix="/v1", tags=["Tools"]) 
    app.include_router(web_interface.router, prefix="", tags=["Web Interface"])

    return app

# --- Server Runner ---
def run_server():
    """A convenience function to run the Uvicorn server."""
    # First, ensure all necessary tools are set up.
    setup_tools()

    config_env = os.environ.get("AGENT_RUNTIME_CONFIG")
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
# uvicorn agent_runtime.api.main:run_server
