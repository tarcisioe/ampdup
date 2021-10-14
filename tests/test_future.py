"""Tests for the ampdup.future module."""
import pytest

from ampdup.future import Future, FutureAlreadySetError


@pytest.mark.anyio
async def test_set_future_twice():
    """Check that setting a future twice fails."""
    f: Future[int] = Future()

    f.set(1)

    with pytest.raises(FutureAlreadySetError):
        f.set(1)
