#!/usr/bin/env python3
"""
Web Scraping Bot Demo Script

This script demonstrates the key features of the Web Scraping Bot
for interview and presentation purposes.

Usage:
    python demo.py [--no-cache] [--monitoring-only] [--interview-mode]

Options:
    --no-cache          Disable caching to demonstrate performance difference
    --monitoring-only   Only demonstrate the monitoring capabilities
    --interview-mode    Enable interview-friendly output with clear section markers
"""

import os
import time
import json
import argparse
import threading
import random
from datetime import datetime
from colorama import init, Fore, Style

# Import core modules
from core.scraper import WebScraper
from core.report_generator import ReportGenerator
from core.email_sender import EmailSender

# Import utility modules
from utils.logger import setup_logger
from utils.cache import CacheManager
from utils.monitoring import get_default_monitor
from utils.metrics_server import start_metrics_server

# Initialize colorama for colored terminal output
init(autoreset=True)

# Set up logger
logger = setup_logger('demo', log_to_console=True, log_level='INFO')

def load_config(config_path='config/config.json'):
    """
    Load configuration from JSON file
    """
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {}

def demo_cache_system():
    """
    Demonstrate the intelligent caching system
    """
    logger.info("\n===== DEMONSTRATING INTELLIGENT CACHING SYSTEM =====")
    
    # Initialize cache manager
    cache_manager = CacheManager()
    
    # Demo storing and retrieving from cache
    test_url = "https://example.com/demo"
    test_data = {"product_name": "Demo Product", "price": 99.99, "in_stock": True}
    
    logger.info("Storing data in cache...")
    cache_manager.store(test_url, test_data)
    
    logger.info("Retrieving data from cache...")
    cached_data = cache_manager.retrieve(test_url)
    
    if cached_data:
        logger.info(f"Cache hit! Retrieved data: {cached_data}")
    else:
        logger.error("Cache miss! Data not found in cache.")
    
    # Demo cache statistics
    stats = cache_manager.get_stats()
    logger.info(f"Cache Statistics: {stats}")
    
    return cache_manager

def demo_web_scraping(use_cache=True):
    """
    Demonstrate the web scraping capabilities
    """
    logger.info("\n===== DEMONSTRATING WEB SCRAPING CAPABILITIES =====")
    
    # Initialize web scraper with cache
    scraper = WebScraper(use_cache=use_cache)
    
    # Demo websites (public and safe to scrape for demo)
    demo_urls = [
        "http://quotes.toscrape.com",
        "http://books.toscrape.com"
    ]
    
    all_results = []
    
    # Set up monitoring
    monitor = get_default_monitor()
    
    for url in demo_urls:
        logger.info(f"Scraping {url}...")
        
        # Track scraping duration
        with monitor.track_duration('scraping_duration_seconds', labels={'target': url}):
            results = scraper.scrape(url)
            
        # Record metrics
        monitor.increment('pages_scraped_count', labels={'target': url})
        monitor.increment('items_scraped_count', len(results), labels={'target': url})
        
        logger.info(f"Scraped {len(results)} items from {url}")
        all_results.extend(results)
    
    return all_results

def demo_report_generation(data):
    """
    Demonstrate report generation capabilities
    """
    logger.info("\n===== DEMONSTRATING REPORT GENERATION =====")
    
    # Initialize report generator
    report_gen = ReportGenerator()
    
    # Generate timestamp for report filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Generate CSV report
    csv_path = f"reports/demo_report_{timestamp}.csv"
    logger.info(f"Generating CSV report: {csv_path}")
    report_gen.generate_csv_report(data, csv_path)
    
    # Generate Excel report
    excel_path = f"reports/demo_report_{timestamp}.xlsx"
    logger.info(f"Generating Excel report: {excel_path}")
    report_gen.generate_excel_report(data, excel_path)
    
    return csv_path, excel_path

def demo_monitoring():
    """
    Demonstrate monitoring capabilities
    """
    logger.info("\n===== DEMONSTRATING MONITORING CAPABILITIES =====")
    
    # Start metrics server
    server_thread = start_metrics_server(port=8000)
    logger.info("Metrics server started on port 8000")
    logger.info("Metrics available at: http://localhost:8000/metrics")
    logger.info("Health check available at: http://localhost:8000/health")
    
    # Get monitor and add some demo metrics
    monitor = get_default_monitor()
    
    # Set some gauge metrics
    monitor.set_gauge('demo_gauge', 42.0, labels={'demo': 'true'})
    
    # Increment some counter metrics
    monitor.increment('demo_counter', 1.0, labels={'demo': 'true'})
    
    # Track duration of an operation
    with monitor.track_duration('demo_duration_seconds', labels={'demo': 'true'}):
        logger.info("Performing a demo operation...")
        time.sleep(2)  # Simulate work
    
    return monitor

def print_section_header(title, interview_mode=False):
    """Print a formatted section header"""
    if interview_mode:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'=' * 80}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 5} {title} {'=' * (73 - len(title))}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 80}")
    else:
        logger.info(f"\n===== {title} =====")

def simulate_real_time_metrics(monitor, duration=60, interview_mode=False):
    """Simulate real-time metrics for the interview demo"""
    if interview_mode:
        print(f"\n{Fore.YELLOW}Simulating real-time metrics for the demo...")
    
    end_time = time.time() + duration
    
    while time.time() < end_time:
        # Simulate scraping activity
        monitor.increment('pages_scraped_count', random.randint(1, 3))
        monitor.increment('items_scraped_count', random.randint(5, 20))
        
        # Simulate cache activity
        if random.random() > 0.3:  # 70% cache hit rate
            monitor.increment('cache_hits')
        else:
            monitor.increment('cache_misses')
        
        # Simulate varying response times
        monitor.observe('response_time_seconds', random.uniform(0.1, 2.0))
        
        # Simulate system metrics
        monitor.set_gauge('cpu_usage_percent', random.uniform(10, 80))
        monitor.set_gauge('memory_usage_mb', random.uniform(100, 500))
        
        # Sleep for a bit
        time.sleep(1)

def main():
    """
    Main demo function
    """
    parser = argparse.ArgumentParser(description='Web Scraping Bot Demo')
    parser.add_argument('--no-cache', action='store_true', help='Disable caching')
    parser.add_argument('--monitoring-only', action='store_true', help='Only demonstrate monitoring')
    parser.add_argument('--interview-mode', action='store_true', help='Enable interview-friendly output')
    args = parser.parse_args()
    
    interview_mode = args.interview_mode
    
    # Print welcome message
    if interview_mode:
        print(f"\n{Fore.GREEN}{Style.BRIGHT}{'=' * 80}")
        print(f"{Fore.GREEN}{Style.BRIGHT}{'=' * 25} WEB SCRAPING BOT DEMO {'=' * 25}")
        print(f"{Fore.GREEN}{Style.BRIGHT}{'=' * 80}")
    else:
        print("\n" + "=" * 80)
        print("WELCOME TO THE WEB SCRAPING BOT DEMO")
        print("=" * 80)
    
    # Load configuration
    config = load_config()
    
    # Start monitoring server
    monitor = demo_monitoring()
    
    # Start simulating metrics in background for interview demo
    if interview_mode:
        metrics_thread = threading.Thread(
            target=simulate_real_time_metrics,
            args=(monitor, 300, interview_mode)
        )
        metrics_thread.daemon = True
        metrics_thread.start()
    
    if not args.monitoring_only:
        # Demo cache system
        print_section_header("INTELLIGENT CACHING SYSTEM", interview_mode)
        cache_manager = demo_cache_system()
        
        # Demo web scraping
        print_section_header("WEB SCRAPING CAPABILITIES", interview_mode)
        scraped_data = demo_web_scraping(use_cache=not args.no_cache)
        
        # Demo report generation
        if scraped_data:
            print_section_header("REPORT GENERATION", interview_mode)
            csv_path, excel_path = demo_report_generation(scraped_data)
            if interview_mode:
                print(f"\n{Fore.GREEN}Reports successfully generated:")
                print(f"{Fore.WHITE}- CSV: {csv_path}")
                print(f"{Fore.WHITE}- Excel: {excel_path}")
            else:
                print(f"\nReports generated:\n- CSV: {csv_path}\n- Excel: {excel_path}")
    
    # Keep the script running to allow viewing metrics
    if interview_mode:
        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}{'=' * 80}")
        print(f"{Fore.MAGENTA}{Style.BRIGHT}{'=' * 20} DEMO IS RUNNING {'=' * 43}")
        print(f"{Fore.MAGENTA}{Style.BRIGHT}Metrics available at: http://localhost:8000/metrics")
        print(f"{Fore.MAGENTA}{Style.BRIGHT}Health check available at: http://localhost:8000/health")
        print(f"{Fore.MAGENTA}{Style.BRIGHT}Press Ctrl+C to exit the demo")
        print(f"{Fore.MAGENTA}{Style.BRIGHT}{'=' * 80}")
    else:
        print("\n" + "=" * 80)
        print("Demo is running. Press Ctrl+C to exit.")
        print("Metrics available at: http://localhost:8000/metrics")
        print("=" * 80 + "\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        if interview_mode:
            print(f"\n{Fore.YELLOW}Demo stopped by user.")
        else:
            print("\nDemo stopped by user.")

if __name__ == "__main__":
    main()