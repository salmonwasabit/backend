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

# Install psycopg2-binary for database connectivity check
RUN pip install --no-cache-dir psycopg2-binary

# Copy application code
COPY app/ ./app/
COPY templates/ ./templates/
COPY static/ ./static/
COPY init_admin.py ./
COPY populate_products.py ./
COPY populate_categories.py ./
COPY entrypoint.sh ./

# Copy brand images from frontend public directory
COPY frontend/public/brands ./static/brands

# Make entrypoint script executable
RUN chmod +x entrypoint.sh

# Create uploads directory
RUN mkdir -p uploads

# Create templates and static directories
RUN mkdir -p templates static

# Expose port
EXPOSE 8000

# Run the application with entrypoint script
CMD ["./entrypoint.sh"]
