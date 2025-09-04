#!/usr/bin/env python3
"""
Monitoring and analytics module for web scraping bot

This module provides monitoring capabilities for the web scraping bot,
including performance metrics, business metrics, and system metrics.
It supports multiple exporters for metrics, including Prometheus and StatsD.

Features:
- Performance metrics tracking (scraping duration, parsing time, etc.)
- Business metrics tracking (products scraped, price changes, etc.)
- System metrics tracking (CPU, memory, disk usage, etc.)
- Multiple exporters (Prometheus, StatsD, etc.)
- Health check endpoints
- Custom metrics registration

Usage:
    from utils.monitoring import get_default_monitor
    
    # Get the default monitor
    monitor = get_default_monitor()
    
    # Track performance metrics
    with monitor.track_duration('scraping_duration_seconds', labels={'target': 'example.com'}):
        # Scraping code here
        pass
    
    # Increment business metrics
    monitor.increment('products_scraped_count', labels={'target': 'example.com'})
    
    # Set gauge metrics
    monitor.set_gauge('cache_hit_ratio', 0.75, labels={'cache_type': 'memory'})
"""

import time
import os
import socket
import threading
import yaml
import json
import psutil
from contextlib import contextmanager
from typing import Dict, List, Optional, Any, Union, Callable

class Metric:
    """
    Base class for all metrics
    
    Attributes:
        name (str): Name of the metric
        description (str): Description of the metric
        labels (dict): Labels for the metric
        value (Any): Current value of the metric
    """
    def __init__(self, name: str, description: str = "", labels: Dict[str, str] = None):
        self.name = name
        self.description = description
        self.labels = labels or {}
        self.value = None

class Counter(Metric):
    """
    Counter metric that can only increase
    
    Attributes:
        value (float): Current value of the counter
    """
    def __init__(self, name: str, description: str = "", labels: Dict[str, str] = None):
        super().__init__(name, description, labels)
        self.value = 0.0
    
    def increment(self, value: float = 1.0):
        """
        Increment the counter by the given value
        
        Args:
            value (float): Value to increment by (default: 1.0)
        """
        self.value += value

class Gauge(Metric):
    """
    Gauge metric that can go up and down
    
    Attributes:
        value (float): Current value of the gauge
    """
    def __init__(self, name: str, description: str = "", labels: Dict[str, str] = None):
        super().__init__(name, description, labels)
        self.value = 0.0
    
    def set(self, value: float):
        """
        Set the gauge to the given value
        
        Args:
            value (float): Value to set
        """
        self.value = value
    
    def increment(self, value: float = 1.0):
        """
        Increment the gauge by the given value
        
        Args:
            value (float): Value to increment by (default: 1.0)
        """
        self.value += value
    
    def decrement(self, value: float = 1.0):
        """
        Decrement the gauge by the given value
        
        Args:
            value (float): Value to decrement by (default: 1.0)
        """
        self.value -= value

class Histogram(Metric):
    """
    Histogram metric for measuring distributions
    
    Attributes:
        buckets (List[float]): Histogram buckets
        values (List[float]): Values recorded in the histogram
    """
    def __init__(self, name: str, description: str = "", labels: Dict[str, str] = None, 
                 buckets: List[float] = None):
        super().__init__(name, description, labels)
        self.buckets = buckets or [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
        self.values = []
    
    def observe(self, value: float):
        """
        Record a value in the histogram
        
        Args:
            value (float): Value to record
        """
        self.values.append(value)

class Monitor:
    """
    Main monitoring class for tracking metrics
    
    Attributes:
        metrics (Dict[str, Metric]): Dictionary of registered metrics
        config (Dict): Monitoring configuration
        logger: Logger instance
        exporters (List): List of metric exporters
    """
    def __init__(self, config: Dict = None, logger = None):
        """
        Initialize the monitor
        
        Args:
            config (Dict): Monitoring configuration
            logger: Logger instance
        """
        self.metrics = {}
        self.config = config or {}
        self.logger = logger
        self.exporters = []
        self.lock = threading.RLock()
        
        # Initialize system metrics collection if enabled
        if self.config.get('system_metrics', {}).get('enabled', True):
            self._init_system_metrics()
    
    def _init_system_metrics(self):
        """
        Initialize system metrics collection
        """
        # Register system metrics
        self.register_gauge('cpu_usage_percent', 'CPU usage percentage')
        self.register_gauge('memory_usage_bytes', 'Memory usage in bytes')
        self.register_gauge('memory_total_bytes', 'Total memory in bytes')
        self.register_gauge('disk_usage_percent', 'Disk usage percentage')
        self.register_counter('network_received_bytes', 'Network bytes received')
        self.register_counter('network_sent_bytes', 'Network bytes sent')
        
        # Start system metrics collection thread
        thread = threading.Thread(target=self._collect_system_metrics, daemon=True)
        thread.start()
    
    def _collect_system_metrics(self):
        """
        Collect system metrics periodically
        """
        interval = self.config.get('metrics', {}).get('collection_interval_seconds', 15)
        
        # Get initial network counters
        net_io_counters = psutil.net_io_counters()
        prev_bytes_recv = net_io_counters.bytes_recv
        prev_bytes_sent = net_io_counters.bytes_sent
        
        while True:
            try:
                # CPU usage
                self.set_gauge('cpu_usage_percent', psutil.cpu_percent())
                
                # Memory usage
                memory = psutil.virtual_memory()
                self.set_gauge('memory_usage_bytes', memory.used)
                self.set_gauge('memory_total_bytes', memory.total)
                
                # Disk usage
                disk = psutil.disk_usage('/')
                self.set_gauge('disk_usage_percent', disk.percent)
                
                # Network usage
                net_io_counters = psutil.net_io_counters()
                bytes_recv = net_io_counters.bytes_recv
                bytes_sent = net_io_counters.bytes_sent
                
                # Increment network counters by the difference
                self.increment('network_received_bytes', bytes_recv - prev_bytes_recv)
                self.increment('network_sent_bytes', bytes_sent - prev_bytes_sent)
                
                # Update previous values
                prev_bytes_recv = bytes_recv
                prev_bytes_sent = bytes_sent
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error collecting system metrics: {e}")
            
            # Sleep for the configured interval
            time.sleep(interval)
    
    def register_counter(self, name: str, description: str = "", labels: Dict[str, str] = None) -> Counter:
        """
        Register a counter metric
        
        Args:
            name (str): Name of the metric
            description (str): Description of the metric
            labels (Dict[str, str]): Labels for the metric
            
        Returns:
            Counter: The registered counter
        """
        with self.lock:
            metric = Counter(name, description, labels)
            self.metrics[self._get_metric_key(name, labels)] = metric
            return metric
    
    def register_gauge(self, name: str, description: str = "", labels: Dict[str, str] = None) -> Gauge:
        """
        Register a gauge metric
        
        Args:
            name (str): Name of the metric
            description (str): Description of the metric
            labels (Dict[str, str]): Labels for the metric
            
        Returns:
            Gauge: The registered gauge
        """
        with self.lock:
            metric = Gauge(name, description, labels)
            self.metrics[self._get_metric_key(name, labels)] = metric
            return metric
    
    def register_histogram(self, name: str, description: str = "", labels: Dict[str, str] = None,
                          buckets: List[float] = None) -> Histogram:
        """
        Register a histogram metric
        
        Args:
            name (str): Name of the metric
            description (str): Description of the metric
            labels (Dict[str, str]): Labels for the metric
            buckets (List[float]): Histogram buckets
            
        Returns:
            Histogram: The registered histogram
        """
        with self.lock:
            metric = Histogram(name, description, labels, buckets)
            self.metrics[self._get_metric_key(name, labels)] = metric
            return metric
    
    def _get_metric_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """
        Get a unique key for a metric based on its name and labels
        
        Args:
            name (str): Name of the metric
            labels (Dict[str, str]): Labels for the metric
            
        Returns:
            str: Unique key for the metric
        """
        if not labels:
            return name
        
        # Sort labels by key to ensure consistent key generation
        sorted_labels = sorted(labels.items())
        labels_str = ','.join(f"{k}={v}" for k, v in sorted_labels)
        return f"{name}{{{labels_str}}}"
    
    def get_or_register_counter(self, name: str, description: str = "", 
                              labels: Dict[str, str] = None) -> Counter:
        """
        Get an existing counter or register a new one
        
        Args:
            name (str): Name of the metric
            description (str): Description of the metric
            labels (Dict[str, str]): Labels for the metric
            
        Returns:
            Counter: The counter
        """
        key = self._get_metric_key(name, labels)
        with self.lock:
            if key in self.metrics:
                return self.metrics[key]
            return self.register_counter(name, description, labels)
    
    def get_or_register_gauge(self, name: str, description: str = "", 
                            labels: Dict[str, str] = None) -> Gauge:
        """
        Get an existing gauge or register a new one
        
        Args:
            name (str): Name of the metric
            description (str): Description of the metric
            labels (Dict[str, str]): Labels for the metric
            
        Returns:
            Gauge: The gauge
        """
        key = self._get_metric_key(name, labels)
        with self.lock:
            if key in self.metrics:
                return self.metrics[key]
            return self.register_gauge(name, description, labels)
    
    def get_or_register_histogram(self, name: str, description: str = "", 
                                labels: Dict[str, str] = None,
                                buckets: List[float] = None) -> Histogram:
        """
        Get an existing histogram or register a new one
        
        Args:
            name (str): Name of the metric
            description (str): Description of the metric
            labels (Dict[str, str]): Labels for the metric
            buckets (List[float]): Histogram buckets
            
        Returns:
            Histogram: The histogram
        """
        key = self._get_metric_key(name, labels)
        with self.lock:
            if key in self.metrics:
                return self.metrics[key]
            return self.register_histogram(name, description, labels, buckets)
    
    def increment(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """
        Increment a counter
        
        Args:
            name (str): Name of the counter
            value (float): Value to increment by
            labels (Dict[str, str]): Labels for the counter
        """
        counter = self.get_or_register_counter(name, labels=labels)
        counter.increment(value)
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """
        Set a gauge value
        
        Args:
            name (str): Name of the gauge
            value (float): Value to set
            labels (Dict[str, str]): Labels for the gauge
        """
        gauge = self.get_or_register_gauge(name, labels=labels)
        gauge.set(value)
    
    def observe(self, name: str, value: float, labels: Dict[str, str] = None):
        """
        Observe a value in a histogram
        
        Args:
            name (str): Name of the histogram
            value (float): Value to observe
            labels (Dict[str, str]): Labels for the histogram
        """
        histogram = self.get_or_register_histogram(name, labels=labels)
        histogram.observe(value)
    
    @contextmanager
    def track_duration(self, name: str, labels: Dict[str, str] = None):
        """
        Track the duration of a block of code
        
        Args:
            name (str): Name of the histogram to record the duration in
            labels (Dict[str, str]): Labels for the histogram
            
        Yields:
            None
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.observe(name, duration, labels)
    
    def get_metrics(self) -> Dict[str, Metric]:
        """
        Get all registered metrics
        
        Returns:
            Dict[str, Metric]: Dictionary of all registered metrics
        """
        with self.lock:
            return self.metrics.copy()

def get_default_monitor(config_path: str = None, logger = None) -> Monitor:
    """
    Get the default monitor instance
    
    Args:
        config_path (str): Path to the monitoring configuration file
        logger: Logger instance
        
    Returns:
        Monitor: The default monitor instance
    """
    # Load configuration
    config = {}
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            if logger:
                logger.error(f"Error loading monitoring configuration: {e}")
    
    # Create and return monitor
    return Monitor(config, logger)