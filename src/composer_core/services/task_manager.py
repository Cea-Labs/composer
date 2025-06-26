from typing import Dict, Any, Literal
import uuid

# In-memory storage for tasks.
# For a production system, this would be replaced by a more robust
# solution like Redis or a database.
task_storage: Dict[str, Dict[str, Any]] = {}

TaskStatus = Literal["pending", "awaiting_approval", "completed", "failed"]

def create_task(prompt: str) -> str:
    """Creates a new task and stores it."""
    task_id = str(uuid.uuid4())
    task_storage[task_id] = {
        "status": "pending",
        "prompt": prompt,
        "plan": None,
        "result": None,
    }
    print(f"Task Manager: Created task {task_id}")
    return task_id

def get_task_status(task_id: str) -> Dict[str, Any] | None:
    """Retrieves the status of a task."""
    return task_storage.get(task_id)

def update_task_plan(task_id: str, plan: str):
    """Updates the task with a plan and sets it to await approval."""
    if task_id in task_storage:
        task_storage[task_id]["plan"] = plan
        task_storage[task_id]["status"] = "awaiting_approval"
        print(f"Task Manager: Updated task {task_id} with plan, awaiting approval.")

def approve_task(task_id: str) -> bool:
    """Marks a task as approved, allowing execution to continue."""
    if task_id in task_storage and task_storage[task_id]["status"] == "awaiting_approval":
        task_storage[task_id]["status"] = "pending" # Set back to pending for execution
        print(f"Task Manager: Approved task {task_id}, resuming.")
        return True
    return False

def update_task_result(task_id: str, status: TaskStatus, result: Any):
    """Updates the result and status of a task."""
    if task_id in task_storage:
        task_storage[task_id]["status"] = status
        task_storage[task_id]["result"] = result
        print(f"Task Manager: Updated task {task_id} to {status}") 