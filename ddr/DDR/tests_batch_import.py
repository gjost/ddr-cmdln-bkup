# -*- coding: utf-8 -*-

from datetime import datetime
import os

import envoy
import git
from nose.tools import assert_raises

import batch_import


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
    batch_import.test_repository(repo)
    # staged but uncommitted files
    for fpath,text in files:
        repo.git.add(fpath)
    assert_raises(batch_import.UncommittedFilesError, batch_import.test_repository, repo)
    # commit
    repo.index.commit('testing testing 123')
    # modified existing files
    for fpath,text in files:
        with open(fpath, 'w') as f:
            f.write('modified')
    assert_raises(batch_import.ModifiedFilesError, batch_import.test_repository, repo)
    cleanup(path, files)

# TODO test_entities
# TODO test_test_entities
# TODO test_load_vocab_files

def test_prep_valid_values():
    json_texts = [
        '{"terms": [{"id": "advertisement"}, {"id": "album"}, {"id": "architecture"}], "id": "genre"}',
        '{"terms": [{"id": "eng"}, {"id": "jpn"}, {"id": "chi"}], "id": "language"}',
    ]
    expected = {u'genre': [u'advertisement', u'album', u'architecture'], u'language': [u'eng', u'jpn', u'chi']}
    assert batch_import.prep_valid_values(json_texts) == expected

# TODO test_populate_object
# TODO test_write_entity_changelog
# TODO test_write_file_changelogs
# TODO test_check_csv_file
# TODO test_ids_in_repo
# TODO test_check_entity_ids
# TODO test_register_entity_ids
# TODO test_import_entities
# TODO test_import_files
