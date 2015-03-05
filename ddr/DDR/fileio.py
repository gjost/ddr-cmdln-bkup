import codecs
import ConfigParser
import csv
import sys
import unicodecsv

csv.field_size_limit(sys.maxsize)  # Some files' XMP data is wayyyyyy too big
CSV_DELIMITER = ','
CSV_QUOTECHAR = '"'
CSV_QUOTING = csv.QUOTE_ALL


# utf-8/strict

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

def read_csv(path):
    """Read CSV file with UTF-8/strict decoding, return list of rows.
    
    @param path: str Absolute path to file.
    @returns: list of rows
    """
    rows = []
    with codecs.open(path, 'rU', 'utf-8') as f:  # the 'U' is for universal-newline mode
        reader = unicodecsv.reader(
            f,
            delimiter=fileio.CSV_DELIMITER,
            quoting=fileio.CSV_QUOTING,
            quotechar=fileio.CSV_QUOTECHAR,
        )
        rows = [row for row in reader]
    return rows

def write_csv(rows, path):
    """Write list of rows to CSV file with UTF-8/strict encoding.
    
    @param: list of rows
    @param path: str Absolute path to file.
    """
    with codecs.open(path, 'wb', 'utf-8') as f:
        writer = unicodecsv.writer(
            f,
            delimiter=CSV_DELIMITER,
            quoting=CSV_QUOTING,
            quotechar=CSV_QUOTECHAR,
        )
        for row in rows:
            writer.writerow(row)


# utf-8/replace

def read_replace(path):
    """Read text file with UTF-8/xmlcharrefreplace.
    
    @param path: str Absolute path to file.
    @returns: unicode
    """
    with codecs.open(path, 'r', encoding='utf-8', errors='xmlcharrefreplace') as f:
        text = f.read()
    return text


# raw -- unsafe!

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

def writelines_raw(lines, path):
    """Write lines of text to file without UTF-8 encoding.
    
    @param lines: list of strings
    @param path: str Absolute path to file.
    """
    with open(fname, 'w') as f:
        f.writelines(lines)

def append_raw(text, path):
    """Append the text to the file without UTF-8 encoding.
    
    @param text: unicode
    @param path: str Absolute path to file.
    """
    with open(path, 'a') as f:
         f.write(text)

def read_csv_raw(path):
    """Read CSV file without UTF-8 decoding, return list of rows.
    
    @param path: str Absolute path to file.
    @returns: list of rows
    """
    rows = []
    with open(path, 'rb') as f:
        reader = csv.reader(f, delimiter=CSV_DELIMITER, quotechar=CSV_QUOTECHAR)
        rows = [row for row in reader]
    return rows

def write_csv_raw(rows, path):
    """Write list of rows to CSV file without UTF-8 encoding.
    
    @param: list of rows
    @param path: str Absolute path to file.
    """
    with open(path, 'wb') as f:
        writer = csv.writer(f, delimiter=CSV_DELIMITER, quotechar=CSV_QUOTECHAR, quoting=CSV_QUOTING)
        for row in rows:
            writer.writerow(row)

def read_config_raw(paths):
    """Reads .ini file without UTF-8 decoding(?).
    
    @param paths: list of absolute paths.
    @returns: ConfigParser object
    """
    config = ConfigParser.ConfigParser()
    config.read(paths)
    return config

def write_config_raw(config, path):
    """Writes .ini file without UTF-8 encoding.
    
    @param config: ConfigParser object
    @param path: Absolute path to write.
    """
    with open(path, 'wb') as f:
        config.write(f)
