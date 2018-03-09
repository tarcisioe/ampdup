from .base_client import BaseMPDClient
from .errors import ClientTypeError


class MPDClient(BaseMPDClient):
    async def run_command(self, command: str):
        if command in ('idle', 'noidle'):
            raise ClientTypeError('Use an IdleClient to use the idle command.')

        return await super().run_command(command)
