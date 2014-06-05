import ConfigParser
import hashlib
import json
import os
import re

from DDR import CONFIG_FILE
from DDR import natural_order_string
from DDR.control import CollectionControlFile, EntityControlFile



class NoConfigError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

if not os.path.exists(CONFIG_FILE):
    raise NoConfigError('No config file!')
config = ConfigParser.ConfigParser()
config.read(CONFIG_FILE)
GITOLITE = config.get('workbench','gitolite')


MODULE_PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(MODULE_PATH, 'templates')
GITIGNORE_TEMPLATE = os.path.join(TEMPLATE_PATH, 'gitignore.tpl')

MODELS = ['collection', 'entity', 'file']

MODELS_DIR = '/usr/local/src/ddr-cmdln/ddr/DDR/models'



def file_hash(path, algo='sha1'):
    if algo == 'sha256':
        h = hashlib.sha256()
    elif algo == 'md5':
        h = hashlib.md5()
    else:
        h = hashlib.sha1()
    block_size=1024
    f = open(path, 'rb')
    while True:
        data = f.read(block_size)
        if not data:
            break
        h.update(data)
    f.close()
    return h.hexdigest()

def metadata_files( basedir, recursive=False, files_first=False, force_read=False, save=False ):
    """Lists absolute paths to .json files in basedir; saves copy if requested.
    
    Skips/excludes .git directories.
    
    @param basedir: Absolute path
    @param recursive: Whether or not to recurse into subdirectories.
    @param files_first: If True, list files,entities,collections; otherwise sort.
    @param force_read: If True, always searches for files instead of using cache.
    @param save: Write a copy to basedir.
    @returns: list of paths
    """
    CACHE_FILENAME = '.metadata_files'
    CACHE_PATH = os.path.join(basedir, CACHE_FILENAME)
    paths = []
    if os.path.exists(CACHE_PATH) and not force_read:
        with open(CACHE_PATH, 'r') as f:
            paths = [line.strip() for line in f.readlines() if '#' not in line]
    else:
        excludes = ['.git', 'tmp', '*~']
        if recursive:
            for root, dirs, files in os.walk(basedir):
                # don't go down into .git directory
                if '.git' in dirs:
                    dirs.remove('.git')
                for f in files:
                    if f.endswith('.json'):
                        path = os.path.join(root, f)
                        exclude = [1 for x in excludes if x in path]
                        if not exclude:
                            paths.append(path)
        else:
            for f in os.listdir(basedir):
                if f.endswith('.json'):
                    path = os.path.join(basedir, f)
                    exclude = [1 for x in excludes if x in path]
                    if not exclude:
                        paths.append(path)
    # files_first is useful for docstore.index
    if files_first:
        collections = []
        entities = []
        files = []
        for f in paths:
            if f.endswith('collection.json'): collections.append(f)
            elif f.endswith('entity.json'): entities.append(f)
            elif f.endswith('.json'): files.append(f)
        paths = files + entities + collections
    else:
        paths.sort()
    # write paths to {basedir}/{CACHE_FILENAME}
    if save:
        # add CACHE_PATH to .gitignore
        gitignore_path = os.path.join(basedir, '.gitignore')
        if os.path.exists(gitignore_path):
            gitignore_present = False
            with open(gitignore_path, 'r') as gif:
                if CACHE_FILENAME in gif.read():
                    gitignore_present = True
            if not gitignore_present:
                with open(gitignore_path, 'a') as giff:
                    giff.write('%s\n' % CACHE_FILENAME)
        # write
        with open(CACHE_PATH, 'w') as f:
            f.write('\n'.join(paths))
    return paths

def make_object_id( model, repo, org=None, cid=None, eid=None, role=None, sha1=None ):
    if   (model == 'file') and repo and org and cid and eid and role and sha1:
        return '%s-%s-%s-%s-%s-%s' % (repo, org, cid, eid, role, sha1)
    elif (model == 'entity') and repo and org and cid and eid:
        return '%s-%s-%s-%s' % (repo, org, cid, eid)
    elif (model == 'collection') and repo and org and cid:
        return '%s-%s-%s' % (repo, org, cid)
    elif (model in ['org', 'organization']) and repo and org:
        return '%s-%s' % (repo, org)
    elif (model in ['repo', 'repository']) and repo:
        return repo
    return None

def split_object_id( object_id=None ):
    """Very naive function that splits an object ID into its parts
    TODO make sure it's actually an object ID first!
    """
    if object_id and isinstance(object_id, basestring):
        parts = object_id.strip().split('-')
        if len(parts) == 6:
            parts.insert(0, 'file')
            return parts
        elif len(parts) == 4:
            parts.insert(0, 'entity')
            return parts
        elif len(parts) == 3:
            parts.insert(0, 'collection')
            return parts
    return None

def id_from_path( path ):
    """Extract ID from path.
    
    >>> _id_from_path('.../ddr-testing-123/collection.json')
    'ddr-testing-123'
    >>> _id_from_path('.../ddr-testing-123/files/ddr-testing-123-1/entity.json')
    'ddr-testing-123-1'
    >>> _id_from_path('.../ddr-testing-123-1-master-a1b2c3d4e5.json')
    'ddr-testing-123-1-master-a1b2c3d4e5.json'
    >>> _id_from_path('.../ddr-testing-123/files/ddr-testing-123-1/')
    None
    >>> _id_from_path('.../ddr-testing-123/something-else.json')
    None
    
    @param path: absolute or relative path to a DDR metadata file
    @returns: DDR object ID
    """
    object_id = None
    model = model_from_path(path)
    if model == 'collection': return os.path.basename(os.path.dirname(path))
    elif model == 'entity': return os.path.basename(os.path.dirname(path))
    elif model == 'file': return os.path.splitext(os.path.basename(path))[0]
    return None

def model_from_dict( data ):
    """Guess model by looking in dict for object_id or path_rel
    """
    if data.get('path_rel',None):
        return 'file'
    object_id = data.get('id', '')
    LEGAL_LENGTHS = [
        1, # repository   (ddr)
        2, # organization (ddr-testing)
        3, # collection   (ddr-testing-123)
        4, # entity       (ddr-testing-123-1)
        6, # file         (ddr-testing-123-1-master-a1b2c3d4e5)
    ]
    parts = object_id.split('-')
    len_parts = len(parts)
    if (len_parts in LEGAL_LENGTHS):
        if   len_parts == 6: return 'file'
        elif len_parts == 4: return 'entity'
        elif len_parts == 3: return 'collection'
        #elif len_parts == 2: return 'organization'
        #elif len_parts == 1: return 'repository'
    return None

def model_from_path( path ):
    """Guess model from the path.
    
    >>> model_from_path('/var/www/media/base/ddr-testing-123/collection.json')
    'collection'
    >>> model_from_path('/var/www/media/base/ddr-testing-123/files/ddr-testing-123-1/entity.json')
    'entity'
    >>> model_from_path('/var/www/media/base/ddr-testing-123/files/ddr-testing-123-1/files/ddr-testing-123-1-master-a1b2c3d4e5.json')
    'file'
    
    @param path: absolute or relative path to metadata JSON file.
    @returns: model
    """
    if 'collection.json' in path: return 'collection'
    elif 'entity.json' in path: return 'entity'
    elif ('master' in path) or ('mezzanine' in path): return 'file'
    return None

def parent_id( object_id ):
    """Given a DDR object ID, returns the parent object ID.
    
    TODO not specific to elasticsearch - move this function so other modules can use
    
    >>> _parent_id('ddr')
    None
    >>> _parent_id('ddr-testing')
    'ddr'
    >>> _parent_id('ddr-testing-123')
    'ddr-testing'
    >>> _parent_id('ddr-testing-123-1')
    'ddr-testing-123'
    >>> _parent_id('ddr-testing-123-1-master-a1b2c3d4e5')
    'ddr-testing-123-1'
    """
    parts = object_id.split('-')
    if   len(parts) == 2: return '-'.join([ parts[0], ])
    elif len(parts) == 3: return '-'.join([ parts[0], parts[1], ])
    elif len(parts) == 4: return '-'.join([ parts[0], parts[1], parts[2] ])
    elif len(parts) == 6: return '-'.join([ parts[0], parts[1], parts[2], parts[3] ])
    return None

def model_fields( model ):
    """
    THIS FUNCTION IS A PLACEHOLDER.
    It's a step on the way to refactoring (COLLECTION|ENTITY|FILE)_FIELDS.
    It gives ddr-public a way to know the order of fields until we have a better solution.
    """
    # TODO model .json files should live in /etc/ddr/models
    if model in ['collection', 'entity', 'file']:
        json_path = os.path.join(MODELS_DIR, '%s.json' % model)
        with open(json_path, 'r') as f:
            data = json.loads(f.read())
        fields = []
        for field in data:
            f = {'name':field['name'],}
            if field.get('form',None) and field['form'].get('label',None):
                f['label'] = field['form']['label']
            fields.append(f)
        return fields
    return []

def module_function(module, function_name, value):
    """If named function is present in module and callable, pass value to it and return result.
    
    Among other things this may be used to prep data for display, prepare it
    for editing in a form, or convert cleaned form data into Python data for
    storage in objects.
    
    @param module: A Python module
    @param function_name: Name of the function to be executed.
    @param value: A single value to be passed to the function, or None.
    @returns: Whatever the specified function returns.
    """
    if (function_name in dir(module)):
        function = getattr(module, function_name)
        value = function(value)
    return value

def module_xml_function(module, function_name, tree, NAMESPACES, f, value):
    """If module function is present and callable, pass value to it and return result.
    
    Same as module_function() but with XML we need to pass namespaces lists to
    the functions.
    Used in dump_ead(), dump_mets().
    
    @param module: A Python module
    @param function_name: Name of the function to be executed.
    @param tree: An lxml tree object.
    @param NAMESPACES: Dict of namespaces used in the XML document.
    @param f: Field dict (from MODEL_FIELDS).
    @param value: A single value to be passed to the function, or None.
    @returns: Whatever the specified function returns.
    """
    if (function_name in dir(module)):
        function = getattr(module, function_name)
        tree = function(tree, NAMESPACES, f, value)
    return tree



class Collection( object ):
    path = None
    path_rel = None
    root = None
    uid = None
    annex_path = None
    changelog_path = None
    control_path = None
    gitignore_path = None
    annex_path_rel = None
    changelog_path_rel = None
    control_path_rel = None
    gitignore_path_rel = None
    git_url = None
    
    def _path_absrel( self, filename, rel=False ):
        if rel:
            return filename
        return os.path.join(self.path, filename)
    
    def __init__( self, path, uid=None ):
        self.path = path
        self.path_rel = os.path.split(self.path)[1]
        self.root = os.path.split(self.path)[0]
        if not uid:
            uid = os.path.basename(self.path)
        self.uid  = uid
        self.annex_path = os.path.join(self.path, '.git', 'annex')
        self.annex_path_rel = os.path.join('.git', 'annex')
        self.changelog_path     = self._path_absrel('changelog'  )
        self.control_path       = self._path_absrel('control'    )
        self.files_path         = self._path_absrel('files'      )
        self.gitignore_path     = self._path_absrel('.gitignore' )
        self.changelog_path_rel = self._path_absrel('changelog',  rel=True)
        self.control_path_rel   = self._path_absrel('control',    rel=True)
        self.files_path_rel     = self._path_absrel('files',      rel=True)
        self.gitignore_path_rel = self._path_absrel('.gitignore', rel=True)
        self.git_url = '{}:{}'.format(GITOLITE, self.uid)
    
    def entity_path( self, entity_uid ):
        return os.path.join(self.files_path, entity_uid)
    
    def changelog( self ):
        if os.path.exists(self.changelog_path):
            return open(self.changelog_path, 'r').read()
        return '%s is empty or missing' % self.changelog_path
    
    def control( self ):
        if not os.path.exists(self.control_path):
            CollectionControlFile.create(self.control_path, self.uid)
        return CollectionControlFile(self.control_path)
    
    def gitignore( self ):
        if not os.path.exists(self.gitignore_path):
            with open(GITIGNORE_TEMPLATE, 'r') as fr:
                gt = fr.read()
            with open(self.gitignore_path, 'w') as fw:
                fw.write(gt)
        with open(self.gitignore_path, 'r') as f:
            return f.read()
    
    @staticmethod
    def collections( collections_root, repository, organization ):
        collections = []
        regex = '^{}-{}-[0-9]+$'.format(repository, organization)
        uid = re.compile(regex)
        for x in os.listdir(collections_root):
            m = uid.search(x)
            if m:
                colldir = os.path.join(collections_root,x)
                if 'collection.json' in os.listdir(colldir):
                    collections.append(colldir)
        collections = sorted(collections, key=lambda c: natural_order_string(c))
        return collections
    
    def entities( self ):
        """Returns relative paths to entities."""
        entities = []
        cpath = self.path
        if cpath[-1] != '/':
            cpath = '{}/'.format(cpath)
        if os.path.exists(self.files_path):
            for uid in os.listdir(self.files_path):
                epath = os.path.join(self.files_path, uid)
                e = Entity(epath)
                entities.append(e)
        entities = sorted(entities, key=lambda e: natural_order_string(e.uid))
        return entities



class Entity( object ):
    path = None
    path_rel = None
    root = None
    parent_path = None
    uid = None
    parent_uid = None
    changelog_path = None
    control_path = None
    files_path = None
    changelog_path_rel = None
    control_path_rel = None
    files_path_rel = None
    
    def _path_absrel( self, filename, rel=False ):
        """
        NOTE: relative == relative to collection root
        """
        if rel:
            p = self.path.replace('%s/' % self.parent_path, '')
            return os.path.join(p, filename)
        return os.path.join(self.path, filename)
    
    def __init__( self, path, uid=None ):
        self.path = path
        self.parent_path = os.path.split(os.path.split(self.path)[0])[0]
        self.root = os.path.split(self.parent_path)[0]
        self.path_rel = self.path.replace('%s/' % self.root, '')
        if not uid:
            uid = os.path.basename(self.path)
        self.uid = uid
        self.parent_uid = os.path.split(self.parent_path)[1]
        self.changelog_path     = self._path_absrel('changelog'  )
        self.control_path       = self._path_absrel('control'    )
        self.files_path         = self._path_absrel('files'      )
        self.changelog_path_rel = self._path_absrel('changelog',  rel=True)
        self.control_path_rel   = self._path_absrel('control',    rel=True)
        self.files_path_rel     = self._path_absrel('files',      rel=True)
    
    def changelog( self ):
        if os.path.exists(self.changelog_path):
            return open(self.changelog_path, 'r').read()
        return '%s is empty or missing' % self.changelog_path
    
    def control( self ):
        if not os.path.exists(self.control_path):
            EntityControlFile.create(self.control_path, self.parent_uid, self.uid)
        return EntityControlFile(self.control_path)
    
    def files( self ):
        """Returns relative paths to payload files."""
        files = []
        prefix_path = self.files_path
        if prefix_path[-1] != '/':
            prefix_path = '{}/'.format(prefix_path)
        if os.path.exists(self.files_path):
            for f in os.listdir(self.files_path):
                files.append(f.replace(prefix_path, ''))
        files = sorted(files, key=lambda f: natural_order_string(f))
        return files
    
    @staticmethod
    def checksum_algorithms():
        return ['md5', 'sha1', 'sha256']
    
    def checksums( self, algo ):
        checksums = []
        if algo not in Entity.checksum_algorithms():
            raise Error('BAD ALGORITHM CHOICE: {}'.format(algo))
        for f in self.files():
            fpath = os.path.join(self.files_path, f)
            cs = file_hash(fpath, algo)
            if cs:
                checksums.append( (cs, fpath) )
        return checksums
