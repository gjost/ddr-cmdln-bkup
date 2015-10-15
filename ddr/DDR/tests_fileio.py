import os

import fileio


TEXT = '{"a": 1, "b": 2}'

def test_read_text():
    path = '/tmp/test_DDR.fileio.read_text.json'
    with open(path, 'w') as f:
        f.write(TEXT)
    data = fileio.read_text(path)
    assert data == TEXT
    # clean up
    os.remove(path)

def test_write_text():
    path = '/tmp/test_DDR.fileio.write_text.json'
    fileio.write_text(TEXT, path)
    with open(path, 'r') as f:
        written = f.read()
    assert written == TEXT
    # clean up
    os.remove(path)
