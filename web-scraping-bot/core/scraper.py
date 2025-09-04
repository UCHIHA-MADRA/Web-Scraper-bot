#!/usr/bin/env python3
"""
Advanced web scraping module with error handling, logging, and multiple scraping methods
"""
import requests
import time
import random
import os
import json
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd
import traceback
import urllib.parse

# Selenium imports for JavaScript-rendered content
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# Import custom modules
from utils.logger import get_default_logger
from utils.exceptions import (
    ScrapingError, NetworkError, ParsingError, 
    RateLimitError, BlockedError, ConfigurationError
)

class WebScraper:
    """
    Advanced web scraper with multiple scraping methods, error handling, and logging
    """
    def __init__(self, config=None):
        """
        Initialize the web scraper
        
        Args:
            config (dict, optional): Scraper configuration
        """
        self.config = config or {}
        self.logger = get_default_logger('web_scraper')
        
        # Initialize session and driver to None
        self.session = None
        self.driver = None
        
        # Set up configuration
        self.user_agent = self.config.get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        self.delay_range = self.config.get('delay_range', [1, 3])  # Default 1-3 seconds
        self.timeout = self.config.get('timeout', 30)  # Default 30 seconds
        self.max_retries = self.config.get('max_retries', 3)  # Default 3 retries
        self.use_selenium = self.config.get('use_selenium', False)  # Default to requests
        self.proxies = self.config.get('proxies', None)  # Optional proxy configuration
        
        # Initialize session
        self._init_session()
        
        # Initialize Selenium if needed
        if self.use_selenium and SELENIUM_AVAILABLE:
            self._init_selenium()
        elif self.use_selenium and not SELENIUM_AVAILABLE:
            self.logger.warning("Selenium requested but not available. Falling back to requests.")
            self.use_selenium = False
    
    def _init_session(self):
        """
        Initialize requests session with headers and proxies
        """
        try:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0'
            })
            
            # Add proxies if configured
            if self.proxies:
                self.session.proxies.update(self.proxies)
                self.logger.info(f"Using proxies: {self.proxies}")
            
            self.logger.info("Requests session initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize requests session: {e}")
            raise ConfigurationError(f"Failed to initialize requests session: {str(e)}")
    
    def _init_selenium(self):
        """
        Initialize Selenium WebDriver
        """
        if not SELENIUM_AVAILABLE:
            self.logger.error("Selenium is not available")
            return
        
        try:
            # Set up Chrome options
            chrome_options = Options()
            
            # Add headless option for production environments
            if self.config.get('headless', True):
                chrome_options.add_argument('--headless')
            
            # Add additional Chrome options
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument(f'user-agent={self.user_agent}')
            
            # Add proxy if configured
            if self.proxies and 'http' in self.proxies:
                chrome_options.add_argument(f'--proxy-server={self.proxies["http"]}')
            
            # Initialize WebDriver
            driver_path = self.config.get('chromedriver_path')
            if driver_path:
                service = Service(executable_path=driver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
            
            # Set page load timeout
            self.driver.set_page_load_timeout(self.timeout)
            
            self.logger.info("Selenium WebDriver initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Selenium WebDriver: {e}")
            self.driver = None
            self.use_selenium = False
    
    def _random_delay(self):
        """
        Implement random delay between requests to avoid rate limiting
        """
        delay = random.uniform(self.delay_range[0], self.delay_range[1])
        self.logger.debug(f"Waiting for {delay:.2f} seconds")
        time.sleep(delay)
    
    def _is_blocked(self, response_text):
        """
        Check if the response indicates we've been blocked
        
        Args:
            response_text (str): HTML response text
            
        Returns:
            bool: True if blocked, False otherwise
        """
        block_indicators = [
            'captcha',
            'blocked',
            'access denied',
            'too many requests',
            'rate limit exceeded',
            'automated access',
            'unusual traffic',
            'security check'
        ]
        
        response_lower = response_text.lower()
        for indicator in block_indicators:
            if indicator in response_lower:
                return True
        
        return False
    
    def _scrape_with_requests(self, url, params=None, headers=None):
        """
        Scrape URL using requests
        
        Args:
            url (str): URL to scrape
            params (dict, optional): URL parameters
            headers (dict, optional): Additional headers
            
        Returns:
            str: HTML content
            
        Raises:
            NetworkError: If connection fails
            RateLimitError: If rate limited
            BlockedError: If blocked by the server
        """
        merged_headers = {}
        if headers:
            merged_headers.update(headers)
        
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Scraping URL: {url} (Attempt {attempt+1}/{self.max_retries})")
                
                # Add random delay between requests
                if attempt > 0:
                    self._random_delay()
                
                # Make the request
                response = self.session.get(
                    url, 
                    params=params, 
                    headers=merged_headers if merged_headers else None,
                    timeout=self.timeout
                )
                
                # Check for HTTP errors
                if response.status_code == 429:
                    self.logger.warning(f"Rate limited (429) for URL: {url}")
                    raise RateLimitError(f"Rate limited with status code 429", url=url, status_code=429)
                
                elif response.status_code >= 400:
                    self.logger.error(f"HTTP error {response.status_code} for URL: {url}")
                    raise NetworkError(f"HTTP error with status code {response.status_code}", 
                                      url=url, status_code=response.status_code)
                
                # Check if we've been blocked
                if self._is_blocked(response.text):
                    self.logger.warning(f"Blocked by server for URL: {url}")
                    raise BlockedError(f"Blocked by server", url=url)
                
                self.logger.debug(f"Successfully scraped URL: {url}")
                return response.text
                
            except (requests.RequestException, ConnectionError) as e:
                self.logger.warning(f"Request failed for URL {url}: {e}")
                if attempt == self.max_retries - 1:
                    self.logger.error(f"Max retries reached for URL: {url}")
                    raise NetworkError(f"Failed to connect after {self.max_retries} attempts: {str(e)}", url=url)
            
            except (RateLimitError, BlockedError):
                # Re-raise these specific exceptions
                raise
            
            except Exception as e:
                self.logger.error(f"Unexpected error scraping URL {url}: {e}")
                if attempt == self.max_retries - 1:
                    raise ScrapingError(f"Unexpected error: {str(e)}", url=url)
    
    def _scrape_with_selenium(self, url, wait_for=None, wait_time=10):
        """
        Scrape URL using Selenium for JavaScript-rendered content
        
        Args:
            url (str): URL to scrape
            wait_for (str, optional): CSS selector to wait for
            wait_time (int, optional): Time to wait for element
            
        Returns:
            str: HTML content
            
        Raises:
            NetworkError: If connection fails
            RateLimitError: If rate limited
            BlockedError: If blocked by the server
        """
        if not self.driver:
            self.logger.error("Selenium WebDriver not initialized")
            raise ConfigurationError("Selenium WebDriver not initialized")
        
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Scraping URL with Selenium: {url} (Attempt {attempt+1}/{self.max_retries})")
                
                # Add random delay between requests
                if attempt > 0:
                    self._random_delay()
                
                # Load the page
                self.driver.get(url)
                
                # Wait for specific element if requested
                if wait_for:
                    WebDriverWait(self.driver, wait_time).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_for))
                    )
                
                # Get the page source
                html_content = self.driver.page_source
                
                # Check if we've been blocked
                if self._is_blocked(html_content):
                    self.logger.warning(f"Blocked by server for URL: {url}")
                    raise BlockedError(f"Blocked by server", url=url)
                
                self.logger.debug(f"Successfully scraped URL with Selenium: {url}")
                return html_content
                
            except TimeoutException as e:
                self.logger.warning(f"Timeout for URL {url}: {e}")
                if attempt == self.max_retries - 1:
                    self.logger.error(f"Max retries reached for URL: {url}")
                    raise NetworkError(f"Timeout after {self.max_retries} attempts: {str(e)}", url=url)
            
            except WebDriverException as e:
                self.logger.warning(f"WebDriver error for URL {url}: {e}")
                if attempt == self.max_retries - 1:
                    self.logger.error(f"Max retries reached for URL: {url}")
                    raise NetworkError(f"WebDriver error after {self.max_retries} attempts: {str(e)}", url=url)
            
            except BlockedError:
                # Re-raise this specific exception
                raise
            
            except Exception as e:
                self.logger.error(f"Unexpected error scraping URL {url} with Selenium: {e}")
                if attempt == self.max_retries - 1:
                    raise ScrapingError(f"Unexpected error: {str(e)}", url=url)
    
    def scrape(self, url, params=None, headers=None, use_selenium=None, wait_for=None, wait_time=10):
        """
        Scrape URL using the appropriate method
        
        Args:
            url (str): URL to scrape
            params (dict, optional): URL parameters
            headers (dict, optional): Additional headers
            use_selenium (bool, optional): Override default Selenium setting
            wait_for (str, optional): CSS selector to wait for (Selenium only)
            wait_time (int, optional): Time to wait for element (Selenium only)
            
        Returns:
            BeautifulSoup: Parsed HTML content
            
        Raises:
            NetworkError: If connection fails
            RateLimitError: If rate limited
            BlockedError: If blocked by the server
            ParsingError: If HTML parsing fails
        """
        try:
            # Determine whether to use Selenium
            should_use_selenium = use_selenium if use_selenium is not None else self.use_selenium
            
            # Log the scraping method
            self.logger.info(f"Scraping URL: {url} using {'Selenium' if should_use_selenium else 'Requests'}")
            
            # Scrape the URL
            if should_use_selenium and self.driver:
                html_content = self._scrape_with_selenium(url, wait_for, wait_time)
            else:
                html_content = self._scrape_with_requests(url, params, headers)
            
            # Parse the HTML content
            soup = BeautifulSoup(html_content, 'lxml')
            return soup
            
        except (NetworkError, RateLimitError, BlockedError):
            # Re-raise these specific exceptions
            raise
            
        except Exception as e:
            self.logger.error(f"Failed to scrape URL {url}: {e}")
            raise ScrapingError(f"Failed to scrape URL: {str(e)}", url=url)
    
    def extract_data(self, soup, selectors):
        """
        Extract data from BeautifulSoup object using selectors
        
        Args:
            soup (BeautifulSoup): Parsed HTML content
            selectors (dict): CSS selectors for data extraction
            
        Returns:
            dict: Extracted data
            
        Raises:
            ParsingError: If data extraction fails
        """
        data = {}
        
        try:
            for key, selector in selectors.items():
                try:
                    # Handle different selector types
                    if isinstance(selector, dict):
                        # Complex selector with additional instructions
                        css = selector.get('css')
                        attr = selector.get('attr')
                        regex = selector.get('regex')
                        transform = selector.get('transform')
                        
                        # Find element
                        element = soup.select_one(css) if css else None
                        
                        if element:
                            # Extract value based on configuration
                            if attr:
                                value = element.get(attr)
                            else:
                                value = element.get_text(strip=True)
                            
                            # Apply regex if specified
                            if regex and value:
                                import re
                                match = re.search(regex, value)
                                if match:
                                    value = match.group(1) if match.groups() else match.group(0)
                            
                            # Apply transformation if specified
                            if transform and value:
                                if transform == 'float':
                                    value = float(value.replace(',', '').replace('$', ''))
                                elif transform == 'int':
                                    value = int(value.replace(',', ''))
                            
                            data[key] = value
                        else:
                            data[key] = None
                            
                    else:
                        # Simple CSS selector
                        element = soup.select_one(selector)
                        data[key] = element.get_text(strip=True) if element else None
                        
                except Exception as e:
                    self.logger.warning(f"Failed to extract {key} using selector {selector}: {e}")
                    data[key] = None
            
            return data
            
        except Exception as e:
            self.logger.error(f"Data extraction failed: {e}")
            raise ParsingError(f"Failed to extract data: {str(e)}")
    
    def scrape_product(self, url, selectors, use_selenium=None):
        """
        Scrape product data from URL
        
        Args:
            url (str): Product URL
            selectors (dict): CSS selectors for data extraction
            use_selenium (bool, optional): Override default Selenium setting
            
        Returns:
            dict: Product data
        """
        try:
            # Add timestamp
            product_data = {
                'url': url,
                'timestamp': datetime.now().isoformat()
            }
            
            # Scrape the URL
            soup = self.scrape(url, use_selenium=use_selenium)
            
            # Extract data
            extracted_data = self.extract_data(soup, selectors)
            product_data.update(extracted_data)
            
            self.logger.info(f"Successfully scraped product data from {url}")
            return product_data
            
        except Exception as e:
            self.logger.error(f"Failed to scrape product {url}: {e}")
            # Return error data
            return {
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def scrape_products(self, products):
        """
        Scrape multiple products
        
        Args:
            products (list): List of product URLs and selectors
            
        Returns:
            list: Product data
        """
        results = []
        
        for product in products:
            try:
                url = product.get('url')
                selectors = product.get('selectors')
                use_selenium = product.get('use_selenium')
                
                if not url or not selectors:
                    self.logger.warning(f"Missing URL or selectors for product: {product}")
                    continue
                
                # Add random delay between requests
                self._random_delay()
                
                # Scrape product
                product_data = self.scrape_product(url, selectors, use_selenium)
                results.append(product_data)
                
            except Exception as e:
                self.logger.error(f"Failed to scrape product: {e}")
                # Add error data
                results.append({
                    'url': product.get('url', 'unknown'),
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e),
                    'error_type': type(e).__name__
                })
        
        return results
    
    def save_to_csv(self, data, filename=None):
        """
        Save scraped data to CSV
        
        Args:
            data (list): List of dictionaries containing scraped data
            filename (str, optional): Output filename
            
        Returns:
            str: Path to saved CSV file
        """
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"scrape_results_{timestamp}.csv"
            
            # Create output directory if it doesn't exist
            output_dir = self.config.get('output_dir', 'data')
            os.makedirs(output_dir, exist_ok=True)
            
            # Create full path
            filepath = os.path.join(output_dir, filename)
            
            # Convert to DataFrame and save
            df = pd.DataFrame(data)
            df.to_csv(filepath, index=False)
            
            self.logger.info(f"Data saved to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Failed to save data to CSV: {e}")
            raise
    
    def close(self):
        """
        Close all connections and resources
        """
        try:
            # Close Selenium WebDriver if initialized
            if self.driver:
                try:
                    self.driver.quit()
                    self.logger.info("Selenium WebDriver closed")
                except Exception as e:
                    self.logger.warning(f"Error closing Selenium WebDriver: {e}")
                finally:
                    self.driver = None
            
            # Close requests session
            if self.session:
                try:
                    self.session.close()
                    self.logger.info("Requests session closed")
                except Exception as e:
                    self.logger.warning(f"Error closing requests session: {e}")
                finally:
                    self.session = None
                    
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        
        # Log exception if one occurred
        if exc_type is not None:
            self.logger.error(f"Exception during context manager: {exc_type.__name__}: {exc_val}")
            self.logger.debug(f"Traceback: {''.join(traceback.format_tb(exc_tb))}")
