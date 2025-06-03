# Base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data logs models

# Expose the port
EXPOSE 8000

# Set environment variables
ENV PORT=8000
ENV DVC_REPO_PATH=/data

# Initialize sample data
RUN python utils/init_data.py

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
