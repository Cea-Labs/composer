#!/bin/bash

# A script that handles everything: starts the server, runs the test, and cleans up.
# Exit on any error.
set -e

# --- Configuration ---
HOST="http://127.0.0.1:8000"
PROMPT="Read the URL from 'url_to_fetch.txt' and then fetch the content of that website."
CURL_OPTS="-sf" # -s for silent, -f to fail on server errors (4xx, 5xx)
SERVER_PID=""
SERVER_LOG="composer-core/server_test.log"

# --- Cleanup function to be called on exit ---
cleanup() {
    EXIT_CODE=$? # Get the exit code of the last command
    echo
    echo "--- Cleaning up ---"
    
    # If the script failed, print the server log for debugging
    if [ $EXIT_CODE -ne 0 ]; then
        echo "Script exited with a non-zero status code: $EXIT_CODE."
        if [ -f "$SERVER_LOG" ]; then
            echo "--- Server Log (from $SERVER_LOG) ---"
            cat "$SERVER_LOG"
            echo "---------------------------------------"
        else
            echo "Server log file not found."
        fi
    fi

    if [ -n "$SERVER_PID" ]; then
        echo "Stopping server (PID: $SERVER_PID)..."
        # Kill the entire process group to ensure uvicorn workers are also terminated
        kill -9 "$SERVER_PID" 2>/dev/null || true
    fi
    
    rm -f "$SERVER_LOG"
    echo "Cleanup complete."
}

# Trap EXIT signal to run cleanup function no matter how the script ends
trap cleanup EXIT

# --- Start Server ---
echo "--- Preparing Server ---"

# Ensure the log file from a previous run is gone
rm -f "$SERVER_LOG"

echo "Checking for and stopping any existing process on port 8000..."
lsof -ti tcp:8000 | xargs kill -9 2>/dev/null || echo "No existing process found."

echo "Starting server in the background, logs will be in $SERVER_LOG"
# Start the server, redirecting both stdout and stderr to the log file
(cd composer-core && poetry run start &> "server_test.log" &)
SERVER_PID=$!

# --- Wait for Server to be Ready ---
echo "Waiting for server to become available..."
TIMEOUT=30 # 30 seconds
ELAPSED=0
while ! curl $CURL_OPTS "$HOST/docs" > /dev/null 2>&1; do
    if [ $ELAPSED -ge $TIMEOUT ]; then
        echo "Error: Server failed to start within $TIMEOUT seconds."
        # The cleanup trap will handle printing the log and exiting
        exit 1
    fi
    sleep 1
    ELAPSED=$((ELAPSED + 1))
    printf "Waited %s seconds...\r" "$ELAPSED"
done

echo "Server is ready and responding."

# --- 1. Submit the initial task ---
echo
echo "--- Starting End-to-End Test ---"
echo "Submitting task..."
RESPONSE=$(curl $CURL_OPTS -X POST "$HOST/v1/tasks" -H "Content-Type: application/json" -d "{\"prompt\": \"$PROMPT\"}")

TASK_ID=$(echo "$RESPONSE" | jq -r .task_id)

if [ -z "$TASK_ID" ] || [ "$TASK_ID" == "null" ]; then
    echo "Error: Failed to create task."
    echo "Response: $RESPONSE"
    exit 1
fi

echo "Task created successfully. Task ID: $TASK_ID"

# --- 2. Poll for 'awaiting_approval' status ---
echo
echo "Polling for 'awaiting_approval' status..."
while true; do
    STATUS_INFO=$(curl $CURL_OPTS "$HOST/v1/tasks/$TASK_ID")
    STATUS=$(echo "$STATUS_INFO" | jq -r .status)
    
    printf "Current status: %s\r" "$STATUS"
    
    if [ "$STATUS" == "awaiting_approval" ]; then
        echo
        echo "Plan is ready for approval:"
        echo "$STATUS_INFO" | jq .plan
        break
    elif [ "$STATUS" == "failed" ]; then
        echo
        echo "Error: Task failed during planning."
        echo "$STATUS_INFO" | jq .
        exit 1
    fi
    
    sleep 2
done

# --- 3. Approve the task ---
echo
echo "Approving the plan..."
curl $CURL_OPTS -X POST "$HOST/v1/tasks/$TASK_ID/approve" > /dev/null
echo "Plan approved."

# --- 4. Poll for 'completed' status ---
echo
echo "Polling for 'completed' status..."
while true; do
    STATUS_INFO=$(curl $CURL_OPTS "$HOST/v1/tasks/$TASK_ID")
    STATUS=$(echo "$STATUS_INFO" | jq -r .status)

    printf "Current status: %s\r" "$STATUS"

    if [ "$STATUS" == "completed" ]; then
        echo
        echo
        echo "--- Test Succeeded! ---"
        echo "Final Result:"
        echo "$STATUS_INFO" | jq .
        break
    elif [ "$STATUS" == "failed" ]; then
        echo
        echo
        echo "--- Test Failed! ---"
        echo "Error details:"
        echo "$STATUS_INFO" | jq .
        exit 1
    fi

    sleep 3
done

echo "--- End-to-End Test Finished ---" 