"""
Logging configuration module for LLM service.
Supports logging to both console and log files in logs/ directory.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Optional
from datetime import datetime


def setup_logger(
    name: str = "llm-service",
    log_dir: Optional[str] = None,
    level: int = logging.INFO,
    console_level: Optional[int] = None,
    file_level: Optional[int] = None,
    log_format: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    when: str = "midnight",
    interval: int = 1,
    use_timed_rotation: bool = True,
    encoding: str = "utf-8"
) -> logging.Logger:
    """
    Setup logger with console and file handlers.
    
    Args:
        name: Logger name (default: "llm-service")
        log_dir: Directory for log files (default: "logs" in current directory)
        level: Default logging level (default: logging.INFO)
        console_level: Console logging level (default: same as level)
        file_level: File logging level (default: same as level)
        log_format: Custom log format string
        max_bytes: Maximum size of log file before rotation (for RotatingFileHandler)
        backup_count: Number of backup files to keep
        when: When to rotate (for TimedRotatingFileHandler): 'S', 'M', 'H', 'D', 'W0'-'W6', 'midnight'
        interval: Interval for rotation
        use_timed_rotation: Use TimedRotatingFileHandler instead of RotatingFileHandler
        encoding: File encoding (default: utf-8)
    
    Returns:
        Configured logger instance
    """
    # Get or create logger
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Set logger level
    logger.setLevel(level)
    
    # Default log format
    if log_format is None:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    
    formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')
    
    # Console handler
    console_level = console_level or level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    file_level = file_level or level
    
    # Determine log directory
    if log_dir is None:
        # Use logs/ directory relative to current file
        current_dir = Path(__file__).parent
        log_dir = current_dir / "logs"
    else:
        log_dir = Path(log_dir)
    
    # Create log directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Log file path
    log_file = log_dir / f"{name}.log"
    
    # Create file handler with rotation
    if use_timed_rotation:
        # Rotate by time (daily by default)
        file_handler = TimedRotatingFileHandler(
            filename=str(log_file),
            when=when,
            interval=interval,
            backupCount=backup_count,
            encoding=encoding
        )
    else:
        # Rotate by size
        file_handler = RotatingFileHandler(
            filename=str(log_file),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=encoding
        )
    
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Log initialization message
    logger.info(f"Logger '{name}' initialized")
    logger.info(f"Console logging level: {logging.getLevelName(console_level)}")
    logger.info(f"File logging level: {logging.getLevelName(file_level)}")
    logger.info(f"Log file: {log_file}")
    
    return logger


def get_logger(
    name: str = "llm-service",
    log_dir: Optional[str] = None,
    level: Optional[str] = None,
    **kwargs
) -> logging.Logger:
    """
    Convenience function to get or create a logger.
    
    Args:
        name: Logger name
        log_dir: Directory for log files
        level: Logging level as string ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        **kwargs: Additional arguments passed to setup_logger
    
    Returns:
        Logger instance
    """
    # Convert string level to logging constant
    if level:
        level = getattr(logging, level.upper(), logging.INFO)
    else:
        level = logging.INFO
    
    # Check if logger already exists
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    # Setup new logger
    return setup_logger(name=name, log_dir=log_dir, level=level, **kwargs)


# Default logger instance - automatically initialized on import
_default_logger = None


def get_default_logger() -> logging.Logger:
    """Get or create the default logger instance."""
    global _default_logger
    if _default_logger is None:
        _default_logger = setup_logger()
    return _default_logger


# Automatically setup default logger on module import
_default_logger = setup_logger()

# Export commonly used functions and default logger
__all__ = ['setup_logger', 'get_logger', 'get_default_logger', 'logger']

# Export default logger instance for convenience
logger = _default_logger

