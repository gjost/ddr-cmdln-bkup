import json

import models
import modules


def test_Module_path():
    class TestModule(object):
        pass
    
    module = TestModule()
    module.__file__ = '/var/www/media/base/ddr/repo_models/testmodule.pyc'
    assert modules.Module(module).path == '/var/www/media/base/ddr/repo_models/testmodule.py'

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

    assert modules.Module(TestModule0()).is_valid() == (False,"TestModule0 not in 'ddr' Repository repo.")
    assert modules.Module(TestModule1()).is_valid() == (False,'TestModule1 has no FIELDS variable.')
    assert modules.Module(TestModule2()).is_valid() == (False,'TestModule2.FIELDS is not a list.')
    assert modules.Module(TestModule3()).is_valid() == (True,'ok')

def test_Module_function():
    class TestModule(object):
        def hello(self, text):
            return 'hello %s' % text
    
    module = TestModule()
    module.__file__ = 'ddr/repo_models'
    assert modules.Module(module).function('hello', 'world') == 'hello world'

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
    assert modules.Module(module).labels_values(document) == expected

# TODO Module_cmp_model_definition_commits

def test_Module_cmp_model_definition_fields():
    document = json.loads(TEST_DOCUMENT)
    module = TestModule()
    module.__file__ = 'ddr/repo_models'
    module.FIELDS = ['fake fields']
    assert modules.Module(module).cmp_model_definition_fields(
        json.dumps(document)
    ) == ([],[])
    
    document.append( {'new': 'new field'} )
    assert modules.Module(module).cmp_model_definition_fields(
        json.dumps(document)
    ) == (['new'],[])
    
    document.pop()
    document.pop()
    assert modules.Module(module).cmp_model_definition_fields(
        json.dumps(document)
    ) == ([],['description'])

def test_Module_path():
    class TestModule(object):
        pass
    
    module = TestModule()
    module.__file__ = '/var/www/media/base/ddr/repo_models/testmodule.pyc'
    assert modules.Module(module).path == '/var/www/media/base/ddr/repo_models/testmodule.py'

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

    assert modules.Module(TestModule0()).is_valid() == (False,"TestModule0 not in 'ddr' Repository repo.")
    assert modules.Module(TestModule1()).is_valid() == (False,'TestModule1 has no FIELDS variable.')
    assert modules.Module(TestModule2()).is_valid() == (False,'TestModule2.FIELDS is not a list.')
    assert modules.Module(TestModule3()).is_valid() == (True,'ok')

def test_Module_function():
    class TestModule(object):
        def hello(self, text):
            return 'hello %s' % text
    
    module = TestModule()
    module.__file__ = 'ddr/repo_models'
    assert modules.Module(module).function('hello', 'world') == 'hello world'

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
    assert modules.Module(module).labels_values(document) == expected

# TODO Module_cmp_model_definition_commits

def test_Module_cmp_model_definition_fields():
    document = json.loads(TEST_DOCUMENT)
    module = TestModule()
    module.__file__ = 'ddr/repo_models'
    module.FIELDS = ['fake fields']
    assert modules.Module(module).cmp_model_definition_fields(
        json.dumps(document)
    ) == ([],[])
    
    document.append( {'new': 'new field'} )
    assert modules.Module(module).cmp_model_definition_fields(
        json.dumps(document)
    ) == (['new'],[])
    
    document.pop()
    document.pop()
    assert modules.Module(module).cmp_model_definition_fields(
        json.dumps(document)
    ) == ([],['description'])
