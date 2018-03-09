from typing import List

from dataclasses import dataclass


__all__ = [
    'ConnectionFailedError',
    'ClientTypeError',
    'CommandError',
]


class ConnectionFailedError(Exception):
    pass


class ClientTypeError(Exception):
    pass


@dataclass
class CommandError(Exception):
    code: int
    line: int
    command: str
    message: str
    partial: List[str]

    def __post_init__(self):
        super().__init__(
            f'[{self.code}@{self.line}] {{{self.command}}} {self.message}'
        )
