#!/usr/bin/env python3
"""
Custom exceptions for the Web Scraping Bot
"""

class WebScraperError(Exception):
    """Base exception for all web scraper errors"""
    def __init__(self, message, details=None):
        self.message = message
        self.details = details
        super().__init__(self.message)

class ConfigurationError(WebScraperError):
    """Raised when there's an issue with the configuration"""
    pass

class ScrapingError(WebScraperError):
    """Raised when there's an issue with the scraping process"""
    def __init__(self, message, url=None, selector=None, details=None):
        self.url = url
        self.selector = selector
        super().__init__(message, details)

class NetworkError(WebScraperError):
    """Raised when there's a network-related issue"""
    def __init__(self, message, url=None, status_code=None, details=None):
        self.url = url
        self.status_code = status_code
        super().__init__(message, details)

class RateLimitError(NetworkError):
    """Raised when rate limiting is detected"""
    pass

class BlockedError(NetworkError):
    """Raised when the scraper is blocked by the target website"""
    pass

class ParsingError(WebScraperError):
    """Raised when there's an issue parsing the scraped content"""
    def __init__(self, message, content_sample=None, details=None):
        self.content_sample = content_sample
        super().__init__(message, details)

class ReportGenerationError(WebScraperError):
    """Raised when there's an issue generating reports"""
    pass

class EmailError(WebScraperError):
    """Raised when there's an issue sending emails"""
    pass

class SecurityError(WebScraperError):
    """Raised when there's a security-related issue"""
    def __init__(self, message, vulnerability_type=None, details=None):
        self.vulnerability_type = vulnerability_type
        super().__init__(message, details)

class DatabaseError(WebScraperError):
    """Raised when there's an issue with database operations"""
    pass