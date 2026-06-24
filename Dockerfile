# Use official slim Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8501

# Install system dependencies (curl is needed for health checks in startup.sh)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy python requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Set execution permission on the startup script
RUN chmod +x startup.sh

# Expose ports: 8000 for FastAPI, 8501 for Streamlit
EXPOSE 8000 7860

# Execute startup.sh to launch both services concurrently
ENTRYPOINT ["./startup.sh"]
