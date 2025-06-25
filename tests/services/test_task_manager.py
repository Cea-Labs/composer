import pytest
from composer_core.services import task_manager

def test_create_and_get_task():
    """
    Tests that a task can be created and its status retrieved correctly.
    """
    # Arrange
    prompt = "test prompt"
    
    # Act
    task_id = task_manager.create_task(prompt=prompt)
    status_info = task_manager.get_task_status(task_id)

    # Assert
    assert task_id is not None
    assert status_info is not None
    assert status_info["status"] == "pending"
    assert status_info["prompt"] == prompt
    assert status_info["result"] is None

def test_update_task():
    """
    Tests that a task's status and result can be updated.
    """
    # Arrange
    task_id = task_manager.create_task(prompt="another prompt")

    # Act
    task_manager.update_task_result(task_id, "completed", "final output")
    status_info = task_manager.get_task_status(task_id)

    # Assert
    assert status_info is not None
    assert status_info["status"] == "completed"
    assert status_info["result"] == "final output" 