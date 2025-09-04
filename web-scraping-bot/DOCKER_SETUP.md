# Docker Setup Guide for Web Scraping Bot Demo

## Prerequisites

To run the full Web Scraping Bot demo with Docker, you'll need to install:

1. Docker Desktop (for Windows/Mac) or Docker Engine (for Linux)
2. Docker Compose

## Installation Instructions

### Windows

1. **Install Docker Desktop for Windows**:
   - Download Docker Desktop from [Docker's official website](https://www.docker.com/products/docker-desktop)
   - Run the installer and follow the prompts
   - After installation, start Docker Desktop
   - Wait for Docker to start (you'll see the Docker icon in the system tray)

2. **Verify Installation**:
   - Open Command Prompt or PowerShell
   - Run `docker --version` to verify Docker is installed
   - Run `docker-compose --version` to verify Docker Compose is installed

### macOS

1. **Install Docker Desktop for Mac**:
   - Download Docker Desktop from [Docker's official website](https://www.docker.com/products/docker-desktop)
   - Install the .dmg file by dragging Docker to your Applications folder
   - Start Docker from your Applications folder
   - Wait for Docker to start (you'll see the Docker icon in the menu bar)

2. **Verify Installation**:
   - Open Terminal
   - Run `docker --version` to verify Docker is installed
   - Run `docker-compose --version` to verify Docker Compose is installed

### Linux

1. **Install Docker Engine**:
   ```bash
   # Update package index
   sudo apt-get update
   
   # Install prerequisites
   sudo apt-get install apt-transport-https ca-certificates curl software-properties-common
   
   # Add Docker's official GPG key
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
   
   # Add Docker repository
   sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
   
   # Update package index again
   sudo apt-get update
   
   # Install Docker
   sudo apt-get install docker-ce
   ```

2. **Install Docker Compose**:
   ```bash
   # Download Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.18.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   
   # Apply executable permissions
   sudo chmod +x /usr/local/bin/docker-compose
   ```

3. **Verify Installation**:
   ```bash
   docker --version
   docker-compose --version
   ```

## Running the Demo Without Docker

If you prefer not to install Docker for the interview demo, you can use the simplified demo instead:

### Windows
```
.\run_simple_demo.bat
```

### Linux/Mac
```
chmod +x ./run_simple_demo.sh
./run_simple_demo.sh
```

### Manual Execution
```
python simple_demo.py
```

## What You'll Miss Without Docker

Without Docker, you won't be able to demonstrate:

1. **Containerized Deployment** - How the application runs in isolated containers
2. **Prometheus Monitoring** - Real-time metrics collection
3. **Grafana Dashboards** - Visualization of performance metrics
4. **Multi-service Architecture** - How different components interact

However, the simplified demo still showcases the core functionality of the Web Scraping Bot, including:

- Intelligent caching
- Web scraping capabilities
- Report generation
- Simulated monitoring metrics

## Alternative for Interview

If Docker installation is not possible before the interview, consider these alternatives:

1. **Screenshots/Videos** - Include screenshots or a brief video of the Docker deployment in your presentation
2. **Cloud Deployment** - Deploy the application to a cloud service and share access during the interview
3. **Focus on Code** - Emphasize the code architecture and design patterns in your presentation