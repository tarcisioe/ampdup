import shlex

from typing import Any, Callable, Dict, List, Tuple

from curio import run
from curio.task import spawn, TaskCancelled
from curio.workers import run_in_thread
from wrapt import decorator

from ampdup import CommandError, IdleMPDClient, MPDClient, MPDError


class CommandSyntaxError(MPDError):
    pass


def position_or_range(argstring: str) -> List[Any]:
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
        'takes either an integer or a range (start:end).'
    )


def one_uri(argstring: str) -> List[Any]:
    args = shlex.split(argstring)
    if len(args) != 1:
        raise CommandSyntaxError('takes exactly one URI.')
    return args


def one_id(argstring: str) -> List[Any]:
    try:
        return [int(argstring)]
    except ValueError as e:
        raise CommandSyntaxError(
            'takes a song id (integer).'
        ) from e


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


ArgFunc = Callable[[str], List[Any]]


@decorator
def optional_dec(wrapped: ArgFunc,
                 _: Any,
                 args: Tuple[str],
                 _2: Dict[str, Any]) -> List[Any]:
    if args == ('',):
        return []

    return wrapped(*args)


def optional(argfunc: ArgFunc) -> ArgFunc:
    return optional_dec(argfunc)  # pylint: disable=no-value-for-parameter


def no_args(argstring: str) -> List[Any]:
    if argstring:
        raise CommandSyntaxError('takes no arguments.')

    return []


def from_and_to(argstring: str) -> List[Any]:
    try:
        start, end = shlex.split(argstring)
    except ValueError as e:
        raise CommandSyntaxError(
            'takes two arguments (from and to).'
        )

    try:
        return [*position_or_range(start), int(end)]
    except ValueError as e:
        raise CommandSyntaxError(
            'takes an integer as the "to" argument.'
        ) from e


def two_ints(argstring: str) -> List[Any]:
    try:
        x, y = shlex.split(argstring)
        return [int(x), int(y)]
    except ValueError as e:
        raise CommandSyntaxError(
            'takes two integers.'
        ) from e


PARSERS: Dict[str, Callable[[str], List[Any]]] = {
    'add': one_uri,
    'add_id': add_id_args,
    'clear': no_args,
    'delete': position_or_range,
    'delete_id': one_id,
    'current_song': no_args,
    'move': from_and_to,
    'move_id': two_ints,
    'playlist_info': optional(position_or_range),
    'status': no_args,
    'stats': no_args,
    'update': optional(one_uri),
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


async def monitor(client: IdleMPDClient):
    try:
        while True:
            changes = await client.idle()
            for line in changes:
                print(line)
    except TaskCancelled:
        return


async def main():
    async with MPDClient.make('localhost', 6600) as m, IdleMPDClient.make('localhost', 6600) as i:  # noqa
        idle = await spawn(monitor(i))
        await commands(m)
        await idle.cancel()


if __name__ == '__main__':
    run(main())
