'''Classes for raising when errors happen.'''
from typing import List

from dataclasses import dataclass


__all__ = [
    'MPDError',
    'ConnectionFailedError',
    'ClientTypeError',
    'CommandError',
    'NoCurrentSongError',
]


class MPDError(Exception):
    '''Base class for errors raised by this library.'''


class ConnectionFailedError(MPDError):
    '''Caused when a client fails to connect.'''


class ClientTypeError(MPDError):
    '''Caused when trying to use the wrong type of client for an operation.

    Example: using the idle client for playback control and vice-versa.
    '''


class NoCurrentSongError(MPDError):
    '''Caused where there is no current song playing and one is expected.'''
    pass


@dataclass
class CommandError(MPDError):
    '''Wraps an error from MPD (an ACK response with error code and reason).

    Members:
        code: The MPD error code.
        line: Which line in a command list caused the error.
        command: The command that caused the error.
        message: The error message provided by MPD, unchanged.
        partial: The (maybe empty) list of lines representing a partial
                 response.
    '''
    code: int
    line: int
    command: str
    message: str
    partial: List[str]

    def __post_init__(self):
        super().__init__(
            f'[{self.code}@{self.line}] {{{self.command}}} {self.message}'
        )
