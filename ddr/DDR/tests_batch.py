from datetime import datetime
import os

from nose.tools import assert_raises

import batch


def test_dtfmt():
    in0 = datetime.fromtimestamp(0);
    fmt0 = '%Y-%m-%dT%H:%M:%S.%f'
    out0 = '1969-12-31T16:00:00.000000'
    assert batch.dtfmt(in0, fmt0) == out0

# TODO test_csv_writer
# TODO test_csv_reader

def test_make_entity_path():
    cpath0 = '/var/www/media/base/ddr-test-123'
    eid0 = 'ddr-test-123-456'
    out0 = '/var/www/media/base/ddr-test-123/files/ddr-test-123-456'
    assert batch.make_entity_path(cpath0, eid0) == out0

def test_make_entity_json_path():
    cpath0 = '/var/www/media/base/ddr-test-123'
    eid0 = 'ddr-test-123-456'
    out0 = '/var/www/media/base/ddr-test-123/files/ddr-test-123-456/entity.json'
    assert batch.make_entity_json_path(cpath0, eid0) == out0

# TODO test_make_tmpdir
# TODO test_write_csv
# TODO test_module_field_names
# TODO test_dump_object
# TODO test_export
# TODO test_read_csv
# TODO test_get_required_fields
# TODO test_prep_valid_values

def test_make_row_dict():
    headers0 = ['id', 'created', 'lastmod', 'title', 'description']
    row0 = ['id', 'then', 'now', 'title', 'descr']
    out0 = {
        'id': 'id',
        'created': 'then',
        'lastmod': 'now',
        'title': 'title', 'description': 'descr',
    }
    assert batch.make_row_dict(headers0, row0) == out0

def test_validate_headers():
    model = 'entity'
    field_names = ['id', 'title', 'notused']
    exceptions = ['notused']
    headers0 = ['id', 'title']
    # UNIX style silent if everything's OK
    assert not batch.validate_headers(model, headers0, field_names, exceptions)
    # bad header
    headers1 = ['id', 'titl']
    assert_raises(
        Exception,
        batch.validate_headers,
        model, headers1, field_names, exceptions)

def test_account_row():
    required_fields0 = ['id', 'title']
    rowd = {'id': 123, 'title': 'title'}
    out0 = []
    assert batch.account_row(required_fields0, rowd) == out0
    required_fields1 = ['id', 'title', 'description']
    out1 = ['description']
    assert batch.account_row(required_fields1, rowd) == out1

# TODO test_validate_row
# TODO test_validate_rows
# TODO test_load_entity
# TODO test_csvload_entity
# TODO test_write_entity_changelog
# TODO test_update_entities
# TODO test_test_entities
# TODO test_load_file
# TODO test_csvload_file
# TODO test_write_file_changelog
# TODO test_update_files
