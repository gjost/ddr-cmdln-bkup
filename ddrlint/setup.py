#!/usr/bin/env python

from distutils.core import setup

setup(
    description = 'ddrlint',
    author = 'Geoffrey Jost',
    url = 'https://github.com/densho/ddr-cmdln/',
    download_url = 'https://github.com/densho/ddr-cmdln.git',
    author_email = 'geoffrey.jost@densho.org',
    version = '0.1',
    install_requires = ['nose'],
    packages = ['ddrlint'],
    package_dir = {'ddrlint': 'ddrlint'},
    package_data = {'ddrlint': []},
    scripts = ['bin/ddrlint',],
    name = 'ddrlint'
)
