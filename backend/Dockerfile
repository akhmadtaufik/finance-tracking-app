FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user and logs directory
RUN useradd -m -s /bin/bash appuser && \
    mkdir -p /app/logs && \
    chown -R appuser:appuser /app

# Copy application code into backend folder structure
COPY . ./backend/

# Ensure all files are owned by appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Run server with correct module path
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
