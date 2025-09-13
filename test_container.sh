#!/bin/bash

# Container deployment verification script
# Tests the agent-runtime-service in containerized environment

set -e

echo "🐳 AGENT RUNTIME SERVICE - CONTAINER VERIFICATION"
echo "=================================================="
echo

# Configuration
CONTAINER_NAME="agent-runtime-test"
HOST="http://localhost:8000"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Cleanup function
cleanup() {
    EXIT_CODE=$?
    echo
    echo -e "${YELLOW}🧹 Cleaning up containers...${NC}"
    
    if [ $EXIT_CODE -ne 0 ]; then
        echo -e "${RED}❌ Container test failed with exit code: $EXIT_CODE${NC}"
        echo -e "${YELLOW}📋 Container logs:${NC}"
        docker logs "$CONTAINER_NAME" --tail 50 || true
    fi

    # Stop and remove container
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
    
    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

trap cleanup EXIT

echo -e "${YELLOW}1. BUILDING CONTAINER IMAGE${NC}"
docker build -t agent-runtime-service:test --target development .
echo -e "${GREEN}✅ Container image built${NC}"

echo -e "${YELLOW}2. STARTING CONTAINER${NC}"
docker run -d \
    --name "$CONTAINER_NAME" \
    -p 8000:8000 \
    -v "$(pwd)/config.yaml:/app/config.yaml:ro" \
    -v "$(pwd)/tool_registry.yaml:/app/tool_registry.yaml:ro" \
    -e AGENT_RUNTIME_CONFIG=/app/config.yaml \
    -e PYTHONPATH=/app/src \
    agent-runtime-service:test

echo -e "${GREEN}✅ Container started: $CONTAINER_NAME${NC}"

echo -e "${YELLOW}3. WAITING FOR SERVICE STARTUP${NC}"
TIMEOUT=60
ELAPSED=0
while ! curl -sf "$HOST/docs" > /dev/null 2>&1; do
    if [ $ELAPSED -ge $TIMEOUT ]; then
        echo -e "${RED}❌ Service failed to start within $TIMEOUT seconds${NC}"
        exit 1
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
    printf "⏱️  Waited %s seconds...\r" "$ELAPSED"
done
echo
echo -e "${GREEN}✅ Service is responding in container${NC}"

echo -e "${YELLOW}4. TESTING CONTAINERIZED API${NC}"

# Test health endpoint
echo "🏥 Testing health check..."
docker exec "$CONTAINER_NAME" curl -sf http://localhost:8000/docs > /dev/null
echo "✅ Internal health check passed"

# Test API endpoints
echo "📍 Testing /docs endpoint..."
curl -sf "$HOST/docs" > /dev/null
echo "✅ /docs endpoint accessible"

echo -e "${YELLOW}5. TESTING FILE CREATION IN CONTAINER${NC}"

# Submit task
echo "📝 Submitting containerized task..."
TASK_RESPONSE=$(curl -sf -X POST "$HOST/v1/tasks" \
    -H "Content-Type: application/json" \
    -d '{"prompt": "Create a file called container_test.txt with the message CONTAINER DEPLOYMENT VERIFIED"}')

TASK_ID=$(echo "$TASK_RESPONSE" | jq -r .task_id)
echo "✅ Task created: $TASK_ID"

# Wait for planning
echo "⏳ Waiting for plan generation..."
for i in {1..30}; do
    STATUS_INFO=$(curl -sf "$HOST/v1/tasks/$TASK_ID")
    STATUS=$(echo "$STATUS_INFO" | jq -r .status)
    
    printf "📊 Status: %s\r" "$STATUS"
    
    if [ "$STATUS" = "awaiting_approval" ]; then
        break
    elif [ "$STATUS" = "failed" ]; then
        echo -e "${RED}❌ Task failed during planning${NC}"
        echo "$STATUS_INFO" | jq .
        exit 1
    fi
    sleep 2
done

echo
echo -e "${GREEN}✅ Plan ready for approval${NC}"

# Approve and execute
curl -sf -X POST "$HOST/v1/tasks/$TASK_ID/approve" > /dev/null
echo "✅ Plan approved"

echo "⚡ Executing in container..."
for i in {1..60}; do
    STATUS_INFO=$(curl -sf "$HOST/v1/tasks/$TASK_ID")
    STATUS=$(echo "$STATUS_INFO" | jq -r .status)
    
    printf "⚡ Status: %s\r" "$STATUS"
    
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
echo -e "${GREEN}✅ Task completed in container${NC}"

# Verify file in container
echo -e "${YELLOW}6. VERIFYING FILE IN CONTAINER${NC}"
if docker exec "$CONTAINER_NAME" test -f "/app/src/agent_runtime/sample_data/container_test.txt"; then
    echo -e "${GREEN}✅ File created successfully in container!${NC}"
    echo "📄 Container file content:"
    docker exec "$CONTAINER_NAME" cat "/app/src/agent_runtime/sample_data/container_test.txt"
    echo
else
    echo -e "${RED}❌ File was not created in container${NC}"
    exit 1
fi

echo -e "${YELLOW}7. TESTING DOCKER COMPOSE${NC}"
echo "🐳 Testing with docker-compose..."
docker-compose down 2>/dev/null || true
docker-compose up -d

# Wait for compose service
sleep 10
if curl -sf "$HOST/docs" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker Compose deployment successful${NC}"
    docker-compose down
else
    echo -e "${RED}❌ Docker Compose deployment failed${NC}"
    docker-compose logs
    docker-compose down
    exit 1
fi

echo
echo -e "${GREEN}🎉 ALL CONTAINER TESTS PASSED!${NC}"
echo "========================================="
echo -e "${GREEN}✅ Container image builds successfully${NC}"
echo -e "${GREEN}✅ Service starts in container${NC}"
echo -e "${GREEN}✅ API endpoints accessible${NC}"
echo -e "${GREEN}✅ Task orchestration works${NC}"
echo -e "${GREEN}✅ File operations work${NC}"
echo -e "${GREEN}✅ Docker Compose deployment works${NC}"
echo
echo -e "${GREEN}🚀 AGENT RUNTIME SERVICE IS CONTAINER-READY!${NC}"