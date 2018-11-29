'''Classes for raising when errors happen.'''
from enum import Enum
from typing import Callable, Dict, List

from dataclasses import dataclass


__all__ = [
    'MPDError',
    'ConnectionFailedError',
    'ClientTypeError',
    'NoCurrentSongError',
    'CommandError',
    'URINotFoundError',
]


class ErrorCode(Enum):
    '''MPD Error codes included in ACK responses.'''
    NOT_LIST = 1
    ARG = 2
    PASSWORD = 3
    PERMISSION = 4
    UNKNOWN = 5

    NO_EXIST = 50
    PLAYLIST_MAX = 51
    SYSTEM = 52
    PLAYLIST_LOAD = 53
    UPDATE_ALREADY = 54
    PLAYER_SYNC = 55
    EXIST = 56


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
    code: ErrorCode
    line: int
    command: str
    message: str
    partial: List[str]

    def __post_init__(self):
        codetext = f'{self.code.name}/{self.code.value}'
        super().__init__(
            f'[{codetext}@{self.line}] {{{self.command}}} {self.message}'
        )


class URINotFoundError(CommandError):
    '''Wraps an error 50 from MPD.'''
    def __init__(self, *args):
        super().__init__(ErrorCode.NO_EXIST, *args)


ErrorFactory = Callable[[int, str, str, List[str]], CommandError]


ERRORS: Dict[ErrorCode, ErrorFactory] = {
    ErrorCode.NO_EXIST: URINotFoundError,
}


def get_error_constructor(error_code: ErrorCode) -> ErrorFactory:
    '''Get the error constructor for an error code, or a generic one.

    If the error code is not mapped to an exception type, a factory function
    for CommandError with the correct code is returned.

    Args:
        error_code: The error code from MPD.

    Returns:
        A function that constructs the correct exception with the remaining
        arguments.
    '''
    return (ERRORS.get(error_code) or
            (lambda *args: CommandError(error_code, *args)))
