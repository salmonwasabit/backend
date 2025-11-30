FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libmagic1 \
    libmagic-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY templates/ ./templates/
COPY static/ ./static/
COPY init_admin.py ./

# Create uploads directory
RUN mkdir -p uploads

# Create templates and static directories
RUN mkdir -p templates static

# Expose port
EXPOSE 8000

# Run the application
CMD ["sh", "-c", "python init_admin.py && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]
