#!/usr/bin/env python3
"""
Unit tests for logger functionality

This module contains tests for the Logger class, including initialization,
log level configuration, and exception logging.
"""
import pytest
import logging
import os
import json
from unittest.mock import patch, mock_open, MagicMock, call

from utils.logger import Logger, get_default_logger

class TestLogger:
    @pytest.fixture
    def logger_instance(self):
        """Create a logger instance for testing"""
        with patch('utils.logger.os.makedirs'):
            with patch('utils.logger.RotatingFileHandler'):
                with patch('utils.logger.logging.getLogger') as mock_get_logger:
                    mock_logger = MagicMock()
                    mock_get_logger.return_value = mock_logger
                    logger = Logger(log_name='test_logger', log_level=logging.INFO)
                    return logger
    
    def test_init(self, logger_instance):
        """Test logger initialization"""
        assert logger_instance.log_name == 'test_logger'
        assert logger_instance.log_level == logging.INFO
        assert logger_instance.log_dir == 'logs'
    
    def test_get_logger(self, logger_instance):
        """Test getting logger instance"""
        logger = logger_instance.get_logger()
        assert logger is not None
    
    @patch('utils.logger.os.makedirs')
    @patch('utils.logger.RotatingFileHandler')
    @patch('utils.logger.logging.getLogger')
    def test_log_levels(self, mock_get_logger, mock_handler, mock_makedirs):
        """Test different log levels"""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Test DEBUG level
        logger_debug = Logger(log_name='debug_logger', log_level=logging.DEBUG)
        assert logger_debug.log_level == logging.DEBUG
        mock_logger.setLevel.assert_called_with(logging.DEBUG)
        
        # Test WARNING level
        mock_logger.reset_mock()
        logger_warning = Logger(log_name='warning_logger', log_level=logging.WARNING)
        assert logger_warning.log_level == logging.WARNING
        mock_logger.setLevel.assert_called_with(logging.WARNING)
    
    @patch('utils.logger.os.makedirs')
    @patch('utils.logger.RotatingFileHandler')
    @patch('utils.logger.logging.getLogger')
    def test_handlers_creation(self, mock_get_logger, mock_handler, mock_makedirs):
        """Test handler creation"""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        logger = Logger(log_name='test_logger', log_level=logging.INFO)
        
        # Should create directory if it doesn't exist
        mock_makedirs.assert_called_once_with('logs', exist_ok=True)
        
        # Should create handlers
        assert mock_handler.call_count >= 2  # At least file and JSON handlers
        assert mock_logger.addHandler.call_count >= 2  # At least file and JSON handlers
    
    def test_log_exception(self, logger_instance):
        """Test exception logging"""
        mock_logger = MagicMock()
        logger_instance.logger = mock_logger
        
        try:
            raise ValueError("Test exception")
        except Exception as e:
            logger_instance.log_exception(e, {'context': 'test'})
        
        mock_logger.error.assert_called_once()
        # Check that the error was logged with context
        args, _ = mock_logger.error.call_args
        assert 'context' in args[0]
        assert 'ValueError' in args[0]
        assert 'Test exception' in args[0]
    
    @patch('utils.logger.Logger')
    def test_get_default_logger(self, mock_logger_class):
        """Test get_default_logger function"""
        mock_logger_instance = MagicMock()
        mock_logger_class.return_value = mock_logger_instance
        mock_logger_instance.get_logger.return_value = 'test_logger'
        
        logger = get_default_logger('test_component')
        
        mock_logger_class.assert_called_once_with(log_name='test_component')
        mock_logger_instance.get_logger.assert_called_once()
        assert logger == 'test_logger'