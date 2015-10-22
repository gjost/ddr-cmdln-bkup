import json

from DDR import dvcs


class Module(object):
    path = None

    def __init__(self, module):
        """
        @param module: collection, entity, files model definitions module
        """
        self.module = module
        self.path = None
        if self.module and self.module.__file__:
            self.path = self.module.__file__.replace('.pyc', '.py')
    
    def is_valid(self):
        """Indicates whether this is a proper module
    
        TODO determine required fields for models
    
        @returns: Boolean,str message
        """
        if not self.module:
            return False,"%s has no module object." % self
        # Is the module located in a 'ddr' Repository repo?
        # collection.__file__ == absolute path to the module
        match = 'ddr/repo_models'
        if not match in self.module.__file__:
            return False,"%s not in 'ddr' Repository repo." % self.module.__name__
        # is fields var present in module?
        fields = getattr(self.module, 'FIELDS', None)
        if not fields:
            return False,'%s has no FIELDS variable.' % self.module.__name__
        # is fields var listy?
        if not isinstance(fields, list):
            return False,'%s.FIELDS is not a list.' % self.module.__name__
        return True,'ok'
    
    def function(self, function_name, value):
        """If named function is present in module and callable, pass value to it and return result.
        
        Among other things this may be used to prep data for display, prepare it
        for editing in a form, or convert cleaned form data into Python data for
        storage in objects.
        
        @param function_name: Name of the function to be executed.
        @param value: A single value to be passed to the function, or None.
        @returns: Whatever the specified function returns.
        """
        if (function_name in dir(self.module)):
            function = getattr(self.module, function_name)
            value = function(value)
        return value
    
    def xml_function(self, function_name, tree, NAMESPACES, f, value):
        """If module function is present and callable, pass value to it and return result.
        
        Same as Module.function but with XML we need to pass namespaces lists to
        the functions.
        Used in dump_ead(), dump_mets().
        
        @param function_name: Name of the function to be executed.
        @param tree: An lxml tree object.
        @param NAMESPACES: Dict of namespaces used in the XML document.
        @param f: Field dict (from MODEL_FIELDS).
        @param value: A single value to be passed to the function, or None.
        @returns: Whatever the specified function returns.
        """
        if (function_name in dir(self.module)):
            function = getattr(self.module, function_name)
            tree = function(tree, NAMESPACES, f, value)
        return tree
    
    def labels_values(self, document):
        """Apply display_{field} functions to prep object data for the UI.
        
        Certain fields require special processing.  For example, structured data
        may be rendered in a template to generate an HTML <ul> list.
        If a "display_{field}" function is present in the ddrlocal.models.collection
        module the contents of the field will be passed to it
        
        @param document: Collection, Entity, File document object
        @returns: list
        """
        lv = []
        for f in self.module.FIELDS:
            if hasattr(document, f['name']) and f.get('form',None):
                key = f['name']
                label = f['form']['label']
                # run display_* functions on field data if present
                value = self.function(
                    'display_%s' % key,
                    getattr(document, f['name'])
                )
                lv.append( {'label':label, 'value':value,} )
        return lv
    
    def cmp_model_definition_commits(self, document):
        """Indicate document's model defs are newer or older than module's.
        
        Prepares repository and document/module commits to be compared
        by DDR.dvcs.cmp_commits.  See that function for how to interpret
        the results.
        Note: if a document has no defs commit it is considered older
        than the module.
        
        @param document: A Collection, Entity, or File object.
        @returns: -1, 0, 1, 128 (A older than B, same, A newer than B, error)
        """
        def parse(txt):
            return txt.strip().split(' ')[0]
        module_commit_raw = dvcs.latest_commit(self.path)
        module_defs_commit = parse(module_commit_raw)
        if not module_defs_commit:
            return 128
        doc_metadata = getattr(document, 'json_metadata', {})
        document_commit_raw = doc_metadata.get('models_commit','')
        document_defs_commit = parse(document_commit_raw)
        if not document_defs_commit:
            return -1
        repo = dvcs.repository(self.path)
        return dvcs.cmp_commits(repo, document_defs_commit, module_defs_commit)
    
    def cmp_model_definition_fields(self, document_json):
        """Indicate whether module adds or removes fields from document
        
        @param document_json: Raw contents of document *.json file
        @returns: list,list Lists of added,removed field names.
        """
        # First item in list is document metadata, everything else is a field.
        document_fields = [field.keys()[0] for field in json.loads(document_json)[1:]]
        module_fields = [field['name'] for field in getattr(self.module, 'FIELDS')]
        # models.load_json() uses MODULE.FIELDS, so get list of fields
        # directly from the JSON document.
        added = [field for field in module_fields if field not in document_fields]
        removed = [field for field in document_fields if field not in module_fields]
        return added,removed
