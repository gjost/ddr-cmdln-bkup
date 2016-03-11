# -*- coding: utf-8 -*-

from datetime import datetime
import os

import envoy
import git
from nose.tools import assert_raises

import batch_update


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
    batch_update.test_repository(repo)
    # staged but uncommitted files
    for fpath,text in files:
        repo.git.add(fpath)
    assert_raises(batch_update.UncommittedFilesError, batch_update.test_repository, repo)
    # commit
    repo.index.commit('testing testing 123')
    # modified existing files
    for fpath,text in files:
        with open(fpath, 'w') as f:
            f.write('modified')
    assert_raises(batch_update.ModifiedFilesError, batch_update.test_repository, repo)
    cleanup(path, files)

# TODO test_test_entities
# TODO test_load_vocab_files

def test_prep_valid_values():
    json_texts = [
        '{"terms": [{"id": "advertisement"}, {"id": "album"}, {"id": "architecture"}], "id": "genre"}',
        '{"terms": [{"id": "eng"}, {"id": "jpn"}, {"id": "chi"}], "id": "language"}',
    ]
    expected = {u'genre': [u'advertisement', u'album', u'architecture'], u'language': [u'eng', u'jpn', u'chi']}
    assert batch_update.prep_valid_values(json_texts) == expected

# TODO test_populate_object
# TODO test_write_entity_changelog
# TODO test_write_file_changelogs
# TODO test_update_entities
# TODO test_update_files
