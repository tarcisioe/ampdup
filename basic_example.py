from typing import Any, List

from ampdup import CommandError, IdleMPDClient, MPDClient, MPDError
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


class CommandSyntaxError(MPDError):
    pass


def parse_playlist_info_args(argstring):
    numbers = argstring.split(':')

    try:
        if len(numbers) == 1:
            return [int(*numbers)]
        if len(numbers) == 2:
            x, y = [int(n) for n in numbers]
            return [(x, y)]
    except ValueError:
        pass

    raise CommandSyntaxError(
        'playlist_info takes either an integer or a range (start:end).'
    )


def parse_args(command: str, argstring: str) -> List[Any]:
    if command == 'playlist_info':
        return parse_playlist_info_args(argstring)
    return [argstring]


async def commands(client: MPDClient):
    while True:
        try:
            command: str = await run_in_thread(input, '>>> ')
        except EOFError:
            print()
            break

        try:
            method, *argstring = command.split(maxsplit=1)
            m = getattr(client, method, None)

            if m is not None:
                if argstring:
                    args = parse_args(method, *argstring)
                else:
                    args = []
                result = await m(*args)
            else:
                result = await client.run_command(command.strip('!'))
        except CommandError as e:
            print(f'Error {e.code}: {e.message}')
        except MPDError as e:
            print(e)
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
