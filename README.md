# 🤖 Web Scraping and Report Generation Bot

A comprehensive RPA bot for automated competitor data collection and Excel report generation with intelligent caching.

## ✨ Features

- **Multi-site scraping** with configurable targets
- **Intelligent caching system** with memory and file-based caching
- **Professional Excel reports** with charts and formatting
- **Email automation** for daily report delivery
- **Scheduling support** for automated runs
- **Robust error handling** and comprehensive logging
- **Anti-detection measures** with delays and headers
- **Command-line interface** for easy interaction

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the bot:**
   ```bash
   python Web_Scraper.py
   ```
   
   Available options:
   - Option 1: Run scraping process
   - Option 2: View configuration
   - Option 3: View cache statistics
   - Option 4: Clear cache

3. **Configure targets in:** `config/config.json`

## 📁 Project Structure

```
web-scraping-bot/
├── Web_Scraper.py          # Main application
├── config/                 # Configuration files
├── utils/                  # Utility modules
│   ├── cache.py           # Caching system
│   └── logger.py          # Advanced logging system
├── reports/                # Generated reports
├── logs/                   # Application logs
├── cache/                  # Cache storage
└── tests/                  # Unit tests
    └── test_cache.py      # Cache system tests
```

## 📊 Sample Output

The bot generates professional Excel reports with:
- Product data tables
- Price trend analysis  
- Store comparison charts
- Summary dashboards

## 🛠️ Configuration

Edit `config/config.json` to add your target websites and configure caching:

```json
{
    "targets": [
        {
            "name": "Your Store",
            "base_url": "https://store.com",
            "products": [
                {
                    "name": "Product Name",
                    "url": "https://store.com/product",
                    "price_selector": ".price",
                    "availability_selector": ".stock"
                }
            ]
        }
    ]
}
```

## 📧 Email Reports

Configure email settings in the config file to receive automated reports.

## 📅 Scheduling

Use the scheduler script for automated daily runs:
```bash
python scripts/scheduler.py
```

## 🧪 Testing

Run tests with:
```bash
python -m pytest tests/
```

## 🚀 Caching System

The bot features a multi-level caching system to improve performance:

- **Memory Cache**: Fast in-memory storage for frequently accessed data
- **File Cache**: JSON-based persistent storage between application runs
- **HTTP Request Cache**: Avoids redundant network requests using requests-cache

Cache commands:
```bash
# View cache statistics
python Web_Scraper.py  # Select option 3

# Clear cache
python Web_Scraper.py  # Select option 4
```

Cache configuration can be adjusted in the initialization of the WebScrapingBot class.

## 📝 License

This project is for educational and legitimate business use only.

## ⚠️ Legal Notice

Always respect website terms of service and robots.txt files.
