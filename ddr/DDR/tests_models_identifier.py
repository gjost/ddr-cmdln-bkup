# coding: utf-8

from datetime import datetime
import json
import os

from DDR.models.identifier import Identifier


# repository -----------------------------------------------------------

def test_organization_from_id():
    i = Identifier.from_id('ddr')
    assert i.id == 'ddr'
    assert i.model == 'repository'

def test_organization_from_idparts():
    i = Identifier.from_idparts(
        {'model':'repository', 'repo':'ddr',}
    )
    assert i.id == 'ddr'
    assert i.model == 'repository'

def test_organization_from_path():
    i = Identifier.from_path('/var/www/media/ddr/ddr')
    assert i.id == 'ddr'
    assert i.model == 'repository'
    i = Identifier.from_path('/var/www/media/ddr/ddr/')
    assert i.id == 'ddr'
    assert i.model == 'repository'

def test_organization_from_url():
    i = Identifier.from_url('http://192.168.56.101/ddr')
    assert i.id == 'ddr'
    assert i.model == 'repository'
    i = Identifier.from_url('http://192.168.56.101/ddr/')
    assert i.id == 'ddr'
    assert i.model == 'repository'


# organization ---------------------------------------------------------

def test_organization_from_id():
    i = Identifier.from_id('ddr-test')
    assert i.id == 'ddr-test'
    assert i.model == 'organization'

def test_organization_from_idparts():
    i = Identifier.from_idparts(
        {'model':'organization', 'repo':'ddr', 'org':'test',}
    )
    assert i.id == 'ddr-test'
    assert i.model == 'organization'

def test_organization_from_path():
    i = Identifier.from_path('/var/www/media/ddr/ddr-test')
    assert i.id == 'ddr-test'
    assert i.model == 'organization'
    i = Identifier.from_path('/var/www/media/ddr/ddr-test/')
    assert i.id == 'ddr-test'
    assert i.model == 'organization'

def test_organization_from_url():
    i = Identifier.from_url('http://192.168.56.101/ddr/test')
    assert i.id == 'ddr-test'
    assert i.model == 'organization'
    i = Identifier.from_url('http://192.168.56.101/ddr/test/')
    assert i.id == 'ddr-test'
    assert i.model == 'organization'


# collection -----------------------------------------------------------

def test_collection_from_id():
    i = Identifier.from_id('ddr-test-123')
    assert i.id == 'ddr-test-123'
    assert i.model == 'collection'

def test_collection_from_idparts():
    i = Identifier.from_idparts(
        {'model':'collection', 'repo':'ddr', 'org':'test', 'cid':123,}
    )
    assert i.id == 'ddr-test-123'
    assert i.model == 'collection'

def test_collection_from_path():
    i = Identifier.from_path('/var/www/media/ddr/ddr-test-123')
    assert i.id == 'ddr-test-123'
    assert i.model == 'collection'
    i = Identifier.from_path('/var/www/media/ddr/ddr-test-123/')
    assert i.id == 'ddr-test-123'
    assert i.model == 'collection'

def test_collection_from_url():
    i = Identifier.from_url('http://192.168.56.101/ddr/test/123')
    assert i.id == 'ddr-test-123'
    assert i.model == 'collection'
    i = Identifier.from_url('http://192.168.56.101/ddr/test/123/')
    assert i.id == 'ddr-test-123'
    assert i.model == 'collection'


# entity ---------------------------------------------------------------

def test_entity_from_id():
    i = Identifier.from_id('ddr-test-123-456')
    assert i.id == 'ddr-test-123-456'
    assert i.model == 'entity'

def test_entity_from_idparts():
    i = Identifier.from_idparts(
        {'model':'entity', 'repo':'ddr', 'org':'test', 'cid':123, 'eid':456,}
    )
    assert i.id == 'ddr-test-123-456'
    assert i.model == 'entity'

def test_entity_from_path():
    i = Identifier.from_path('/var/www/media/ddr/ddr-test-123/files/ddr-test-123-456')
    assert i.id == 'ddr-test-123-456'
    assert i.model == 'entity'
    i = Identifier.from_path('/var/www/media/ddr/ddr-test-123/files/ddr-test-123-456/')
    assert i.id == 'ddr-test-123-456'
    assert i.model == 'entity'
    i = Identifier.from_path('/mnt/nfsdrive/ddr/ddr-test-123/files/ddr-test-123-456')
    assert i.id == 'ddr-test-123-456'
    assert i.model == 'entity'

def test_entity_from_url():
    i = Identifier.from_url('http://192.168.56.101/ddr/test/123/456')
    assert i.id == 'ddr-test-123-456'
    assert i.model == 'entity'
    i = Identifier.from_url('http://192.168.56.101/ddr/test/123/456/')
    assert i.id == 'ddr-test-123-456'
    assert i.model == 'entity'


# file -----------------------------------------------------------------

def test_file_from_id():
    i = Identifier.from_id('ddr-test-123-456-master-a1b2c3d4e5')
    assert i.id == 'ddr-test-123-456-master-a1b2c3d4e5'
    assert i.model == 'file'

def test_file_from_idparts():
    i = Identifier.from_idparts(
        {
            'model':'file',
            'repo':'ddr', 'org':'test', 'cid':123,
            'eid':456, 'role':'master', 'sha1':'a1b2c3d4e5',
        }
    )
    assert i.id == 'ddr-test-123-456-master-a1b2c3d4e5'
    assert i.model == 'file'

def test_file_from_path():
    i = Identifier.from_path(
        '/var/www/media/ddr/ddr-test-123/files/ddr-test-123-456/files/ddr-test-123-456-master-a1b2c3d4e5'
    )
    assert i.id == 'ddr-test-123-456-master-a1b2c3d4e5'
    assert i.model == 'file'
    i = Identifier.from_path(
        '/var/www/media/ddr/ddr-test-123/files/ddr-test-123-456/files/ddr-test-123-456-master-a1b2c3d4e5/'
    )
    assert i.id == 'ddr-test-123-456-master-a1b2c3d4e5'
    assert i.model == 'file'

def test_file_from_url():
    i = Identifier.from_url(
        'http://192.168.56.101/ddr/test/123/456/master/a1b2c3d4e5'
    )
    assert i.id == 'ddr-test-123-456-master-a1b2c3d4e5'
    assert i.model == 'file'
    i = Identifier.from_url(
        'http://192.168.56.101/ddr/test/123/456/master/a1b2c3d4e5/'
    )
    assert i.id == 'ddr-test-123-456-master-a1b2c3d4e5'
    assert i.model == 'file'
