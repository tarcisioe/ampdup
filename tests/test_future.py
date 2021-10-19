"""Tests for the ampdup.future module."""
import pytest

from ampdup.future import Future, FutureAlreadySetError


@pytest.mark.anyio
async def test_get_set_future() -> None:
    """Checks that a set future returns the set value."""
    f: Future[int] = Future()

    f.set(1)
    assert await f.get() == 1


@pytest.mark.anyio
async def test_get_failed_future() -> None:
    """Checks that a failed future raises."""
    f: Future[int] = Future()

    class DummyError(Exception):
        """Error class for testing."""

    f.fail(DummyError())

    with pytest.raises(DummyError):
        await f.get()


@pytest.mark.anyio
async def test_set_future_twice() -> None:
    """Check that setting a future twice fails."""
    f: Future[int] = Future()

    f.set(1)

    with pytest.raises(FutureAlreadySetError):
        f.set(1)


@pytest.mark.anyio
async def test_fail_set_future() -> None:
    """Check that failing a set future fails."""
    f: Future[int] = Future()

    f.set(1)

    with pytest.raises(FutureAlreadySetError):
        f.fail(ValueError('Oh no!'))


@pytest.mark.anyio
async def test_set_failed_future() -> None:
    """Check that setting a failed future fails."""
    f: Future[int] = Future()

    f.fail(ValueError('Oh no!'))

    with pytest.raises(FutureAlreadySetError):
        f.set(1)


@pytest.mark.anyio
async def test_fail_future_twice() -> None:
    """Check that failing a future twice fails."""
    f: Future[int] = Future()

    f.fail(ValueError('Oh no!'))

    with pytest.raises(FutureAlreadySetError):
        f.fail(ValueError('Oh no!'))


@pytest.mark.anyio
async def test_future_set_after_get() -> None:
    """Check that setting a future after a call to get works, with multiple getters."""
    from anyio import Event, create_task_group

    will_get = Event()

    async def get_future(f: Future[int]) -> None:
        will_get.set()
        assert await f.get() == 3

    f: Future[int] = Future()

    async with create_task_group() as tg:
        tg.start_soon(get_future, f)
        tg.start_soon(get_future, f)
        tg.start_soon(get_future, f)
        await will_get.wait()
        f.set(3)
