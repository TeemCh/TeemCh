"""
Logging utility for the content scraper
"""

import logging
import os
from datetime import datetime


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Create logs directory if it doesn't exist
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Set logging level
        logger.setLevel(logging.INFO)
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s - %(name)s - %(message)s'
        )
        
        # File handler
        log_filename = f"{log_dir}/scraper_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger


def setup_file_logging(log_level: str = "INFO", log_file: str = None):
    """
    Setup file logging for the entire application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Specific log file path (optional)
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Default log file
    if not log_file:
        log_file = f"{log_dir}/content_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Log the setup
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level {log_level}, output to {log_file}")


class ScrapeLogger:
    """Context manager for scraping session logging"""
    
    def __init__(self, session_name: str, platform: str):
        self.session_name = session_name
        self.platform = platform
        self.logger = get_logger(f"scraper.{platform}")
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"Starting scraping session: {self.session_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        if exc_type is None:
            self.logger.info(f"Scraping session completed successfully: {self.session_name} (Duration: {duration})")
        else:
            self.logger.error(f"Scraping session failed: {self.session_name} (Duration: {duration}) - Error: {exc_val}")
    
    def log_progress(self, message: str):
        """Log progress message"""
        self.logger.info(f"[{self.session_name}] {message}")
    
    def log_error(self, message: str, exception: Exception = None):
        """Log error message"""
        if exception:
            self.logger.error(f"[{self.session_name}] {message} - {str(exception)}")
        else:
            self.logger.error(f"[{self.session_name}] {message}")
    
    def log_warning(self, message: str):
        """Log warning message"""
        self.logger.warning(f"[{self.session_name}] {message}")