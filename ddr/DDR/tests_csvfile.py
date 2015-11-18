# -*- coding: utf-8 -*-

from collections import OrderedDict
from datetime import datetime
import os

import envoy
import git
from nose.tools import assert_raises

import config
import csvfile
import identifier
import modules


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

def test_make_rowds():
    rows0 = [
        ['id', 'created', 'lastmod', 'title', 'description'],
        ['id0', 'then', 'now', 'title0', 'descr0'],
        ['id1', 'later', 'later', 'title1', 'descr1'],
    ]
    expected = (
        ['id', 'created', 'lastmod', 'title', 'description'],
        [
            OrderedDict([
                ('id', 'id0'), ('created', 'then'), ('lastmod', 'now'),
                ('title', 'title0'), ('description', 'descr0')
            ]),
            OrderedDict([
                ('id', 'id1'), ('created', 'later'), ('lastmod', 'later'),
                ('title', 'title1'), ('description', 'descr1')
            ])
        ]
    )
    assert csvfile.make_rowds(rows0) == expected

def test_validate_headers():
    headers0 = ['id', 'title']
    field_names0 = ['id', 'title', 'notused']
    exceptions = ['notused']
    # UNIX style silent if everything's OK
    assert not csvfile.validate_headers(headers0, field_names0, exceptions)
    # missing header
    headers1 = ['id']
    field_names1 = ['id', 'title', 'notused']
    assert_raises(
        Exception,
        csvfile.validate_headers,
        headers1, field_names1, exceptions
    )
    # bad header
    headers2 = ['id', 'title', 'badheader']
    field_names2 = ['id', 'title']
    assert_raises(
        Exception,
        csvfile.validate_headers,
        headers2, field_names2, exceptions
    )

def test_account_row():
    required_fields0 = ['id', 'title']
    rowd = {'id': 123, 'title': 'title'}
    out0 = []
    assert csvfile.account_row(required_fields0, rowd) == out0
    required_fields1 = ['id', 'title', 'description']
    out1 = ['description']
    assert csvfile.account_row(required_fields1, rowd) == out1

def test_validate_id():
    in0 = 'ddr-testing-123'
    expected0 = identifier.Identifier('ddr-testing-123')
    assert csvfile.validate_id(in0).id == expected0.id
    in1 = 'not a valid ID'
    expected1 = identifier.Identifier('ddr-testing-123')
    out1 = csvfile.validate_id(in1)
    assert not out1



def test_check_row_values():

    class TestSchema(object):
        __file__ = None
        FIELDS = [
            {
                'name': 'id',
            },
            {
                'name': 'status',
            }
        ]

    module = modules.Module(TestSchema())
    headers = ['id', 'status']
    valid_values = {
        'status': ['inprocess', 'complete',]
    }
    
    rowd0 = {
        'id': 'ddr-test-123',
        'status': 'inprocess',
    }
    out0 = csvfile.check_row_values(module, headers, valid_values, rowd0)
    print('out0 %s' % out0)
    expected0 = []
    assert out0 == expected0

    # invalid ID
    rowd1 = {
        'id': 'not a valid ID',
        'status': 'inprogress',
    }
    out1 = csvfile.check_row_values(module, headers, valid_values, rowd1)
    print('out1 %s' % out1)
    expected1 = ['id']
    assert out1 == expected1
    
    rowd2 = {
        'id': 'ddr-test-123',
        'status': 'inprogress',
    }
    out2 = csvfile.check_row_values(module, headers, valid_values, rowd1)
    print('out2 %s' % out2)
    expected2 = ['status']
    assert out2 == expected2

# TODO test_validate_rowds
