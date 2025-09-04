#!/usr/bin/env python3
"""
Unit tests for email sender functionality

This module contains tests for the email sending capabilities,
including SMTP configuration, email formatting, attachment handling,
and error handling during the email sending process.
"""

import pytest
import os
import json
from unittest.mock import patch, mock_open, MagicMock, call
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Import test helpers
from test_helpers import generate_test_config, assert_dict_contains_subset

# Import the module to test
sys_path_setup = """
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
exec(sys_path_setup)

from core.email_sender import EmailSender

class TestEmailSender:
    @pytest.fixture
    def email_config(self):
        """
        Create a test email configuration
        
        Returns:
            dict: Email configuration dictionary
        """
        return {
            'smtp_server': 'smtp.example.com',
            'smtp_port': 587,
            'smtp_username': 'test@example.com',
            'smtp_password': 'test_password',
            'use_tls': True,
            'from_email': 'reports@example.com',
            'recipients': ['user1@example.com', 'user2@example.com'],
            'subject_template': 'Scraping Report: ${date}',
            'body_template': 'Please find attached the latest scraping report.'
        }
    
    @pytest.fixture
    def email_sender(self, email_config, mock_logger):
        """
        Create an email sender instance for testing
        
        Args:
            email_config: Test email configuration
            mock_logger: Mock logger fixture from conftest.py
            
        Returns:
            EmailSender: Configured email sender instance
        """
        config = generate_test_config()
        config['email'] = email_config
        return EmailSender(config, mock_logger)
    
    def test_init(self, email_sender, email_config):
        """
        Test email sender initialization
        
        Verifies that the email sender is properly initialized with
        the correct configuration and logger.
        """
        assert email_sender.config is not None
        assert email_sender.logger is not None
        assert email_sender.smtp_server == email_config['smtp_server']
        assert email_sender.smtp_port == email_config['smtp_port']
        assert email_sender.smtp_username == email_config['smtp_username']
        assert email_sender.smtp_password == email_config['smtp_password']
        assert email_sender.use_tls == email_config['use_tls']
        assert email_sender.from_email == email_config['from_email']
        assert email_sender.recipients == email_config['recipients']
    
    @patch('smtplib.SMTP')
    def test_send_email_success(self, mock_smtp, email_sender):
        """
        Test successful email sending
        
        Verifies that the email is properly formatted and sent via SMTP
        when all parameters are valid.
        """
        # Setup mock
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_smtp_instance
        
        # Test data
        subject = 'Test Subject'
        body = 'Test Body'
        attachments = []
        
        # Call the method
        result = email_sender.send_email(subject, body, attachments)
        
        # Verify SMTP was initialized correctly
        mock_smtp.assert_called_once_with(email_sender.smtp_server, email_sender.smtp_port)
        
        # Verify TLS was started
        mock_smtp_instance.starttls.assert_called_once()
        
        # Verify login was called
        mock_smtp_instance.login.assert_called_once_with(
            email_sender.smtp_username, email_sender.smtp_password
        )
        
        # Verify sendmail was called for each recipient
        assert mock_smtp_instance.sendmail.call_count == len(email_sender.recipients)
        
        # Verify result
        assert result is True
    
    @patch('smtplib.SMTP')
    def test_send_email_with_attachments(self, mock_smtp, email_sender, tmp_path):
        """
        Test email sending with attachments
        
        Verifies that attachments are properly added to the email
        and the email is sent correctly.
        """
        # Setup mock
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_smtp_instance
        
        # Create a test file
        test_file = tmp_path / "test_attachment.txt"
        test_file.write_text("This is a test attachment")
        
        # Test data
        subject = 'Test Subject with Attachment'
        body = 'Test Body with Attachment'
        attachments = [str(test_file)]
        
        # Call the method
        result = email_sender.send_email(subject, body, attachments)
        
        # Verify SMTP interactions
        mock_smtp.assert_called_once()
        mock_smtp_instance.sendmail.assert_called()
        
        # Verify result
        assert result is True
    
    @patch('smtplib.SMTP')
    def test_send_email_smtp_error(self, mock_smtp, email_sender):
        """
        Test email sending with SMTP error
        
        Verifies that the email sender handles SMTP errors gracefully
        and returns appropriate error status.
        """
        # Setup mock to raise exception
        mock_smtp.side_effect = smtplib.SMTPException("SMTP Error")
        
        # Test data
        subject = 'Test Subject'
        body = 'Test Body'
        attachments = []
        
        # Call the method
        result = email_sender.send_email(subject, body, attachments)
        
        # Verify result
        assert result is False
        
        # Verify logger was called with error
        email_sender.logger.error.assert_called()
    
    def test_format_subject(self, email_sender):
        """
        Test subject formatting
        
        Verifies that the subject template is correctly formatted
        with the provided data.
        """
        # Test data
        template = "Report for ${project} on ${date}"
        data = {"project": "Test Project", "date": "2023-01-01"}
        
        # Call the method
        result = email_sender.format_subject(template, data)
        
        # Verify result
        assert result == "Report for Test Project on 2023-01-01"
    
    def test_format_body(self, email_sender):
        """
        Test body formatting
        
        Verifies that the body template is correctly formatted
        with the provided data, including HTML formatting if applicable.
        """
        # Test data
        template = "<p>Hello ${name},</p><p>Here is your ${report_type} report.</p>"
        data = {"name": "John", "report_type": "weekly"}
        
        # Call the method
        result = email_sender.format_body(template, data)
        
        # Verify result
        assert result == "<p>Hello John,</p><p>Here is your weekly report.</p>"