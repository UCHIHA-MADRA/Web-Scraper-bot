# Web Scraping Bot - Quick Start Guide

## Prerequisites

- Python 3.9 or higher
- Docker and Docker Compose (for containerized demo)
- Git (for cloning the repository)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/web-scraping-bot.git
cd web-scraping-bot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Demo

#### Option 1: Using the Demo Scripts

**Windows:**
```bash
.\run_demo.bat
```

**Linux/Mac:**
```bash
chmod +x run_demo.sh
./run_demo.sh
```

#### Option 2: Manual Execution

**Full Demo:**
```bash
python demo.py --interview-mode
```

**Monitoring Only:**
```bash
python demo.py --monitoring-only --interview-mode
```

**Without Caching (to demonstrate performance difference):**
```bash
python demo.py --no-cache --interview-mode
```

### 4. Docker Deployment

```bash
docker-compose up -d
```

This will start the following services:
- Web Scraper
- Scheduler
- Dashboard
- Prometheus
- Grafana

## Accessing the Demo

### Web Dashboard
- URL: http://localhost:5000

### Monitoring
- Metrics: http://localhost:8000/metrics
- Health Check: http://localhost:8000/health
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (login: admin/admin)

## Demo Walkthrough

1. **Start the demo** using one of the methods above
2. **Observe the intelligent caching system** in action
   - First run shows cache misses
   - Second run shows cache hits and performance improvement
3. **View the scraped data** and generated reports
4. **Explore the monitoring dashboard** in Grafana
   - Performance metrics
   - Business metrics
   - System metrics
5. **Stop the demo**
   - For script: Press Ctrl+C
   - For Docker: `docker-compose down`

## Troubleshooting

### Common Issues

1. **Port conflicts**
   - Ensure ports 5000, 8000, 9090, and 3000 are available
   - Modify docker-compose.yml if needed

2. **Missing dependencies**
   - Run `pip install -r requirements.txt` again
   - Check for error messages

3. **Docker issues**
   - Ensure Docker is running
   - Try `docker-compose down` followed by `docker-compose up -d`

### Getting Help

If you encounter any issues, please check the logs:
- Demo logs: `logs/demo.log`
- Docker logs: `docker-compose logs`