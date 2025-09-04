#!/usr/bin/env python3
"""
Email sender module with enhanced error handling and logging
"""
import os
import smtplib
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
import ssl

# Import custom modules
from utils.logger import get_default_logger
from utils.exceptions import EmailError

class EmailSender:
    """
    Email sender class with enhanced error handling and logging
    """
    def __init__(self, config=None):
        """
        Initialize the email sender
        
        Args:
            config (dict, optional): Email configuration
        """
        self.config = config or {}
        self.logger = get_default_logger('email_sender')
        
        # Load email templates if available
        self.templates_path = self.config.get('templates_path', 'config/email_templates.json')
        self.templates = self._load_templates()
        
        # Set up email configuration
        self.smtp_server = self.config.get('smtp_server')
        self.smtp_port = self.config.get('smtp_port')
        self.username = self.config.get('username')
        self.password = self.config.get('password')
        self.use_tls = self.config.get('use_tls', True)
        self.use_ssl = self.config.get('use_ssl', False)
        self.default_sender = self.config.get('default_sender')
        
        # Validate configuration
        if self.smtp_server and self.smtp_port and self.username and self.password:
            self.logger.info(f"Email sender initialized with server {self.smtp_server}:{self.smtp_port}")
        else:
            self.logger.warning("Email sender initialized with incomplete configuration")
    
    def _load_templates(self):
        """
        Load email templates from JSON file
        
        Returns:
            dict: Email templates
        """
        templates = {}
        try:
            if os.path.exists(self.templates_path):
                with open(self.templates_path, 'r') as f:
                    templates = json.load(f)
                self.logger.info(f"Loaded {len(templates)} email templates from {self.templates_path}")
            else:
                self.logger.warning(f"Email templates file not found: {self.templates_path}")
        except Exception as e:
            self.logger.error(f"Error loading email templates: {e}")
        
        return templates
    
    def send_email(self, recipients, subject=None, body=None, attachments=None, template_name=None, template_vars=None):
        """
        Send email with attachments
        
        Args:
            recipients (str or list): Email recipient(s)
            subject (str, optional): Email subject
            body (str, optional): Email body
            attachments (list, optional): List of file paths to attach
            template_name (str, optional): Name of template to use
            template_vars (dict, optional): Variables to substitute in template
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.smtp_server or not self.smtp_port or not self.username or not self.password:
            error_msg = "Email configuration is incomplete"
            self.logger.error(error_msg)
            raise EmailError(error_msg)
        
        try:
            # Convert single recipient to list
            if isinstance(recipients, str):
                recipients = [recipients]
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.default_sender or self.username
            msg['To'] = ', '.join(recipients)
            
            # Set subject with date if not provided
            if not subject:
                subject = f"Web Scraping Report - {datetime.now().strftime('%Y-%m-%d')}"
            msg['Subject'] = subject
            
            # Use template if specified
            if template_name and template_name in self.templates:
                template = self.templates[template_name]
                template_body = template.get('body', '')
                
                # Apply template variables
                if template_vars:
                    for key, value in template_vars.items():
                        placeholder = f"{{{{{key}}}}}"
                        template_body = template_body.replace(placeholder, str(value))
                
                body = template_body
                
                # Use template subject if not explicitly provided
                if not subject and 'subject' in template:
                    msg['Subject'] = template['subject']
            
            # Add body
            if body:
                msg.attach(MIMEText(body, 'html' if '<html>' in body.lower() else 'plain'))
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)
            
            # Connect to server and send email
            self._send_message(msg, recipients)
            
            self.logger.info(f"Email sent successfully to {len(recipients)} recipient(s)")
            return True
            
        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            self.logger.error(error_msg)
            raise EmailError(error_msg, details={'recipients': recipients, 'subject': subject})
    
    def _add_attachment(self, msg, filepath):
        """
        Add attachment to email message
        
        Args:
            msg (MIMEMultipart): Email message
            filepath (str): Path to file
        """
        try:
            if not os.path.exists(filepath):
                self.logger.warning(f"Attachment not found: {filepath}")
                return
            
            with open(filepath, 'rb') as f:
                attachment = MIMEApplication(f.read())
            
            # Set attachment filename
            filename = os.path.basename(filepath)
            attachment.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(attachment)
            
            self.logger.debug(f"Added attachment: {filename}")
        except Exception as e:
            self.logger.warning(f"Failed to add attachment {filepath}: {e}")
    
    def _send_message(self, msg, recipients):
        """
        Send email message via SMTP
        
        Args:
            msg (MIMEMultipart): Email message
            recipients (list): List of recipients
        """
        server = None
        try:
            # Create server connection
            if self.use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                
                # Use TLS if specified
                if self.use_tls:
                    server.starttls()
            
            # Login
            server.login(self.username, self.password)
            
            # Send email
            server.sendmail(msg['From'], recipients, msg.as_string())
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP authentication failed: {str(e)}"
            self.logger.error(error_msg)
            raise EmailError(error_msg, details={'smtp_server': self.smtp_server})
        
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {str(e)}"
            self.logger.error(error_msg)
            raise EmailError(error_msg)
        
        except Exception as e:
            error_msg = f"Error sending email: {str(e)}"
            self.logger.error(error_msg)
            raise EmailError(error_msg)
        
        finally:
            # Close connection
            if server:
                try:
                    server.quit()
                except Exception as e:
                    self.logger.warning(f"Error closing SMTP connection: {e}")
    
    def send_report_email(self, report_path, recipients, subject=None, body=None):
        """
        Send report email with attachment
        
        Args:
            report_path (str): Path to report file
            recipients (str or list): Email recipient(s)
            subject (str, optional): Email subject
            body (str, optional): Email body
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Generate default subject and body if not provided
            if not subject:
                subject = f"Web Scraping Report - {datetime.now().strftime('%Y-%m-%d')}"
            
            if not body:
                body = f"Please find attached the web scraping report for {datetime.now().strftime('%Y-%m-%d')}."
            
            # Send email with report attachment
            return self.send_email(
                recipients=recipients,
                subject=subject,
                body=body,
                attachments=[report_path]
            )
        except Exception as e:
            error_msg = f"Failed to send report email: {str(e)}"
            self.logger.error(error_msg)
            raise EmailError(error_msg, details={'report_path': report_path, 'recipients': recipients})
    
    def test_connection(self):
        """
        Test SMTP connection
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        server = None
        try:
            self.logger.info(f"Testing connection to {self.smtp_server}:{self.smtp_port}")
            
            # Create server connection
            if self.use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                
                # Use TLS if specified
                if self.use_tls:
                    server.starttls()
            
            # Login
            server.login(self.username, self.password)
            
            self.logger.info("SMTP connection test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"SMTP connection test failed: {e}")
            return False
            
        finally:
            # Close connection
            if server:
                try:
                    server.quit()
                except:
                    pass
