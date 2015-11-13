# -*- coding: utf-8 -*-

from datetime import datetime
import os

import envoy
import git
from nose.tools import assert_raises

import config
import csvfile


def test_make_row_dict():
    headers0 = ['id', 'created', 'lastmod', 'title', 'description']
    row0 = ['id', 'then', 'now', 'title', 'descr']
    out0 = {
        'id': 'id',
        'created': 'then',
        'lastmod': 'now',
        'title': 'title', 'description': 'descr',
    }
    assert csvfile.make_row_dict(headers0, row0) == out0

def test_validate_headers():
    field_names = ['id', 'title', 'notused']
    exceptions = ['notused']
    headers0 = ['id', 'title']
    # UNIX style silent if everything's OK
    assert not csvfile.validate_headers(headers0, field_names, exceptions)
    # bad header
    headers1 = ['id', 'titl']
    assert_raises(
        Exception,
        csvfile.validate_headers,
        headers1, field_names, exceptions
    )

def test_account_row():
    required_fields0 = ['id', 'title']
    rowd = {'id': 123, 'title': 'title'}
    out0 = []
    assert csvfile.account_row(required_fields0, rowd) == out0
    required_fields1 = ['id', 'title', 'description']
    out1 = ['description']
    assert csvfile.account_row(required_fields1, rowd) == out1

# TODO test_validate_id
# TODO test_check_row_values
# TODO test_validate_rows
