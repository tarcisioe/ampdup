"""Tests for parsing songs."""
from ampdup import Song
from ampdup.parsing import from_lines


def test_song_from_lines():
    """Create a song object from lines."""
    lines = [
        'file: path/to/song.mp3',
        'Last-Modified: 2018-02-07T09:41:04Z',
        'Artist: Testman',
        'Title: Sounds From the Depths of Testing',
        'Album: Journey Through Testing',
        'Track: 3',
        'Date: 4',
        'Genre: Test Rock',
        'Time: 42',
        'duration: 42.0',
        'Pos: 7',
        'Id: 123',
        'prio: 30',
    ]

    song = Song(
        file='path/to/song.mp3',
        last_modified='2018-02-07T09:41:04Z',
        artist='Testman',
        title='Sounds From the Depths of Testing',
        album='Journey Through Testing',
        track=3,
        date='4',
        genre='Test Rock',
        time=42,
        duration=42.0,
        pos=7,
        id=123,
        prio=30,
    )

    assert from_lines(Song, lines) == song
