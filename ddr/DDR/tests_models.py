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

# TODO metadata_files

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

def test_model_from_path():
    assert models.model_from_path('.../ddr-testing-123/collection.json') == 'collection'
    assert models.model_from_path('.../ddr-testing-123-1/entity.json') == 'entity'
    assert models.model_from_path('.../ddr-testing-123-1-master-a1b2c3d4e5.json') == 'file'

def test_parent_id():
    assert models.parent_id('ddr') == None
    assert models.parent_id('ddr-testing') == 'ddr'
    assert models.parent_id('ddr-testing-123') == 'ddr-testing'
    assert models.parent_id('ddr-testing-123-1') == 'ddr-testing-123'
    assert models.parent_id('ddr-testing-123-1-master-a1b2c3d4e5') == 'ddr-testing-123-1'

# TODO model_fields

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
    assert c.gitignore_path == '/tmp/ddr-testing-123/.gitignore'
    assert c.changelog_path_rel == 'changelog'
    assert c.control_path_rel == 'control'
    assert c.files_path_rel == 'files'
    assert c.gitignore_path_rel == '.gitignore'
    # TODO assert c.git_url

def test_Collection_path_absrel():
    c = models.Collection('/tmp/ddr-testing-123')
    assert c._path_absrel('path/to/file') == '/tmp/ddr-testing-123/path/to/file'
    assert c._path_absrel('path/to/file', rel=True) == 'path/to/file'

def test_Collection_entity_path():
    c = models.Collection('/tmp/ddr-testing-123')
    assert c.entity_path('11') == '/tmp/ddr-testing-123/files/11'

def test_Collection_changelog():
    c = models.Collection('/tmp/ddr-testing-123')
    assert c.changelog() == '/tmp/ddr-testing-123/changelog is empty or missing'
    # TODO test reading changelog

# TODO Collection.control
# TODO Collection.gitignore
# TODO Collection.collections
# TODO Collection.entities

def test_Entity__init__():
    e = models.Entity('/tmp/ddr-testing-123/files/1')
    assert e.path == '/tmp/ddr-testing-123/files/1'
    assert e.path_rel == 'ddr-testing-123/files/1'
    assert e.root == '/tmp'
    assert e.parent_path == '/tmp/ddr-testing-123'
    assert e.uid == '1'
    assert e.parent_uid == 'ddr-testing-123'
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

def test_Entity_changelog():
    e = models.Entity('/tmp/ddr-testing-123/files/1')
    assert e.changelog() == '/tmp/ddr-testing-123/files/1/changelog is empty or missing'
    # TODO test reading changelog

# TODO Entity.control
# TODO Entity.files
def test_Entity_checksum_algorithms():
    assert models.Entity.checksum_algorithms() == ['md5', 'sha1', 'sha256']

# TODO Entity.checksums

# TODO File.*
