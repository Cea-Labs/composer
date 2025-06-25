import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from composer_core.services import orchestrator, task_manager

@pytest.mark.asyncio
@patch("composer_core.services.orchestrator.managed_tool_registry")
@patch("composer_core.services.agent_service.Runner")
async def test_orchestrator_runs_task_successfully(MockRunner, MockToolRegistry):
    """
    Tests the full orchestration flow for a successful task.
    """
    # Arrange
    task_id = task_manager.create_task(prompt="test prompt")
    
    # Mock the agent runner to return a successful result
    mock_runner_result = MagicMock()
    mock_runner_result.final_output = "Mocked final output"
    MockRunner.run = AsyncMock(return_value=mock_runner_result)

    # Act
    await orchestrator.run_task_and_update_status(task_id, "test prompt")

    # Assert
    status_info = task_manager.get_task_status(task_id)
    assert status_info is not None
    assert status_info["status"] == "completed"
    assert status_info["result"] == "Mocked final output"
    MockToolRegistry.assert_called_once()
    MockRunner.run.assert_awaited_once()

@pytest.mark.asyncio
@patch("composer_core.services.orchestrator.managed_tool_registry")
@patch("composer_core.services.agent_service.Runner")
async def test_orchestrator_handles_failure(MockRunner, MockToolRegistry):
    """
    Tests that the orchestrator correctly handles a failure during task execution.
    """
    # Arrange
    task_id = task_manager.create_task(prompt="failing prompt")
    error_message = "Something went wrong"
    MockRunner.run = AsyncMock(side_effect=Exception(error_message))

    # Act
    await orchestrator.run_task_and_update_status(task_id, "failing prompt")

    # Assert
    status_info = task_manager.get_task_status(task_id)
    assert status_info is not None
    assert status_info["status"] == "failed"
    assert status_info["result"] == error_message
    MockToolRegistry.assert_called_once()
    MockRunner.run.assert_awaited_once() 