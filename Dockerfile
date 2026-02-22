FROM python:3.12-slim

# Install build tools and Node.js (required for C extensions and the claude CLI)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates g++ && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install the Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code

WORKDIR /app

# Install only the runtime dependencies needed by the A2A server + starsim
RUN pip install --no-cache-dir \
    a2a-sdk \
    claude-agent-sdk \
    click \
    uvicorn \
    typing_extensions \
    fastmcp \
    starsim

# Copy only the A2A server source (no eval code, no problems/answers)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/
COPY README.md pyproject.toml ./
COPY src/ src/
RUN uv pip install --no-deps -e . --system

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create non-root user (claude CLI refuses bypassPermissions as root)
RUN useradd -m -s /bin/bash agent
RUN chown agent:agent /app -R
RUN mkdir -p /home/agent/agent_logs && chown agent:agent /home/agent/agent_logs

USER agent

EXPOSE 9100

ENTRYPOINT ["docker-entrypoint.sh"]
