#!/usr/bin/env python3
"""
Metrics server for exposing monitoring metrics

This module provides a simple HTTP server for exposing monitoring metrics
to Prometheus. It uses the monitoring module to collect metrics and
exposes them via an HTTP endpoint.

Usage:
    from utils.metrics_server import start_metrics_server
    
    # Start the metrics server in a background thread
    start_metrics_server(port=8000)
"""

import threading
import time
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional

from utils.monitoring import get_default_monitor

class MetricsHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for metrics endpoint
    """
    def do_GET(self):
        """
        Handle GET requests
        """
        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(self._get_metrics().encode('utf-8'))
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def _get_metrics(self) -> str:
        """
        Get metrics in Prometheus format
        
        Returns:
            str: Metrics in Prometheus format
        """
        monitor = get_default_monitor()
        metrics = monitor.get_metrics()
        
        output = []
        
        for key, metric in metrics.items():
            # Extract metric name (without labels)
            metric_name = metric.name
            
            # Add metric help comment
            if metric.description:
                output.append(f"# HELP {metric_name} {metric.description}")
            
            # Add metric type comment
            if isinstance(metric, type(monitor).Counter):
                output.append(f"# TYPE {metric_name} counter")
            elif isinstance(metric, type(monitor).Gauge):
                output.append(f"# TYPE {metric_name} gauge")
            elif isinstance(metric, type(monitor).Histogram):
                output.append(f"# TYPE {metric_name} histogram")
            
            # Add metric value
            if metric.labels:
                labels_str = ','.join([f'{k}="{v}"' for k, v in metric.labels.items()])
                output.append(f"{metric_name}{{{labels_str}}} {metric.value}")
            else:
                output.append(f"{metric_name} {metric.value}")
        
        return '\n'.join(output)
    
    def log_message(self, format, *args):
        """
        Suppress logging
        """
        return

def start_metrics_server(host: str = '0.0.0.0', port: int = 8000) -> threading.Thread:
    """
    Start the metrics server in a background thread
    
    Args:
        host (str): Host to bind to
        port (int): Port to bind to
        
    Returns:
        threading.Thread: The server thread
    """
    server = HTTPServer((host, port), MetricsHandler)
    
    def run_server():
        server.serve_forever()
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    
    return thread