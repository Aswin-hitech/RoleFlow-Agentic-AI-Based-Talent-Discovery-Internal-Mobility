# ==============================================================================
# RoleFlow — Backend Container Scaffolding (Template Only)
# ==============================================================================
# NOTE: This Dockerfile is provided as unconfigured architectural scaffolding.
# It is NOT integrated into the active runtime environment.
#
# Primary runtime execution:
#   cd backend && python app.py
# ==============================================================================

FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    FLASK_ENV=production

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY . .

# Expose backend port
EXPOSE 5000

# Default entrypoint (app.py is the primary source)
CMD ["python", "app.py"]
