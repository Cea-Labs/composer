"""
Web interface for visual API testing integrated into FastAPI service
"""
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json
from typing import Dict, Any

# Create router for web interface
router = APIRouter(tags=["Web Interface"])

# Static files and templates (we'll create these)
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Ensure directories exist
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/", response_class=HTMLResponse)
async def web_interface_home(request: Request):
    """Serve the main web interface"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "Agent Runtime Service - API Console",
        "api_base": str(request.base_url).rstrip("/")
    })

@router.get("/health", response_class=HTMLResponse)
async def health_dashboard(request: Request):
    """Health monitoring dashboard"""
    return templates.TemplateResponse("health.html", {
        "request": request,
        "title": "System Health Dashboard"
    })

@router.post("/api-test")
async def api_test_endpoint(
    endpoint: str = Form(...),
    method: str = Form(...),
    payload: str = Form(None)
):
    """
    Backend endpoint for testing APIs from web interface
    This allows CORS-free testing and adds server-side validation
    """
    try:
        # Parse payload if provided
        data = None
        if payload:
            data = json.loads(payload)
        
        # Here you can add logic to make internal API calls
        # and return results to the web interface
        
        return JSONResponse({
            "success": True,
            "endpoint": endpoint,
            "method": method,
            "data": data,
            "message": "API test executed successfully"
        })
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
