import asyncio
import httpx
import os
import subprocess
import sys
from pathlib import Path

# --- Setup Project Root ---
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# --- Test Configuration ---
HOST = "http://127.0.0.1:8000"
SERVER_LOG = PROJECT_ROOT / "logs" / "comprehensive_test.log"
PROMPT = (
    "Fetch the content of 'https://v7t.space', create a new page in Notion with the title 'V7T Space Summary', "
    "use the fetched content as the page's content, and then send an email from my personal Gmail account to "
    "'test@example.com' with the subject 'Notion Page Created' and the body 'I have just created a new page "
    "in Notion with a summary of V7T Space.'"
)
POLL_INTERVAL = 5  # seconds
TIMEOUT = 120  # seconds

# --- Helper Functions ---

def print_header(title):
    print(f"\\n{'='*20}")
    print(f" {title}")
    print(f"{'='*20}")

async def wait_for_server():
    print_header("Waiting for Server")
    async with httpx.AsyncClient() as client:
        for i in range(TIMEOUT // 2):
            try:
                response = await client.get(f"{HOST}/docs")
                if response.status_code == 200:
                    print("Server is ready and responding.")
                    return True
            except httpx.ConnectError:
                pass
            print(f"Waited {i*2} seconds...")
            await asyncio.sleep(2)
    print("Error: Server failed to start within the timeout period.")
    return False

# --- Main Test Logic ---

async def run_comprehensive_test():
    server_process = None
    try:
        # 1. Start the main application server
        print_header("Starting Server")
        SERVER_LOG.parent.mkdir(exist_ok=True)
        with open(SERVER_LOG, "w") as log_file:
            server_process = subprocess.Popen(
                ["poetry", "run", "start"],
                cwd=PROJECT_ROOT / "src",
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env={**os.environ, "COMPOSER_CONFIG": str(PROJECT_ROOT / "config.yaml")}
            )
        
        if not await wait_for_server():
            raise RuntimeError("Server failed to start.")

        # 2. Submit the task
        print_header("Submitting Task")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{HOST}/v1/tasks", json={"prompt": PROMPT})
            response.raise_for_status()
            task_id = response.json()["task_id"]
            print(f"Task created successfully. Task ID: {task_id}")

            # 3. Poll for plan approval
            print_header("Polling for Plan Approval")
            for _ in range(TIMEOUT // POLL_INTERVAL):
                status_response = await client.get(f"{HOST}/v1/tasks/{task_id}")
                status_info = status_response.json()
                status = status_info["status"]
                print(f"Current status: {status}")
                if status == "awaiting_approval":
                    print("Plan is ready for approval:")
                    print(status_info.get("plan", "No plan found."))
                    break
                if status in ["failed", "completed"]:
                    raise RuntimeError(f"Task entered unexpected state '{status}' before approval.")
                await asyncio.sleep(POLL_INTERVAL)
            else:
                raise TimeoutError("Task did not reach 'awaiting_approval' in time.")

            # 4. Approve the plan
            print_header("Approving Plan")
            await client.post(f"{HOST}/v1/tasks/{task_id}/approve")
            print("Plan approved. Execution has started.")

            # 5. Poll for completion
            print_header("Polling for Final Result")
            for _ in range(TIMEOUT // POLL_INTERVAL):
                status_response = await client.get(f"{HOST}/v1/tasks/{task_id}")
                status_info = status_response.json()
                status = status_info["status"]
                print(f"Current status: {status}")
                if status == "completed":
                    print_header("Test Completed Successfully!")
                    print("Final Result:")
                    print(status_info.get("result", "No result found."))
                    return
                if status == "failed":
                    raise RuntimeError(f"Task failed during execution. Final status: {status_info}")
                await asyncio.sleep(POLL_INTERVAL)
            else:
                raise TimeoutError("Task did not complete in time.")

    except Exception as e:
        print_header("Test Failed")
        print(f"An error occurred: {e}")
    finally:
        if server_process:
            print_header("Shutting Down Server")
            server_process.terminate()
            server_process.wait()
            print("Server shut down.")
        
        if SERVER_LOG.exists():
            print_header("Server Log")
            print(SERVER_LOG.read_text())


if __name__ == "__main__":
    asyncio.run(run_comprehensive_test()) 