import codecs
import json


def read_text(path):
    """Read text file; make sure text is in UTF-8.
    
    @param path: str Absolute path to file.
    @returns: unicode
    """
    # TODO use codecs.open utf-8
    with open(path, 'r') as f:
        text = f.read()
    return text

def write_text(text, path):
    """Write text to UTF-8 file.
    
    @param text: unicode
    @param path: str Absolute path to file.
    """
    # TODO use codecs.open utf-8
    with open(path, 'w') as f:
        f.write(text)
