# coding: utf-8

import codecs
import os

import fileio


TEXT_UTF8 = u'тє$тїпg 1 2 З'
# contents of TEXT_UTF8 in bytes
TEXT_UTF8_BYTES = '\xd1\x82\xd1\x94$\xd1\x82\xd1\x97\xd0\xbfg 1 2 \xd0\x97'

TEXT_CP1252_BYTES = ''


def test_read():
    path = '/tmp/test.DDR.fileio.read'
    with codecs.open(path, 'w', encoding='utf-8', errors='strict') as f:
        f.write(TEXT_UTF8)
    text = fileio.read(path)
    assert text == TEXT_UTF8

def test_write():
    path = '/tmp/test.DDR.fileio.write'
    fileio.write(TEXT_UTF8, path)
    with codecs.open(path, 'r', encoding='utf-8', errors='strict') as f:
        text = f.read()
    assert text == TEXT_UTF8

def test_read_replace():
    path = '/tmp/test.DDR.fileio.read_replace'
    #fileio.read_replace(path)
    pass

TEXT_ASCII = """line 0
line 1
line 2
"""

LINES_ASCII = [
    'line 0',
    'line 1',
    'line 2',
]

def test_read_raw():
    path = '/tmp/test.DDR.fileio.read_raw'
    with open(path, 'w') as f:
        f.write(TEXT_ASCII)
    text = fileio.read_raw(path)
    assert text == TEXT_ASCII
    # clean up
    os.remove(path)
    
    # read UTF-8 text
    with codecs.open(path, 'w', encoding='utf-8', errors='strict') as f:
        f.write(TEXT_UTF8)
    text = fileio.read_raw(path)
    assert text == TEXT_UTF8_BYTES
    # clean up
    os.remove(path)

def test_write_raw():
    path = '/tmp/test.DDR.fileio.write_raw'
    fileio.write_raw(TEXT_ASCII, path)
    with open(path, 'r') as f:
        text = f.read()
    assert text == TEXT_ASCII
    # clean up
    os.remove(path)

def test_readlines_raw():
    path = '/tmp/test.DDR.fileio.readlines_raw'
    with open(path, 'w') as f:
        f.write(TEXT_ASCII)
    lines = fileio.readlines_raw(path)
    assert lines == LINES_ASCII
    # clean up
    os.remove(path)
