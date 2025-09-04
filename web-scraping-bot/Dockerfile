FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome for Selenium
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt psutil pyyaml

# Copy application code
COPY . .

# Create directories
RUN mkdir -p logs reports data data/cache monitoring

# Set environment variables
ENV PYTHONPATH=/app \
    MONITORING_CONFIG=/app/monitoring/monitoring_config.yaml \
    DEPLOYMENT_CONFIG=/app/deployment/deployment_config.yaml

# Expose ports for monitoring
EXPOSE 8000

# Run the application
CMD ["python", "Web_Scraper.py"]
