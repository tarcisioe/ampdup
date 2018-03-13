from ampdup.parsing import normalize


def test_normalize():
    '''Normalize creates valid Python identifier names.'''
    assert normalize('file') == 'file'
    assert normalize('Album') == 'album'
    assert normalize('Last-Modified') == 'last_modified'
