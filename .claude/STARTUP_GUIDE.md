# Starting Agent Runtime Service from Main Folder

## Current Structure
```
/Users/v7t/dev/agents/
├── Cellery/                     # Product overview
├── agent-runtime-service/       # This service
```

## Option 1: Add Startup Script to Cellery Root (Recommended)

Create a startup script in the Cellery main folder:

```bash
# /Users/v7t/dev/agents/Cellery/start-agent-runtime.sh
#!/bin/bash
cd agent-runtime-service
poetry run start
```

Then from Cellery folder:
```bash
chmod +x start-agent-runtime.sh
./start-agent-runtime.sh
```

## Option 2: Use Absolute Path

From any directory:
```bash
cd /Users/v7t/dev/agents/agent-runtime-service && poetry run start
```

## Option 3: Docker Compose Setup (Future)

Eventually, you'll want a `docker-compose.yml` in Cellery root:

```yaml
# /Users/v7t/dev/agents/Cellery/docker-compose.yml
version: '3.8'
services:
  agent-runtime:
    build: ./agent-runtime-service
    ports:
      - "8000:8000"
    environment:
      - AGENT_RUNTIME_CONFIG=/app/config.yaml
    volumes:
      - ./agent-runtime-service:/app
```

## Option 4: Poetry Script from Parent

Add to Cellery folder's `pyproject.toml`:
```toml
[tool.poetry.scripts]
start-runtime = "subprocess:run(['poetry', 'run', 'start'], cwd='agent-runtime-service')"
```

## Option 5: Make Command (Recommended for Development)

Create `/Users/v7t/dev/agents/Cellery/Makefile`:
```makefile
start-runtime:
	cd agent-runtime-service && poetry run start

stop-runtime:
	pkill -f "agent_runtime"

test-runtime:
	cd agent-runtime-service && poetry run python test_flows/comprehensive_e2e_test.py

.PHONY: start-runtime stop-runtime test-runtime
```

Then use:
```bash
make start-runtime
make test-runtime  
make stop-runtime
```

## Current Working Commands

**From agent-runtime-service directory:**
```bash
poetry run start
```

**From any directory:**
```bash
cd /Users/v7t/dev/agents/agent-runtime-service && poetry run start
```

**Environment variable override:**
```bash
AGENT_RUNTIME_CONFIG=/path/to/config.yaml cd /Users/v7t/dev/agents/agent-runtime-service && poetry run start
```

## Recommended Setup

1. Create the Makefile approach in Cellery root folder
2. This gives you simple commands from the main directory
3. Easy to extend for other services later

Would you like me to create the Makefile for you?