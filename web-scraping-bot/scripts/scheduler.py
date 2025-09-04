#!/usr/bin/env python3
"""
Advanced scheduling system
"""
import schedule
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Web_Scraper import WebScrapingBot

def run_daily_scraping():
    """Run daily scraping task"""
    bot = WebScrapingBot()
    bot.run_scraping()

def run_weekly_summary():
    """Generate weekly summary"""
    print("Generating weekly summary...")
    # Weekly summary logic here

def main():
    print("📅 Starting scheduler...")
    
    # Schedule daily scraping at 9 AM
    schedule.every().day.at("09:00").do(run_daily_scraping)
    
    # Schedule weekly summary on Sundays
    schedule.every().sunday.at("10:00").do(run_weekly_summary)
    
    print("Scheduler running... Press Ctrl+C to stop")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
