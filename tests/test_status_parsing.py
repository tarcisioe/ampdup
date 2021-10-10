"""Tests for status parsing."""
from ampdup import Single, State, Status
from ampdup.parsing import from_lines


def test_status_from_lines():
    """Create a status object from lines."""
    lines = [
        'volume: 55',
        'repeat: 0',
        'random: 0',
        'single: 0',
        'consume: 0',
        'playlist: 11',
        'playlistlength: 16',
        'mixrampdb: 0.000000',
        'state: play',
        'song: 0',
        'songid: 271',
        'time: 116:144',
        'elapsed: 116.285',
        'bitrate: 192',
        'duration: 144.480',
        'audio: 44100:24:2',
        'nextsong: 1',
        'nextsongid: 272',
    ]

    status = Status(
        volume=55,
        repeat=False,
        random=False,
        single=Single.DISABLED,
        consume=False,
        playlist=11,
        playlistlength=16,
        mixrampdb=0.000000,
        state=State.PLAY,
        song=0,
        songid=271,
        time='116:144',
        elapsed=116.285,
        bitrate=192,
        duration=144.480,
        audio='44100:24:2',
        nextsong=1,
        nextsongid=272,
        error=None,
        mixrampdelay=None,
        updating_db=None,
        xfade=None,
    )

    assert from_lines(Status, lines) == status
