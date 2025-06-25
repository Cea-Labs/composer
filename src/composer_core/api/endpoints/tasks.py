from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from composer_core.services import task_manager
from composer_core.services import orchestrator

router = APIRouter()

# --- API Models ---
class TaskCreationRequest(BaseModel):
    prompt: str

class TaskCreationResponse(BaseModel):
    task_id: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: task_manager.TaskStatus
    result: str | None = None

# --- Endpoints ---
@router.post("/tasks", response_model=TaskCreationResponse, status_code=202)
async def submit_task(request: TaskCreationRequest, background_tasks: BackgroundTasks):
    """
    Submits a new task to the agent.
    The task is processed in the background.
    """
    task_id = task_manager.create_task(prompt=request.prompt)
    background_tasks.add_task(orchestrator.run_task_and_update_status, task_id, request.prompt)
    return TaskCreationResponse(task_id=task_id)


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Retrieves the status and result of a previously submitted task.
    """
    status_info = task_manager.get_task_status(task_id)
    if not status_info:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskStatusResponse(task_id=task_id, status=status_info["status"], result=status_info["result"]) 