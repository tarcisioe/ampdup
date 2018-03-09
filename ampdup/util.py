import sys

if sys.version_info < (3, 7):
    from aiocontext import async_contextmanager as asynccontextmanager
else:
    from contextlib import asynccontextmanager  # noqa # pylint: disable=no-name-in-module


__all__ = [
    'asynccontextmanager',
]
