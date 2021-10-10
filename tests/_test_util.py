"""Utilities module for testing."""


def is_windows():
    """Check if python is running on Windows."""
    import sys

    return sys.platform == 'win32'
