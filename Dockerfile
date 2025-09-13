# Multi-stage build for Agent Runtime Service
# Production-ready containerized deployment

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (required for MCP servers)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Development stage
FROM base as development

WORKDIR /app

# Copy source code (needed for hatchling to read README.md)
COPY . .

# Install dependencies
RUN uv sync --dev

# Install MCP server dependencies
RUN npm install -g @modelcontextprotocol/server-filesystem @kazuph/mcp-fetch

EXPOSE 8000

CMD ["uv", "run", "agent-runtime"]

# Production stage
FROM base as production

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

WORKDIR /app

# Copy source code
COPY . .

# Install production dependencies only
RUN uv sync --no-dev

# Install MCP server dependencies
RUN npm install -g @modelcontextprotocol/server-filesystem @kazuph/mcp-fetch

# Create necessary directories
RUN mkdir -p logs src/agent_runtime/sample_data

# Set ownership
RUN chown -R app:app /app

# Switch to non-root user  
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

EXPOSE 8000

CMD ["uv", "run", "agent-runtime"]