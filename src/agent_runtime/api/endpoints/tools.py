from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel
import yaml
from pathlib import Path

from agent_runtime.constants import PROJECT_ROOT
from agent_runtime.services.orchestrator import OrchestratorManager


router = APIRouter()


class ToolStatus(BaseModel):
    id: str
    type: str
    enabled: bool
    connected: bool
    name: Optional[str] = None


def _load_tool_registry() -> list[dict]:
    path = PROJECT_ROOT / "tool_registry.yaml"
    if not path.exists():
        return []
    with open(path, "r") as f:
        data = yaml.safe_load(f) or {}
    return data.get("tool_registry", [])


def _collect_connected_ids() -> set[str]:
    connected: set[str] = set()
    # Inspect active orchestrators for currently running servers
    try:
        for orch in OrchestratorManager._instances.values():  # type: ignore[attr-defined]
            if getattr(orch, "active_servers", None):
                for srv in orch.active_servers:  # type: ignore[attr-defined]
                    sid = getattr(srv, "server_id", None)
                    if sid:
                        connected.add(sid)
    except Exception:
        # If inspection fails for any reason, fall back to empty set
        pass
    return connected


@router.get("/tools/status", response_model=List[ToolStatus])
async def get_tools_status() -> List[ToolStatus]:
    registry = _load_tool_registry()
    connected_ids = _collect_connected_ids()

    statuses: List[ToolStatus] = []
    for entry in registry:
        tool_id = entry.get("id")
        if not tool_id:
            continue
        enabled = bool(entry.get("enabled", False))
        tool_type = entry.get("type", "unknown")
        name = entry.get("name")

        statuses.append(
            ToolStatus(
                id=tool_id,
                type=tool_type,
                enabled=enabled,
                connected=(tool_id in connected_ids),
                name=name,
            )
        )

    return statuses

