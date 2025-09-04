# Web Scraping Bot - Interview Demo

## Quick Start Guide

### Prerequisites
- Python 3.6 or higher
- No additional dependencies required for the simple demo

### Running the Demo

#### Windows
```
.\run_simple_demo.bat
```

#### Linux/Mac
```
chmod +x ./run_simple_demo.sh
./run_simple_demo.sh
```

#### Manual Execution
```
python simple_demo.py
```

## Demo Features

The simplified demo showcases the following features of the Web Scraping Bot:

1. **Intelligent Caching System**
   - Demonstrates how the bot stores and retrieves data from cache
   - Shows cache statistics and performance improvements

2. **Web Scraping Capabilities**
   - Simulates scraping from multiple e-commerce websites
   - Displays extracted product information

3. **Report Generation**
   - Creates CSV reports with scraped data
   - Generates text-based reports for easy viewing

4. **Monitoring Capabilities**
   - Shows key performance metrics
   - Demonstrates how the system would integrate with Prometheus and Grafana in production

## Full System Demo

For a complete demonstration including Prometheus, Grafana, and Docker deployment:

1. Review the `DEMO_GUIDE.md` for detailed instructions
2. Use `docker-compose up` to start all services if Docker is installed
3. Access the monitoring dashboards at:
   - Grafana: http://localhost:3000
   - Prometheus: http://localhost:9090
   - Web Dashboard: http://localhost:8080

## Interview Materials

The following files are available to help prepare for the interview:

- `INTERVIEW_CHEATSHEET.md`: Key talking points and technical details
- `ARCHITECTURE.md`: System architecture overview
- `DEMO_PRESENTATION.md`: Presentation outline for the interview
- `QUICK_START.md`: Comprehensive setup instructions

## Troubleshooting

If you encounter any issues running the demo:

1. Ensure Python is installed and in your PATH
2. Try running `python simple_demo.py` directly
3. Check that you have read/write permissions in the current directory