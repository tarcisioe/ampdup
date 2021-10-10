"""Utilities module for testing."""


def is_windows():
    """Check if python is running on Windows."""
    import sys

    return sys.platform == 'win32'


def is_asyncio():
    """Check if the current event loop is asyncio."""
    from sniffio import current_async_library

    return current_async_library() == 'asyncio'
