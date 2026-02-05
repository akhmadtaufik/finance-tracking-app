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

# Create logs directory with proper permissions
RUN mkdir -p /app/logs && chmod 777 /app/logs

# Copy application code into backend folder structure
COPY . ./backend/

# Expose port
EXPOSE 8000

# Run server with correct module path
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
