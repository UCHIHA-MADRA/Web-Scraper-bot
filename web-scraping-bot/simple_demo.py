#!/usr/bin/env python3
"""
Simplified Web Scraping Bot Demo Script

This script demonstrates the key features of the Web Scraping Bot
for interview and presentation purposes without external dependencies.

Usage:
    python simple_demo.py
"""

import os
import time
import json
import random
import argparse
from datetime import datetime

# Set up basic console colors without colorama
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Sample product data for demo
SAMPLE_PRODUCTS = [
    {"id": "1", "name": "Smartphone X", "price": 799.99, "rating": 4.5, "in_stock": True},
    {"id": "2", "name": "Laptop Pro", "price": 1299.99, "rating": 4.8, "in_stock": True},
    {"id": "3", "name": "Wireless Headphones", "price": 199.99, "rating": 4.2, "in_stock": True},
    {"id": "4", "name": "Smart Watch", "price": 249.99, "rating": 4.0, "in_stock": False},
    {"id": "5", "name": "Tablet Ultra", "price": 499.99, "rating": 4.6, "in_stock": True},
]

# Sample websites for demo
SAMPLE_WEBSITES = [
    "https://example-electronics.com",
    "https://sample-tech-store.com",
    "https://demo-gadget-shop.com",
]

def print_header(title):
    """Print a formatted section header"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 80}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 5} {title} {'=' * (73 - len(title))}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 80}{Colors.END}")

def simulate_cache():
    """Simulate the intelligent caching system"""
    print_header("INTELLIGENT CACHING SYSTEM")
    
    # Simulate cache operations
    cache = {}
    cache_hits = 0
    cache_misses = 0
    
    print("\nFirst scraping run (no cache)...")
    for website in SAMPLE_WEBSITES:
        # Simulate scraping time
        print(f"  Scraping {website}...")
        time.sleep(random.uniform(0.5, 1.5))
        
        # Generate random subset of products for this website
        num_products = random.randint(2, len(SAMPLE_PRODUCTS))
        products = random.sample(SAMPLE_PRODUCTS, num_products)
        
        # Store in cache
        cache[website] = products
        cache_misses += 1
        
        print(f"  {Colors.GREEN}✓ Scraped {len(products)} products{Colors.END}")
    
    print("\nSecond scraping run (with cache)...")
    for website in SAMPLE_WEBSITES:
        print(f"  Checking cache for {website}...")
        time.sleep(0.1)  # Small delay for demonstration
        
        if website in cache:
            print(f"  {Colors.BLUE}✓ Cache hit! Retrieved {len(cache[website])} products{Colors.END}")
            cache_hits += 1
        else:
            print(f"  {Colors.YELLOW}✗ Cache miss! Scraping {website}...{Colors.END}")
            time.sleep(random.uniform(0.5, 1.5))
            cache_misses += 1
    
    # Print cache statistics
    print(f"\n{Colors.BOLD}Cache statistics:{Colors.END}")
    print(f"  Hits: {cache_hits}")
    print(f"  Misses: {cache_misses}")
    print(f"  Hit ratio: {cache_hits / (cache_hits + cache_misses):.2%}")
    
    return cache

def simulate_scraping():
    """Simulate web scraping capabilities"""
    print_header("WEB SCRAPING CAPABILITIES")
    
    all_data = {}
    
    for website in SAMPLE_WEBSITES:
        print(f"\nScraping {website}...")
        
        # Simulate scraping time
        start_time = time.time()
        time.sleep(random.uniform(0.5, 2.0))
        
        # Generate random subset of products for this website
        num_products = random.randint(3, len(SAMPLE_PRODUCTS))
        products = random.sample(SAMPLE_PRODUCTS, num_products)
        
        # Update product prices slightly to simulate different stores
        for product in products:
            product = product.copy()  # Create a copy to avoid modifying the original
            # Vary price by ±10%
            product["price"] = round(product["price"] * random.uniform(0.9, 1.1), 2)
        
        all_data[website] = products
        elapsed = time.time() - start_time
        
        print(f"  {Colors.GREEN}✓ Scraped {len(products)} products in {elapsed:.2f} seconds{Colors.END}")
        for product in products[:2]:  # Show just a couple of products
            print(f"    - {product['name']}: ${product['price']}")
        if len(products) > 2:
            print(f"    - ... and {len(products) - 2} more products")
    
    return all_data

def simulate_report_generation(data):
    """Simulate report generation"""
    print_header("REPORT GENERATION")
    
    # Ensure reports directory exists
    os.makedirs("reports", exist_ok=True)
    
    # Generate timestamp for report filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Simulate CSV report generation
    csv_path = f"reports/demo_report_{timestamp}.csv"
    print(f"\nGenerating CSV report: {csv_path}")
    time.sleep(1.0)  # Simulate processing time
    
    # Actually create a simple CSV file for demo purposes
    try:
        with open(csv_path, 'w') as f:
            # Write header
            f.write("website,product_id,name,price,rating,in_stock\n")
            
            # Write data
            for website, products in data.items():
                for product in products:
                    f.write(f"{website},{product['id']},{product['name']},{product['price']},{product['rating']},{product['in_stock']}\n")
        
        print(f"  {Colors.GREEN}✓ CSV report generated successfully{Colors.END}")
    except Exception as e:
        print(f"  {Colors.RED}✗ Error generating CSV report: {e}{Colors.END}")
    
    # Simulate Excel report generation
    excel_path = f"reports/demo_report_{timestamp}.txt"  # Using .txt instead of .xlsx to avoid dependencies
    print(f"\nGenerating Excel-like report: {excel_path}")
    time.sleep(1.5)  # Simulate processing time
    
    # Actually create a simple text file for demo purposes
    try:
        with open(excel_path, 'w') as f:
            f.write("DEMO EXCEL-LIKE REPORT\n")
            f.write("===================\n\n")
            
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("PRODUCT SUMMARY\n")
            f.write("---------------\n")
            
            total_products = sum(len(products) for products in data.values())
            total_value = sum(sum(p['price'] for p in products) for products in data.values())
            
            f.write(f"Total Products: {total_products}\n")
            f.write(f"Total Value: ${total_value:.2f}\n")
            f.write(f"Average Price: ${total_value / total_products:.2f}\n\n")
            
            f.write("PRODUCT DETAILS\n")
            f.write("---------------\n")
            
            for website, products in data.items():
                f.write(f"\nWebsite: {website}\n")
                for product in products:
                    f.write(f"  - {product['name']}: ${product['price']} ")
                    f.write("(In Stock)" if product['in_stock'] else "(Out of Stock)")
                    f.write(f", Rating: {product['rating']}\n")
        
        print(f"  {Colors.GREEN}✓ Excel-like report generated successfully{Colors.END}")
    except Exception as e:
        print(f"  {Colors.RED}✗ Error generating Excel-like report: {e}{Colors.END}")
    
    return csv_path, excel_path

def simulate_monitoring():
    """Simulate monitoring capabilities"""
    print_header("MONITORING CAPABILITIES")
    
    print("\nSimulating metrics collection...")
    
    # Simulate metrics
    metrics = {
        "scraping_duration_seconds": {
            "count": 15,
            "sum": 23.5,
            "avg": 1.57,
            "min": 0.8,
            "max": 3.2
        },
        "pages_scraped_count": 42,
        "items_scraped_count": 156,
        "cache_hit_ratio": 0.72,
        "memory_usage_mb": 128.5,
        "cpu_usage_percent": 23.4
    }
    
    # Display metrics
    print(f"\n{Colors.BOLD}Sample metrics:{Colors.END}")
    print(f"  Scraping Duration: avg={metrics['scraping_duration_seconds']['avg']:.2f}s, ")
    print(f"                     min={metrics['scraping_duration_seconds']['min']:.2f}s, ")
    print(f"                     max={metrics['scraping_duration_seconds']['max']:.2f}s")
    print(f"  Pages Scraped: {metrics['pages_scraped_count']}")
    print(f"  Items Scraped: {metrics['items_scraped_count']}")
    print(f"  Cache Hit Ratio: {metrics['cache_hit_ratio']:.2%}")
    print(f"  Memory Usage: {metrics['memory_usage_mb']:.1f} MB")
    print(f"  CPU Usage: {metrics['cpu_usage_percent']:.1f}%")
    
    print(f"\n{Colors.YELLOW}In a production environment, these metrics would be:{Colors.END}")
    print("  1. Collected by Prometheus")
    print("  2. Visualized in Grafana dashboards")
    print("  3. Used for alerting on anomalies")
    
    return metrics

def main():
    """Main demo function"""
    parser = argparse.ArgumentParser(description='Web Scraping Bot Demo')
    args = parser.parse_args()
    
    # Print welcome message
    print(f"\n{Colors.GREEN}{Colors.BOLD}{'=' * 80}{Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}{'=' * 25} WEB SCRAPING BOT DEMO {'=' * 25}{Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}{'=' * 80}{Colors.END}")
    
    try:
        # Demo cache system
        cache = simulate_cache()
        input("\nPress Enter to continue...")
        
        # Demo web scraping
        scraped_data = simulate_scraping()
        input("\nPress Enter to continue...")
        
        # Demo report generation
        csv_path, excel_path = simulate_report_generation(scraped_data)
        print(f"\n{Colors.GREEN}Reports generated:{Colors.END}")
        print(f"  - CSV: {csv_path}")
        print(f"  - Excel-like: {excel_path}")
        input("\nPress Enter to continue...")
        
        # Demo monitoring
        metrics = simulate_monitoring()
        
        # Demo completion
        print(f"\n{Colors.GREEN}{Colors.BOLD}{'=' * 80}{Colors.END}")
        print(f"{Colors.GREEN}{Colors.BOLD}{'=' * 30} DEMO COMPLETE {'=' * 30}{Colors.END}")
        print(f"{Colors.GREEN}{Colors.BOLD}{'=' * 80}{Colors.END}")
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Demo stopped by user.{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}Error in demo: {e}{Colors.END}")
    
    print("\nThank you for watching the Web Scraping Bot demo!")

if __name__ == "__main__":
    main()