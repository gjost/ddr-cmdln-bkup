import codecs


def read(path):
    """Read text file with strict UTF-8 decoding.
    
    @param path: str Absolute path to file.
    @returns: unicode
    """
    with codecs.open(path, 'r', encoding='utf-8', errors='strict') as f:
        text = f.read()
    return text

def write(text, path):
    """Write text to file with strict UTF-8 encoding.
    
    @param text: unicode
    @param path: str Absolute path to file.
    """
    with codecs.open(path, 'w', encoding='utf-8', errors='strict') as f:
        f.write(text)

def read_replace(path):
    """Read text file with UTF-8/xmlcharrefreplace.
    
    @param path: str Absolute path to file.
    @returns: unicode
    """
    with codecs.open(path, 'r', encoding='utf-8', errors='xmlcharrefreplace') as f:
        text = f.read()
    return text

def read_raw(path):
    """Read text file without UTF-8 decoding.
    
    @param path: str Absolute path to file.
    @returns: unicode
    """
    with open(path, 'r') as f:
        text = f.read()
    return text

def write_raw(text, path):
    """Write text to file without UTF-8 encoding
    
    @param text: unicode
    @param path: str Absolute path to file.
    """
    with open(path, 'w') as f:
        f.write(text)

def readlines_raw(path):
    """Read text file without UTF-8 decoding, split into lines.
    
    @param path: str Absolute path to file.
    @returns: list of strings
    """
    with open(path, 'r') as f:
        lines = [line.strip() for line in f.readlines()]
    return lines
