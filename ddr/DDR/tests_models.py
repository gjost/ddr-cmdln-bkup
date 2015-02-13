from datetime import datetime
import json
import os

import models


def test_file_hash():
    path = '/tmp/test-hash-%s' % datetime.now().strftime('%Y%m%dT%H%M%S')
    text = 'hash'
    sha1 = '2346ad27d7568ba9896f1b7da6b5991251debdf2'
    sha256 = 'd04b98f48e8f8bcc15c6ae5ac050801cd6dcfd428fb5f9e65c4e16e7807340fa'
    md5 = '0800fc577294c34e0b28ad2839435945'
    with open(path, 'w') as f:
        f.write(text)
    assert models.file_hash(path, 'sha1') == sha1
    assert models.file_hash(path, 'sha256') == sha256
    assert models.file_hash(path, 'md5') == md5
    os.remove(path)

def test_metadata_files():
    basedir = '/tmp'
    cachedir = '.metadata_files'
    cache_path = os.path.join(basedir, cachedir)
    if os.path.exists(cache_path):
        os.remove(cache_path)
    assert not os.path.exists(cache_path)
    paths0 = models.metadata_files('/tmp', recursive=True, force_read=True)
    print('paths: %s' % paths0)
    assert os.path.exists(cache_path)
    paths1 = models.metadata_files('/tmp', recursive=True, force_read=True)
    print('paths: %s' % paths1)

# TODO sort_file_paths
# TODO document_metadata

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

# TODO read_json

def test_write_json():
    data = {'a':1, 'b':2}
    path = '/tmp/ddrlocal.models.write_json.json'
    models.write_json(data, path)
    with open(path, 'r') as f:
        written = f.readlines()
    assert written == ['{\n', '    "a": 1,\n', '    "b": 2\n', '}']
    # clean up
    os.remove(path)

def test_load_json():
    document = Document()
    models.load_json(document, testmodule, TEST_DOCUMENT)
    assert document.id == 'ddr-test-123'
    assert document.timestamp == u'2014-09-19T03:14:59'
    assert document.status == 1
    assert document.title == 'TITLE'
    assert document.description == 'DESCRIPTION'

# TODO prep_json
# TODO from_json


def test_dissect_path():
    c0 = models.dissect_path('/base/ddr-test-123/collection.json')
    c1 = models.dissect_path('/base/ddr-test-123')
    assert c0
    assert c1
    assert c0.base_path == c1.base_path
    assert c0.collection_path == c1.collection_path
    assert c0.entity_path == c1.entity_path
    assert c0.object_type == c1.object_type
    assert c0.object_id == c1.object_id
    assert c0.repo == c1.repo
    assert c0.org == c1.org
    assert c0.cid == c1.cid
    assert c0.eid == c1.eid
    assert c0.base_path == '/base'
    assert c0.collection_path == '/base/ddr-test-123'
    assert c0.object_type == 'collection'
    assert c0.object_id == 'ddr-test-123'
    assert c0.repo == 'ddr'
    assert c0.org == 'test'
    assert c0.cid == '123'
    assert c0.eid == None
    assert c0.role == None
    assert c0.sha1 == None
    assert c0.file_id == None
    assert c0.entity_id == None
    assert c0.collection_id == 'ddr-test-123'
    
    e0 = models.dissect_path('/base/ddr-test-123/files/ddr-test-123-1/entity.json')
    e1 = models.dissect_path('/base/ddr-test-123/files/ddr-test-123-1/files')
    e2 = models.dissect_path('/base/ddr-test-123/files/ddr-test-123-1')
    assert e0
    assert e1
    assert e2
    assert e0.base_path == e1.base_path == e2.base_path
    assert e0.collection_path == e1.collection_path == e2.collection_path
    assert e0.entity_path == e1.entity_path == e2.entity_path
    assert e0.object_type == e1.object_type == e2.object_type
    assert e0.object_id == e1.object_id == e2.object_id
    assert e0.repo == e1.repo == e2.repo
    assert e0.org == e1.org == e2.org
    assert e0.cid == e1.cid == e2.cid
    assert e0.eid == e1.eid == e2.eid
    assert e0.base_path == '/base'
    assert e0.collection_path == '/base/ddr-test-123'
    assert e0.entity_path == '/base/ddr-test-123/files/ddr-test-123-1'
    assert e0.object_type == 'entity'
    assert e0.object_id == 'ddr-test-123-1'
    assert e0.repo == 'ddr'
    assert e0.org == 'test'
    assert e0.cid == '123'
    assert e0.eid == '1'
    assert e0.role == None
    assert e0.sha1 == None
    assert e0.file_id == None
    assert e0.entity_id == 'ddr-test-123-1'
    assert e0.collection_id == 'ddr-test-123'
    
    f0 = models.dissect_path('/base/ddr-test-123/files/ddr-test-123-1/files/ddr-test-123-1-master-abc-a.jpg')
    f1 = models.dissect_path('/base/ddr-test-123/files/ddr-test-123-1/files/ddr-test-123-1-master-abc.json')
    f2 = models.dissect_path('/base/ddr-test-123/files/ddr-test-123-1/files/ddr-test-123-1-master-abc.jpg')
    f3 = models.dissect_path('/base/ddr-test-123/files/ddr-test-123-1/files/ddr-test-123-1-master-abc.pdf')
    f4 = models.dissect_path('/base/ddr-test-123/files/ddr-test-123-1/files/ddr-test-123-1-master-abc')
    assert f0
    assert f1
    assert f2
    assert f3
    assert f4
    assert f0.base_path == f1.base_path == f2.base_path == f3.base_path == f4.base_path
    assert f0.collection_path == f1.collection_path == f2.collection_path == f3.collection_path == f4.collection_path
    assert f0.entity_path == f1.entity_path == f2.entity_path == f3.entity_path == f4.entity_path
    assert f0.object_type == f1.object_type == f2.object_type == f3.object_type == f4.object_type
    assert f0.object_id == f1.object_id == f2.object_id == f3.object_id == f4.object_id
    assert f0.repo == f1.repo == f2.repo == f3.repo == f4.repo
    assert f0.org == f1.org == f2.org == f3.org == f4.org
    assert f0.cid == f1.cid == f2.cid == f3.cid == f4.cid
    assert f0.eid == f1.eid == f2.eid == f3.eid == f4.eid
    assert f0.role == f1.role == f2.role == f3.role == f4.role
    assert f0.sha1 == f1.sha1 == f2.sha1 == f3.sha1 == f4.sha1
    assert f0.base_path == '/base'
    assert f0.collection_path == '/base/ddr-test-123'
    assert f0.entity_path == '/base/ddr-test-123/files/ddr-test-123-1'
    assert f0.object_type == 'file'
    assert f0.object_id == 'ddr-test-123-1-master-abc'
    assert f0.repo == 'ddr'
    assert f0.org == 'test'
    assert f0.cid == '123'
    assert f0.eid == '1'
    assert f0.role == 'master'
    assert f0.sha1 == 'abc'
    assert f0.file_id == 'ddr-test-123-1-master-abc'
    assert f0.entity_id == 'ddr-test-123-1'
    assert f0.collection_id == 'ddr-test-123'

def test_make_object_id():
    assert models.make_object_id('file','ddr','test','123','1','role','a1') == 'ddr-test-123-1-role-a1'
    assert models.make_object_id('entity','ddr','test','123','1') == 'ddr-test-123-1'
    assert models.make_object_id('collection','ddr','test','123') == 'ddr-test-123'
    assert models.make_object_id('organization','ddr','test') == 'ddr-test'
    assert models.make_object_id('org','ddr','test') == 'ddr-test'
    assert models.make_object_id('repository','ddr') == 'ddr'
    assert models.make_object_id('repo','ddr') == 'ddr'
    # edge cases
    assert models.make_object_id('repo','ddr','test','123','1','role','a1') == 'ddr'
    # mistakes
    assert models.make_object_id('file','ddr') == None
    assert models.make_object_id('badmodel','ddr','test','123','1','role','a1') == None

def test_split_object_id():
    assert models.split_object_id('ddr-test-123-1-role-a1') == ['file', 'ddr','test','123','1','role','a1']
    assert models.split_object_id('ddr-test-123-1') == ['entity', 'ddr','test','123','1']
    assert models.split_object_id('ddr-test-123') == ['collection', 'ddr','test','123']
    assert models.split_object_id('ddr-test-123-1-role-a1-xx') == None
    assert models.split_object_id('ddr-test-123-1-role') == None
    assert models.split_object_id('ddr-test') == None
    assert models.split_object_id('ddr') == None

def test_id_from_path():
    assert models.id_from_path('.../ddr-testing-123/collection.json') == 'ddr-testing-123'
    assert models.id_from_path('.../ddr-testing-123-1/entity.json') == 'ddr-testing-123-1'
    assert models.id_from_path('.../ddr-testing-123-1-master-a1.json') == 'ddr-testing-123-1-master-a1'
    assert models.id_from_path('.../ddr-testing-123/files/ddr-testing-123-1/') ==  None
    assert models.id_from_path('.../ddr-testing-123/something-else.json') ==  None

def test_model_from_path():
    assert models.model_from_path('.../ddr-testing-123/collection.json') == 'collection'
    assert models.model_from_path('.../ddr-testing-123-1/entity.json') == 'entity'
    assert models.model_from_path('.../ddr-testing-123-1-master-a1b2c3d4e5.json') == 'file'

MODELFROMDICT_NOID = {}
MODELFROMDICT_FILE = {'path_rel':'this/is/a/path'}
MODELFROMDICT_ENTITY = {'id': 'ddr-test-123-1'}
MODELFROMDICT_COLL = {'id': 'ddr-test-123'}
MODELFROMDICT_ORG = {'id': 'ddr-test'}
MODELFROMDICT_REPO = {'id': 'ddr'}

def test_model_from_dict():
    assert models.model_from_dict(MODELFROMDICT_NOID) == None
    assert models.model_from_dict(MODELFROMDICT_FILE) == 'file'
    assert models.model_from_dict(MODELFROMDICT_ENTITY) == 'entity'
    assert models.model_from_dict(MODELFROMDICT_COLL) == 'collection'
    assert models.model_from_dict(MODELFROMDICT_ORG) == None
    assert models.model_from_dict(MODELFROMDICT_REPO) == None

# TODO path_from_id

def test_parent_id():
    assert models.parent_id('ddr') == None
    assert models.parent_id('ddr-testing') == 'ddr'
    assert models.parent_id('ddr-testing-123') == 'ddr-testing'
    assert models.parent_id('ddr-testing-123-1') == 'ddr-testing-123'
    assert models.parent_id('ddr-testing-123-1-master-a1b2c3d4e5') == 'ddr-testing-123-1'

def test_Module_path():
    class TestModule(object):
        pass
    
    module = TestModule()
    module.__file__ = '/var/www/media/base/ddr/repo_models/testmodule.pyc'
    assert models.Module(module).path == '/var/www/media/base/ddr/repo_models/testmodule.py'

def test_Module_is_valid():
    class TestModule0(object):
        __name__ = 'TestModule0'
        __file__ = ''
    
    class TestModule1(object):
        __name__ = 'TestModule1'
        __file__ = 'ddr/repo_models'
    
    class TestModule2(object):
        __name__ = 'TestModule2'
        __file__ = 'ddr/repo_models'
        FIELDS = 'not a list'
    
    class TestModule3(object):
        __name__ = 'TestModule3'
        __file__ = 'ddr/repo_models'
        FIELDS = ['fake fields']

    assert models.Module(TestModule0()).is_valid() == (False,"TestModule0 not in 'ddr' Repository repo.")
    assert models.Module(TestModule1()).is_valid() == (False,'TestModule1 has no FIELDS variable.')
    assert models.Module(TestModule2()).is_valid() == (False,'TestModule2.FIELDS is not a list.')
    assert models.Module(TestModule3()).is_valid() == (True,'ok')

def test_Module_function():
    class TestModule(object):
        def hello(self, text):
            return 'hello %s' % text
    
    module = TestModule()
    module.__file__ = 'ddr/repo_models'
    assert models.Module(module).function('hello', 'world') == 'hello world'

# TODO Module_xml_function

def test_Module_labels_values():
    class TestModule(object):
        __name__ = 'TestModule'
        __file__ = 'ddr/repo_models'
        FIELDS = ['fake fields']
    
    class TestDocument():
        pass
    
    module = TestModule()
    document = TestDocument()
    models.load_json(document, module, TEST_DOCUMENT)
    expected = [
        {'value': u'ddr-test-123', 'label': 'ID'},
        {'value': u'2014-09-19T03:14:59', 'label': 'Timestamp'},
        {'value': 1, 'label': 'Status'},
        {'value': u'TITLE', 'label': 'Title'},
        {'value': u'DESCRIPTION', 'label': 'Description'}
    ]
    assert models.Module(module).labels_values(document) == expected

# TODO Module_cmp_model_definition_commits

def test_Module_cmp_model_definition_fields():
    document = json.loads(TEST_DOCUMENT)
    module = TestModule()
    module.__file__ = 'ddr/repo_models'
    module.FIELDS = ['fake fields']
    assert models.Module(module).cmp_model_definition_fields(
        json.dumps(document)
    ) == ([],[])
    
    document.append( {'new': 'new field'} )
    assert models.Module(module).cmp_model_definition_fields(
        json.dumps(document)
    ) == (['new'],[])
    
    document.pop()
    document.pop()
    assert models.Module(module).cmp_model_definition_fields(
        json.dumps(document)
    ) == ([],['description'])


MODEL_FIELDS_INHERITABLE = [
    {'name':'id',},
    {'name':'record_created',},
    {'name':'record_lastmod',},
    {'name':'status', 'inheritable':True,},
    {'name':'public', 'inheritable':True,},
    {'name':'title',},
]
def test_Inheritance_inheritable_fields():
    assert models.Inheritance.inheritable_fields(MODEL_FIELDS_INHERITABLE) == ['status','public']

# TODO Inheritance_inherit
# TODO Inheritance_selected_inheritables
# TODO Inheritance_update_inheritables


# Locking_lock
# Locking_unlock
# Locking_locked
def test_locking():
    lock_path = '/tmp/test-lock-%s' % datetime.now().strftime('%Y%m%dT%H%M%S')
    text = 'we are locked. go away.'
    # before locking
    assert models.Locking.locked(lock_path) == False
    assert models.Locking.unlock(lock_path, text) == 'not locked'
    # locking
    assert models.Locking.lock(lock_path, text) == 'ok'
    # locked
    assert models.Locking.locked(lock_path) == text
    assert models.Locking.lock(lock_path, text) == 'locked'
    assert models.Locking.unlock(lock_path, 'not the right text') == 'miss'
    # unlocking
    assert models.Locking.unlock(lock_path, text) == 'ok'
    # unlocked
    assert models.Locking.locked(lock_path) == False
    assert models.Locking.unlock(lock_path, text) == 'not locked'
    assert not os.path.exists(lock_path)


def test_Collection__init__():
    c = models.Collection('/tmp/ddr-testing-123')
    assert c.path == '/tmp/ddr-testing-123'
    assert c.path_rel == 'ddr-testing-123'
    assert c.root == '/tmp'
    assert c.uid == 'ddr-testing-123'
    assert c.annex_path == '/tmp/ddr-testing-123/.git/annex'
    assert c.annex_path_rel == '.git/annex'
    assert c.changelog_path == '/tmp/ddr-testing-123/changelog'
    assert c.control_path == '/tmp/ddr-testing-123/control'
    assert c.files_path == '/tmp/ddr-testing-123/files'
    assert c.lock_path == '/tmp/ddr-testing-123/lock'
    assert c.gitignore_path == '/tmp/ddr-testing-123/.gitignore'
    assert c.changelog_path_rel == 'changelog'
    assert c.control_path_rel == 'control'
    assert c.files_path_rel == 'files'
    assert c.gitignore_path_rel == '.gitignore'
    # TODO assert c.git_url

# TODO Collection.__repr__

def test_Collection_path_absrel():
    c = models.Collection('/tmp/ddr-testing-123')
    assert c._path_absrel('path/to/file') == '/tmp/ddr-testing-123/path/to/file'
    assert c._path_absrel('path/to/file', rel=True) == 'path/to/file'

# TODO Collection.create
# TODO Collection.from_json
# TODO Collection.model_def_commits
# TODO Collection.model_def_fields
# TODO Collection.labels_values
# TODO Collection.inheritable_fields
# TODO Collection.load_json
# TODO Collection.dump_json
# TODO Collection.write_json

# Collection.locking
# Collection.unlock
# Collection.locked
def test_Collection_locking():
    c = models.Collection('/tmp/ddr-testing-123')
    text = 'we are locked. go away.'
    os.mkdir(c.path)
    # before locking
    assert models.locked(c.lock_path) == False
    assert models.unlock(c.lock_path, text) == 'not locked'
    # locking
    assert models.lock(c.lock_path, text) == 'ok'
    # locked
    assert models.locked(c.lock_path) == text
    assert models.lock(c.lock_path, text) == 'locked'
    assert models.unlock(c.lock_path, 'not the right text') == 'miss'
    # unlocking
    assert models.unlock(c.lock_path, text) == 'ok'
    # unlocked
    assert models.locked(c.lock_path) == False
    assert models.unlock(c.lock_path, text) == 'not locked'
    assert not os.path.exists(c.lock_path)
    os.rmdir(c.path)

def test_Collection_changelog():
    c = models.Collection('/tmp/ddr-testing-123')
    assert c.changelog() == '/tmp/ddr-testing-123/changelog is empty or missing'
    # TODO test reading changelog

# TODO Collection.control
# TODO Collection.ead
# TODO Collection.dump_ead
# TODO Collection.gitignore
# TODO Collection.collection_paths

def test_Collection_entity_path():
    c = models.Collection('/tmp/ddr-testing-123')
    assert c.entity_path('11') == '/tmp/ddr-testing-123/files/11'

# TODO Collection.entity_paths
# TODO Collection.entities
# TODO Collection.repo_fetch
# TODO Collection.repo_status
# TODO Collection.repo_annex_status
# TODO Collection.repo_synced
# TODO Collection.repo_ahead
# TODO Collection.repo_behind
# TODO Collection.repo_diverged
# TODO Collection.repo_conflicted


def test_Entity__init__():
    e = models.Entity('/tmp/ddr-testing-123/files/1')
    assert e.path == '/tmp/ddr-testing-123/files/1'
    assert e.path_rel == 'ddr-testing-123/files/1'
    assert e.root == '/tmp'
    assert e.parent_path == '/tmp/ddr-testing-123'
    assert e.uid == '1'
    assert e.parent_uid == 'ddr-testing-123'
    assert e.lock_path == '/tmp/ddr-testing-123/files/1/lock'
    assert e.changelog_path == '/tmp/ddr-testing-123/files/1/changelog'
    assert e.control_path == '/tmp/ddr-testing-123/files/1/control'
    assert e.files_path == '/tmp/ddr-testing-123/files/1/files'
    assert e.changelog_path_rel == 'files/1/changelog'
    assert e.control_path_rel == 'files/1/control'
    assert e.files_path_rel == 'files/1/files'

def test_Entity_path_absrel():
    e = models.Entity('/tmp/ddr-testing-123/files/1')
    assert e._path_absrel('filename') == '/tmp/ddr-testing-123/files/1/filename'
    assert e._path_absrel('filename', rel=True) == 'files/1/filename'

# TODO Entity._path_absrel
# TODO Entity.__repr__
# TODO Entity.create
# TODO Entity.from_json
# TODO Entity.model_def_commits
# TODO Entity.model_def_fields
# TODO Entity.labels_values
# TODO Entity.inherit
# TODO Entity.inheritable_fields

# Entity.locking
# Entity.unlock
# Entity.locked
def test_Entity_locking():
    e = models.Entity('/tmp/ddr-testing-123-1')
    text = 'we are locked. go away.'
    os.mkdir(e.path)
    # before locking
    assert models.locked(e.lock_path) == False
    assert models.unlock(e.lock_path, text) == 'not locked'
    # locking
    assert models.lock(e.lock_path, text) == 'ok'
    # locked
    assert models.locked(e.lock_path) == text
    assert models.lock(e.lock_path, text) == 'locked'
    assert models.unlock(e.lock_path, 'not the right text') == 'miss'
    # unlocking
    assert models.unlock(e.lock_path, text) == 'ok'
    # unlocked
    assert models.locked(e.lock_path) == False
    assert models.unlock(e.lock_path, text) == 'not locked'
    assert not os.path.exists(e.lock_path)
    os.rmdir(e.path)

# TODO Entity.load_json
# TODO Entity.dump_json
# TODO Entity.write_json

def test_Entity_changelog():
    e = models.Entity('/tmp/ddr-testing-123/files/1')
    assert e.changelog() == '/tmp/ddr-testing-123/files/1/changelog is empty or missing'
    # TODO test reading changelog

# TODO Entity.control
# TODO Entity.mets
# TODO Entity.dump_mets

def test_Entity_checksum_algorithms():
    assert models.Entity.checksum_algorithms() == ['md5', 'sha1', 'sha256']

# TODO Entity.checksums
# TODO Entity.file_paths
# TODO Entity.load_file_objects
# TODO Entity.files_master
# TODO Entity.files_mezzanine
# TODO Entity.detect_file_duplicates
# TODO Entity.rm_file_duplicates
# TODO Entity.file
# TODO Entity._addfile_log_path
# TODO Entity.addfile_logger
# TODO Entity.add_file
# TODO Entity.add_file_commit
# TODO Entity.add_access


# TODO File.__init__
# TODO File.__repr__
# TODO File.model_def_commits
# TODO File.model_def_fields
# TODO File.labels_values
# TODO File.files_rel
# TODO File.present
# TODO File.access_present
# TODO File.inherit
# TODO File.from_json
# TODO File.load_json
# TODO File.dump_json
# TODO File.write_json
# TODO File.file_name
# TODO File.set_path
# TODO File.set_access
# TODO File.file
# TODO File.access_filename
# TODO File.links_incoming
# TODO File.links_outgoing
# TODO File.links_all
