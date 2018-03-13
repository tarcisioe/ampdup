# pylint: skip-file

from abc import abstractmethod
from typing import AnyStr, Generic, List, Union


class AsyncIO(Generic[AnyStr]):
    """Generic base class for async TextIO and BinaryIO."""

    __slots__ = ()

    @abstractmethod
    async def readline(self, limit: int = -1) -> AnyStr:
        pass

    @abstractmethod
    async def readlines(self, hint: int = -1) -> List[AnyStr]:
        pass

    @abstractmethod
    async def write(self, s: AnyStr) -> int:
        pass

    @abstractmethod
    async def writelines(self, lines: List[AnyStr]) -> None:
        pass

    @abstractmethod
    async def __aenter__(self) -> 'AsyncIO[AnyStr]':
        pass

    @abstractmethod
    async def __aexit__(self, type, value, traceback) -> None:
        pass


class AsyncBinaryIO(AsyncIO[bytes]):
    """Typed version of an async IO object, counterparte to typing.BinaryIO."""

    __slots__ = ()

    @abstractmethod
    async def write(self, s: Union[bytes, bytearray]) -> int:
        pass

    @abstractmethod
    async def __aenter__(self) -> 'AsyncBinaryIO':
        pass
