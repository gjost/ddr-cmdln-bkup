import os

import fileio


# TODO read_text

def test_write_text():
    data = {'a':1, 'b':2}
    path = '/tmp/ddrlocal.models.write_text.json'
    fileio.write_text(data, path)
    with open(path, 'r') as f:
        written = f.readlines()
    assert written == ['{\n', '    "a": 1,\n', '    "b": 2\n', '}']
    # clean up
    os.remove(path)
