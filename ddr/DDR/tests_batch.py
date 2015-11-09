# -*- coding: utf-8 -*-

from datetime import datetime
import os

import envoy
import git
from nose.tools import assert_raises

import batch


# TODO test_to_unicode_or_bust

def test_get_required_fields():
    # we're using a class not a module but functionally it's the same
    fields = [
        {'name':'id', 'form':{'required':True}},
        {'name':'title', 'form':{'required':True}},
        {'name':'description', 'form':{'required':False}},
        {'name':'formless'},
        {'name':'files', 'form':{'required':True}},
    ]
    exceptions = ['files', 'whatever']
    expected = ['id', 'title']
    assert batch.get_required_fields(fields, exceptions) == expected

# TODO test_load_vocab_files

def test_prep_valid_values():
    json_texts = [
        '{"terms": [{"id": "advertisement"}, {"id": "album"}, {"id": "architecture"}], "id": "genre"}',
        '{"terms": [{"id": "eng"}, {"id": "jpn"}, {"id": "chi"}], "id": "language"}',
    ]
    expected = {u'genre': [u'advertisement', u'album', u'architecture'], u'language': [u'eng', u'jpn', u'chi']}
    assert batch.prep_valid_values(json_texts) == expected

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

#def test_validate_row():
#    class TestModule(object):
#        @staticmethod
#        def csvload_language(data): return data
#        @staticmethod
#        def csvload_status(data): return data
#        @staticmethod
#        def csvvalidate_language(valid_values, data): return False
#        @staticmethod
#        def csvvalidate_status(valid_values, data): return False
#    module = TestModule()
#    headers = ['id', 'language', 'status']
#    valid_values = {
#        'language': ['eng', 'jpn'],
#        'status': ['ok', 'not ok']
#    }
#    rowds_valid = [
#        [ {'id':'ddr-test-123', 'language':'eng', 'status':'ok'}, [] ],
#    ]
#    rowds_invalid = [
#        [ {'id':'ddr-test-124', 'language':'chi', 'status':'not ok'}, ['language','status'] ],
#    ]
#    for rowd,expected in rowds_valid:
#        assert batch.validate_row(module, headers, valid_values, rowd) == expected
#    for rowd,expected in rowds_invalid:
#        assert batch.validate_row(module, headers, valid_values, rowd) == expected

# TODO test_validate_rows
# TODO test_load_entity
# TODO test_csvload_entity
# TODO test_write_entity_changelog
# TODO test_update_entities

def test_test_repository():
    def cleanup(path, files):
        envoy.run('rm -Rf %s' % path)
    
    path = '/tmp/test-batch-repo'
    files = [
        [os.path.join(path,'file0'), 'file0'],
        [os.path.join(path,'file1'), 'file1'],
    ]
    # prep
    cleanup(path, files)
    os.makedirs(path)
    for fpath,text in files:
        with open(fpath, 'w') as f:
            f.write(text)
    # clean repo - no Exceptions
    repo = git.Repo.init(path)
    batch.test_repository(repo)
    # staged but uncommitted files
    for fpath,text in files:
        repo.git.add(fpath)
    assert_raises(batch.UncommittedFilesError, batch.test_repository, repo)
    # commit
    repo.index.commit('testing testing 123')
    # modified existing files
    for fpath,text in files:
        with open(fpath, 'w') as f:
            f.write('modified')
    assert_raises(batch.ModifiedFilesError, batch.test_repository, repo)
    cleanup(path, files)

# TODO test_test_entities
# TODO test_new_files
# TODO test_load_file
# TODO test_csvload_file
# TODO test_write_file_changelogs
# TODO test_update_files
