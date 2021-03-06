from datetime import datetime
import json
import os
import shutil

import models
import identifier

BASEDIR = '/tmp/test-ddr-models'
MEDIA_BASE = os.path.join(BASEDIR, 'ddr')

class TestModule(object):
    __name__ = 'TestModule'
    __file__ = 'ddr/repo_models'
    FIELDS = [
        {
            'name': 'id',
            'model_type': str,
            'form': {
                'label': 'Object ID',
            },
            'default': '',
        },
        {
            'name': 'timestamp',
            'model_type': datetime,
            'form': {
                'label': 'Last Modified',
            },
            'default': '',
        },
        {
            'name': 'status',
            'model_type': str,
            'form': {
                'label': 'Status',
            },
            'default': '',
        },
        {
            'name': 'title',
            'model_type': str,
            'form': {
                'label': 'Title',
            },
            'default': '',
        },
        {
            'name': 'description',
            'model_type': str,
            'form': {
                'label': 'Description',
            },
            'default': '',
        },
    ]

class TestDocument():
    pass

TEST_DOCUMENT = """[
    {
        "application": "https://github.com/densho/ddr-local.git",
        "commit": "52155f819ccfccf72f80a11e1cc53d006888e283  (HEAD, repo-models) 2014-09-16 16:30:42 -0700",
        "git": "git version 1.7.10.4; git-annex version: 3.20120629",
        "models": "",
        "release": "0.10"
    },
    {"id": "ddr-test-123"},
    {"timestamp": "2014-09-19T03:14:59"},
    {"status": 1},
    {"title": "TITLE"},
    {"description": "DESCRIPTION"}
]"""


# TODO sort_file_paths
# TODO object_metadata
# TODO is_object_metadata

def test_load_json():
    class Document(object):
        pass
    
    document = Document()
    module = TestModule()
    models.load_json(document, module, TEST_DOCUMENT)
    assert document.id == 'ddr-test-123'
    assert document.timestamp == u'2014-09-19T03:14:59'
    assert document.status == 1
    assert document.title == 'TITLE'
    assert document.description == 'DESCRIPTION'

# TODO prep_json
# TODO from_json
# TODO load_xml
# TODO prep_xml
# TODO from_xml


# TODO Stub


# Collection

def test_Collection__init__():
    cid = 'ddr-testing-123'
    path_abs = os.path.join(MEDIA_BASE, cid)
    c = models.Collection(path_abs)
    assert c.root == MEDIA_BASE
    assert c.id == 'ddr-testing-123'
    assert c.path == path_abs
    assert c.path_abs == path_abs
    assert c.gitignore_path == os.path.join(path_abs, '.gitignore')
    assert c.annex_path == os.path.join(path_abs, '.git/annex')
    assert c.files_path == os.path.join(path_abs, 'files')
    assert c.lock_path == os.path.join(path_abs, 'lock')
    assert c.control_path == os.path.join(path_abs, 'control')
    assert c.changelog_path == os.path.join(path_abs, 'changelog')
    assert c.path_rel == None
    assert c.gitignore_path_rel == '.gitignore'
    assert c.annex_path_rel == '.git/annex'
    assert c.files_path_rel == 'files'
    assert c.control_path_rel == 'control'
    assert c.changelog_path_rel == 'changelog'
    # TODO assert c.git_url

# TODO Collection.__repr__
# TODO Collection.create
# TODO Collection.from_identifier
# TODO Collection.from_json
# TODO Collection.parent
# TODO Collection.children
# TODO Collection.labels_values
# TODO Collection.inheritable_fields
# TODO Collection.selected_inheritables
# TODO Collection.update_inheritables
# TODO Collection.load_json
# TODO Collection.dump_json
# TODO Collection.write_json
# TODO Collection.post_json

# Collection.lock
# Collection.unlock
# Collection.locked
def test_Collection_locking():
    cid = 'ddr-testing-123'
    path_abs = os.path.join(MEDIA_BASE, cid)
    c = models.Collection(path_abs)
    text = 'testing'
    # prep
    if os.path.exists(path_abs):
        shutil.rmtree(path_abs)
    os.makedirs(c.path)
    # before locking
    assert c.locked() == False
    assert not os.path.exists(c.lock_path)
    # locking
    assert c.lock(text) == 'ok'
    # locked
    assert c.locked() == text
    assert os.path.exists(c.lock_path)
    # unlocking
    assert c.unlock(text) == 'ok'
    assert c.locked() == False
    assert not os.path.exists(c.lock_path)
    # clean up
    if os.path.exists(path_abs):
        shutil.rmtree(path_abs)

# TODO Collection.changelog
# TODO Collection.control
# TODO Collection.ead
# TODO Collection.dump_ead
# TODO Collection.write_ead
# TODO Collection.gitignore
# TODO Collection.collection_paths
# TODO Collection.repo_fetch
# TODO Collection.repo_status
# TODO Collection.repo_annex_status
# TODO Collection.repo_synced
# TODO Collection.repo_ahead
# TODO Collection.repo_behind
# TODO Collection.repo_diverged
# TODO Collection.repo_conflicted


def test_Entity__init__():
    collection_id = 'ddr-testing-123'
    entity_id = 'ddr-testing-123-456'
    collection_path = os.path.join(MEDIA_BASE, collection_id)
    path_abs = os.path.join(collection_path, 'files', entity_id)
    e = models.Entity(path_abs)
    assert e.parent_path == collection_path
    assert e.parent_id == collection_id
    assert e.root == MEDIA_BASE
    assert e.id == 'ddr-testing-123-456'
    assert e.path == path_abs
    assert e.path_abs == path_abs
    assert e.files_path == os.path.join(path_abs, 'files')
    assert e.lock_path == os.path.join(path_abs, 'lock')
    assert e.control_path == os.path.join(path_abs, 'control')
    assert e.changelog_path == os.path.join(path_abs, 'changelog')
    assert e.path_rel == 'files/ddr-testing-123-456'
    assert e.files_path_rel == 'files/ddr-testing-123-456/files'
    assert e.control_path_rel == 'files/ddr-testing-123-456/control'
    assert e.changelog_path_rel == 'files/ddr-testing-123-456/changelog'

# TODO Entity.__repr__
# TODO Entity.create
# TODO Entity.from_identifier
# TODO Entity.from_json
# TODO Entity.parent
# TODO Entity.children
# TODO Entity.labels_values
# TODO Entity.inheritable_fields
# TODO Entity.selected_inheritables
# TODO Entity.update_inheritables
# TODO Entity.inherit

# Entity.lock
# Entity.unlock
# Entity.locked
def test_Entity_locking():
    collection_id = 'ddr-testing-123'
    entity_id = 'ddr-testing-123-456'
    collection_path = os.path.join(MEDIA_BASE, collection_id)
    path_abs = os.path.join(collection_path, 'files', entity_id)
    e = models.Entity(path_abs)
    text = 'testing'
    # prep
    if os.path.exists(path_abs):
        shutil.rmtree(path_abs)
    os.makedirs(e.path)
    # before locking
    assert e.locked() == False
    assert not os.path.exists(e.lock_path)
    # locking
    assert e.lock(text) == 'ok'
    # locked
    assert e.locked() == text
    assert os.path.exists(e.lock_path)
    # unlocking
    assert e.unlock(text) == 'ok'
    assert e.locked() == False
    assert not os.path.exists(e.lock_path)
    # clean up
    if os.path.exists(path_abs):
        shutil.rmtree(path_abs)

# TODO Entity.load_json
# TODO Entity.dump_json
# TODO Entity.write_json
# TODO Entity.post_json

def test_Entity_changelog():
    collection_id = 'ddr-testing-123'
    entity_id = 'ddr-testing-123-456'
    collection_path = os.path.join(MEDIA_BASE, collection_id)
    path_abs = os.path.join(collection_path, 'files', entity_id)
    e = models.Entity(path_abs)
    changelog_path = os.path.join(path_abs, 'changelog')
    assert e.changelog() == '%s is empty or missing' % changelog_path
    # TODO test reading changelog

# TODO Entity.control
# TODO Entity.mets
# TODO Entity.dump_mets
# TODO Entity.write_mets

def test_Entity_checksum_algorithms():
    assert models.Entity.checksum_algorithms() == ['md5', 'sha1', 'sha256']

# TODO Entity.checksums
# TODO Entity.file_paths
# TODO Entity.load_file_objects
# TODO Entity.detect_file_duplicates
# TODO Entity.rm_file_duplicates
# TODO Entity.file
# TODO Entity.addfile_logger
# TODO Entity.add_file
# TODO Entity.add_access
# TODO Entity.add_file_commit
# TODO Entity.prep_rm_file


# TODO File.__init__
# TODO File.__repr__
# TODO File.from_identifer
# TODO File.from_json
# TODO File.parent
# TODO File.children
# TODO File.labels_values
# TODO File.files_rel
# TODO File.present
# TODO File.access_present
# TODO File.inherit
# TODO File.load_json
# TODO File.dump_json
# TODO File.write_json
# TODO File.post_json
# TODO File.file_name
# TODO File.set_path
# TODO File.set_access
# TODO File.file
# TODO File.access_filename
# TODO File.links_incoming
# TODO File.links_outgoing
# TODO File.links_all
