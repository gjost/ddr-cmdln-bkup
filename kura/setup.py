#!/usr/bin/env python

from distutils.core import setup

setup(
    description = 'ddr-kura',
    author = 'Geoffrey Jost',
    url = 'https://github.com/densho/ddr-cmdln/',
    download_url = 'https://github.com/densho/ddr-cmdln.git',
    author_email = 'geoffrey.jost@densho.org',
    version = '0.1',
    install_requires = ['nose'],
    packages = ['Kura'],
    package_dir = {'Kura': 'Kura'},
    package_data = {'Kura': ['*.tpl', 'templates/*',]},
    scripts = ['bin/collection','bin/entity',],
    name = 'kura'
)
