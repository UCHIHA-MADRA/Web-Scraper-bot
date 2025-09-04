#!/bin/bash

echo "==================================================="
echo "Web Scraping Bot - Interview Demo"
echo "==================================================="
echo ""

echo "Checking environment..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python not found. Please install Python 3.9 or higher."
    exit 1
fi

echo "Checking dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies."
    exit 1
fi

echo ""
echo "==================================================="
echo "Starting Web Scraping Bot Demo"
echo "==================================================="
echo ""

echo "Choose a demo option:"
echo "1. Full Demo (Scraping, Caching, Reports, Monitoring)"
echo "2. Monitoring Only Demo"
echo "3. Docker Compose Demo (All Services)"
echo ""

read -p "Enter option (1-3): " option

if [ "$option" = "1" ]; then
    echo "Starting Full Demo..."
    python3 demo.py
elif [ "$option" = "2" ]; then
    echo "Starting Monitoring Only Demo..."
    python3 demo.py --monitoring-only
elif [ "$option" = "3" ]; then
    echo "Starting Docker Compose Demo..."
    docker-compose up -d
    echo ""
    echo "Services started! Access the following URLs:"
    echo "- Grafana Dashboard: http://localhost:3000 (admin/admin)"
    echo "- Prometheus: http://localhost:9090"
    echo "- Web Dashboard: http://localhost:5000"
    echo ""
    echo "Press Enter to stop the services..."
    read
    docker-compose down
else
    echo "Invalid option selected."
    exit 1
fi

echo ""
echo "Demo completed."
echo ""