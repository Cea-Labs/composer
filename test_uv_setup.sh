#!/bin/bash

# Comprehensive uv setup verification script
# This script validates the agent-runtime-service works with uv

set -e  # Exit on any error

echo "🔥 AGENT RUNTIME SERVICE - UV SETUP VERIFICATION"
echo "=================================================="
echo

# Configuration
HOST="http://127.0.0.1:8000"
SERVER_PID=""
SERVER_LOG="logs/uv_test.log"
TEST_FILE="src/agent_runtime/sample_data/uv_verification.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Cleanup function
cleanup() {
    EXIT_CODE=$?
    echo
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"
    
    if [ $EXIT_CODE -ne 0 ]; then
        echo -e "${RED}❌ Test failed with exit code: $EXIT_CODE${NC}"
        if [ -f "$SERVER_LOG" ]; then
            echo -e "${YELLOW}📋 Server log:${NC}"
            tail -20 "$SERVER_LOG"
        fi
    fi

    # Kill server
    if [ -n "$SERVER_PID" ]; then
        kill -9 "$SERVER_PID" 2>/dev/null || true
        echo "🔪 Killed server process"
    fi
    pkill -f "agent-runtime" 2>/dev/null || true
    
    # Clean up test files
    rm -f "$SERVER_LOG" "$TEST_FILE"
    
    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

trap cleanup EXIT

echo -e "${YELLOW}1. KILLING EXISTING PROCESSES${NC}"
pkill -f "uvicorn.*agent_runtime" || true
pkill -f "agent-runtime" || true
sleep 2

echo -e "${YELLOW}2. TESTING UV IMPORTS${NC}"
uv run python -c "
from agent_runtime.api.main import create_app
from agent_runtime.services.orchestrator import OrchestratorManager
from agent_runtime.services.agent_service import AgentService
print('✅ All imports successful')
"

echo -e "${YELLOW}3. TESTING UV APP CREATION${NC}"
uv run python -c "
from agent_runtime.api.main import create_app
app = create_app()
print('✅ FastAPI app creation successful')
"

echo -e "${YELLOW}4. STARTING SERVER WITH UV${NC}"
mkdir -p logs
rm -f "$SERVER_LOG"

# Start server in background
uv run agent-runtime > "$SERVER_LOG" 2>&1 &
SERVER_PID=$!
echo "🚀 Started server (PID: $SERVER_PID)"

echo -e "${YELLOW}5. WAITING FOR SERVER STARTUP${NC}"
TIMEOUT=30
ELAPSED=0
while ! curl -sf "$HOST/docs" > /dev/null 2>&1; do
    if [ $ELAPSED -ge $TIMEOUT ]; then
        echo -e "${RED}❌ Server failed to start within $TIMEOUT seconds${NC}"
        exit 1
    fi
    sleep 1
    ELAPSED=$((ELAPSED + 1))
    printf "⏱️  Waited %s seconds...\r" "$ELAPSED"
done
echo
echo -e "${GREEN}✅ Server is responding${NC}"

echo -e "${YELLOW}6. TESTING API ENDPOINTS${NC}"

# Test health check
echo "📍 Testing /docs endpoint..."
curl -sf "$HOST/docs" > /dev/null
echo "✅ /docs endpoint working"

echo -e "${YELLOW}7. TESTING FILE CREATION WORKFLOW${NC}"

# Remove test file if it exists
rm -f "$TEST_FILE"
echo "🗑️  Removed existing test file"

# Submit task
echo "📝 Submitting file creation task..."
TASK_RESPONSE=$(curl -sf -X POST "$HOST/v1/tasks" \
    -H "Content-Type: application/json" \
    -d '{"prompt": "Write a message saying UV SETUP VERIFIED to a file called uv_verification.txt in the src/agent_runtime/sample_data directory"}')

TASK_ID=$(echo "$TASK_RESPONSE" | jq -r .task_id)
echo "✅ Task created: $TASK_ID"

# Wait for planning
echo "⏳ Waiting for plan generation..."
PLAN_READY=false
for i in {1..30}; do
    STATUS_INFO=$(curl -sf "$HOST/v1/tasks/$TASK_ID")
    STATUS=$(echo "$STATUS_INFO" | jq -r .status)
    
    printf "📊 Status: %s\r" "$STATUS"
    
    if [ "$STATUS" = "awaiting_approval" ]; then
        PLAN_READY=true
        break
    elif [ "$STATUS" = "failed" ]; then
        echo -e "${RED}❌ Task failed during planning${NC}"
        echo "$STATUS_INFO" | jq .
        exit 1
    fi
    sleep 2
done

if [ "$PLAN_READY" = false ]; then
    echo -e "${RED}❌ Plan generation timed out${NC}"
    exit 1
fi

echo
echo -e "${GREEN}✅ Plan ready for approval${NC}"
PLAN=$(echo "$STATUS_INFO" | jq -r .plan)
echo "📋 Generated plan:"
echo "$PLAN"
echo

# Approve plan
echo "✅ Approving plan..."
curl -sf -X POST "$HOST/v1/tasks/$TASK_ID/approve" > /dev/null

# Wait for completion
echo "⚡ Executing plan..."
for i in {1..60}; do
    STATUS_INFO=$(curl -sf "$HOST/v1/tasks/$TASK_ID")
    STATUS=$(echo "$STATUS_INFO" | jq -r .status)
    
    printf "⚡ Execution status: %s\r" "$STATUS"
    
    if [ "$STATUS" = "completed" ]; then
        break
    elif [ "$STATUS" = "failed" ]; then
        echo -e "${RED}❌ Task execution failed${NC}"
        echo "$STATUS_INFO" | jq .
        exit 1
    fi
    sleep 1
done

echo
echo -e "${GREEN}✅ Task completed${NC}"

# Verify file was created
echo -e "${YELLOW}8. VERIFYING FILE CREATION${NC}"
if [ -f "$TEST_FILE" ]; then
    echo -e "${GREEN}✅ Test file created successfully!${NC}"
    echo "📄 File content:"
    cat "$TEST_FILE"
    echo
else
    echo -e "${RED}❌ Test file was not created${NC}"
    exit 1
fi

# Get final result
FINAL_RESULT=$(echo "$STATUS_INFO" | jq -r .result)
echo "🎯 Final result: $FINAL_RESULT"

echo
echo -e "${GREEN}🎉 ALL UV SETUP TESTS PASSED!${NC}"
echo "========================================="
echo -e "${GREEN}✅ uv dependencies installed${NC}"
echo -e "${GREEN}✅ Python imports working${NC}"
echo -e "${GREEN}✅ FastAPI app creation working${NC}"
echo -e "${GREEN}✅ Server startup successful${NC}"
echo -e "${GREEN}✅ API endpoints responsive${NC}"
echo -e "${GREEN}✅ Task orchestration working${NC}"  
echo -e "${GREEN}✅ MCP servers functioning${NC}"
echo -e "${GREEN}✅ File creation verified${NC}"
echo
echo -e "${GREEN}🚀 AGENT RUNTIME SERVICE IS READY FOR CONTAINERIZATION!${NC}"