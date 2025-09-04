#!/usr/bin/env python3
"""
Advanced logging module for the Web Scraping Bot

This module provides a comprehensive logging system with the following features:
- Structured logging with JSON format support
- Log rotation to manage file sizes
- Multiple output formats (standard and JSON)
- Console and file logging simultaneously
- Exception tracking with detailed traceback
- Different log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)

Typical usage:
    from utils.logger import get_default_logger
    
    # Get a logger with a specific name
    logger = get_default_logger('component_name')
    
    # Log messages at different levels
    logger.debug('Detailed debugging information')
    logger.info('General information')
    logger.warning('Warning message')
    logger.error('Error message')
    
    # Log exceptions with context
    try:
        # Some code that might raise an exception
        result = process_data()
    except Exception as e:
        logger.exception('Error processing data', exc_info=e)
"""

import logging
import logging.handlers
import os
import json
from datetime import datetime
import traceback

class Logger:
    """
    Advanced logger with rotation, formatting, and different log levels
    
    This class provides a configurable logging system that outputs logs to both
    console and files, with support for standard and JSON formats. It handles
    log rotation automatically to prevent log files from growing too large.
    
    Attributes:
        log_name (str): Name of the logger instance
        log_level (int): Minimum log level to record
        log_dir (str): Directory where log files are stored
        logger (logging.Logger): The configured logger instance
    """
    def __init__(self, log_name='web_scraper', log_level=logging.INFO, log_dir='logs'):
        """
        Initialize logger with specified name, level, and directory
        
        This constructor sets up a complete logging system with multiple handlers:
        1. A rotating file handler for standard formatted logs
        2. A rotating file handler for JSON formatted logs
        3. A console handler for immediate feedback during development
        
        Args:
            log_name (str): Name of the logger, used in log messages and filenames
            log_level (int): Minimum logging level to record, should be one of:
                             logging.DEBUG (10): Detailed debugging information
                             logging.INFO (20): General information (default)
                             logging.WARNING (30): Warning messages
                             logging.ERROR (40): Error messages
                             logging.CRITICAL (50): Critical errors
            log_dir (str): Directory to store log files, created if it doesn't exist
        
        Note:
            Log files will be named '{log_name}.log' and '{log_name}_json.log'
            and will be automatically rotated when they reach 10MB in size.
        """
        self.log_name = log_name
        self.log_level = log_level
        self.log_dir = log_dir
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger(log_name)
        self.logger.setLevel(log_level)
        
        # Remove existing handlers if any
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Create formatters
        standard_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
        )
        
        class JsonFormatter(logging.Formatter):
            """Custom formatter that outputs log records as JSON objects
            
            This formatter converts standard log records into structured JSON format,
            making logs easier to parse and analyze with log management tools.
            """
            def format(self, record):
                """Format the log record as a JSON string
                
                Args:
                    record: The log record to format
                    
                Returns:
                    str: JSON-formatted log entry
                """
                log_data = {
                    'timestamp': datetime.now().isoformat(),
                    'level': record.levelname,
                    'name': record.name,
                    'message': record.getMessage(),
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno,
                    'thread': record.thread,
                    'thread_name': record.threadName
                }
                return json.dumps(log_data)
        
        json_formatter = JsonFormatter()
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, f'{log_name}.log'),
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(standard_formatter)
        self.logger.addHandler(file_handler)
        
        # JSON file handler for structured logging
        json_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, f'{log_name}_json.log'),
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        json_handler.setFormatter(json_formatter)
        self.logger.addHandler(json_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(standard_formatter)
        self.logger.addHandler(console_handler)
    
    def get_logger(self):
        """
        Get the configured logger instance
        
        This method returns the fully configured logging.Logger instance
        that can be used for logging messages at various levels.
        
        Returns:
            logging.Logger: Configured logger instance with all handlers attached
            
        Example:
            logger_instance = Logger(log_name='my_component')
            logger = logger_instance.get_logger()
            logger.info('Component initialized successfully')
        """
        return self.logger
    
    def log_exception(self, exception, context=None):
        """
        Log an exception with detailed traceback and optional context information
        
        This method provides enhanced exception logging by capturing the full traceback
        and formatting it as a structured JSON object. Additional context can be provided
        to help with debugging and troubleshooting.
        
        Args:
            exception (Exception): The exception object to log
            context (dict, optional): Additional contextual information about when/where
                                      the exception occurred, such as function parameters,
                                      system state, or other relevant data
        
        Example:
            try:
                result = process_item(item_id=123)
            except ValueError as e:
                logger.log_exception(e, {'item_id': 123, 'operation': 'process_item'})
        """
        error_details = {
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'traceback': traceback.format_exc()
        }
        
        if context:
            error_details['context'] = context
        
        self.logger.error(f"Exception: {json.dumps(error_details)}")

# Create a default logger instance
def get_default_logger(name='web_scraper'):
    """
    Get a pre-configured logger instance with standard settings
    
    This is the recommended way to obtain a logger throughout the application.
    It ensures consistent logging configuration across all components.
    
    The default logger is configured with:
    - INFO level logging
    - Both console and file output
    - Standard and JSON formatted logs
    - Automatic log rotation
    
    Args:
        name (str): Name for the logger, used to identify the component in logs
        
    Returns:
        logging.Logger: Configured logger instance ready for use
        
    Example:
        # In a component module
        from utils.logger import get_default_logger
        
        logger = get_default_logger('data_processor')
        logger.info('Processing started')
        
        try:
            result = process_data()
            logger.info(f'Processing completed with result: {result}')
        except Exception as e:
            logger.exception('Processing failed', exc_info=e)
    
    Returns:
        logging.Logger: Fully configured logger instance ready for immediate use
    
    Example:
        # In a scraper module
        logger = get_default_logger('product_scraper')
        logger.info('Starting product scraping process')
    """
    return Logger(log_name=name).get_logger()