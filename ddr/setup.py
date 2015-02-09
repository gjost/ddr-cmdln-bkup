#!/usr/bin/env python

from distutils.core import setup

setup(
    description = 'ddr-cmdln',
    author = 'Geoffrey Jost',
    url = 'https://github.com/densho/ddr-cmdln/',
    download_url = 'https://github.com/densho/ddr-cmdln.git',
    author_email = 'geoffrey.jost@densho.org',
    version = '0.9-beta',
    install_requires = ['nose'],
    packages = ['DDR', 'DDR.converters'],
    package_dir = {'DDR': 'DDR'},
    package_data = {'DDR': ['*.tpl', 'models/*', 'templates/*',]},
    scripts = ['bin/ddr', 'bin/ddr-checkencoding', 'bin/ddrfilter', 'bin/ddrindex', 'bin/ddrmassupdate', 'bin/ddrpubcopy', 'bin/ddrdensho255fix'],
    name = 'ddr'
)
