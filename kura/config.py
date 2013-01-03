#!/usr/bin/python -OO

# Reads config files from /etc/kura.
# TODO Also read from ~/.kura

import ConfigParser
import sys

def read_config(path='/etc/kura.conf'):
    config = ConfigParser.ConfigParser()
    config.read([path])
    return config

def to_text(config):
    lines = []
    for section in config.sections():
        lines.append('[%s]' % section)
        for item in config.items(section):
            lines.append('%s: %s' % item)
    return '\n'.join(lines)

if __name__ == '__main__':
    config = read_config(sys.argv[1])
    print to_text(config)
