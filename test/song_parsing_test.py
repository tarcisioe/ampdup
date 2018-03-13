from ampdup import Song


def test_song_from_lines():
    '''Create a song object from lines.'''
    lines = [
        'file: path/to/song.mp3',
        'last_modified: ABCDE',
        'artist: Testman',
        'title: Sounds From the Depths of Testing',
        'album: Journey Through Testing',
        'track: 3',
        'date: 4',
        'genre: Test Rock',
        'time: 42',
        'duration: 42.0',
        'pos: 7',
        'id: 123',

    ]

    song = Song(
        file='path/to/song.mp3',
        last_modified='ABCDE',
        artist='Testman',
        title='Sounds From the Depths of Testing',
        album='Journey Through Testing',
        track=3,
        date=4,
        genre='Test Rock',
        time=42,
        duration=42.0,
        pos=7,
        id=123,
    )

    assert Song.from_lines(lines) == song
