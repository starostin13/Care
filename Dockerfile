# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create directory for database and set permissions
RUN mkdir -p /app/data && chmod 755 /app/data

# Expose port
EXPOSE 5555

# Set environment variables
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=5555
ENV DATABASE_PATH=/app/data/game_database.db

# Health check (проверяем Flask сервер)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5555/health')" || exit 1

# Run the hybrid application (Flask + Telegram bot)
CMD ["python", "run_hybrid.py"]