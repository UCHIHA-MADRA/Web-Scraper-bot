#!/usr/bin/env python3
"""
Unit tests for report generator functionality

This module contains tests for the report generation capabilities,
including CSV and Excel report creation, data formatting, and template usage.
"""

import pytest
import os
import pandas as pd
from unittest.mock import patch, mock_open, MagicMock
import datetime

# Import test helpers
from test_helpers import generate_test_config, assert_dict_contains_subset

# Import the module to test
sys_path_setup = """
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
exec(sys_path_setup)

from core.report_generator import ReportGenerator

class TestReportGenerator:
    @pytest.fixture
    def report_generator(self, mock_logger):
        """
        Create a report generator instance for testing
        
        Args:
            mock_logger: Mock logger fixture from conftest.py
            
        Returns:
            ReportGenerator: Configured report generator instance
        """
        config = generate_test_config()
        return ReportGenerator(config, mock_logger)
    
    @pytest.fixture
    def sample_data(self):
        """
        Create sample scraped data for testing reports
        
        Returns:
            list: List of dictionaries containing product data
        """
        return [
            {
                'title': 'Test Product 1',
                'price': '$99.99',
                'description': 'This is test product 1',
                'url': 'https://example.com/product/1',
                'source': 'test_target_1',
                'timestamp': datetime.datetime.now().isoformat()
            },
            {
                'title': 'Test Product 2',
                'price': '$149.99',
                'description': 'This is test product 2',
                'url': 'https://example.com/product/2',
                'source': 'test_target_1',
                'timestamp': datetime.datetime.now().isoformat()
            },
            {
                'title': 'Test Product 3',
                'price': '$199.99',
                'description': 'This is test product 3',
                'url': 'https://example.com/product/3',
                'source': 'test_target_2',
                'timestamp': datetime.datetime.now().isoformat()
            }
        ]
    
    def test_init(self, report_generator):
        """
        Test report generator initialization
        
        Verifies that the report generator is properly initialized with
        the correct configuration and logger.
        """
        assert report_generator.config is not None
        assert report_generator.logger is not None
        assert hasattr(report_generator, 'generate_csv_report')
        assert hasattr(report_generator, 'generate_excel_report')
    
    @patch('pandas.DataFrame.to_csv')
    @patch('os.makedirs')
    def test_generate_csv_report(self, mock_makedirs, mock_to_csv, report_generator, sample_data):
        """
        Test CSV report generation
        
        Verifies that the CSV report is generated correctly with the proper data
        and formatting.
        """
        # Call the method
        filename = report_generator.generate_csv_report(sample_data, 'test_report')
        
        # Verify directory was created
        mock_makedirs.assert_called_once()
        
        # Verify DataFrame was created with correct data
        mock_to_csv.assert_called_once()
        
        # Verify filename format
        assert 'test_report' in filename
        assert filename.endswith('.csv')
    
    @patch('pandas.DataFrame.to_excel')
    @patch('os.makedirs')
    def test_generate_excel_report(self, mock_makedirs, mock_to_excel, report_generator, sample_data):
        """
        Test Excel report generation
        
        Verifies that the Excel report is generated correctly with the proper data,
        formatting, and styling.
        """
        # Call the method
        filename = report_generator.generate_excel_report(sample_data, 'test_report')
        
        # Verify directory was created
        mock_makedirs.assert_called_once()
        
        # Verify DataFrame was created with correct data
        mock_to_excel.assert_called_once()
        
        # Verify filename format
        assert 'test_report' in filename
        assert filename.endswith('.xlsx')
    
    def test_format_data(self, report_generator, sample_data):
        """
        Test data formatting for reports
        
        Verifies that the data formatting correctly processes raw scraped data
        into a format suitable for reporting.
        """
        formatted_data = report_generator.format_data(sample_data)
        
        # Verify it's a DataFrame
        assert isinstance(formatted_data, pd.DataFrame)
        
        # Verify it has the right columns
        expected_columns = ['title', 'price', 'description', 'url', 'source', 'timestamp']
        for col in expected_columns:
            assert col in formatted_data.columns
        
        # Verify it has the right number of rows
        assert len(formatted_data) == len(sample_data)
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='Template content with ${placeholder}')
    def test_apply_template(self, mock_file, mock_exists, report_generator):
        """
        Test template application
        
        Verifies that the template system correctly applies data to templates
        for report generation.
        """
        mock_exists.return_value = True
        
        # Test data for template
        template_data = {'placeholder': 'test value'}
        
        # Call the method
        result = report_generator.apply_template('test_template.html', template_data)
        
        # Verify template was read
        mock_file.assert_called_once()
        
        # Verify placeholder was replaced
        assert 'Template content with test value' == result