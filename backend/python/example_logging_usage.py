#!/usr/bin/env python3
"""
Example script to demonstrate the new logging configuration.
Run this to test your logging setup in different environments.

Usage:
    # Development mode (default)
    python example_logging_usage.py
    
    # Production mode
    APP_ENV=production python example_logging_usage.py
    
    # Testing mode
    APP_ENV=testing python example_logging_usage.py
"""

import logging
import os
import sys

# Add the app directory to Python path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import configure_logging
from app.config import settings

def test_logging():
    """Test different logging levels"""
    
    # Configure logging based on environment
    configure_logging()
    
    # Get a logger for your application
    logger = logging.getLogger("app.example")
    
    print(f"Current environment: {settings.environment}")
    print(f"Is development: {settings.is_development}")
    print("Testing different log levels...\n")
    
    # Test different log levels
    logger.debug("This is a DEBUG message - only visible in development")
    logger.info("This is an INFO message - visible in development")
    logger.warning("This is a WARNING message - visible in all environments")
    logger.error("This is an ERROR message - visible in all environments and saved to file")
    logger.critical("This is a CRITICAL message - visible in all environments and saved to file")
    
    print("\nCheck the console output above and error.log file for results!")

if __name__ == "__main__":
    test_logging()
