import shlex

from typing import Any, Callable, Dict, List

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


def parse_playlist_info_args(argstring: str) -> List[Any]:
    numbers = argstring.split(':')

    if not numbers:
        return []

    try:
        if len(numbers) == 1:
            return [int(*numbers)]
        if len(numbers) == 2:
            x, y = [int(n) for n in numbers]
            return [(x, y)]
    except ValueError:
        pass

    raise CommandSyntaxError(
        'takes either an integer or a range (start:end).'
    )


def one_uri(argstring: str) -> List[Any]:
    args = shlex.split(argstring)
    if len(args) != 1:
        raise CommandSyntaxError('takes exactly one URI.')
    return args


def one_optional_uri(argstring: str) -> List[Any]:
    if not argstring:
        return []

    return one_uri(argstring)


def add_id_args(argstring: str) -> List[Any]:
    try:
        uri, *pos = shlex.split(argstring)
    except ValueError as e:
        raise CommandSyntaxError(
            'takes one URI and an optional position'
        ) from e

    if pos:
        pos_arg, = pos
        position = int(pos_arg)
        return [uri, position]
    return [uri]


def no_args(argstring: str) -> List[Any]:
    if argstring:
        raise CommandSyntaxError('takes no arguments.')

    return []


PARSERS: Dict[str, Callable[[str], List[Any]]] = {
    'add': one_uri,
    'add_id': add_id_args,
    'clear': no_args,
    'current_song': no_args,
    'playlist_info': parse_playlist_info_args,
    'status': no_args,
    'stats': no_args,
    'update': one_optional_uri,
}


def parse_args(command: str, argstring: str = '') -> List[Any]:
    parser = PARSERS.get(command)

    if parser is None:
        return [argstring]

    return parser(argstring)


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
                args = parse_args(method, *argstring)
                result = await m(*args)
            else:
                result = await client.run_command(command.strip('!'))
        except CommandError as e:
            exc_name = type(e).__name__
            exc_code = f'{e.code.value} ({e.code.name})'
            exc_command = f' @ {e.command}' if e.command else ''
            print(f'{exc_name}: {exc_code}{exc_command}: {e.message}')
        except MPDError as e:
            exc_name = type(e).__name__
            print(f'{exc_name}: {method} {str(e)}')
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
