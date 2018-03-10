'''MPD output parsing utilities.'''


def normalize(s: str) -> str:
    '''normalize'''
    return s.lower().replace('-', '_')
