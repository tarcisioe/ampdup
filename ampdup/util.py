'''Utility module.'''

import sys

from typing import Sequence


if sys.version_info < (3, 7):
    from aiocontext import async_contextmanager as asynccontextmanager
else:
    from contextlib import asynccontextmanager  # noqa # pylint: disable=no-name-in-module


__all__ = [
    'asynccontextmanager',
]


def has_any_prefix(s: str, prefixes: Sequence[str]) -> bool:
    '''Checks if a string has any of the provided prefixes.'''
    return any(s.startswith(prefix) for prefix in prefixes)
