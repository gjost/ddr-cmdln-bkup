from datetime import datetime
import json

from nose.tools import assert_raises
from nose.plugins.attrib import attr

import docstore
import identifier


"""
NOTE: You can disable tests requiring Elasticseach server:

    $ nosetests -a '!elasticsearch'

"""


HOSTS = [{'host':'127.0.0.1', 'port':9200}]


@attr('elasticsearch')
def test_get_connection():
    es = docstore._get_connection(HOSTS)
    assert es
    assert es.cat.client.ping() == True

def test_make_index_name():
    assert docstore.make_index_name('abc-def_ghi.jkl/mno\\pqr stu') == 'abc-def_ghi.jkl-mno-pqrstu'
    assert docstore.make_index_name('qnfs/kinkura/gold') == 'qnfs-kinkura-gold'

# index_exists
# index_names
# create_index
# delete_index
@attr('elasticsearch')
def test_index():
    index = 'test%s' % datetime.now().strftime('%Y%m%d%H%M%S')
    es = docstore._get_connection(HOSTS)
    exists_initial = docstore.index_exists(HOSTS, index)
    created = docstore.create_index(HOSTS, index)
    names = docstore.index_names(HOSTS)
    exists_created = docstore.index_exists(HOSTS, index)
    deleted = docstore.delete_index(HOSTS, index)
    exists_deleted = docstore.index_exists(HOSTS, index)
    assert exists_initial == False
    assert created == {u'acknowledged': True}
    assert index in names
    assert exists_created == True
    assert deleted == {u'acknowledged': True}
    assert exists_deleted == False

# set_alias
# target_index
def test_parse_cataliases():
    cataliases = u'ddrworkstation documents0 \nwd5000bmv-2 documents0 \n'
    expected = [('ddrworkstation','documents0'), ('wd5000bmv-2','documents0')]
    assert docstore._parse_cataliases(cataliases) == expected

#def test_make_mappings():
#    assert False

# put_mappings

# put_facets
# list_facets
# facet_terms

def test_is_publishable():
    data0 = [{'id': 'ddr-testing-123-1'}]
    data1 = [{'id': 'ddr-testing-123-1'}, {'public':0}, {'status':'inprogress'}]
    data2 = [{'id': 'ddr-testing-123-1'}, {'public':0}, {'status':'completed'}]
    data3 = [{'id': 'ddr-testing-123-1'}, {'public':1}, {'status':'inprogress'}]
    data4 = [{'id': 'ddr-testing-123-1'}, {'public':1}, {'status':'completed'}]
    assert docstore._is_publishable(data0) == False
    assert docstore._is_publishable(data1) == False
    assert docstore._is_publishable(data2) == False
    assert docstore._is_publishable(data3) == False
    assert docstore._is_publishable(data4) == True

def test_filter_payload():
    data = [{'id': 'ddr-testing-123-1'}, {'title': 'Title'}, {'secret': 'this is a secret'}]
    public_fields = ['id', 'title']
    docstore._filter_payload(data, public_fields)
    assert data == [{'id': 'ddr-testing-123-1'}, {'title': 'Title'}]

def test_clean_creators():
    data0 = [u'Ninomiya, L.A.']
    data1 = [u'Mitsuoka, Norio: photographer']
    data2 = [{u'namepart': u'Boyle, Rob:editor', u'role': u'author'},
             {u'namepart': u'Cross, Brian:editor', u'role': u'author'}]
    data3 = [{u'namepart': u'"YMCA:publisher"', u'role': u'author'}]
    data4 = [{u'namepart': u'Heart Mountain YMCA', u'role': u'author'}]
    data5 = [{u'namepart': u'', u'role': u'author'}]
    expected0 = [u'Ninomiya, L.A.']
    expected1 = [u'Mitsuoka, Norio: photographer']
    expected2 = [u'Boyle, Rob:editor', u'Cross, Brian:editor']
    expected3 = [u'"YMCA:publisher"']
    expected4 = [u'Heart Mountain YMCA']
    expected5 = []
    assert docstore._clean_creators(data0) == expected0
    assert docstore._clean_creators(data1) == expected1
    assert docstore._clean_creators(data2) == expected2
    assert docstore._clean_creators(data3) == expected3
    assert docstore._clean_creators(data4) == expected4
    assert docstore._clean_creators(data5) == expected5

def test_clean_facility():
    data0 = ['Facility [123]']
    data1 = 'Facility [123]'
    data2 = ['123']
    data3 = [123]
    data4 = '123'
    data5 = 123
    expected = ['123']
    assert docstore._clean_facility(data0) == expected
    assert docstore._clean_facility(data1) == expected
    assert docstore._clean_facility(data2) == expected
    assert docstore._clean_facility(data3) == expected
    assert docstore._clean_facility(data4) == expected
    assert docstore._clean_facility(data5) == expected

def test_clean_parent():
    data0 = 'ddr-testing-123'
    data1 = {'href':'', 'uuid':'', 'label':'ddr-testing-123'}
    expected0 = {'href': '', 'uuid': '', 'label': 'ddr-testing-123'}
    expected1 = {'href': '', 'uuid': '', 'label': 'ddr-testing-123'}
    assert docstore._clean_parent(data0) == expected0
    assert docstore._clean_parent(data1) == expected1

def test_clean_topics():
    data0 = ['Topics [123]']
    data1 = 'Topics [123]'
    data2 = ['123']
    data3 = [123]
    data4 = '123'
    data5 = 123
    expected = ['123']
    assert docstore._clean_topics(data0) == expected
    assert docstore._clean_topics(data1) == expected
    assert docstore._clean_topics(data2) == expected
    assert docstore._clean_topics(data3) == expected
    assert docstore._clean_topics(data4) == expected
    assert docstore._clean_topics(data5) == expected

def test_clean_dict():
    d = {'a': 'abc', 'b': 'bcd', 'x':'' }
    docstore._clean_dict(d)
    assert d == {'a': 'abc', 'b': 'bcd'}

def test_clean_payload():
    data = [
        {'what': 'app version, commit data, etc'},
        {'id': 'ddr-testing-141'},
        {'record_created': '2013-09-13T14:49:43'},
        {'creators': [u'Mitsuoka, Norio: photographer']},
        {'facility': 'Tule Lake [10]'},
        {'parent': {'href':'', 'uuid':'', 'label':'ddr-testing-123'}},
        {'topics': ['Topics [123]']},
        {'none': None},
        {'empty': ''},
    ]
    docstore._clean_payload(data)
    expected = [
        {'what': 'app version, commit data, etc'},
        {'id': 'ddr-testing-141'},
        {'record_created': '2013-09-13T14:49:43'},
        {'creators': [u'Mitsuoka, Norio: photographer']},
        {'facility': ['10']},
        {'parent': {'href': '', 'uuid': '', 'label': 'ddr-testing-123'}},
        {'topics': ['123']},
        {},
        {}
    ]
    assert data == expected

# post
# exists
# get

def test_all_list_fields():
    fields = docstore.all_list_fields()
    expected = ['id', 'title', 'description', 'url', 'signature_file',
                'basename_orig', 'label', 'access_rel', 'sort']
    assert fields == expected

def test_validate_number():
    assert_raises(docstore.PageNotAnInteger, docstore._validate_number, None, 10)
    assert_raises(docstore.PageNotAnInteger, docstore._validate_number, 'x', 10)
    assert docstore._validate_number(1, 10) == 1
    assert docstore._validate_number(10, 10) == 10
    assert_raises(docstore.EmptyPage, docstore._validate_number, 0, 10)
    assert_raises(docstore.EmptyPage, docstore._validate_number, 11, 10)

def test_page_bottom_top():
    # _page_bottom_top(total, index, page_size) -> bottom,top,num_pages
    # index within bounds
    assert docstore._page_bottom_top(100,  1, 10) == (0, 10, 10)
    assert docstore._page_bottom_top(100,  2, 10) == (10, 20, 10)
    assert docstore._page_bottom_top(100,  9, 10) == (80, 90, 10)
    assert docstore._page_bottom_top(100, 10, 10) == (90, 100, 10)
    assert docstore._page_bottom_top( 10,  1,  5) == (0, 5, 2)
    assert docstore._page_bottom_top( 10,  2,  5) == (5, 10, 2)
    # index out of bounds
    assert_raises(docstore.EmptyPage, docstore._page_bottom_top, 10,0,5)
    assert_raises(docstore.EmptyPage, docstore._page_bottom_top, 10,3,5)

MASSAGE_QUERY_RESULTS	= {
    'hits': {
        'hits': [
            {
                '_id': 'ddr-test-123',
                '_index': 'fakeindex',
                '_type': 'collection',
                'fields': {
                    'index': 'fakeindex',
                    'model': 'collection',
                    'type': 'collection',
                    'id': 'ddr-test-123',
                    'title': 'TITLE TEXT',
                    'description': 'DESCRIPTION TEXT',
                    'signature_file': 'ddr-test-123-1-master-a1b2c3'
                }
            },
            {
                '_id': 'ddr-test-123-1',
                '_index': 'fakeindex',
                '_type': 'entity',
                'fields': {
                    'index': 'fakeindex',
                    'model': 'entity',
                    'type': 'entity',
                    'id': 'ddr-test-123-1',
                    'title': 'TITLE TEXT',
                    'description': 'DESCRIPTION TEXT',
                    'signature_file': 'ddr-test-123-1-master-a1b2c3'
                }
            },
            {
                '_id': 'ddr-test-123-1-master-a1b2c3',
                '_index': 'fakeindex',
                '_type': 'file',
                '_source': {
                    'index': 'fakeindex',
                    'model': 'file',
                    'type': 'file',
                    'id': 'ddr-test-123-1-master-a1b2c3',
                    'title': 'TITLE TEXT',
                    'description': 'DESCRIPTION TEXT',
                    'signature_file': 'ddr-test-123-1-master-a1b2c3'
                }
            },
            {
                '_id': 'ddr-test-123-2',
                '_index': 'fakeindex',
                '_type': 'entity',
                'fields': {
                    'index': 'fakeindex',
                    'model': 'entity',
                    'type': 'entity',
                    'id': 'ddr-test-123-2',
                    'title': 'TITLE TEXT',
                    'description': 'DESCRIPTION TEXT',
                    'signature_file': 'ddr-test-123-1-master-a1b2c3'
                }
            },
        ],
        'total': 7
    },
}
MASSAGE_EXPECTED0 = [
    {'index': 'fakeindex', 'description': 'DESCRIPTION TEXT', 'title': 'TITLE TEXT', 'model': 'collection', 'type': 'collection', 'id': 'ddr-test-123', 'signature_file': 'ddr-test-123-1-master-a1b2c3'},
    {'index': 'fakeindex', 'description': 'DESCRIPTION TEXT', 'title': 'TITLE TEXT', 'model': 'entity', 'type': 'entity', 'id': 'ddr-test-123-1', 'signature_file': 'ddr-test-123-1-master-a1b2c3'},
    {'placeholder': True, 'id': 'ddr-test-123-1-master-a1b2c3', 'n': 2},
    {'placeholder': True, 'id': 'ddr-test-123-2', 'n': 3}
]
MASSAGE_EXPECTED1 = [
    {'placeholder': True, 'id': 'ddr-test-123', 'n': 0},
    {'placeholder': True, 'id': 'ddr-test-123-1', 'n': 1},
    {'index': 'fakeindex', 'description': 'DESCRIPTION TEXT', 'title': 'TITLE TEXT', 'model': 'file', 'type': 'file', 'id': 'ddr-test-123-1-master-a1b2c3', 'signature_file': 'ddr-test-123-1-master-a1b2c3'},
    {'index': 'fakeindex', 'description': 'DESCRIPTION TEXT', 'title': 'TITLE TEXT', 'model': 'entity', 'type': 'entity', 'id': 'ddr-test-123-2', 'signature_file': 'ddr-test-123-1-master-a1b2c3'}
]

def test_massage_query_results():
    objects0 = docstore.massage_query_results(MASSAGE_QUERY_RESULTS, page_size=2, thispage=1)
    objects1 = docstore.massage_query_results(MASSAGE_QUERY_RESULTS, page_size=2, thispage=2)
    assert objects0 == MASSAGE_EXPECTED0
    assert objects1 == MASSAGE_EXPECTED1

def test_clean_sort():
    data0 = 'whatever'
    data1 = [['a', 'asc'], ['b', 'asc'], 'whatever']
    data2 = [['a', 'asc'], ['b', 'asc']]
    expected0 = ''
    expected1 = ''
    expected2 = 'a:asc,b:asc'
    assert docstore._clean_sort(data0) == expected0
    assert docstore._clean_sort(data1) == expected1
    assert docstore._clean_sort(data2) == expected2

# search
# delete
# _model_fields


def test_public_fields():
    
    class PublicFieldsModule(object):
        pass

    entity = PublicFieldsModule()
    entity.FIELDS = [
        {"elasticsearch": {"public": True}, "name": "id"},
        {"elasticsearch": {"public": True}, "name": "title"},
        {"elasticsearch": {"public": False}, "name": "notes"},
        {"name": "noelastic"}
    ]
    file_ = PublicFieldsModule()
    file_.FIELDS = [
        {"elasticsearch": {"public": True}, "name": "id"},
        {"elasticsearch": {"public": True}, "name": "title"},
        {"elasticsearch": {"public": False}, "name": "notes"},
        {"name": "noelastic"}
    ]
    MODULES = {
        'entity': entity,
        'file': file_,
    }
    EXPECTED = {
        'entity': ['id', 'title'],
        'file': ['id', 'title', 'path_rel', 'id'],
    }
    assert docstore.public_fields(MODULES) == EXPECTED

# _parents_status

def test_file_parent_ids():
    i0 = identifier.Identifier('ddr-testing-123')
    i1 = identifier.Identifier('ddr-testing-123-1')
    i2 = identifier.Identifier('ddr-testing-123-1-master-a1')
    expected0 = []
    expected1 = ['ddr-testing-123']
    expected2 = ['ddr-testing-123', 'ddr-testing-123-1']
    assert docstore._file_parent_ids(i0) == expected0
    assert docstore._file_parent_ids(i1) == expected1
    assert docstore._file_parent_ids(i2) == expected2

def test_publishable_or_not():
    PATHS = [
        '/tmp/ddr/ddr-test-123/files/ddr-test-123-1/files/ddr-test-123-1-master-96c.json',
        '/tmp/ddr/ddr-test-123/files/ddr-test-123-2/files/ddr-test-123-2-master-c46.json',
        '/tmp/ddr/ddr-test-123/files/ddr-test-123-1/entity.json',
        '/tmp/ddr/ddr-test-123/files/ddr-test-123-2/entity.json',
        '/tmp/ddr/ddr-test-123/collection.json',
        '/tmp/ddr/ddr-test-124/files/ddr-test-124-1/files/ddr-test-124-1-master-6c9.json',
        '/tmp/ddr/ddr-test-124/files/ddr-test-124-2/files/ddr-test-124-2-master-46c.json',
        '/tmp/ddr/ddr-test-124/files/ddr-test-124-1/entity.json',
        '/tmp/ddr/ddr-test-124/files/ddr-test-124-2/entity.json',
        '/tmp/ddr/ddr-test-124/collection.json',
       ]
    PARENTS = {
        u'ddr-test-123-1': {'status': u'completed', 'public': u'1'},
        u'ddr-test-123-2': {'status': u'completed', 'public': u'0'},
        u'ddr-test-123': {'status': u'completed', 'public': u'1'},
        u'ddr-test-124-1': {'status': u'completed', 'public': u'1'},
        u'ddr-test-124-2': {'status': u'completed', 'public': u'0'},
        u'ddr-test-124': {'status': u'completed', 'public': u'1'},
       }
    EXPECTED_SUCCESSFUL = [
        '/tmp/ddr/ddr-test-123/files/ddr-test-123-1/files/ddr-test-123-1-master-96c.json',
        '/tmp/ddr/ddr-test-123/files/ddr-test-123-1/entity.json',
        '/tmp/ddr/ddr-test-123/files/ddr-test-123-2/entity.json',
        '/tmp/ddr/ddr-test-123/collection.json',
        '/tmp/ddr/ddr-test-124/files/ddr-test-124-1/files/ddr-test-124-1-master-6c9.json',
        '/tmp/ddr/ddr-test-124/files/ddr-test-124-1/entity.json',
        '/tmp/ddr/ddr-test-124/files/ddr-test-124-2/entity.json',
        '/tmp/ddr/ddr-test-124/collection.json'
       ]
    EXPECTED_BAD = [
        ('/tmp/ddr/ddr-test-123/files/ddr-test-123-2/files/ddr-test-123-2-master-c46.json',
         403, "parent unpublishable: ['ddr-test-123-2']"),
        ('/tmp/ddr/ddr-test-124/files/ddr-test-124-2/files/ddr-test-124-2-master-46c.json',
         403, "parent unpublishable: ['ddr-test-124-2']")
       ]
    successful_paths,bad_paths = docstore._publishable_or_not(PATHS, PARENTS)
    assert successful_paths == EXPECTED_SUCCESSFUL
    assert bad_paths == EXPECTED_BAD

# _has_access_file
# _store_signature_file
# _choose_signatures
# load_document_json

def test_indexer():
    hosts = [{'host': '127.0.0.1', 'port': 9999}]
    index = 'fakeindex'
    results = docstore.index(hosts, index, '/tmp', recursive=True, public=True)
    assert results == {'successful': 0, 'bad': [], 'total': 0}
                       
