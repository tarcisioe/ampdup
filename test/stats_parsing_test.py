from ampdup.stats import Stats
from ampdup.parsing import from_lines


def test_status_from_lines():
    '''Create a status object from lines.'''
    lines = [
        'uptime: 363249',
        'playtime: 11000',
        'artists: 55',
        'albums: 387',
        'songs: 4199',
        'db_playtime: 1095183',
        'db_update: 1519007314',
    ]

    stats = Stats(
        uptime=363249,
        playtime=11000,
        artists=55,
        albums=387,
        songs=4199,
        db_playtime=1095183,
        db_update=1519007314,
    )

    assert from_lines(Stats, lines) == stats
