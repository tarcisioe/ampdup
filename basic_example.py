from typing import List

from ampdup import CommandError, IdleMPDClient, MPDClient
from curio import run
from curio.task import spawn, TaskCancelled
from curio.workers import run_in_thread


async def monitor(client: IdleMPDClient):
    try:
        while True:
            changes = await client.idle()
            for line in changes:
                print(line)
    except TaskCancelled:
        return


async def commands(client: MPDClient):
    while True:
        try:
            command = await run_in_thread(input, '>>> ')
        except EOFError:
            print()
            break

        try:
            m = getattr(client, command, None)
            if m is not None:
                result = await m()
            else:
                result = await client.run_command(command)
        except CommandError as e:
            print(f"Error {e.code}: {e.message}")
        else:
            if isinstance(result, List):
                for line in result:
                    print(line)
            else:
                print(result)


async def main():
    async with MPDClient.make('localhost', 6600) as m, IdleMPDClient.make('localhost', 6600) as i:
        idle = await spawn(monitor(i))
        await commands(m)
        await idle.cancel()


if __name__ == '__main__':
    run(main())
