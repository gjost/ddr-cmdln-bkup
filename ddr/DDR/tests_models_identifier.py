# coding: utf-8

from datetime import datetime
import json
import os

from nose.tools import assert_raises

from DDR.models.identifier import Identifier

BASE_PATH = '/var/www/media/ddr'



REPO_ID = 'ddr'
REPO_REPR = '<Identifier ddr>'
REPO_MODEL = 'repository'

def test_repository_from_id():
    i0 = Identifier.from_id('ddr')
    i1 = Identifier.from_id('ddr', BASE_PATH)
    assert str(i0)  == str(i1)  == REPO_REPR
    assert i0.id    == i1.id    == REPO_ID
    assert i0.model == i1.model == REPO_MODEL
    assert i0.basepath == None
    assert i1.basepath == BASE_PATH

def test_repository_from_idparts():
    i0 = Identifier.from_idparts(
        {'model':'repository', 'repo':'ddr',}
    )
    i1 = Identifier.from_idparts(
        {'model':'repository', 'repo':'ddr',},
        BASE_PATH
    )
    assert str(i0)  == str(i1)  == REPO_REPR
    assert i0.id    == i1.id    == REPO_ID
    assert i0.model == i1.model == REPO_MODEL
    assert i0.basepath == None
    assert i1.basepath == BASE_PATH

def test_repository_from_path():
    i0 = Identifier.from_path('/var/www/media/ddr/ddr')
    assert str(i0) == REPO_REPR
    assert i0.id == REPO_ID
    assert i0.model == REPO_MODEL
    assert i0.basepath == BASE_PATH

def test_repository_from_url():
    i0 = Identifier.from_url('http://192.168.56.101/ddr')
    i1 = Identifier.from_url('http://192.168.56.101/ddr/', BASE_PATH)
    assert str(i0)  == str(i1)  == REPO_REPR
    assert i0.id    == i1.id    == REPO_ID
    assert i0.model == i1.model == REPO_MODEL
    assert i0.basepath == None
    assert i1.basepath == BASE_PATH


ORG_ID = 'ddr-test'
ORG_REPR = '<Identifier ddr-test>'
ORG_MODEL = 'organization'

def test_organization_from_id():
    i0 = Identifier.from_id('ddr-test')
    i1 = Identifier.from_id('ddr-test', BASE_PATH)
    assert str(i0)  == str(i1)  == ORG_REPR
    assert i0.id    == i1.id    == ORG_ID
    assert i0.model == i1.model == ORG_MODEL
    assert i0.basepath == None
    assert i1.basepath == BASE_PATH

def test_organization_from_idparts():
    i0 = Identifier.from_idparts(
        {'model':'organization', 'repo':'ddr', 'org':'test',}
    )
    i1 = Identifier.from_idparts(
        {'model':'organization', 'repo':'ddr', 'org':'test',},
        BASE_PATH
    )
    assert str(i0)  == str(i1)  == ORG_REPR
    assert i0.id    == i1.id    == ORG_ID
    assert i0.model == i1.model == ORG_MODEL
    assert i0.basepath == None
    assert i1.basepath == BASE_PATH

def test_organization_from_path():
    i0 = Identifier.from_path('/var/www/media/ddr/ddr-test')
    i1 = Identifier.from_path('/var/www/media/ddr/ddr-test/')
    assert str(i0)  == str(i1)  == ORG_REPR
    assert i0.id    == i1.id    == ORG_ID
    assert i0.model == i1.model == ORG_MODEL
    assert i0.basepath == i1.basepath == BASE_PATH

def test_organization_from_url():
    i0 = Identifier.from_url('http://192.168.56.101/ddr/test')
    i1 = Identifier.from_url('http://192.168.56.101/ddr/test/', BASE_PATH)
    assert str(i0)  == str(i1)  == ORG_REPR
    assert i0.id    == i1.id    == ORG_ID
    assert i0.model == i1.model == ORG_MODEL
    assert i0.basepath == None
    assert i1.basepath == BASE_PATH


COLLECTION_ID = 'ddr-test-123'
COLLECTION_REPR = '<Identifier ddr-test-123>'
COLLECTION_MODEL = 'collection'

def test_collection_from_id():
    i0 = Identifier.from_id('ddr-test-123')
    i1 = Identifier.from_id('ddr-test-123', BASE_PATH)
    assert str(i0)  == str(i1)  == COLLECTION_REPR
    assert i0.id    == i1.id    == COLLECTION_ID
    assert i0.model == i1.model == COLLECTION_MODEL
    assert i0.basepath == None
    assert i1.basepath == BASE_PATH

def test_collection_from_idparts():
    i0 = Identifier.from_idparts(
        {'model':'collection', 'repo':'ddr', 'org':'test', 'cid':123,}
    )
    i1 = Identifier.from_idparts(
        {'model':'collection', 'repo':'ddr', 'org':'test', 'cid':123,},
        BASE_PATH
    )
    assert str(i0)  == str(i1)  == COLLECTION_REPR
    assert i0.id    == i1.id    == COLLECTION_ID
    assert i0.model == i1.model == COLLECTION_MODEL
    assert i0.basepath == None
    assert i1.basepath == BASE_PATH

def test_collection_from_path():
    i0 = Identifier.from_path('/var/www/media/ddr/ddr-test-123')
    i1 = Identifier.from_path('/var/www/media/ddr/ddr-test-123/')
    assert str(i0)  == str(i1)  == COLLECTION_REPR
    assert i0.id    == i1.id    == COLLECTION_ID
    assert i0.model == i1.model == COLLECTION_MODEL
    assert i0.basepath == i1.basepath == BASE_PATH

def test_collection_from_url():
    i0 = Identifier.from_url('http://192.168.56.101/ddr/test/123')
    i1 = Identifier.from_url('http://192.168.56.101/ddr/test/123/')
    i2 = Identifier.from_url('http://192.168.56.101/ddr/test/123/', BASE_PATH)
    assert str(i0)  == str(i1)  == COLLECTION_REPR
    assert i0.id    == i1.id    == COLLECTION_ID
    assert i0.model == i1.model == COLLECTION_MODEL
    assert i0.basepath == i1.basepath == None
    assert i2.basepath == BASE_PATH


ENTITY_ID = 'ddr-test-123-456'
ENTITY_REPR = '<Identifier ddr-test-123-456>'
ENTITY_MODEL = 'entity'

def test_entity_from_id():
    i0 = Identifier.from_id('ddr-test-123-456')
    i1 = Identifier.from_id('ddr-test-123-456', BASE_PATH)
    assert str(i0)  == str(i1)  == ENTITY_REPR
    assert i0.id    == i1.id    == ENTITY_ID
    assert i0.model == i1.model == ENTITY_MODEL
    assert i0.basepath == None
    assert i1.basepath == BASE_PATH

def test_entity_from_idparts():
    i0 = Identifier.from_idparts(
        {'model':'entity', 'repo':'ddr', 'org':'test', 'cid':123, 'eid':456,}
    )
    i1 = Identifier.from_idparts(
        {'model':'entity', 'repo':'ddr', 'org':'test', 'cid':123, 'eid':456,},
        BASE_PATH
    )
    assert str(i0)  == str(i1)  == ENTITY_REPR
    assert i0.id    == i1.id    == ENTITY_ID
    assert i0.model == i1.model == ENTITY_MODEL
    assert i0.basepath == None
    assert i1.basepath == BASE_PATH

def test_entity_from_path():
    i0 = Identifier.from_path('/var/www/media/ddr/ddr-test-123/files/ddr-test-123-456')
    i1 = Identifier.from_path('/var/www/media/ddr/ddr-test-123/files/ddr-test-123-456/')
    assert str(i0)  == str(i1)  == ENTITY_REPR
    assert i0.id    == i1.id    == ENTITY_ID
    assert i0.model == i1.model == ENTITY_MODEL
    assert i0.basepath == i1.basepath == BASE_PATH
    
    i2 = Identifier.from_path('/mnt/nfsdrive/ddr/ddr-test-123/files/ddr-test-123-456')
    assert i2.id == ENTITY_ID
    assert str(i2) == ENTITY_REPR
    assert i2.model == ENTITY_MODEL
    assert i2.basepath == '/mnt/nfsdrive/ddr'

def test_entity_from_url():
    i0 = Identifier.from_url('http://192.168.56.101/ddr/test/123/456')
    i1 = Identifier.from_url('http://192.168.56.101/ddr/test/123/456/', BASE_PATH)
    assert str(i0)  == str(i1)  == ENTITY_REPR
    assert i0.id    == i1.id    == ENTITY_ID
    assert i0.model == i1.model == ENTITY_MODEL
    assert i0.basepath == None
    assert i1.basepath == BASE_PATH


FILE_ID = 'ddr-test-123-456-master-a1b2c3d4e5'
FILE_REPR = '<Identifier ddr-test-123-456-master-a1b2c3d4e5>'
FILE_MODEL = 'file'

def test_file_from_id():
    i0 = Identifier.from_id('ddr-test-123-456-master-a1b2c3d4e5')
    i1 = Identifier.from_id('ddr-test-123-456-master-a1b2c3d4e5', BASE_PATH)
    assert str(i0)  == str(i1)  == FILE_REPR
    assert i0.id    == i1.id    == FILE_ID
    assert i0.model == i1.model == FILE_MODEL
    assert i0.basepath == None
    assert i1.basepath == BASE_PATH

def test_file_from_idparts():
    i0 = Identifier.from_idparts(
        {
            'model':'file',
            'repo':'ddr', 'org':'test', 'cid':123,
            'eid':456, 'role':'master', 'sha1':'a1b2c3d4e5',
        }
    )
    i1 = Identifier.from_idparts(
        {
            'model':'file',
            'repo':'ddr', 'org':'test', 'cid':123,
            'eid':456, 'role':'master', 'sha1':'a1b2c3d4e5',
        },
        BASE_PATH
    )
    assert str(i0)  == str(i1)  == FILE_REPR
    assert i0.id    == i1.id    == FILE_ID
    assert i0.model == i1.model == FILE_MODEL
    assert i0.basepath == None
    assert i1.basepath == BASE_PATH

def test_file_from_path():
    i0 = Identifier.from_path(
        '/var/www/media/ddr/ddr-test-123/files/ddr-test-123-456/files/ddr-test-123-456-master-a1b2c3d4e5'
    )
    i1 = Identifier.from_path(
        '/var/www/media/ddr/ddr-test-123/files/ddr-test-123-456/files/ddr-test-123-456-master-a1b2c3d4e5/'
    )
    assert str(i0)  == str(i1)  == FILE_REPR
    assert i0.id    == i1.id    == FILE_ID
    assert i0.model == i1.model == FILE_MODEL
    assert i0.basepath == i1.basepath == BASE_PATH

def test_file_from_url():
    i0 = Identifier.from_url(
        'http://192.168.56.101/ddr/test/123/456/master/a1b2c3d4e5'
    )
    i1 = Identifier.from_url(
        'http://192.168.56.101/ddr/test/123/456/master/a1b2c3d4e5/',
        BASE_PATH
    )
    assert str(i0)  == str(i1)  == FILE_REPR
    assert i0.id    == i1.id    == FILE_ID
    assert i0.model == i1.model == FILE_MODEL
    assert i0.basepath == None
    assert i1.basepath == BASE_PATH



REPO_COLLECTION_ID = None
ORG_COLLECTION_ID = None
COLLECTION_COLLECTION_ID = 'ddr-test-123'
ENTITY_COLLECTION_ID = 'ddr-test-123'
FILE_COLLECTION_ID = 'ddr-test-123'

def test_collection_id():
    i0 = Identifier.from_id('ddr')
    i1 = Identifier.from_id('ddr-test')
    i2 = Identifier.from_id('ddr-test-123')
    i3 = Identifier.from_id('ddr-test-123-456')
    i4 = Identifier.from_id('ddr-test-123-456-master-a1b2c3d4e5')
    assert_raises(Exception, i0, 'collection_id')
    assert_raises(Exception, i1, 'collection_id')
    assert i2.collection_id() == COLLECTION_COLLECTION_ID
    assert i3.collection_id() == ENTITY_COLLECTION_ID
    assert i4.collection_id() == FILE_COLLECTION_ID



REPO_COLLECTION_PATH = None
ORG_COLLECTION_PATH = None
COLLECTION_COLLECTION_PATH = '/var/www/media/ddr/ddr-test-123'
ENTITY_COLLECTION_PATH = '/var/www/media/ddr/ddr-test-123'
FILE_COLLECTION_PATH = '/var/www/media/ddr/ddr-test-123'

def test_collection_path():
    i0 = Identifier.from_id('ddr')
    i1 = Identifier.from_id('ddr-test')
    i2 = Identifier.from_id('ddr-test-123')
    i3 = Identifier.from_id('ddr-test-123-456')
    i4 = Identifier.from_id('ddr-test-123-456-master-a1b2c3d4e5')
    assert_raises(Exception, i0, 'collection_path')
    assert_raises(Exception, i1, 'collection_path')
    assert_raises(Exception, i2, 'collection_path')
    assert_raises(Exception, i3, 'collection_path')
    assert_raises(Exception, i4, 'collection_path')
    
    i0 = Identifier.from_id('ddr', BASE_PATH)
    i1 = Identifier.from_id('ddr-test', BASE_PATH)
    i2 = Identifier.from_id('ddr-test-123', BASE_PATH)
    i3 = Identifier.from_id('ddr-test-123-456', BASE_PATH)
    i4 = Identifier.from_id('ddr-test-123-456-master-a1b2c3d4e5', BASE_PATH)
    assert_raises(Exception, i0, 'collection_path')
    assert_raises(Exception, i1, 'collection_path')
    assert i2.collection_path() == COLLECTION_COLLECTION_PATH
    assert i3.collection_path() == ENTITY_COLLECTION_PATH
    assert i4.collection_path() == FILE_COLLECTION_PATH



REPO_PARENT_ID       = None
ORG_PARENT_ID        = 'ddr'
COLLECTION_PARENT_ID = 'ddr-test'
ENTITY_PARENT_ID     = 'ddr-test-123'
FILE_PARENT_ID       = 'ddr-test-123-456'

def test_parent_id():
    i0 = Identifier.from_id('ddr')
    i1 = Identifier.from_id('ddr-test')
    i2 = Identifier.from_id('ddr-test-123')
    i3 = Identifier.from_id('ddr-test-123-456')
    i4 = Identifier.from_id('ddr-test-123-456-master-a1b2c3d4e5')
    assert i0.parent_id() == REPO_PARENT_ID
    assert i1.parent_id() == ORG_PARENT_ID
    assert i2.parent_id() == COLLECTION_PARENT_ID
    assert i3.parent_id() == ENTITY_PARENT_ID
    assert i4.parent_id() == FILE_PARENT_ID



REPO_PATH_ABS       = '/var/www/media/ddr/ddr'
ORG_PATH_ABS        = '/var/www/media/ddr/ddr-test'
COLLECTION_PATH_ABS = '/var/www/media/ddr/ddr-test-123'
ENTITY_PATH_ABS     = '/var/www/media/ddr/ddr-test-123/files/ddr-test-123-456'
FILE_PATH_ABS       = '/var/www/media/ddr/ddr-test-123/files/ddr-test-123-456/files/ddr-test-123-456-master-a1b2c3d4e5'
REPO_PATH_ABS_JSON       = '/var/www/media/ddr/ddr/repository.json'
ORG_PATH_ABS_JSON        = '/var/www/media/ddr/ddr-test/organization.json'
COLLECTION_PATH_ABS_JSON = '/var/www/media/ddr/ddr-test-123/collection.json'
ENTITY_PATH_ABS_JSON     = '/var/www/media/ddr/ddr-test-123/files/ddr-test-123-456/entity.json'
FILE_PATH_ABS_JSON       = '/var/www/media/ddr/ddr-test-123/files/ddr-test-123-456/files/ddr-test-123-456-master-a1b2c3d4e5/ddr-test-123-456-master-a1b2c3d4e5.json'
FILE_PATH_ABS_ACCESS = '/var/www/media/ddr/ddr-test-123/files/ddr-test-123-456/files/ddr-test-123-456-master-a1b2c3d4e5/ddr-test-123-456-master-a1b2c3d4e5-a.jpg'

def test_path_abs():
    ri0 = Identifier.from_id(
        'ddr'
    )
    assert_raises(Exception, ri0, 'path_abs')
    assert_raises(Exception, ri0, 'path_abs', 'json')
    assert_raises(Exception, ri0, 'path_abs', 'BAD')
    ri1 = Identifier.from_id(
        'ddr',
        BASE_PATH
    )
    assert ri1.path_abs()       == REPO_PATH_ABS
    assert ri1.path_abs('json') == REPO_PATH_ABS_JSON
    assert_raises(Exception, ri1, 'path_abs', 'BAD')
    
    oi0 = Identifier.from_id(
        'ddr-test'
    )
    assert_raises(Exception, oi0, 'path_abs')
    assert_raises(Exception, oi0, 'path_abs', 'json')
    assert_raises(Exception, oi0, 'path_abs', 'BAD')
    oi1 = Identifier.from_id(
        'ddr-test',
        BASE_PATH
    )
    assert oi1.path_abs()       == ORG_PATH_ABS
    assert oi1.path_abs('json') == ORG_PATH_ABS_JSON
    assert_raises(Exception, oi1, 'path_abs', 'BAD')
    
    ci0 = Identifier.from_id(
        'ddr-test-123'
    )
    assert_raises(Exception, ci0, 'path_abs')
    assert_raises(Exception, ci0, 'path_abs', 'json')
    assert_raises(Exception, ci0, 'path_abs', 'BAD')
    ci1 = Identifier.from_id(
        'ddr-test-123',
        BASE_PATH
    )
    assert ci1.path_abs()       == COLLECTION_PATH_ABS
    assert ci1.path_abs('json') == COLLECTION_PATH_ABS_JSON
    assert_raises(Exception, ci1, 'path_abs', 'BAD')
    
    ei0 = Identifier.from_id(
        'ddr-test-123-456'
    )
    assert_raises(Exception, ei0, 'path_abs')
    assert_raises(Exception, ei0, 'path_abs', 'json')
    assert_raises(Exception, ei0, 'path_abs', 'BAD')
    ei1 = Identifier.from_id(
        'ddr-test-123-456',
        BASE_PATH
    )
    assert ei1.path_abs()       == ENTITY_PATH_ABS
    assert ei1.path_abs('json') == ENTITY_PATH_ABS_JSON
    assert_raises(Exception, ei1, 'path_abs', 'BAD')
    
    fi0 = Identifier.from_id(
        'ddr-test-123-456-master-a1b2c3d4e5'
    )
    assert_raises(Exception, fi0, 'path_abs')
    assert_raises(Exception, fi0, 'path_abs', 'access')
    assert_raises(Exception, fi0, 'path_abs', 'json')
    assert_raises(Exception, fi0, 'path_abs', 'BAD')
    fi1 = Identifier.from_id(
        'ddr-test-123-456-master-a1b2c3d4e5',
        BASE_PATH
    )
    assert fi1.path_abs()         == FILE_PATH_ABS
    assert fi1.path_abs('access') == FILE_PATH_ABS_ACCESS
    assert fi1.path_abs('json')   == FILE_PATH_ABS_JSON
    assert_raises(Exception, fi1, 'path_abs', 'BAD')
    
    fi2 = Identifier.from_path('/mnt/nfsdrive/ddr/ddr-test-123/files/ddr-test-123-456')
    assert fi2.path_abs()       == '/mnt/nfsdrive/ddr/ddr-test-123/files/ddr-test-123-456'
    assert fi2.path_abs('json') == '/mnt/nfsdrive/ddr/ddr-test-123/files/ddr-test-123-456/entity.json'



REPO_PATH_REL       = None
ORG_PATH_REL        = None
COLLECTION_PATH_REL = None
ENTITY_PATH_REL     = 'files/ddr-test-123-456'
FILE_PATH_REL       = 'files/ddr-test-123-456/files/ddr-test-123-456-master-a1b2c3d4e5'
REPO_PATH_REL_JSON       = 'repository.json'
ORG_PATH_REL_JSON        = 'organization.json'
COLLECTION_PATH_REL_JSON = 'collection.json'
ENTITY_PATH_REL_JSON     = 'files/ddr-test-123-456/entity.json'
FILE_PATH_REL_JSON       = 'files/ddr-test-123-456/files/ddr-test-123-456-master-a1b2c3d4e5/ddr-test-123-456-master-a1b2c3d4e5.json'    
FILE_PATH_REL_ACCESS = 'files/ddr-test-123-456/files/ddr-test-123-456-master-a1b2c3d4e5/ddr-test-123-456-master-a1b2c3d4e5-a.jpg'

def test_path_rel():
    i0 = Identifier.from_id('ddr')
    assert i0.path_rel()         == REPO_PATH_REL
    assert i0.path_rel('json')   == REPO_PATH_REL_JSON
    assert_raises(Exception, i0, 'path_rel', 'BAD')
    
    i1 = Identifier.from_id('ddr-test')
    assert i1.path_rel()         == ORG_PATH_REL
    assert i1.path_rel('json')   == ORG_PATH_REL_JSON
    assert_raises(Exception, i1, 'path_rel', 'BAD')
    
    i2 = Identifier.from_id('ddr-test-123')
    assert i2.path_rel()         == COLLECTION_PATH_REL
    assert i2.path_rel('json')   == COLLECTION_PATH_REL_JSON
    assert_raises(Exception, i2, 'path_rel', 'BAD')
    
    i3 = Identifier.from_id('ddr-test-123-456')
    assert i3.path_rel()         == ENTITY_PATH_REL
    assert i3.path_rel('json')   == ENTITY_PATH_REL_JSON
    assert_raises(Exception, i3, 'path_rel', 'BAD')
    
    i4 = Identifier.from_id('ddr-test-123-456-master-a1b2c3d4e5')
    assert i4.path_rel()         == FILE_PATH_REL
    assert i4.path_rel('access') == FILE_PATH_REL_ACCESS
    assert i4.path_rel('json')   == FILE_PATH_REL_JSON
    assert_raises(Exception, i4, 'path_rel', 'BAD')


REPO_EDITOR_URL       = '/ui/ddr'
ORG_EDITOR_URL        = '/ui/ddr-test'
COLLECTION_EDITOR_URL = '/ui/ddr-test-123'
ENTITY_EDITOR_URL     = '/ui/ddr-test-123-456'
FILE_EDITOR_URL       = '/ui/ddr-test-123-456-master-a1b2c3d4e5'
REPO_PUBLIC_URL       = '/ddr'
ORG_PUBLIC_URL        = '/ddr/test'
COLLECTION_PUBLIC_URL = '/ddr/test/123'
ENTITY_PUBLIC_URL     = '/ddr/test/123/456'
FILE_PUBLIC_URL       = '/ddr/test/123/456/master/a1b2c3d4e5'

def test_urlpath():
    i0 = Identifier.from_id('ddr')
    assert i0.urlpath('editor') == REPO_EDITOR_URL
    assert i0.urlpath('public') == REPO_PUBLIC_URL
    
    i1 = Identifier.from_id('ddr-test')
    assert i1.urlpath('editor') == ORG_EDITOR_URL
    assert i1.urlpath('public') == ORG_PUBLIC_URL
    
    i2 = Identifier.from_id('ddr-test-123')
    assert i2.urlpath('editor') == COLLECTION_EDITOR_URL
    assert i2.urlpath('public') == COLLECTION_PUBLIC_URL
    
    i3 = Identifier.from_id('ddr-test-123-456')
    assert i3.urlpath('editor') == ENTITY_EDITOR_URL
    assert i3.urlpath('public') == ENTITY_PUBLIC_URL
    
    i4 = Identifier.from_id('ddr-test-123-456-master-a1b2c3d4e5')
    assert i4.urlpath('editor') == FILE_EDITOR_URL
    assert i4.urlpath('public') == FILE_PUBLIC_URL
