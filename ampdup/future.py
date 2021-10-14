"""Implementation of a loop-agnostic Future class."""

from dataclasses import dataclass, field
from typing import Generic, TypeVar, Union

from anyio import Event

from .maybe import Maybe, Nothing

T = TypeVar('T')


class FutureAlreadySetError(Exception):
    """Signal an attempt to set a Future twice."""


class FutureValueError(Exception):
    """Signal an attempt to set a Future to an unsupported value."""


@dataclass
class Future(Generic[T]):
    """A class wrapping a value that may not yet have been set."""

    _fulfilled: Event = field(default_factory=Event, init=False)
    _value: Maybe[Union[T, Exception]] = field(default=Nothing, init=False)

    def _check_already_set(self):
        if self._fulfilled.is_set():
            raise FutureAlreadySetError('Future cannot be reset.')

    def _set_value(self, value: Union[T, Exception]) -> None:
        self._check_already_set()
        self._value = value
        self._fulfilled.set()

    def set(self, value: T) -> None:
        """Set the value of the future to a success value.

        Args:
            value: The value to set the Future to. Cannot be an Exception.
        """
        if isinstance(value, Exception):
            raise FutureValueError(
                'Cannot set the value of a future to an Exception. Use .fail() instead.'
            )
        self._set_value(value)

    def fail(self, error: Exception) -> None:
        """Signal failure and cause calls to `get()` to raise.

        Args:
            error: The exception that should be raised when `get()` is called.
        """
        self._set_value(error)

    async def get(self) -> T:
        """Get the value from the future asynchronously.

        If the future was set by `fail()`, raises the exception.
        """
        await self._fulfilled.wait()
        assert self._value is not Nothing

        if isinstance(self._value, Exception):
            raise self._value

        return self._value
