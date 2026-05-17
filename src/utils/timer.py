"""
Simple timer utility for tracking execution time.
"""

import time
from contextlib import contextmanager
from src.utils.logger import get_logger

logger = get_logger("timer")


class Timer:
    """
    Context manager and decorator for timing code blocks.
    
    Usage:
        # As context manager
        with Timer("Data collection"):
            collect_data()
        
        # As decorator
        @Timer.decorator("API Call")
        def fetch_data():
            ...
    """

    def __init__(self, description: str = "Operation"):
        self.description = description
        self.start_time = None
        self.end_time = None
        self.elapsed = None

    def __enter__(self):
        self.start_time = time.time()
        logger.info(f"⏱️  Started: {self.description}")
        return self

    def __exit__(self, *args):
        self.end_time = time.time()
        self.elapsed = self.end_time - self.start_time
        logger.info(f"✅ Finished: {self.description} [{self._format_time()}]")

    def _format_time(self) -> str:
        if self.elapsed < 60:
            return f"{self.elapsed:.2f}s"
        elif self.elapsed < 3600:
            mins = int(self.elapsed // 60)
            secs = self.elapsed % 60
            return f"{mins}m {secs:.1f}s"
        else:
            hours = int(self.elapsed // 3600)
            mins = int((self.elapsed % 3600) // 60)
            return f"{hours}h {mins}m"

    @staticmethod
    def decorator(description: str):
        def wrapper(func):
            def inner(*args, **kwargs):
                with Timer(description):
                    return func(*args, **kwargs)
            return inner
        return wrapper