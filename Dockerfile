FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY . .

# Install dependencies
RUN uv sync

# Expose port for MCP server
EXPOSE 8000

# Run MCP server
CMD ["uv", "run", "python", "mcp_server.py"]
