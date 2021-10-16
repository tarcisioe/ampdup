"""Implementation of a loop-agnostic Future class."""

from dataclasses import dataclass, field
from typing import Generic, Protocol, TypeVar

from anyio import Event

T = TypeVar('T')


class FutureAlreadySetError(Exception):
    """Signal an attempt to set a Future twice."""


class FutureValueError(Exception):
    """Signal an attempt to set a Future to an unsupported value."""


class PendingFutureError(Exception):
    """Signal an attempt to get directly from a pending future."""


@dataclass(frozen=True)
class StateChange(Generic[T]):
    """Information generated when a future changes state."""

    next_state: 'FutureState[T]'
    event: Event


class FutureState(Generic[T], Protocol):
    """The internal state of a Future."""

    def set(self, value: T) -> StateChange[T]:
        """Produce a new state when the future is set from this given state.

        When the state changes, an event must be provided to signal tasks that are
        waiting for the future to be set.
        """
        ...

    def fail(self, error: Exception) -> StateChange[T]:
        """Produce a new state when the future is failed from this given state."""
        ...

    async def wait_fulfilled(self) -> None:
        """Wait until the future is fulfilled."""
        ...

    def get(self) -> T:
        """Get the value of the future if available in the state."""
        ...


@dataclass(frozen=True)
class BaseSetFuture(Generic[T]):
    """Base for a future state that has something set."""

    @staticmethod
    def set(value: T) -> StateChange[T]:
        """Fails since in this state the future is already set."""
        raise FutureAlreadySetError('Future cannot be reset.')

    @staticmethod
    def fail(error: Exception) -> StateChange[T]:
        """Fails since in this state the future is already set."""
        raise FutureAlreadySetError('Future cannot be reset.')

    @staticmethod
    async def wait_fulfilled() -> None:
        """There is nothing to wait since the future is already set."""


@dataclass(frozen=True)
class SuccessfulFuture(BaseSetFuture[T]):
    """The state of a successful Future (a value has been set)."""

    value: T

    def get(self) -> T:
        """Return the set value."""
        return self.value


@dataclass(frozen=True)
class FailedFuture(BaseSetFuture[T]):
    """The state of a failed Future (an Exception has been set)."""

    error: Exception

    def get(self) -> T:
        """Raise the set error."""
        raise self.error


@dataclass(frozen=True)
class PendingFuture(Generic[T]):
    """The state of a pending Future."""

    _fulfilled: Event = field(default_factory=Event, init=False)

    def set(self, value: T) -> StateChange[T]:
        """Produce a new SuccessFuture state with the given value."""
        return StateChange(SuccessfulFuture(value), self._fulfilled)

    def fail(self, error: Exception) -> StateChange[T]:
        """Produce a new FailedFuture state with the given error."""
        return StateChange(FailedFuture(error), self._fulfilled)

    async def wait_fulfilled(self) -> None:
        """Wait until the future is fulfilled (goes through a state change)."""
        await self._fulfilled.wait()

    @staticmethod
    def get() -> T:  # pragma: no cover
        """Fail since the future is still pending. Should never be called."""
        raise ValueError('Future is pending.')


@dataclass
class Future(Generic[T]):
    """A class wrapping a value that may not yet have been set.

    T must not be derived from Exception. There seems to be no way to enforce
    this through static typing yet.
    """

    _state: FutureState[T] = field(default_factory=PendingFuture, init=False)

    def set(self, value: T) -> None:
        """Set the value of the future to a success value.

        Args:
            value: The value to set the Future to. Cannot be an Exception.
        """
        state_change = self._state.set(value)
        self._state = state_change.next_state
        state_change.event.set()

    def fail(self, error: Exception) -> None:
        """Signal failure and cause calls to `get()` to raise.

        Args:
            error: The exception that should be raised when `get()` is called.
        """
        state_change = self._state.fail(error)
        self._state = state_change.next_state
        state_change.event.set()

    async def get(self) -> T:
        """Get the value from the future asynchronously.

        If the future was set by `fail()`, raises the exception.
        """
        await self._state.wait_fulfilled()
        return self._state.get()


__all__ = [
    'Future',
]
