"""
Memory Management Utilities

Provides tools for monitoring and optimizing memory usage.
"""
import gc
import logging
from typing import Dict
import psutil
import os

logger = logging.getLogger(__name__)


def get_memory_usage() -> Dict[str, float]:
    """
    Get current memory usage statistics.
    
    Returns:
        Dictionary with memory stats in MB
    """
    try:
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        return {
            "rss_mb": memory_info.rss / (1024 * 1024),  # Resident Set Size
            "vms_mb": memory_info.vms / (1024 * 1024),  # Virtual Memory Size
            "percent": process.memory_percent(),
            "available_mb": psutil.virtual_memory().available / (1024 * 1024)
        }
    except Exception as e:
        logger.error(f"Failed to get memory usage: {e}")
        return {}


def force_garbage_collection():
    """
    Force Python garbage collection to free memory.
    """
    try:
        collected = gc.collect()
        logger.info(f"Garbage collection freed {collected} objects")
        return collected
    except Exception as e:
        logger.error(f"Garbage collection failed: {e}")
        return 0


def check_memory_threshold(threshold_percent: float = 80.0) -> bool:
    """
    Check if memory usage exceeds threshold.
    
    Args:
        threshold_percent: Memory usage threshold (0-100)
    
    Returns:
        True if memory usage is below threshold
    """
    try:
        usage = get_memory_usage()
        current_percent = usage.get("percent", 0)
        
        if current_percent > threshold_percent:
            logger.warning(
                f"Memory usage high: {current_percent:.1f}% "
                f"(threshold: {threshold_percent}%)"
            )
            return False
        return True
    except Exception as e:
        logger.error(f"Memory check failed: {e}")
        return True


def cleanup_memory():
    """
    Perform memory cleanup operations.
    """
    try:
        before = get_memory_usage()
        logger.info(f"Memory before cleanup: {before.get('rss_mb', 0):.1f} MB")
        
        # Force garbage collection
        force_garbage_collection()
        
        # Get memory after cleanup
        after = get_memory_usage()
        freed = before.get('rss_mb', 0) - after.get('rss_mb', 0)
        
        logger.info(
            f"Memory after cleanup: {after.get('rss_mb', 0):.1f} MB "
            f"(freed: {freed:.1f} MB)"
        )
        
        return freed
    except Exception as e:
        logger.error(f"Memory cleanup failed: {e}")
        return 0


def log_memory_usage(context: str = ""):
    """
    Log current memory usage with context.
    
    Args:
        context: Description of current operation
    """
    try:
        usage = get_memory_usage()
        logger.info(
            f"Memory Usage {context}: "
            f"RSS={usage.get('rss_mb', 0):.1f} MB, "
            f"Percent={usage.get('percent', 0):.1f}%, "
            f"Available={usage.get('available_mb', 0):.1f} MB"
        )
    except Exception as e:
        logger.error(f"Failed to log memory usage: {e}")
