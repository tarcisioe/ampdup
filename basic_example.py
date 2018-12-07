import shlex

from asyncio import create_task, get_running_loop, run, sleep, CancelledError
from typing import Any, Callable, Dict, List, Tuple, Union

from wrapt import decorator

from ampdup import (
    CommandError, ConnectionFailedError, IdleMPDClient, MPDClient, MPDError,
    SearchType, Single, SongId, Tag
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


def priority_and_range(argstring: str) -> List[Any]:
    try:
        first, second = argstring.split()
    except ValueError as e:
        raise CommandSyntaxError(
            'takes two arguments (priority and range).'
        ) from e

    try:
        priority = int(first)
    except ValueError as e:
        raise CommandSyntaxError(
            'needs an integer as priority.'
        ) from e

    try:
        start, end = [int(n) if n else None
                      for n in second.split(':', maxsplit=1)]
    except ValueError as e:
        raise CommandSyntaxError(
            'takes a range.'
        ) from e

    return [priority, (start, end)]


def priority_and_id(argstring: str) -> List[Any]:
    try:
        first, second = argstring.split()
    except ValueError as e:
        raise CommandSyntaxError(
            'takes two arguments (priority and song id).'
        ) from e

    try:
        priority = int(first)
    except ValueError as e:
        raise CommandSyntaxError(
            'needs an integer as priority.'
        ) from e

    try:
        song_id = SongId(second)
    except ValueError as e:
        raise CommandSyntaxError(
            'needs an integer as song id.'
        ) from e

    return [priority, song_id]


def type_what(argstring: str) -> List[Any]:
    try:
        search_type_str, what = shlex.split(argstring)
    except ValueError as e:
        raise CommandSyntaxError(
            'takes two arguments (type and what).'
        ) from e

    search_type: Union[Tag, SearchType]

    try:
        search_type = Tag(search_type_str)
    except ValueError:
        try:
            search_type = SearchType(search_type_str)
        except ValueError as f:
            raise CommandSyntaxError('No such search type.') from f

    return [[(search_type, what)]]


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


def one_int(error: str) -> Callable[[str], List[Any]]:
    def inner(argstring: str) -> List[Any]:
        try:
            return [int(argstring)]
        except ValueError as e:
            raise CommandSyntaxError(
                error
            ) from e
    return inner


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


def one_float(error: str) -> Callable[[str], List[Any]]:
    def inner(argstring: str) -> List[Any]:
        try:
            return [float(argstring)]
        except ValueError as e:
            raise CommandSyntaxError(
                error
            ) from e
    return inner


def single_mode(argstring: str) -> List[Any]:
    try:
        return [Single(argstring)]
    except ValueError as e:
        raise CommandSyntaxError(
            'takes either 0, 1 or oneshot.'
        ) from e


def int_and_float(error: str) -> Callable[[str], List[Any]]:
    def inner(argstring: str) -> List[Any]:
        try:
            x, y = shlex.split(argstring)
            return [int(x), float(y)]
        except ValueError as e:
            raise CommandSyntaxError(
                error
            ) from e
    return inner


one_id = one_int('takes a song id.')
two_ids = two_ints('takes two song ids.')
one_bool = one_int('takes a boolean (0 or 1).')


PARSERS: Dict[str, Callable[[str], List[Any]]] = {
    'add': one_uri,
    'add_id': add_id_args,
    'clear': no_args,
    'consume': one_bool,
    'current_song': no_args,
    'delete': position_or_range,
    'delete_id': one_id,
    'find': type_what,
    'move': from_and_to,
    'move_id': two_ids,
    'next': no_args,
    'pause': one_bool,
    'play': optional(one_int('takes a position.')),
    'play_id': optional(one_id),
    'playlist_find': tag_and_needle,
    'playlist_id': optional(one_id),
    'playlist_info': optional(position_or_range),
    'playlist_search': tag_and_needle,
    'previous': no_args,
    'prio': priority_and_range,
    'prio_id': priority_and_id,
    'random': one_bool,
    'range_id': id_and_timerange,
    'repeat': one_bool,
    'search': type_what,
    'seek': int_and_float('takes a position and a time in seconds.'),
    'seek_id': int_and_float('takes a song id and a time in seconds.'),
    'seek_cur_abs': one_float('takes a time in seconds.'),
    'seek_cur_rel': one_float('takes a time delta in seconds.'),
    'setvol': one_int('takes an amount between 0-100.'),
    'shuffle': optional(range_arg),
    'single': single_mode,
    'swap': two_ints('takes two song positions.'),
    'swap_id': two_ids,
    'status': no_args,
    'stats': no_args,
    'stop': no_args,
    'update': optional(one_uri),
}


def parse_args(command: str, argstring: str = '') -> List[Any]:
    parser = PARSERS.get(command)

    if parser is None:
        return [argstring]

    return parser(argstring)


async def commands(client: MPDClient):
    loop = get_running_loop()
    while True:
        try:
            command: str = await loop.run_in_executor(None,
                                                      lambda: input('>>> '))
        except EOFError:
            print()
            break

        try:
            method, *argstring = command.split(maxsplit=1)
            m = getattr(client, method, None)

            if m is not None:
                args = parse_args(method, *argstring)
                try:
                    result = await m(*args)
                except ConnectionFailedError:
                    print('Connection had been lost. Retrying...')
                    await client.reconnect()
                    result = await m(*args)
            else:
                pass
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
            elif result is not None:
                print(result)


async def monitor(client: IdleMPDClient):
    try:
        while True:
            try:
                changes = await client.idle()
            except ConnectionFailedError:
                await sleep(1)
                try:
                    await client.reconnect()
                except ConnectionFailedError:
                    continue
            else:
                for line in changes:
                    print(line)
    except CancelledError:
        return


async def main():
    async with MPDClient.make('localhost', 6600) as m, IdleMPDClient.make('localhost', 6600) as i:  # noqa
        loop = get_running_loop()
        idle = loop.create_task(monitor(i))
        await commands(m)
        idle.cancel()


if __name__ == '__main__':
    run(main())
