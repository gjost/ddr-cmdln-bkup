#!/usr/bin/env python

import codecs
from distutils.core import setup
import os
import re

here = os.path.abspath(os.path.dirname(__file__))

def read(*parts):
    # intentionally *not* adding an encoding option to open
    return codecs.open(os.path.join(here, *parts), 'r').read()

def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^VERSION = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

long_description = read('README.rst')

setup(
    description = 'ddr-cmdln',
    author = 'Geoffrey Jost',
    version = find_version('DDR', '__init__.py'),
    url = 'https://github.com/densho/ddr-cmdln/',
    download_url = 'https://github.com/densho/ddr-cmdln.git',
    author_email = 'geoffrey.jost@densho.org',
    long_description = long_description,
    install_requires = [
        'nose'
    ],
    packages = [
        'DDR',
        'DDR.converters'
    ],
    package_dir = {
        'DDR': 'DDR'
    },
    package_data = {'DDR': [
        '*.tpl',
        'models/*',
        'templates/*',
    ]},
    scripts = [
        'bin/ddr',
        'bin/ddr-checkencoding',
        'bin/ddr-export',
        'bin/ddr-import',
        'bin/ddrfilter',
        'bin/ddrindex',
        'bin/ddrmassupdate',
        'bin/ddrpubcopy',
        'bin/ddrdensho255fix',
    ],
    name = 'ddr'
)
