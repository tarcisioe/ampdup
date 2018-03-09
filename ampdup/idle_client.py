from .base_client import BaseMPDClient
from .errors import ClientTypeError


class IdleMPDClient(BaseMPDClient):
    async def run_command(self, command: str):
        if command not in ('idle', 'noidle'):
            raise ClientTypeError(
                'Use an MPDClient to run commands other than idle and noidle.'
            )

        return await super().run_command(command)

    async def idle(self):
        return await self.run_command("idle")

    async def noidle(self):
        return await self.run_command("noidle")
