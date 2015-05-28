# coding: utf-8

from datetime import datetime
import json
import os

from nose.tools import assert_raises

from DDR.models.identifier import Identifier


# repository -----------------------------------------------------------

REPO_ID = 'ddr'
REPO_REPR = '<Identifier ddr>'
REPO_MODEL = 'repository'
REPO_PARENT_ID = None
REPO_PATH_ABS = '/var/www/media/ddr/ddr'
REPO_PATH_REL = None
REPO_PATH_ABS_JSON = '/var/www/media/ddr/ddr/repository.json'
REPO_PATH_REL_JSON = 'repository.json'

def test_repository_from_id():
    i0 = Identifier.from_id('ddr')
    assert i0.id == REPO_ID
    assert str(i0) == REPO_REPR
    assert i0.model == REPO_MODEL
    assert_raises(Exception, i0, 'collection_id')
    assert i0.parent_id() == REPO_PARENT_ID
    assert_raises(Exception, i0, 'path_abs')
    assert_raises(Exception, i0, 'path_abs', 'json')
    assert_raises(Exception, i0, 'path_abs', 'BAD')
    assert i0.path_rel() == REPO_PATH_REL
    assert i0.path_rel('json') == REPO_PATH_REL_JSON
    assert_raises(Exception, i0, 'path_rel', 'BAD')
    
    i1 = Identifier.from_id('ddr', '/var/www/media/ddr')
    assert i1.id == REPO_ID
    assert str(i1) == REPO_REPR
    assert i1.model == REPO_MODEL
    assert_raises(Exception, i0, 'collection_id')
    assert i1.parent_id() == REPO_PARENT_ID
    assert i1.path_abs() == REPO_PATH_ABS
    assert i1.path_rel() == REPO_PATH_REL
    assert i1.path_abs('json') == REPO_PATH_ABS_JSON
    assert i1.path_rel('json') == REPO_PATH_REL_JSON
    assert_raises(Exception, i1, 'path_abs', 'BAD')
    assert_raises(Exception, i1, 'path_rel', 'BAD')

def test_repository_from_idparts():
    i0 = Identifier.from_idparts(
        {'model':'repository', 'repo':'ddr',}
    )
    assert i0.id == REPO_ID
    assert str(i0) == REPO_REPR
    assert i0.model == REPO_MODEL
    assert_raises(Exception, i0, 'collection_id')
    assert i0.parent_id() == REPO_PARENT_ID
    assert_raises(Exception, i0, 'path_abs')
    assert_raises(Exception, i0, 'path_abs', 'json')
    assert_raises(Exception, i0, 'path_abs', 'BAD')
    assert i0.path_rel() == REPO_PATH_REL
    assert i0.path_rel('json') == REPO_PATH_REL_JSON
    assert_raises(Exception, i0, 'path_rel', 'BAD')
    
    i1 = Identifier.from_idparts(
        {'model':'repository', 'repo':'ddr',},
        '/var/www/media/ddr'
    )
    assert i1.id == REPO_ID
    assert str(i1) == REPO_REPR
    assert i1.model == REPO_MODEL
    assert_raises(Exception, i0, 'collection_id')
    assert i1.parent_id() == REPO_PARENT_ID
    assert i1.path_abs() == REPO_PATH_ABS
    assert i1.path_rel() == REPO_PATH_REL
    assert i1.path_abs('json') == REPO_PATH_ABS_JSON
    assert i1.path_rel('json') == REPO_PATH_REL_JSON
    assert_raises(Exception, i1, 'path_abs', 'BAD')
    assert_raises(Exception, i1, 'path_rel', 'BAD')

def test_repository_from_path():
    i0 = Identifier.from_path('/var/www/media/ddr/ddr')
    assert i0.id == REPO_ID
    assert str(i0) == REPO_REPR
    assert i0.model == REPO_MODEL
    assert_raises(Exception, i0, 'collection_id')
    assert i0.parent_id() == REPO_PARENT_ID
    assert i0.path_abs() == REPO_PATH_ABS
    assert_raises(Exception, i0, 'path_abs', 'json')
    assert_raises(Exception, i0, 'path_abs', 'BAD')
    assert i0.path_rel() == REPO_PATH_REL
    assert i0.path_rel('json') == REPO_PATH_REL_JSON
    assert_raises(Exception, i0, 'path_rel', 'BAD')

def test_repository_from_url():
    i0 = Identifier.from_url('http://192.168.56.101/ddr')
    assert i0.id == REPO_ID
    assert str(i0) == REPO_REPR
    assert i0.model == REPO_MODEL
    assert_raises(Exception, i0, 'collection_id')
    assert i0.parent_id() == REPO_PARENT_ID
    assert_raises(Exception, i0, 'path_abs')
    assert_raises(Exception, i0, 'path_abs', 'json')
    assert_raises(Exception, i0, 'path_abs', 'BAD')
    assert i0.path_rel() == REPO_PATH_REL
    assert i0.path_rel('json') == REPO_PATH_REL_JSON
    assert_raises(Exception, i0, 'path_rel', 'BAD')
    
    i1 = Identifier.from_url('http://192.168.56.101/ddr/', '/var/www/media/ddr')
    assert i1.id == REPO_ID
    assert str(i1) == REPO_REPR
    assert i1.model == REPO_MODEL
    assert_raises(Exception, i0, 'collection_id')
    assert i1.parent_id() == REPO_PARENT_ID
    assert i1.path_abs() == REPO_PATH_ABS
    assert i1.path_rel() == REPO_PATH_REL
    assert i1.path_abs('json') == REPO_PATH_ABS_JSON
    assert i1.path_rel('json') == REPO_PATH_REL_JSON
    assert_raises(Exception, i1, 'path_abs', 'BAD')
    assert_raises(Exception, i1, 'path_rel', 'BAD')


# organization ---------------------------------------------------------

ORG_ID = 'ddr-test'
ORG_REPR = '<Identifier ddr-test>'
ORG_MODEL = 'organization'
ORG_PARENT_ID = 'ddr'
ORG_PATH_ABS = '/var/www/media/ddr/ddr-test'
ORG_PATH_REL = None
ORG_PATH_ABS_JSON = '/var/www/media/ddr/ddr-test/organization.json'
ORG_PATH_REL_JSON = 'organization.json'

def test_organization_from_id():
    i0 = Identifier.from_id('ddr-test')
    assert i0.id == ORG_ID
    assert str(i0) == ORG_REPR
    assert i0.model == ORG_MODEL
    assert_raises(Exception, i0, 'collection_id')
    assert i0.parent_id() == ORG_PARENT_ID
    assert_raises(Exception, i0, 'path_abs')
    assert_raises(Exception, i0, 'path_abs', 'json')
    assert_raises(Exception, i0, 'path_abs', 'BAD')
    assert i0.path_rel() == ORG_PATH_REL
    assert i0.path_rel('json') == ORG_PATH_REL_JSON
    assert_raises(Exception, i0, 'path_rel', 'BAD')
    
    i1 = Identifier.from_id('ddr-test', '/var/www/media/ddr')
    assert i1.id == ORG_ID
    assert str(i1) == ORG_REPR
    assert i1.model == ORG_MODEL
    assert_raises(Exception, i0, 'collection_id')
    assert i1.parent_id() == ORG_PARENT_ID
    assert i1.path_abs() == ORG_PATH_ABS
    assert i1.path_rel() == ORG_PATH_REL
    assert i1.path_abs('json') == ORG_PATH_ABS_JSON
    assert i1.path_rel('json') == ORG_PATH_REL_JSON
    assert_raises(Exception, i1, 'path_abs', 'BAD')
    assert_raises(Exception, i1, 'path_rel', 'BAD')

def test_organization_from_idparts():
    i0 = Identifier.from_idparts(
        {'model':'organization', 'repo':'ddr', 'org':'test',}
    )
    assert i0.id == ORG_ID
    assert str(i0) == ORG_REPR
    assert i0.model == ORG_MODEL
    assert_raises(Exception, i0, 'collection_id')
    assert i0.parent_id() == ORG_PARENT_ID
    assert_raises(Exception, i0, 'path_abs')
    assert_raises(Exception, i0, 'path_abs', 'json')
    assert_raises(Exception, i0, 'path_abs', 'BAD')
    assert i0.path_rel() == ORG_PATH_REL
    assert i0.path_rel('json') == ORG_PATH_REL_JSON
    assert_raises(Exception, i0, 'path_rel', 'BAD')
    
    i1 = Identifier.from_idparts(
        {'model':'organization', 'repo':'ddr', 'org':'test',},
        '/var/www/media/ddr'
    )
    assert i1.id == ORG_ID
    assert str(i1) == ORG_REPR
    assert i1.model == ORG_MODEL
    assert_raises(Exception, i0, 'collection_id')
    assert i1.parent_id() == ORG_PARENT_ID
    assert i1.path_abs() == ORG_PATH_ABS
    assert i1.path_rel() == ORG_PATH_REL
    assert i1.path_abs('json') == ORG_PATH_ABS_JSON
    assert i1.path_rel('json') == ORG_PATH_REL_JSON
    assert_raises(Exception, i1, 'path_abs', 'BAD')
    assert_raises(Exception, i1, 'path_rel', 'BAD')

def test_organization_from_path():
    i0 = Identifier.from_path('/var/www/media/ddr/ddr-test')
    assert i0.id == ORG_ID
    assert str(i0) == ORG_REPR
    assert i0.model == ORG_MODEL
    assert_raises(Exception, i0, 'collection_id')
    assert i0.parent_id() == ORG_PARENT_ID
    assert_raises(Exception, i0, 'path_abs')
    assert_raises(Exception, i0, 'path_abs', 'json')
    assert_raises(Exception, i0, 'path_abs', 'BAD')
    assert i0.path_rel() == ORG_PATH_REL
    assert i0.path_rel('json') == ORG_PATH_REL_JSON
    assert_raises(Exception, i0, 'path_rel', 'BAD')
    
    i1 = Identifier.from_path('/var/www/media/ddr/ddr-test/')
    assert i1.id == ORG_ID
    assert str(i1) == ORG_REPR
    assert i1.model == ORG_MODEL
    assert_raises(Exception, i0, 'collection_id')
    assert i1.parent_id() == ORG_PARENT_ID
    assert i1.path_abs() == ORG_PATH_ABS
    assert i1.path_rel() == ORG_PATH_REL
    assert i1.path_abs('json') == ORG_PATH_ABS_JSON
    assert i1.path_rel('json') == ORG_PATH_REL_JSON
    assert_raises(Exception, i1, 'path_abs', 'BAD')
    assert_raises(Exception, i1, 'path_rel', 'BAD')

def test_organization_from_url():
    i0 = Identifier.from_url('http://192.168.56.101/ddr/test')
    assert i0.id == ORG_ID
    assert str(i0) == ORG_REPR
    assert i0.model == ORG_MODEL
    assert_raises(Exception, i0, 'collection_id')
    assert i0.parent_id() == ORG_PARENT_ID
    assert_raises(Exception, i0, 'path_abs')
    assert_raises(Exception, i0, 'path_abs', 'json')
    assert_raises(Exception, i0, 'path_abs', 'BAD')
    assert i0.path_rel() == ORG_PATH_REL
    assert i0.path_rel('json') == ORG_PATH_REL_JSON
    assert_raises(Exception, i0, 'path_rel', 'BAD')
    
    i1 = Identifier.from_url('http://192.168.56.101/ddr/test/', '/var/www/media/ddr')
    assert i1.id == ORG_ID
    assert str(i1) == ORG_REPR
    assert i1.model == ORG_MODEL
    assert_raises(Exception, i0, 'collection_id')
    assert i1.parent_id() == ORG_PARENT_ID
    assert i1.path_abs() == ORG_PATH_ABS
    assert i1.path_rel() == ORG_PATH_REL
    assert i1.path_abs('json') == ORG_PATH_ABS_JSON
    assert i1.path_rel('json') == ORG_PATH_REL_JSON
    assert_raises(Exception, i1, 'path_abs', 'BAD')
    assert_raises(Exception, i1, 'path_rel', 'BAD')


# collection -----------------------------------------------------------

COLLECTION_ID = 'ddr-test-123'
COLLECTION_REPR = '<Identifier ddr-test-123>'
COLLECTION_MODEL = 'collection'
COLLECTION_COLLECTION_ID = 'ddr-test-123'
COLLECTION_COLLECTION_PATH = '/var/www/media/ddr/ddr-test-123'
COLLECTION_PARENT_ID = 'ddr-test'
COLLECTION_PATH_ABS = '/var/www/media/ddr/ddr-test-123'
COLLECTION_PATH_REL = None
COLLECTION_PATH_ABS_JSON = '/var/www/media/ddr/ddr-test-123/collection.json'
COLLECTION_PATH_REL_JSON = 'collection.json'

def test_collection_from_id():
    i0 = Identifier.from_id('ddr-test-123')
    assert i0.id == COLLECTION_ID
    assert str(i0) == COLLECTION_REPR
    assert i0.model == COLLECTION_MODEL
    assert i0.collection_id() == COLLECTION_COLLECTION_ID
    assert_raises(Exception, i0, 'collection_path')
    assert i0.parent_id() == COLLECTION_PARENT_ID
    assert_raises(Exception, i0, 'path_abs')
    assert_raises(Exception, i0, 'path_abs', 'json')
    assert_raises(Exception, i0, 'path_abs', 'BAD')
    assert i0.path_rel() == COLLECTION_PATH_REL
    assert i0.path_rel('json') == COLLECTION_PATH_REL_JSON
    assert_raises(Exception, i0, 'path_rel', 'BAD')
    
    i1 = Identifier.from_id('ddr-test-123', '/var/www/media/ddr')
    assert i1.id == COLLECTION_ID
    assert str(i1) == COLLECTION_REPR
    assert i1.model == COLLECTION_MODEL
    assert i1.collection_id() == COLLECTION_COLLECTION_ID
    assert i1.collection_path() == COLLECTION_COLLECTION_PATH
    assert i1.parent_id() == COLLECTION_PARENT_ID
    assert i1.path_abs() == COLLECTION_PATH_ABS
    assert i1.path_rel() == COLLECTION_PATH_REL
    assert i1.path_abs('json') == COLLECTION_PATH_ABS_JSON
    assert i1.path_rel('json') == COLLECTION_PATH_REL_JSON
    assert_raises(Exception, i1, 'path_abs', 'BAD')
    assert_raises(Exception, i1, 'path_rel', 'BAD')

def test_collection_from_idparts():
    i0 = Identifier.from_idparts(
        {'model':'collection', 'repo':'ddr', 'org':'test', 'cid':123,}
    )
    assert i0.id == COLLECTION_ID
    assert str(i0) == COLLECTION_REPR
    assert i0.model == COLLECTION_MODEL
    assert i0.collection_id() == COLLECTION_COLLECTION_ID
    assert_raises(Exception, i0, 'collection_path')
    assert i0.parent_id() == COLLECTION_PARENT_ID
    assert_raises(Exception, i0, 'path_abs')
    assert_raises(Exception, i0, 'path_abs', 'json')
    assert_raises(Exception, i0, 'path_abs', 'BAD')
    assert i0.path_rel() == COLLECTION_PATH_REL
    assert i0.path_rel('json') == COLLECTION_PATH_REL_JSON
    assert_raises(Exception, i0, 'path_rel', 'BAD')
    
    i1 = Identifier.from_idparts(
        {'model':'collection', 'repo':'ddr', 'org':'test', 'cid':123,},
        '/var/www/media/ddr'
    )
    assert i1.id == COLLECTION_ID
    assert str(i1) == COLLECTION_REPR
    assert i1.model == COLLECTION_MODEL
    assert i1.collection_id() == COLLECTION_COLLECTION_ID
    assert i1.collection_path() == COLLECTION_COLLECTION_PATH
    assert i1.parent_id() == COLLECTION_PARENT_ID
    assert i1.path_abs() == COLLECTION_PATH_ABS
    assert i1.path_rel() == COLLECTION_PATH_REL
    assert i1.path_abs('json') == COLLECTION_PATH_ABS_JSON
    assert i1.path_rel('json') == COLLECTION_PATH_REL_JSON
    assert_raises(Exception, i1, 'path_abs', 'BAD')
    assert_raises(Exception, i1, 'path_rel', 'BAD')

def test_collection_from_path():
    i0 = Identifier.from_path('/var/www/media/ddr/ddr-test-123')
    assert i0.id == COLLECTION_ID
    assert str(i0) == COLLECTION_REPR
    assert i0.model == COLLECTION_MODEL
    assert i0.collection_id() == COLLECTION_COLLECTION_ID
    assert_raises(Exception, i0, 'collection_path')
    assert i0.parent_id() == COLLECTION_PARENT_ID
    assert_raises(Exception, i0, 'path_abs')
    assert_raises(Exception, i0, 'path_abs', 'json')
    assert_raises(Exception, i0, 'path_abs', 'BAD')
    assert i0.path_rel() == COLLECTION_PATH_REL
    assert i0.path_rel('json') == COLLECTION_PATH_REL_JSON
    assert_raises(Exception, i0, 'path_rel', 'BAD')
    
    i1 = Identifier.from_path('/var/www/media/ddr/ddr-test-123/')
    assert i1.id == COLLECTION_ID
    assert str(i1) == COLLECTION_REPR
    assert i1.model == COLLECTION_MODEL
    assert i1.collection_id() == COLLECTION_COLLECTION_ID
    assert i1.collection_path() == COLLECTION_COLLECTION_PATH
    assert i1.parent_id() == COLLECTION_PARENT_ID
    assert i1.path_abs() == COLLECTION_PATH_ABS
    assert i1.path_rel() == COLLECTION_PATH_REL
    assert i1.path_abs('json') == COLLECTION_PATH_ABS_JSON
    assert i1.path_rel('json') == COLLECTION_PATH_REL_JSON
    assert_raises(Exception, i1, 'path_abs', 'BAD')
    assert_raises(Exception, i1, 'path_rel', 'BAD')

def test_collection_from_url():
    i0 = Identifier.from_url('http://192.168.56.101/ddr/test/123')
    assert i0.id == COLLECTION_ID
    assert str(i0) == COLLECTION_REPR
    assert i0.model == COLLECTION_MODEL
    assert i0.collection_id() == COLLECTION_COLLECTION_ID
    assert_raises(Exception, i0, 'collection_path')
    assert i0.parent_id() == COLLECTION_PARENT_ID
    assert_raises(Exception, i0, 'path_abs')
    assert_raises(Exception, i0, 'path_abs', 'json')
    assert_raises(Exception, i0, 'path_abs', 'BAD')
    assert i0.path_rel() == COLLECTION_PATH_REL
    assert i0.path_rel('json') == COLLECTION_PATH_REL_JSON
    assert_raises(Exception, i0, 'path_rel', 'BAD')
    
    i1 = Identifier.from_url('http://192.168.56.101/ddr/test/123/')
    assert i1.id == COLLECTION_ID
    assert str(i1) == COLLECTION_REPR
    assert i1.model == COLLECTION_MODEL
    assert i1.collection_id() == COLLECTION_COLLECTION_ID
    assert_raises(Exception, i1, 'collection_path')
    assert i1.parent_id() == COLLECTION_PARENT_ID
    assert_raises(Exception, i1, 'path_abs')
    assert_raises(Exception, i1, 'path_abs', 'json')
    assert_raises(Exception, i1, 'path_abs', 'BAD')
    assert i1.path_rel() == COLLECTION_PATH_REL
    assert i1.path_rel('json') == COLLECTION_PATH_REL_JSON
    assert_raises(Exception, i1, 'path_rel', 'BAD')
    
    i2 = Identifier.from_url('http://192.168.56.101/ddr/test/123/', '/var/www/media/ddr')
    assert i2.id == COLLECTION_ID
    assert str(i2) == COLLECTION_REPR
    assert i2.model == COLLECTION_MODEL
    assert i2.collection_id() == COLLECTION_COLLECTION_ID
    assert i2.collection_path() == COLLECTION_COLLECTION_PATH
    assert i2.parent_id() == COLLECTION_PARENT_ID
    assert i2.path_abs() == COLLECTION_PATH_ABS
    assert i2.path_rel() == COLLECTION_PATH_REL
    assert i2.path_abs('json') == COLLECTION_PATH_ABS_JSON
    assert i2.path_rel('json') == COLLECTION_PATH_REL_JSON
    assert_raises(Exception, i2, 'path_abs', 'BAD')
    assert_raises(Exception, i2, 'path_rel', 'BAD')


# entity ---------------------------------------------------------------

ENTITY_ID = 'ddr-test-123-456'
ENTITY_REPR = '<Identifier ddr-test-123-456>'
ENTITY_MODEL = 'entity'
ENTITY_COLLECTION_ID = 'ddr-test-123'
ENTITY_COLLECTION_PATH = '/var/www/media/ddr/ddr-test-123'
ENTITY_PARENT_ID = 'ddr-test-123'
ENTITY_PATH_ABS = '/var/www/media/ddr/ddr-test-123/files/ddr-test-123-456'
ENTITY_PATH_REL = 'files/ddr-test-123-456'
ENTITY_PATH_ABS_JSON = '/var/www/media/ddr/ddr-test-123/files/ddr-test-123-456/entity.json'
ENTITY_PATH_REL_JSON = 'files/ddr-test-123-456/entity.json'

def test_entity_from_id():
    i0 = Identifier.from_id('ddr-test-123-456')
    assert str(i0) == ENTITY_REPR
    assert i0.id == ENTITY_ID
    assert i0.model == ENTITY_MODEL
    assert i0.collection_id() == ENTITY_COLLECTION_ID
    assert_raises(Exception, i0, 'collection_path')
    assert i0.parent_id() == ENTITY_PARENT_ID
    assert_raises(Exception, i0, 'path_abs')
    assert_raises(Exception, i0, 'path_abs', 'json')
    assert_raises(Exception, i0, 'path_abs', 'BAD')
    assert i0.path_rel() == ENTITY_PATH_REL
    assert i0.path_rel('json') == ENTITY_PATH_REL_JSON
    assert_raises(Exception, i0, 'path_rel', 'BAD')
    
    i1 = Identifier.from_id('ddr-test-123-456', '/var/www/media/ddr')
    assert i1.id == ENTITY_ID
    assert str(i1) == ENTITY_REPR
    assert i1.model == ENTITY_MODEL
    assert i1.collection_id() == ENTITY_COLLECTION_ID
    assert i1.collection_path() == ENTITY_COLLECTION_PATH
    assert i1.parent_id() == ENTITY_PARENT_ID
    assert i1.path_abs() == ENTITY_PATH_ABS
    assert i1.path_rel() == ENTITY_PATH_REL
    assert i1.path_abs('json') == ENTITY_PATH_ABS_JSON
    assert i1.path_rel('json') == ENTITY_PATH_REL_JSON
    assert_raises(Exception, i1, 'path_abs', 'BAD')
    assert_raises(Exception, i1, 'path_rel', 'BAD')

def test_entity_from_idparts():
    i0 = Identifier.from_idparts(
        {'model':'entity', 'repo':'ddr', 'org':'test', 'cid':123, 'eid':456,}
    )
    assert i0.id == ENTITY_ID
    assert str(i0) == ENTITY_REPR
    assert i0.model == ENTITY_MODEL
    assert i0.collection_id() == ENTITY_COLLECTION_ID
    assert_raises(Exception, i0, 'collection_path')
    assert i0.parent_id() == ENTITY_PARENT_ID
    assert_raises(Exception, i0, 'path_abs')
    assert_raises(Exception, i0, 'path_abs', 'json')
    assert_raises(Exception, i0, 'path_abs', 'BAD')
    assert i0.path_rel() == ENTITY_PATH_REL
    assert i0.path_rel('json') == ENTITY_PATH_REL_JSON
    assert_raises(Exception, i0, 'path_rel', 'BAD')
    
    i1 = Identifier.from_idparts(
        {'model':'entity', 'repo':'ddr', 'org':'test', 'cid':123, 'eid':456,},
        '/var/www/media/ddr'
    )
    assert i1.id == ENTITY_ID
    assert str(i1) == ENTITY_REPR
    assert i1.model == ENTITY_MODEL
    assert i1.collection_id() == ENTITY_COLLECTION_ID
    assert i1.collection_path() == ENTITY_COLLECTION_PATH
    assert i1.parent_id() == ENTITY_PARENT_ID
    assert i1.path_abs() == ENTITY_PATH_ABS
    assert i1.path_rel() == ENTITY_PATH_REL
    assert i1.path_abs('json') == ENTITY_PATH_ABS_JSON
    assert i1.path_rel('json') == ENTITY_PATH_REL_JSON
    assert_raises(Exception, i1, 'path_abs', 'BAD')
    assert_raises(Exception, i1, 'path_rel', 'BAD')

def test_entity_from_path():
    i0 = Identifier.from_path('/var/www/media/ddr/ddr-test-123/files/ddr-test-123-456')
    assert i0.id == ENTITY_ID
    assert str(i0) == ENTITY_REPR
    assert i0.model == ENTITY_MODEL
    assert i0.collection_id() == ENTITY_COLLECTION_ID
    assert_raises(Exception, i0, 'collection_path')
    assert i0.parent_id() == ENTITY_PARENT_ID
    assert_raises(Exception, i0, 'path_abs')
    assert_raises(Exception, i0, 'path_abs', 'json')
    assert_raises(Exception, i0, 'path_abs', 'BAD')
    assert i0.path_rel() == ENTITY_PATH_REL
    assert i0.path_rel('json') == ENTITY_PATH_REL_JSON
    assert_raises(Exception, i0, 'path_rel', 'BAD')
    
    i1 = Identifier.from_path('/var/www/media/ddr/ddr-test-123/files/ddr-test-123-456/')
    assert i1.id == ENTITY_ID
    assert str(i1) == ENTITY_REPR
    assert i1.model == ENTITY_MODEL
    assert i1.collection_id() == ENTITY_COLLECTION_ID
    assert i1.collection_path() == ENTITY_COLLECTION_PATH
    assert i1.parent_id() == ENTITY_PARENT_ID
    assert i1.path_abs() == ENTITY_PATH_ABS
    assert i1.path_rel() == ENTITY_PATH_REL
    assert i1.path_abs('json') == ENTITY_PATH_ABS_JSON
    assert i1.path_rel('json') == ENTITY_PATH_REL_JSON
    assert_raises(Exception, i1, 'path_abs', 'BAD')
    assert_raises(Exception, i1, 'path_rel', 'BAD')
    
    i2 = Identifier.from_path('/mnt/nfsdrive/ddr/ddr-test-123/files/ddr-test-123-456')
    assert i2.id == ENTITY_ID
    assert str(i2) == ENTITY_REPR
    assert i2.model == ENTITY_MODEL
    assert i2.collection_id() == ENTITY_COLLECTION_ID
    assert i2.collection_path() == '/mnt/nfsdrive/ddr/ddr-test-123'
    assert i2.parent_id() == ENTITY_PARENT_ID
    assert i2.path_abs() == '/mnt/nfsdrive/ddr/ddr-test-123/files/ddr-test-123-456'
    assert i2.path_rel()== ENTITY_PATH_REL
    assert i2.path_abs('json') == '/mnt/nfsdrive/ddr/ddr-test-123/files/ddr-test-123-456/entity.json'
    assert i2.path_rel('json') == ENTITY_PATH_REL_JSON
    assert_raises(Exception, i2, 'path_abs', 'BAD')
    assert_raises(Exception, i2, 'path_rel', 'BAD')

def test_entity_from_url():
    i0 = Identifier.from_url('http://192.168.56.101/ddr/test/123/456')
    assert i0.id == ENTITY_ID
    assert str(i0) == ENTITY_REPR
    assert i0.model == ENTITY_MODEL
    assert i0.collection_id() == ENTITY_COLLECTION_ID
    assert_raises(Exception, i0, 'collection_path')
    assert i0.parent_id() == ENTITY_PARENT_ID
    assert_raises(Exception, i0, 'path_abs')
    assert_raises(Exception, i0, 'path_abs', 'json')
    assert_raises(Exception, i0, 'path_abs', 'BAD')
    assert i0.path_rel() == ENTITY_PATH_REL
    assert i0.path_rel('json') == ENTITY_PATH_REL_JSON
    assert_raises(Exception, i0, 'path_rel', 'BAD')
    
    i1 = Identifier.from_url('http://192.168.56.101/ddr/test/123/456/', '/var/www/media/ddr')
    assert i1.id == ENTITY_ID
    assert str(i1) == ENTITY_REPR
    assert i1.model == ENTITY_MODEL
    assert i1.collection_id() == ENTITY_COLLECTION_ID
    assert i1.collection_path() == ENTITY_COLLECTION_PATH
    assert i1.parent_id() == ENTITY_PARENT_ID
    assert i1.path_abs() == ENTITY_PATH_ABS
    assert i1.path_rel() == ENTITY_PATH_REL
    assert i1.path_abs('json') == ENTITY_PATH_ABS_JSON
    assert i1.path_rel('json') == ENTITY_PATH_REL_JSON
    assert_raises(Exception, i1, 'path_abs', 'BAD')
    assert_raises(Exception, i1, 'path_rel', 'BAD')


# file -----------------------------------------------------------------

FILE_ID = 'ddr-test-123-456-master-a1b2c3d4e5'
FILE_REPR = '<Identifier ddr-test-123-456-master-a1b2c3d4e5>'
FILE_MODEL = 'file'
FILE_COLLECTION_ID = 'ddr-test-123'
FILE_COLLECTION_PATH = '/var/www/media/ddr/ddr-test-123'
FILE_PARENT_ID = 'ddr-test-123-456'
FILE_PATH_ABS = '/var/www/media/ddr/ddr-test-123/files/ddr-test-123-456/files/ddr-test-123-456-master-a1b2c3d4e5'
FILE_PATH_REL = 'files/ddr-test-123-456/files/ddr-test-123-456-master-a1b2c3d4e5'
FILE_PATH_ABS_ACCESS = '/var/www/media/ddr/ddr-test-123/files/ddr-test-123-456/files/ddr-test-123-456-master-a1b2c3d4e5/ddr-test-123-456-master-a1b2c3d4e5-a.jpg'
FILE_PATH_REL_ACCESS = 'files/ddr-test-123-456/files/ddr-test-123-456-master-a1b2c3d4e5/ddr-test-123-456-master-a1b2c3d4e5-a.jpg'
FILE_PATH_ABS_JSON = '/var/www/media/ddr/ddr-test-123/files/ddr-test-123-456/files/ddr-test-123-456-master-a1b2c3d4e5/ddr-test-123-456-master-a1b2c3d4e5.json'
FILE_PATH_REL_JSON = 'files/ddr-test-123-456/files/ddr-test-123-456-master-a1b2c3d4e5/ddr-test-123-456-master-a1b2c3d4e5.json'    

def test_file_from_id():
    i0 = Identifier.from_id('ddr-test-123-456-master-a1b2c3d4e5')
    assert i0.id == FILE_ID
    assert str(i0) == FILE_REPR
    assert i0.model == FILE_MODEL
    assert i0.collection_id() == FILE_COLLECTION_ID
    assert_raises(Exception, i0, 'collection_path')
    assert i0.parent_id() == FILE_PARENT_ID
    assert_raises(Exception, i0, 'path_abs')
    assert_raises(Exception, i0, 'path_abs', 'access')
    assert_raises(Exception, i0, 'path_abs', 'json')
    assert_raises(Exception, i0, 'path_abs', 'BAD')
    assert i0.path_rel() == FILE_PATH_REL
    assert i0.path_rel('access') == FILE_PATH_REL_ACCESS
    assert i0.path_rel('json') == FILE_PATH_REL_JSON
    assert_raises(Exception, i0, 'path_rel', 'BAD')
    
    i1 = Identifier.from_id('ddr-test-123-456-master-a1b2c3d4e5', '/var/www/media/ddr')
    assert i1.id == FILE_ID
    assert str(i1) == FILE_REPR
    assert i1.collection_id() == FILE_COLLECTION_ID
    assert i1.collection_path() == FILE_COLLECTION_PATH
    assert i1.parent_id() == FILE_PARENT_ID
    assert i1.path_abs() == FILE_PATH_ABS
    assert i1.path_rel() == FILE_PATH_REL
    assert i1.path_abs('access') == FILE_PATH_ABS_ACCESS
    assert i1.path_rel('access') == FILE_PATH_REL_ACCESS
    assert i1.path_abs('json') == FILE_PATH_ABS_JSON
    assert i1.path_rel('json') == FILE_PATH_REL_JSON
    assert_raises(Exception, i1, 'path_abs', 'BAD')
    assert_raises(Exception, i1, 'path_rel', 'BAD')

def test_file_from_idparts():
    i0 = Identifier.from_idparts(
        {
            'model':'file',
            'repo':'ddr', 'org':'test', 'cid':123,
            'eid':456, 'role':'master', 'sha1':'a1b2c3d4e5',
        }
    )
    assert i0.id == FILE_ID
    assert str(i0) == FILE_REPR
    assert i0.model == FILE_MODEL
    assert i0.collection_id() == FILE_COLLECTION_ID
    assert_raises(Exception, i0, 'collection_path')
    assert i0.parent_id() == FILE_PARENT_ID
    assert_raises(Exception, i0, 'path_abs')
    assert_raises(Exception, i0, 'path_abs', 'access')
    assert_raises(Exception, i0, 'path_abs', 'json')
    assert_raises(Exception, i0, 'path_abs', 'BAD')
    assert i0.path_rel() == FILE_PATH_REL
    assert i0.path_rel('access') == FILE_PATH_REL_ACCESS
    assert i0.path_rel('json') == FILE_PATH_REL_JSON
    assert_raises(Exception, i0, 'path_rel', 'BAD')
    
    i1 = Identifier.from_idparts(
        {
            'model':'file',
            'repo':'ddr', 'org':'test', 'cid':123,
            'eid':456, 'role':'master', 'sha1':'a1b2c3d4e5',
        },
        '/var/www/media/ddr'
    )
    assert i1.id == FILE_ID
    assert str(i1) == FILE_REPR
    assert i1.model == FILE_MODEL
    assert i1.collection_id() == FILE_COLLECTION_ID
    assert i1.collection_path() == FILE_COLLECTION_PATH
    assert i1.parent_id() == FILE_PARENT_ID
    assert i1.path_abs() == FILE_PATH_ABS
    assert i1.path_rel() == FILE_PATH_REL
    assert i1.path_abs('access') == FILE_PATH_ABS_ACCESS
    assert i1.path_rel('access') == FILE_PATH_REL_ACCESS
    assert i1.path_abs('json') == FILE_PATH_ABS_JSON
    assert i1.path_rel('json') == FILE_PATH_REL_JSON
    assert_raises(Exception, i1, 'path_abs', 'BAD')
    assert_raises(Exception, i1, 'path_rel', 'BAD')

def test_file_from_path():
    i0 = Identifier.from_path(
        '/var/www/media/ddr/ddr-test-123/files/ddr-test-123-456/files/ddr-test-123-456-master-a1b2c3d4e5'
    )
    assert i0.id == FILE_ID
    assert str(i0) == FILE_REPR
    assert i0.model == FILE_MODEL
    assert i0.collection_id() == FILE_COLLECTION_ID
    assert_raises(Exception, i0, 'collection_path')
    assert i0.parent_id() == FILE_PARENT_ID
    assert_raises(Exception, i0, 'path_abs')
    assert_raises(Exception, i0, 'path_abs', 'access')
    assert_raises(Exception, i0, 'path_abs', 'json')
    assert_raises(Exception, i0, 'path_abs', 'BAD')
    assert i0.path_rel() == FILE_PATH_REL
    assert i0.path_rel('access') == FILE_PATH_REL_ACCESS
    assert i0.path_rel('json') == FILE_PATH_REL_JSON
    assert_raises(Exception, i0, 'path_rel', 'BAD')
    
    i1 = Identifier.from_path(
        '/var/www/media/ddr/ddr-test-123/files/ddr-test-123-456/files/ddr-test-123-456-master-a1b2c3d4e5/'
    )
    assert i1.id == FILE_ID
    assert str(i1) == FILE_REPR
    assert i1.model == FILE_MODEL
    assert i1.collection_id() == FILE_COLLECTION_ID
    assert i1.collection_path() == FILE_COLLECTION_PATH
    assert i1.parent_id() == FILE_PARENT_ID
    assert i1.path_abs() == FILE_PATH_ABS
    assert i1.path_rel() == FILE_PATH_REL
    assert i1.path_abs('access') == FILE_PATH_ABS_ACCESS
    assert i1.path_rel('access') == FILE_PATH_REL_ACCESS
    assert i1.path_abs('json') == FILE_PATH_ABS_JSON
    assert i1.path_rel('json') == FILE_PATH_REL_JSON
    assert_raises(Exception, i1, 'path_abs', 'BAD')
    assert_raises(Exception, i1, 'path_rel', 'BAD')

def test_file_from_url():
    i0 = Identifier.from_url(
        'http://192.168.56.101/ddr/test/123/456/master/a1b2c3d4e5'
    )
    assert i0.id == FILE_ID
    assert str(i0) == FILE_REPR
    assert i0.model == FILE_MODEL
    assert i0.collection_id() == FILE_COLLECTION_ID
    assert_raises(Exception, i0, 'collection_path')
    assert i0.path_rel('json') == FILE_PATH_REL_JSON
    assert i0.parent_id() == FILE_PARENT_ID
    assert_raises(Exception, i0, 'path_abs')
    assert_raises(Exception, i0, 'path_abs', 'access')
    assert_raises(Exception, i0, 'path_abs', 'json')
    assert_raises(Exception, i0, 'path_abs', 'BAD')
    assert i0.path_rel() == FILE_PATH_REL
    assert i0.path_rel('access') == FILE_PATH_REL_ACCESS
    print(i0.path_rel('json'))
    assert_raises(Exception, i0, 'path_rel', 'BAD')
    
    i1 = Identifier.from_url(
        'http://192.168.56.101/ddr/test/123/456/master/a1b2c3d4e5/',
        '/var/www/media/ddr'
    )
    assert i1.id == FILE_ID
    assert str(i1) == FILE_REPR
    assert i1.model == FILE_MODEL
    assert i1.collection_id() == FILE_COLLECTION_ID
    assert i1.collection_path() == FILE_COLLECTION_PATH
    assert i1.parent_id() == FILE_PARENT_ID
    assert i1.path_abs() == FILE_PATH_ABS
    assert i1.path_rel() == FILE_PATH_REL
    assert i1.path_abs('access') == FILE_PATH_ABS_ACCESS
    assert i1.path_rel('access') == FILE_PATH_REL_ACCESS
    assert i1.path_abs('json') == FILE_PATH_ABS_JSON
    assert i1.path_rel('json') == FILE_PATH_REL_JSON
    assert_raises(Exception, i1, 'path_abs', 'BAD')
    assert_raises(Exception, i1, 'path_rel', 'BAD')


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
