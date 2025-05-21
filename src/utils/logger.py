"""
Logging utilities for the MATLAB AI Agent.

This module provides a configurable logging system with colored output
for the MATLAB AI Agent CLI.
"""

import os
import sys
import logging
from enum import Enum

import colorlog


class LogLevel(Enum):
    """Log levels enum for easier access."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    SUCCESS = 25  # Custom level between INFO and WARNING
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


# Register SUCCESS level
logging.addLevelName(LogLevel.SUCCESS.value, 'SUCCESS')


def success(self, message, *args, **kwargs):
    """Custom success level method for logger."""
    self._log(LogLevel.SUCCESS.value, message, args, **kwargs)


# Add success method to Logger class
logging.Logger.success = success


class MatlabAILogger:
    """Professional logger for MATLAB AI Agent with colored output."""

    def __init__(self, name="matlab_ai_agent", level=LogLevel.INFO.value):
        """
        Initialize the logger with appropriate handlers and formatters.

        Args:
            name: The name of the logger
            level: The logging level (default: INFO)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Clear existing handlers if present
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        # Create a colored console handler
        console_handler = colorlog.StreamHandler()
        console_handler.setLevel(level)

        # Create a colored formatter
        console_formatter = colorlog.ColoredFormatter(
            fmt=(
                '%(log_color)s%(asctime)s [%(levelname)8s] '
                '%(message)s%(reset)s'
            ),
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'blue',
                'SUCCESS': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red,bg_white',
            },
            secondary_log_colors={},
            style='%'
        )

        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # Create a file handler if log directory exists or can be created
        log_dir = os.path.join(os.getcwd(), "logs")
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
                self._add_file_handler(log_dir, name)
            except Exception:
                # Silently continue if log directory can't be created
                pass
        else:
            self._add_file_handler(log_dir, name)

    def _add_file_handler(self, log_dir, name):
        """Add a file handler for persistent logging."""
        file_handler = logging.FileHandler(
            os.path.join(log_dir, f"{name}.log")
        )
        file_handler.setLevel(LogLevel.DEBUG.value)
        file_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)8s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

    def debug(self, message, *args, **kwargs):
        """Log a debug message."""
        self.logger.debug(message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        """Log an info message."""
        self.logger.info(message, *args, **kwargs)

    def success(self, message, *args, **kwargs):
        """Log a success message."""
        self.logger.success(message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        """Log a warning message."""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        """Log an error message."""
        self.logger.error(message, *args, **kwargs)

    def critical(self, message, *args, **kwargs):
        """Log a critical message."""
        self.logger.critical(message, *args, **kwargs)

    def set_level(self, level):
        """Change the logging level dynamically."""
        if isinstance(level, LogLevel):
            level = level.value

        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            if isinstance(handler, colorlog.StreamHandler):
                handler.setLevel(level)


# Create a singleton instance for import
logger = MatlabAILogger()
