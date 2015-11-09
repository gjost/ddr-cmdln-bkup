# -*- coding: utf-8 -*-

from datetime import datetime
import os

import envoy
import git
from nose.tools import assert_raises

import batch_export


def test_dtfmt():
    in0 = datetime.fromtimestamp(0);
    fmt0 = '%Y-%m-%dT%H:%M:%S.%f'
    out0 = '1969-12-31T16:00:00.000000'
    assert batch_export.dtfmt(in0, fmt0) == out0

def test_normalize_text():
    assert batch_export.normalize_text('  this is a test') == 'this is a test'
    assert batch_export.normalize_text('this is a test  ') == 'this is a test'
    assert batch_export.normalize_text('this\r\nis a test') == 'this\\nis a test'
    assert batch_export.normalize_text('this\ris a test') == 'this\\nis a test'
    assert batch_export.normalize_text('this\\nis a test') == 'this\\nis a test'
    assert batch_export.normalize_text(['this is a test']) == ['this is a test']
    assert batch_export.normalize_text({'this': 'is a test'}) == {'this': 'is a test'}

# TODO test_make_tmpdir

def test_module_field_names():
    # we're using a class not a module but functionally it's the same
    class TestModule(object):
        MODEL = None
        FIELDS_CSV_EXCLUDED = []
        FIELDS = []
    m = TestModule()
    m.FIELDS = [{'name':'id'}, {'name':'title'}, {'name':'description'}]
    m.FIELDS_CSV_EXCLUDED = ['description']
    # test
    m.MODEL = 'collection'
    assert batch_export.module_field_names(m) == ['id', 'title']
    m.MODEL = 'entity'
    assert batch_export.module_field_names(m) == ['id', 'title']
    m.MODEL = 'file'
    assert batch_export.module_field_names(m) == ['file_id', 'id', 'title']
    m.MODEL = 'entity'

# TODO test_dump_object
# TODO test_export
