#!/usr/bin/env python

from distutils.core import setup

setup(
    description = 'ddr-cmdln',
    author = 'Geoffrey Jost',
    url = 'https://github.com/densho/ddr-cmdln/',
    download_url = 'https://github.com/densho/ddr-cmdln.git',
    author_email = 'geoffrey.jost@densho.org',
    version = '0.1',
    install_requires = ['nose'],
    packages = ['DDR'],
    package_dir = {'DDR': 'DDR'},
    package_data = {'DDR': ['*.tpl', 'templates/*',]},
    scripts = ['bin/ddr', 'bin/ddrfilter', 'bin/ddrindex', 'bin/ddrmassupdate', 'bin/ddrpubcopy',],
    name = 'ddr'
)
