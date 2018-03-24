import shlex

from typing import Any, Callable, Dict, List, Tuple

from curio import run
from curio.task import spawn, TaskCancelled
from curio.workers import run_in_thread
from wrapt import decorator

from ampdup import (
    CommandError, IdleMPDClient, MPDClient, MPDError, SongId, Tag
)


class CommandSyntaxError(MPDError):
    pass


def range_arg(argstring: str) -> List[Any]:
    try:
        x, y = [int(n) for n in argstring.split(':', maxsplit=1)]
        return [(x, y)]
    except ValueError:
        raise CommandSyntaxError(
            'takes a range (start:end).'
        )


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


def id_and_timerange(argstring: str) -> List[Any]:
    try:
        first, second = argstring.split()
    except ValueError as e:
        raise CommandSyntaxError(
            'takes two arguments (song id and time range).'
        ) from e

    try:
        song_id = SongId(first)
    except ValueError as e:
        raise CommandSyntaxError(
            'needs an integer as song id.'
        ) from e

    try:
        start, end = [float(n) if n else None
                      for n in second.split(':', maxsplit=1)]
    except ValueError as e:
        raise CommandSyntaxError(
            'takes a range of floats as time range.'
        ) from e

    return [song_id, (start, end)]


def tag_and_needle(argstring: str) -> List[Any]:
    try:
        first, second = argstring.split()
    except ValueError as e:
        raise CommandSyntaxError(
            'takes two arguments (tag and needle).'
        ) from e

    try:
        tag = Tag(first)
    except ValueError as e:
        raise CommandSyntaxError(
            'needs a supported tag.'
        ) from e

    return [tag, second]


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


def two_ints(error: str) -> Callable[[str], List[Any]]:
    def inner(argstring: str) -> List[Any]:
        try:
            x, y = shlex.split(argstring)
            return [int(x), int(y)]
        except ValueError as e:
            raise CommandSyntaxError(
                error
            ) from e
    return inner


PARSERS: Dict[str, Callable[[str], List[Any]]] = {
    'add': one_uri,
    'add_id': add_id_args,
    'clear': no_args,
    'delete': position_or_range,
    'delete_id': one_id,
    'current_song': no_args,
    'move': from_and_to,
    'move_id': two_ints('takes two song ids.'),
    'playlist_id': optional(one_id),
    'playlist_info': optional(position_or_range),
    'playlist_search': tag_and_needle,
    'range_id': id_and_timerange,
    'shuffle': optional(range_arg),
    'swap': two_ints('takes two song positions.'),
    'swap_id': two_ints('takes two song ids.'),
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
