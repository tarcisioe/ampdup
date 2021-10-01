from ampdup.parsing import normalize, parse_error, parse_single
from ampdup.errors import ErrorCode, CommandError, URINotFoundError


def test_normalize():
    '''Normalize creates valid Python identifier names.'''
    assert normalize('file') == 'file'
    assert normalize('Album') == 'album'
    assert normalize('Last-Modified') == 'last_modified'


def test_parse_unknown_command_error():
    '''Parse an unknown command error.'''

    ack_line = 'ACK [5@0] {} unknown command "aaa"'

    expected = CommandError(ErrorCode.UNKNOWN,
                            0,
                            '',
                            'unknown command "aaa"',
                            [])

    assert parse_error(ack_line, []) == expected


def test_parse_not_found_error():
    '''Parse a URI not found error.'''

    ack_line = 'ACK [50@0] {add} No such directory'

    expected = URINotFoundError(0,
                                'add',
                                'No such directory',
                                [])

    assert parse_error(ack_line, []) == expected


def test_parse_single_result():
    '''Parse a single result.'''
    result = ['name: value']

    assert parse_single(result) == 'value'


def test_parse_single_typed_result():
    '''Parse a single result and convert.'''
    result = ['name: 42']

    assert parse_single(result, int) == 42
