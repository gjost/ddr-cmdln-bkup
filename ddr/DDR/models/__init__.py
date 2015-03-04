# coding: utf-8

"""
NOTE: Much of the code in this module used to be in ddr-local
(ddr-local/ddrlocal/ddrlocal/models/__init__.py).  Please refer to that project
for history prior to Feb 2015.
"""

import codecs
from datetime import datetime
import glob
import hashlib
import json
import logging
logger = logging.getLogger(__name__)
import os
import re
import shutil
from StringIO import StringIO
import sys
import traceback

import envoy
from lxml import etree

from DDR import VERSION, GITOLITE
from DDR import INSTALL_PATH, REPO_MODELS_PATH, MEDIA_BASE
from DDR import DATETIME_FORMAT, TIME_FORMAT, LOG_DIR
from DDR import ACCESS_FILE_APPEND, ACCESS_FILE_EXTENSION, ACCESS_FILE_GEOMETRY
from DDR import format_json, natural_order_string, natural_sort
from DDR import changelog
from DDR.control import CollectionControlFile, EntityControlFile
from DDR import dvcs
from DDR import fileio
from DDR import imaging
from DDR.models.xml import EAD, METS
#from DDR import commands
# NOTE: DDR.commands imports DDR.models.Collection which is a circular import
# so the following is imported in Entity.add_access
#from DDR.commands import entity_annex_add

if REPO_MODELS_PATH not in sys.path:
    sys.path.append(REPO_MODELS_PATH)
try:
    from repo_models import collection as collectionmodule
    from repo_models import entity as entitymodule
    from repo_models import files as filemodule
except ImportError:
    from DDR.models import collectionmodule
    from DDR.models import entitymodule
    from DDR.models import filemodule

MODULE_PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(INSTALL_PATH, 'ddr', 'DDR', 'templates')
GITIGNORE_TEMPLATE = os.path.join(TEMPLATE_PATH, 'gitignore.tpl')

MODELS = ['collection', 'entity', 'file']

MODELS_DIR = '/usr/local/src/ddr-cmdln/ddr/DDR/models'

COLLECTION_FILES_PREFIX = 'files'
ENTITY_FILES_PREFIX = 'files'



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



# metadata files: finding, reading, writing ----------------------------

def metadata_files( basedir, recursive=False, model=None, files_first=False, force_read=False ):
    """Lists absolute paths to .json files in basedir; saves copy if requested.
    
    Skips/excludes .git directories.
    TODO depth (go down N levels from basedir)
    
    @param basedir: Absolute path
    @param recursive: Whether or not to recurse into subdirectories.
    @param model: list Restrict to the named model ('collection','entity','file').
    @param files_first: If True, list files,entities,collections; otherwise sort.
    @param force_read: If True, always searches for files instead of using cache.
    @returns: list of paths
    """
    def model_exclude(m, p):
        exclude = 0
        if m:
            if (m == 'collection') and not ('collection.json' in p):
                exclude = 1
            elif (m == 'entity') and not ('entity.json' in p):
                exclude = 1
            elif (m == 'file') and not (('master' in p.lower()) or ('mezz' in p.lower())):
                exclude = 1
        return exclude
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
                        modexclude = model_exclude(model, path)
                        if not (exclude or modexclude):
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
    return paths

def sort_file_paths(json_paths, rank='role-eid-sort'):
    """Sort file JSON paths in human-friendly order.
    
    @param json_paths: 
    @param rank: 'role-eid-sort' or 'eid-sort-role'
    """
    paths = {}
    keys = []
    while json_paths:
        path = json_paths.pop()
        model,repo,org,cid,eid,role,sha1 = Identity.split_object_id(Identity.id_from_path(path))
        sort = 0
        with open(path, 'r') as f:
            for line in f.readlines():
                if 'sort' in line:
                    sort = line.split(':')[1].replace('"','').strip()
        if rank == 'eid-sort-role':
            key = '-'.join([eid,sort,role,sha1])
        elif rank == 'role-eid-sort':
            key = '-'.join([role,eid,sort,sha1])
        paths[key] = path
        keys.append(key)
    keys_sorted = [key for key in natural_sort(keys)]
    paths_sorted = []
    while keys_sorted:
        val = paths.pop(keys_sorted.pop(), None)
        if val:
            paths_sorted.append(val)
    return paths_sorted

def document_metadata(module, document_repo_path):
    """Metadata for the ddrlocal/ddrcmdln and models definitions used.
    
    @param module: collection, entity, files model definitions module
    @param document_repo_path: Absolute path to root of document's repo
    @returns: dict
    """
    data = {
        'application': 'https://github.com/densho/ddr-cmdln.git',
        'app_commit': dvcs.latest_commit(INSTALL_PATH),
        'app_release': VERSION,
        'models_commit': dvcs.latest_commit(Module(module).path),
        'git_version': dvcs.git_version(document_repo_path),
    }
    return data

def load_json(document, module, json_text):
    """Populates object from JSON-formatted text.
    
    Goes through module.FIELDS turning data in the JSON file into
    object attributes.
    
    @param document: Collection/Entity/File object.
    @param module: collection/entity/file module from 'ddr' repo.
    @param json_text: JSON-formatted text
    @returns: dict
    """
    json_data = json.loads(json_text)
    ## software and commit metadata
    #if data:
    #    setattr(document, 'json_metadata', data[0])
    # field values from JSON
    for mf in module.FIELDS:
        for f in json_data:
            if hasattr(f, 'keys') and (f.keys()[0] == mf['name']):
                setattr(document, f.keys()[0], f.values()[0])
    # Fill in missing fields with default values from module.FIELDS.
    # Note: should not replace fields that are just empty.
    for mf in module.FIELDS:
        if not hasattr(document, mf['name']):
            setattr(document, mf['name'], mf.get('default',None))
    return json_data

def prep_json(obj, module, template=False,
              template_passthru=['id', 'record_created', 'record_lastmod'],
              exceptions=[]):
    """Arranges object data in list-of-dicts format before serialization.
    
    DDR keeps data in Git is to take advantage of versioning.  Python
    dicts store data in random order which makes it impossible to
    meaningfully compare diffs of the data over time.  DDR thus stores
    data as an alphabetically arranged list of dicts, with several
    exceptions.
    
    The first dict in the list is not part of the object itself but
    contains metadata about the state of the DDR application at the time
    the file was last written: the Git commit of the app, the release
    number, and the versions of Git and git-annex used.
    
    Python data types that cannot be represented in JSON (e.g. datetime)
    are converted into strings.
    
    @param obj: Collection/Entity/File object.
    @param module: collection/entity/file module from 'ddr' repo.
    @param template: Boolean True if object to be used as blank template.
    @param template_passthru: list
    @param exceptions: list
    @returns: dict
    """
    data = []
    for mf in module.FIELDS:
        item = {}
        key = mf['name']
        val = ''
        if template and (key not in template_passthru) and hasattr(mf,'form'):
            # write default values
            val = mf['form']['initial']
        elif hasattr(obj, mf['name']):
            # write object's values
            val = getattr(obj, mf['name'])
            # special cases
            if val:
                # JSON requires dates to be represented as strings
                if hasattr(val, 'fromtimestamp') and hasattr(val, 'strftime'):
                    val = val.strftime(DATETIME_FORMAT)
            # end special cases
        item[key] = val
        if key not in exceptions:
            data.append(item)
    return data

def from_json(model, json_path):
    """Read the specified JSON file and properly instantiate object.
    
    @param model: LocalCollection, LocalEntity, or File
    @param json_path: absolute path to the object's .json file
    @returns: object
    """
    document = None
    if os.path.exists(json_path):
        document = model(os.path.dirname(json_path))
        document_uid = document.id  # save this just in case
        document.load_json(fileio.read_raw(json_path))
        if not document.id:
            # id gets overwritten if document.json is blank
            document.id = document_uid
    return document


class Path( object ):
    pass

class Identity(object):

    @staticmethod
    def dissect_path( path_abs ):
        """Slices up an absolute path and extracts as much as it can.
        
        TODO use caching to speed this up
        
        @param path_abs: absolute path to object json file.
        @returns: Identifier object
        """
        p = Path()
        p.path = path_abs
        p.path_abs = path_abs
        FIELDS = [
            'base_path', 'git_path', 'annex_path', 'gitignore_path',
            'collection_path', 'entity_path', 'file_path', 'access_path',
            'json_path', 'changelog_path', 'control_path', 'entities_path',
            'files_path', 'file_path_rel', 'access_path_rel', 'json_path_rel',
            'changelog_path_rel', 'control_path_rel', 'entities_path_rel',
            'files_path_rel', 'object_id', 'object_type', 'model',
            'repo', 'org', 'cid', 'eid', 'role', 'sha1',
            'file_id', 'entity_id', 'collection_id', 'parent_id',
        ]
        for f in FIELDS:
            setattr(p, f, None)
        
        # remove trailing slash if this is a directory
        if path_abs[-1] == os.path.sep:
            path_abs = path_abs[:-1]
        
        model = None
        if ('master' in path_abs.lower()) or ('mezzanine' in path_abs.lower()):
            model = 'file'
        elif ('entity.json' in path_abs) or ('files' in path_abs):
            model = 'entity'
        elif ('collection.json' in path_abs) or (not 'files' in path_abs):
            model = 'collection'
        
        if model == 'file':
            # /basepath/collection_id/files/entity_id/files/file_id-a.jpg
            # /basepath/collection_id/files/entity_id/files/file_id.ext
            # /basepath/collection_id/files/entity_id/files/file_id.json
            # /basepath/collection_id/files/entity_id/files/file_id
            ACCESS_FILE_STUB = '%s%s' % (ACCESS_FILE_APPEND, ACCESS_FILE_EXTENSION)
            
            pathname,ext = os.path.splitext(path_abs)
            if ext and (pathname[-2:] == '-a'):
                p.object_id = os.path.basename(pathname[:-2])
            else:
                p.object_id = os.path.basename(pathname)
            
            which = 'unknown'
            if   os.path.splitext(path_abs)[1]:     which = 'file'   # file_id with extension
            elif ('.json' in path_abs):             which = 'json'   # the *.json file
            elif ACCESS_FILE_STUB in path_abs:      which = 'access' # access file
            elif not os.path.splitext(path_abs)[1]: which = 'noext'  # file_id with no extension
            
            def find_file_path(pattern):
                # figure out original file path
                for fp in glob.glob(pattern):
                    if not ('.json' in fp) or (ACCESS_FILE_STUB in fp):
                        return fp
                return None
                
            if which == 'file':
                p.file_path = path_abs
                p.json_path = '%s.json' % os.path.splitext(path_abs)[0]
                p.access_path = '%s%s' % (os.path.splitext(p.file_path)[0], ACCESS_FILE_STUB)
                p.object_type,p.repo,p.org,p.cid,p.eid,p.role,p.sha1 = Identity.split_object_id(p.object_id)
            
            elif which == 'json':
                p.json_path = path_abs
                pattern = os.path.splitext(path_abs)[0]
                p.file_path = find_file_path(pattern)
                p.access_path = '%s%s' % (os.path.splitext(p.file_path)[0], ACCESS_FILE_STUB)
                p.object_type,p.repo,p.org,p.cid,p.eid,p.role,p.sha1 = Identity.split_object_id(p.object_id)
            
            elif which == 'access':
                p.access_path = p.path_abs
                pattern = '%s*' % path_abs.replace(ACCESS_FILE_STUB,'')
                p.file_path = find_file_path(pattern)
                p.json_path = '%s.json' % os.path.splitext(path_abs)[0]
                p.object_type,p.repo,p.org,p.cid,p.eid,p.role,p.sha1 = Identity.split_object_id(p.object_id)
            
            elif which == 'noext':
                p.json_path = '%s.json' % path_abs
                pattern = '%s*' % path_abs
                p.file_path = find_file_path(pattern)
                p.access_path = '%s%s' % (p.file_path, ACCESS_FILE_STUB)
                p.object_type,p.repo,p.org,p.cid,p.eid,p.role,p.sha1 = Identity.split_object_id(p.object_id)
            
            p.entity_path = os.path.dirname(os.path.dirname(p.path))
            p.collection_path = os.path.dirname(os.path.dirname(p.entity_path))
            p.base_path = os.path.dirname(p.collection_path)
            
            if p.file_path: p.file_path_rel = p.file_path.replace(p.base_path, '')
            if p.access_path: p.access_path_rel = p.access_path.replace(p.base_path, '')
            if p.json_path: p.json_path_rel = p.json_path.replace(p.base_path, '')
            
            p.git_path = os.path.join(p.collection_path, '.git')
            p.annex_path = os.path.join(p.collection_path, '.git', 'annex')
            p.gitignore_path = os.path.join(p.collection_path, '.gitignore')
            
            p.model = p.object_type
            p.role = p.role.lower()
            
            p.file_id = Identity.make_object_id('file', p.repo,p.org,p.cid,p.eid,p.role,p.sha1)
            p.entity_id = Identity.make_object_id('entity', p.repo,p.org,p.cid,p.eid)
            p.collection_id = Identity.make_object_id('collection', p.repo,p.org,p.cid)
            p.parent_id = p.entity_id
        
        elif model == 'entity':
            # /basepath/collection_id/files/entity_id/entity.json
            if (os.path.basename(path_abs) == 'entity.json'):
                p.entity_path = os.path.dirname(path_abs)
                p.json_path = path_abs
            elif (os.path.basename(path_abs) == 'files'):
                p.entity_path = os.path.dirname(path_abs)
                p.json_path = os.path.join(p.entity_path, 'entity.json')
            else:
                p.entity_path = path_abs
                p.json_path = os.path.join(path_abs, 'entity.json')
            
            p.collection_path = os.path.dirname(os.path.dirname(p.entity_path))
            p.base_path = os.path.dirname(p.collection_path)
            
            p.git_path = os.path.join(p.collection_path, '.git')
            p.annex_path = os.path.join(p.collection_path, '.git', 'annex')
            p.gitignore_path = os.path.join(p.collection_path, '.gitignore')
            # these are for the entity not the collection
            p.changelog_path = os.path.join(p.entity_path, 'changelog')
            p.control_path = os.path.join(p.entity_path, 'control')
            p.files_path = os.path.join(p.entity_path, 'files')
    
            p.changelog_path_rel = p.changelog_path.replace(p.base_path, '')
            p.control_path_rel = p.control_path.replace(p.base_path, '')
            p.files_path_rel = p.files_path.replace(p.base_path, '')
            
            p.object_id = os.path.basename(p.entity_path)
            
            p.object_type,p.repo,p.org,p.cid,p.eid = Identity.split_object_id(p.object_id)
            p.model = p.object_type
            
            p.entity_id = Identity.make_object_id('entity', p.repo,p.org,p.cid,p.eid)
            p.collection_id = Identity.make_object_id('collection', p.repo,p.org,p.cid)
            p.parent_id = p.collection_id
        
        elif model == 'collection':
            if (os.path.basename(path_abs) == 'collection.json'):
                p.collection_path = os.path.dirname(path_abs)
                p.json_path = path_abs
            else:
                p.collection_path = path_abs
                p.json_path = os.path.join(path_abs, 'collection.json')
            
            p.base_path = os.path.dirname(p.collection_path)
            
            p.git_path = os.path.join(p.collection_path, '.git')
            p.annex_path = os.path.join(p.collection_path, '.git', 'annex')
            p.gitignore_path = os.path.join(p.collection_path, '.gitignore')
            p.changelog_path = os.path.join(p.collection_path, 'changelog')
            p.control_path = os.path.join(p.collection_path, 'control')
            p.entities_path = os.path.join(p.collection_path, 'files')
            
            p.object_id = os.path.basename(p.collection_path)
            
            p.object_type,p.repo,p.org,p.cid = Identity.split_object_id(p.object_id)
            p.model = p.object_type
            
            p.collection_id = p.object_id
        
        return p
    
    @staticmethod
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
    
    @staticmethod
    def split_object_id( object_id=None ):
        """Very naive function that splits an object ID into its parts
        TODO make sure it's actually an object ID first!
        """
        if object_id and isinstance(object_id, basestring):
            parts = object_id.strip().split('-')
            if len(parts) == 6:
                parts.insert(0, 'file')
                return parts
            elif len(parts) == 5:
                # file ID without the SHA1 hash; used to mark new files in batch CSV
                parts.insert(0, 'file partial')
                return parts
            elif len(parts) == 4:
                parts.insert(0, 'entity')
                return parts
            elif len(parts) == 3:
                parts.insert(0, 'collection')
                return parts
            elif len(parts) == 2:
                parts.insert(0, 'organization')
                return parts
            elif len(parts) == 1:
                parts.insert(0, 'repository')
                return parts
        return None
    
    @staticmethod
    def id_from_path( path ):
        """Extract ID from path.
        
        >>> Identity.id_from_path('.../ddr-testing-123/collection.json')
        'ddr-testing-123'
        >>> Identity.id_from_path('.../ddr-testing-123/files/ddr-testing-123-1/entity.json')
        'ddr-testing-123-1'
        >>> Identity.d_from_path('.../ddr-testing-123-1-master-a1b2c3d4e5.json')
        'ddr-testing-123-1-master-a1b2c3d4e5.json'
        >>> Identity.id_from_path('.../ddr-testing-123/files/ddr-testing-123-1/')
        None
        >>> Identity.id_from_path('.../ddr-testing-123/something-else.json')
        None
        
        @param path: absolute or relative path to a DDR metadata file
        @returns: DDR object ID
        """
        # rm trailing slash
        if path[-1] == os.sep:
            path = path[:-1]
        object_id = None
        model = Identity.model_from_path(path)
        if model == 'collection':
            if 'collection.json' in path:
                return os.path.basename(os.path.dirname(path))
            else:
                return os.path.split(path)[1]
        elif model == 'entity':
            if 'entity.json' in path:
                return os.path.basename(os.path.dirname(path))
            else:
                return os.path.split(path)[1]
        elif model == 'file':
            return os.path.splitext(os.path.basename(path))[0]
        return None
    
    @staticmethod
    def model_from_path( path ):
        """Guess model from the path.
        
        >>> Identity.model_from_path('/var/www/media/base/ddr-testing-123')
        'collection'
        >>> Identity.model_from_path('/var/www/media/base/ddr-testing-123/collection.json')
        'collection'
        >>> Identity.model_from_path('/var/www/media/base/ddr-testing-123/files/ddr-testing-123-1')
        'entity'
        >>> Identity.model_from_path('/var/www/media/base/ddr-testing-123/files/ddr-testing-123-1/entity.json')
        'entity'
        >>> Identity.model_from_path('/var/www/media/base/ddr-testing-123/files/ddr-testing-123-1/files/ddr-testing-123-1-master-a1b2c3d4e5.json')
        'file'
        
        @param path: absolute or relative path to metadata JSON file.
        @returns: model
        """
        # rm trailing slash
        if path[-1] == os.sep:
            path = path[:-1]
        # metadata file paths
        if 'collection.json' in path: return 'collection'
        elif 'entity.json' in path: return 'entity'
        elif ('master' in path.lower()) or ('mezzanine' in path.lower()): return 'file'
        # directories
        basename = os.path.basename(path)
        parts = Identity.split_object_id(basename)
        if parts[0] in MODELS:
            return parts[0]
        return None
    
    @staticmethod
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
    
    @staticmethod
    def path_from_id( object_id, base_dir='' ):
        """Return's path to object* given the object ID and (optional) base_dir.
        
        * Does not append 'entity.json' or file extension.
        
        @param object_id:
        @param base_dir: Absolute path, with no trailing slash.
        @returns: Relative path or (if base_dir) absolute path
        """
        path = None
        repo = None; org = None; cid = None; eid = None; role = None; sha1 = None
        parts = Identity.split_object_id(object_id)
        model = parts[0]
        base = '%s/' % base_dir
        if model == 'collection':
            repo = parts[1]; org = parts[2]; cid = parts[3]
            path = '%s%s-%s-%s' % (
                base, repo,org,cid)
        elif model == 'entity':
            repo = parts[1]; org = parts[2]; cid = parts[3]; eid = parts[4]
            path = '%s%s-%s-%s/files/%s-%s-%s-%s' % (
                base, repo,org,cid, repo,org,cid,eid)
        elif model == 'file partial':
            repo = parts[1]; org = parts[2]; cid = parts[3]; eid = parts[4]; role = parts[5]
            path = '%s%s-%s-%s/files/%s-%s-%s-%s/files/%s-%s-%s-%s-%s' % (
                base, repo,org,cid, repo,org,cid,eid, repo,org,cid,eid,role)
        elif model == 'file':
            repo = parts[1]; org = parts[2]; cid = parts[3]; eid = parts[4]; role = parts[5]; sha1 = parts[6]
            path = '%s%s-%s-%s/files/%s-%s-%s-%s/files/%s-%s-%s-%s-%s-%s' % (
                base, repo,org,cid, repo,org,cid,eid, repo,org,cid,eid,role,sha1)
        return path
    
    @staticmethod
    def json_path_from_dir(model, path):
        """Given path to collection/entity dir, return path to .json
        
        >>> Identity.json_path_from_dir('collection', '/path/ddr-test-123')
        '/path/ddr-test-123/collection.json'
        >>> Identity.json_path_from_dir('entity', '/path/ddr-test-123/files//ddr-test-123-45')
        '/path/ddr-test-123/files//ddr-test-123-45/entity.json'
        >>> Identity.json_path_from_dir('entity', 'files/ddr-test-123-45')
        'files/ddr-test-123-45/entity.json'
        
        @param model: 'collection' or 'entity'
        @param path: Absolute or relative path to collection/entity dir
        """
        if model == 'collection':
            json_path = os.path.join(path, 'collection.json')
        elif model == 'entity':
            json_path = os.path.join(path, 'entity.json')
        elif model == 'file':
            json_path = '%s.json' % path
        else:
            raise Exception('Unrecognized model: "%s"' % model)
        return json_path
    
    @staticmethod
    def parent_id( object_id ):
        """Given a DDR object ID, returns the parent object ID.
        
        TODO not specific to elasticsearch - move this function so other modules can use
        
        >>> Identity.parent_id('ddr')
        None
        >>> Identity.parent_id('ddr-testing')
        'ddr'
        >>> Identity.parent_id('ddr-testing-123')
        'ddr-testing'
        >>> Identity.parent_id('ddr-testing-123-1')
        'ddr-testing-123'
        >>> Identity.parent_id('ddr-testing-123-1-master-a1b2c3d4e5')
        'ddr-testing-123-1'
        """
        parts = object_id.split('-')
        if   len(parts) == 2: return '-'.join([ parts[0], ])
        elif len(parts) == 3: return '-'.join([ parts[0], parts[1], ])
        elif len(parts) == 4: return '-'.join([ parts[0], parts[1], parts[2] ])
        elif len(parts) == 5: return '-'.join([ parts[0], parts[1], parts[2], parts[3] ])
        elif len(parts) == 6: return '-'.join([ parts[0], parts[1], parts[2], parts[3] ])
        return None


class Module(object):
    path = None

    def __init__(self, module):
        """
        @param module: collection, entity, files model definitions module
        """
        self.module = module
        self.path = self.module.__file__.replace('.pyc', '.py')
    
    def is_valid(self):
        """Indicates whether this is a proper module
    
        TODO determine required fields for models
    
        @returns: Boolean,str message
        """
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
        @returns: int
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


class Inheritance(object):

    @staticmethod
    def _child_jsons( path ):
        """List all the .json files under path directory; excludes specified dir.
        
        @param path: Absolute directory path.
        @return list of paths
        """
        return [
            p for p in metadata_files(basedir=path, recursive=True)
            if os.path.dirname(p) != path
        ]
    
    @staticmethod
    def _selected_field_values( parent_object, inheritables ):
        """Gets list of selected inherited fieldnames and their values from the parent object
        
        @param parent_object
        @param inheritables
        @returns: list of (fieldname,value) tuples
        """
        field_values = []
        for field in inheritables:
            value = getattr(parent_object, field)
            field_values.append( (field,value) )
        return field_values
    
    @staticmethod
    def inheritable_fields( MODEL_FIELDS ):
        """Returns a list of fields that can inherit or grant values.
        
        Inheritable fields are marked 'inheritable':True in MODEL_FIELDS.
        
        @param MODEL_FIELDS
        @returns: list
        """
        inheritable = []
        for f in MODEL_FIELDS:
            if f.get('inheritable', None):
                inheritable.append(f['name'])
        return inheritable
    
    @staticmethod
    def selected_inheritables( inheritables, cleaned_data ):
        """Indicates which inheritable fields from the list were selected in the form.
        
        Selector fields are assumed to be BooleanFields named "FIELD_inherit".
        
        @param inheritables: List of field/attribute names.
        @param cleaned_data: form.cleaned_data.
        @return
        """
        fieldnames = {}
        for field in inheritables:
            fieldnames['%s_inherit' % field] = field
        selected = []
        if fieldnames:
            for key in cleaned_data.keys():
                if (key in fieldnames.keys()) and cleaned_data[key]:
                    selected.append(fieldnames[key])
        return selected
        
    @staticmethod
    def update_inheritables( parent_object, objecttype, inheritables, cleaned_data ):
        """Update specified inheritable fields of child objects using form data.
        
        @param parent_object: Collection or Entity with values to be inherited.
        @param cleaned_data: Form cleaned_data from POST.
        @returns: tuple List of changed object Ids, list of changed objects' JSON files.
        """
        child_ids = []
        changed_files = []
        # values of selected inheritable fields from parent
        field_values = Inheritance._selected_field_values(parent_object, inheritables)
        # load child objects and apply the change
        if field_values:
            for json_path in Inheritance._child_jsons(parent_object.path):
                child = None
                p = Identity.dissect_path(json_path)
                if p.model == 'collection':
                    child = Collection.from_json(p.collection_path)
                elif p.model == 'entity':
                    child = Entity.from_json(p.entity_path)
                elif p.model == 'file':
                    child = File.from_json(json_path)
                if child:
                    # set field if exists in child and doesn't already match parent value
                    changed = False
                    for field,value in field_values:
                        if hasattr(child, field):
                            existing_value = getattr(child,field)
                            if existing_value != value:
                                setattr(child, field, value)
                                changed = True
                    # write json and add to list of changed IDs/files
                    if changed:
                        child.write_json()
                        if hasattr(child, 'id'):         child_ids.append(child.id)
                        elif hasattr(child, 'basename'): child_ids.append(child.basename)
                        changed_files.append(json_path)
        return child_ids,changed_files
    
    @staticmethod
    def inherit( parent, child ):
        """Set inheritable fields in child object with values from parent.
        
        @param parent: A webui.models.Collection or webui.models.Entity
        @param child: A webui.models.Entity or webui.models.File
        """
        for field in parent.inheritable_fields():
            if hasattr(parent, field) and hasattr(child, field):
                setattr(child, field, getattr(parent, field))


class Locking(object):
    
    @staticmethod
    def lock( lock_path, text ):
        """Writes lockfile to collection dir; complains if can't.
        
        Celery tasks don't seem to know their own task_id, and there don't
        appear to be any handlers that can be called just *before* a task
        is fired. so it appears to be impossible for a task to lock itself.
        
        This method should(?) be called immediately after starting the task:
        >> result = collection_sync.apply_async((args...), countdown=2)
        >> lock_status = collection.lock(result.task_id)
        
        >>> path = '/tmp/ddr-testing-123'
        >>> os.mkdir(path)
        >>> c = Collection(path)
        >>> c.lock('abcdefg')
        'ok'
        >>> c.lock('abcdefg')
        'locked'
        >>> c.unlock('abcdefg')
        'ok'
        >>> os.rmdir(path)
        
        TODO return 0 if successful
        
        @param lock_path
        @param text
        @returns 'ok' or 'locked'
        """
        if os.path.exists(lock_path):
            return 'locked'
        with open(lock_path, 'w') as f:
            f.write(text)
        return 'ok'
    
    @staticmethod
    def unlock( lock_path, text ):
        """Removes lockfile or complains if can't
        
        This method should be called by celery Task.after_return()
        See "Abstract classes" section of
        http://celery.readthedocs.org/en/latest/userguide/tasks.html#custom-task-classes
        
        >>> path = '/tmp/ddr-testing-123'
        >>> os.mkdir(path)
        >>> c = Collection(path)
        >>> c.lock('abcdefg')
        'ok'
        >>> c.unlock('xyz')
        'task_id miss'
        >>> c.unlock('abcdefg')
        'ok'
        >>> c.unlock('abcdefg')
        'not locked'
        >>> os.rmdir(path)
        
        TODO return 0 if successful
        
        @param lock_path
        @param text
        @returns 'ok', 'not locked', 'task_id miss', 'blocked'
        """
        if not os.path.exists(lock_path):
            return 'not locked'
        with open(lock_path, 'r') as f:
            lockfile_text = f.read().strip()
        if lockfile_text and (lockfile_text != text):
            return 'miss'
        os.remove(lock_path)
        if os.path.exists(lock_path):
            return 'blocked'
        return 'ok'
    
    @staticmethod
    def locked( lock_path ):
        """Returns contents of lockfile if collection repo is locked, False if not
        
        >>> c = Collection('/tmp/ddr-testing-123')
        >>> c.locked()
        False
        >>> c.lock('abcdefg')
        'ok'
        >>> c.locked()
        'abcdefg'
        >>> c.unlock('abcdefg')
        'ok'
        >>> c.locked()
        False
        
        @param lock_path
        """
        if os.path.exists(lock_path):
            with open(lock_path, 'r') as f:
                text = f.read().strip()
            return text
        return False
    


# objects --------------------------------------------------------------


class Collection( object ):
    root = None
    uid = None
    id = None
    repo = None
    org = None
    cid = None
    path = None; path_rel = None
    annex_path = None; annex_path_rel = None
    json_path = None; json_path_rel = None
    files_path = None; files_path_rel = None
    changelog_path = None; changelog_path_rel = None
    control_path = None; control_path_rel = None
    ead_path = None; ead_path_rel = None
    gitignore_path = None; gitignore_path_rel = None
    lock_path = None
    git_url = None
    _status = ''
    _astatus = ''
    _unsynced = 0
    
    def _path_absrel( self, filename, rel=False ):
        if rel:
            return filename
        return os.path.join(self.path, filename)
    
    def __init__( self, path, uid=None ):
        """
        >>> c = Collection('/tmp/ddr-testing-123')
        >>> c.uid
        'ddr-testing-123'
        >>> c.repo
        'ddr'
        >>> c.org
        'testing'
        >>> c.cid
        '123'
        >>> c.ead_path_rel
        'ead.xml'
        >>> c.ead_path
        '/tmp/ddr-testing-123/ead.xml'
        >>> c.json_path_rel
        'collection.json'
        >>> c.json_path
        '/tmp/ddr-testing-123/collection.json'
        """
        self.path = path
        self.path_rel = os.path.split(self.path)[1]
        self.root = os.path.split(self.path)[0]
        if not uid:
            uid = os.path.basename(self.path)
        self.uid  = uid
        self.id = uid
        self_model,self.repo,self.org,self.cid = Identity.split_object_id(uid)
        self.annex_path         = os.path.join(self.path, '.git', 'annex')
        self.annex_path_rel     = os.path.join('.git', 'annex')
        self.json_path          = self._path_absrel('collection.json')
        self.json_path_rel      = self._path_absrel('collection.json',rel=True)
        self.files_path         = self._path_absrel('files')
        self.files_path_rel     = self._path_absrel('files', rel=True)
        self.changelog_path     = self._path_absrel('changelog')
        self.changelog_path_rel = self._path_absrel('changelog', rel=True)
        self.control_path       = self._path_absrel('control')
        self.control_path_rel   = self._path_absrel('control', rel=True)
        self.ead_path           = self._path_absrel('ead.xml')
        self.ead_path_rel       = self._path_absrel('ead.xml', rel=True)
        self.gitignore_path     = self._path_absrel('.gitignore')
        self.gitignore_path_rel = self._path_absrel('.gitignore', rel=True)
        self.lock_path          = self._path_absrel('lock')
        self.git_url = '{}:{}'.format(GITOLITE, self.uid)
    
    def __repr__(self):
        """Returns string representation of object.
        
        >>> c = Collection('/tmp/ddr-testing-123')
        >>> c
        <Collection ddr-testing-123>
        """
        return "<Collection %s>" % (self.id)
    
    @staticmethod
    def create(path):
        """Creates a new collection with the specified collection ID.
        
        Also sets initial field values if present.
        
        >>> c = Collection.create('/tmp/ddr-testing-120')
        
        @param path: Absolute path to collection; must end in valid DDR collection id.
        @returns: Collection object
        """
        collection = Collection(path)
        for f in collectionmodule.FIELDS:
            if hasattr(f, 'name') and hasattr(f, 'initial'):
                setattr(collection, f['name'], f['initial'])
        return collection
    
    @staticmethod
    def from_json(collection_abs):
        """Creates a Collection and populates with data from JSON file.
        
        @param collection_abs: Absolute path to collection directory.
        @returns: Collection
        """
        return from_json(Collection, os.path.join(collection_abs, 'collection.json'))
    
    def model_def_commits( self ):
        return Module(collectionmodule).cmp_model_definition_commits(self)
    
    def model_def_fields( self ):
        return Module(collectionmodule).cmp_model_definition_fields(fileio.read_raw(self.json_path))
    
    def labels_values(self):
        """Apply display_{field} functions to prep object data for the UI.
        """
        return Module(collectionmodule).labels_values(self)
    
    def inheritable_fields( self ):
        """Returns list of Collection object's field names marked as inheritable.
        
        >>> c = Collection.from_json('/tmp/ddr-testing-123')
        >>> c.inheritable_fields()
        ['status', 'public', 'rights']
        """
        return Inheritance.inheritable_fields(collectionmodule.FIELDS )

    def selected_inheritables(self, cleaned_data ):
        """Returns names of fields marked as inheritable in cleaned_data.
        
        Fields are considered selected if dict contains key/value pairs in the form
        'FIELD_inherit':True.
        
        @param cleaned_data: dict Fieldname:value pairs.
        @returns: list
        """
        return Inheritance.selected_inheritables(self.inheritable_fields(), cleaned_data)
    
    def update_inheritables( self, inheritables, cleaned_data ):
        """Update specified fields of child objects.
        
        @param inheritables: list Names of fields that shall be inherited.
        @param cleaned_data: dict Fieldname:value pairs.
        @returns: tuple [changed object Ids],[changed objects' JSON files]
        """
        return Inheritance.update_inheritables(self, 'collection', inheritables, cleaned_data)
    
    def load_json(self, json_text):
        """Populates Collection from JSON-formatted text.
        
        Goes through COLLECTION_FIELDS, turning data in the JSON file into
        object attributes.
        
        @param json_text: JSON-formatted text
        """
        load_json(self, collectionmodule, json_text)
        # special cases
        if hasattr(self, 'record_created') and self.record_created:
            self.record_created = datetime.strptime(self.record_created, DATETIME_FORMAT)
        else:
            self.record_created = datetime.now()
        if hasattr(self, 'record_lastmod') and self.record_lastmod:
            self.record_lastmod = datetime.strptime(self.record_lastmod, DATETIME_FORMAT)
        else:
            self.record_lastmod = datetime.now()
    
    def dump_json(self, template=False, doc_metadata=False):
        """Dump Collection data to JSON-formatted text.
        
        @param template: [optional] Boolean. If true, write default values for fields.
        @param doc_metadata: boolean. Insert document_metadata().
        @returns: JSON-formatted text
        """
        data = prep_json(self, collectionmodule, template=template)
        if doc_metadata:
            data.insert(0, document_metadata(collectionmodule, self.path))
        return format_json(data)
    
    def write_json(self):
        """Write JSON file to disk.
        """
        fileio.write_raw(self.dump_json(doc_metadata=True), self.json_path)
    
    def lock( self, text ): return Locking.lock(self.lock_path, text)
    def unlock( self, text ): return Locking.unlock(self.lock_path, text)
    def locked( self ): return Locking.locked(self.lock_path)
    
    def changelog( self ):
        if os.path.exists(self.changelog_path):
            return open(self.changelog_path, 'r').read()
        return '%s is empty or missing' % self.changelog_path
    
    def control( self ):
        if not os.path.exists(self.control_path):
            CollectionControlFile.create(self.control_path, self.uid)
        return CollectionControlFile(self.control_path)
    
    def ead( self ):
        """Returns a ddrlocal.models.xml.EAD object for the collection.
        
        TODO Do we really need this?
        """
        if not os.path.exists(self.ead_path):
            EAD.create(self.ead_path)
        return EAD(self)
    
    def dump_ead(self):
        """Dump Collection data to ead.xml file.
        
        TODO render a Django/Jinja template instead of using lxml
        TODO This should not actually write the XML! It should return XML to the code that calls it.
        """
        NAMESPACES = None
        tree = etree.fromstring(self.ead().xml)
        for f in collectionmodule.FIELDS:
            key = f['name']
            value = ''
            if hasattr(self, f['name']):
                value = getattr(self, key)
                # run ead_* functions on field data if present
                tree = Module(collectionmodule).xml_function(
                    'ead_%s' % key,
                    tree, NAMESPACES, f,
                    value
                )
        xml_pretty = etree.tostring(tree, pretty_print=True)
        with open(self.ead_path, 'w') as f:
            f.write(xml_pretty)
    
    def gitignore( self ):
        if not os.path.exists(self.gitignore_path):
            with open(GITIGNORE_TEMPLATE, 'r') as fr:
                gt = fr.read()
            with open(self.gitignore_path, 'w') as fw:
                fw.write(gt)
        with open(self.gitignore_path, 'r') as f:
            return f.read()
    
    @staticmethod
    def collection_paths( collections_root, repository, organization ):
        """Returns collection paths.
        """
        paths = []
        regex = '^{}-{}-[0-9]+$'.format(repository, organization)
        uid = re.compile(regex)
        for x in os.listdir(collections_root):
            m = uid.search(x)
            if m:
                colldir = os.path.join(collections_root,x)
                if 'collection.json' in os.listdir(colldir):
                    paths.append(colldir)
        return natural_sort(paths)
    
    def entity_path( self, entity_uid ):
        return os.path.join(self.files_path, entity_uid)
    
    def entity_paths( self ):
        """Returns relative paths to entities.
        """
        paths = []
        cpath = self.path
        if cpath[-1] != '/':
            cpath = '{}/'.format(cpath)
        if os.path.exists(self.files_path):
            for uid in os.listdir(self.files_path):
                epath = os.path.join(self.files_path, uid)
                paths.append(epath)
        return natural_sort(paths)
    
    def entities( self, quick=None ):
        """Returns list of the Collection's Entity objects.
        
        >>> c = Collection.from_json('/tmp/ddr-testing-123')
        >>> c.entities()
        [<Entity ddr-testing-123-1>, <Entity ddr-testing-123-2>, ...]
        
        @param quick: Boolean List only titles and IDs
        """
        # empty class used for quick view
        class ListEntity( object ):
            def __repr__(self):
                return "<DDRListEntity %s>" % (self.id)
        entity_paths = []
        if os.path.exists(self.files_path):
            # TODO use cached list if available
            for eid in os.listdir(self.files_path):
                path = os.path.join(self.files_path, eid)
                entity_paths.append(path)
        entity_paths = natural_sort(entity_paths)
        entities = []
        for path in entity_paths:
            if quick:
                # fake Entity with just enough info for lists
                entity_json_path = os.path.join(path,'entity.json')
                if os.path.exists(entity_json_path):
                    for line in fileio.readlines_raw(entity_json_path):
                        if '"title":' in line:
                            e = ListEntity()
                            e.id = e.uid = eid = os.path.basename(path)
                            e.repo,e.org,e.cid,e.eid = eid.split('-')
                            # make a miniature JSON doc out of just title line
                            e.title = json.loads('{%s}' % line)['title']
                            entities.append(e)
            else:
                entity = Entity.from_json(path)
                for lv in entity.labels_values():
                    if lv['label'] == 'title':
                        entity.title = lv['value']
                entities.append(entity)
        return entities
    
    def repo_fetch( self ):
        """Fetch latest changes to collection repo from origin/master.
        """
        result = '-1'
        if os.path.exists(os.path.join(self.path, '.git')):
            result = dvcs.fetch(self.path)
        else:
            result = '%s is not a git repository' % self.path
        return result
    
    def repo_status( self ):
        """Get status of collection repo vis-a-vis origin/master.
        
        The repo_(synced,ahead,behind,diverged,conflicted) functions all use
        the result of this function so that git-status is only called once.
        """
        if not self._status and (os.path.exists(os.path.join(self.path, '.git'))):
            status = dvcs.repo_status(self.path, short=True)
            if status:
                self._status = status
        return self._status
    
    def repo_annex_status( self ):
        """Get annex status of collection repo.
        """
        if not self._astatus and (os.path.exists(os.path.join(self.path, '.git'))):
            astatus = dvcs.annex_status(self.path)
            if astatus:
                self._astatus = astatus
        return self._astatus
    
    def repo_synced( self ):     return dvcs.synced(self.repo_status())
    def repo_ahead( self ):      return dvcs.ahead(self.repo_status())
    def repo_behind( self ):     return dvcs.behind(self.repo_status())
    def repo_diverged( self ):   return dvcs.diverged(self.repo_status())
    def repo_conflicted( self ): return dvcs.conflicted(self.repo_status())



ENTITY_FILE_KEYS = ['path_rel',
                    'role',
                    'sha1',
                    'sha256',
                    'md5',
                    'public',]

class EntityAddFileLogger():
    logpath = None
    
    def entry(self, ok, msg ):
        """Returns log of add_files activity; adds an entry if status,msg given.
        
        @param ok: Boolean. ok or not ok.
        @param msg: Text message.
        @returns log: A text file.
        """
        entry = '[{}] {} - {}\n'.format(datetime.now().isoformat('T'), ok, msg)
        with open(self.logpath, 'a') as f:
            f.write(entry)
    
    def ok(self, msg): self.entry('ok', msg)
    def not_ok(self, msg): self.entry('not ok', msg)
    
    def log(self):
        log = ''
        if os.path.exists(self.logpath):
            with open(self.logpath, 'r') as f:
                log = f.read()
        return log

class Entity( object ):
    root = None
    uid = None
    id = None
    repo = None
    org = None
    cid = None
    eid = None
    path = None; path_rel = None
    parent_path = None
    parent_uid = None
    json_path = None; json_path_rel = None
    files_path = None; files_path_rel = None
    changelog_path = None; changelog_path_rel = None
    control_path = None; control_path_rel = None
    mets_path = None; mets_path_rel = None
    lock_path = None
    _file_objects = 0
    _file_objects_loaded = 0
    
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
        self.id = uid
        self_model,self.repo,self.org,self.cid,self.eid = Identity.split_object_id(uid)
        self.parent_uid = os.path.split(self.parent_path)[1]
        self.json_path          = self._path_absrel('entity.json')
        self.json_path_rel      = self._path_absrel('entity.json',rel=True)
        self.files_path         = self._path_absrel('files')
        self.files_path_rel     = self._path_absrel('files', rel=True)
        self.changelog_path     = self._path_absrel('changelog')
        self.changelog_path_rel = self._path_absrel('changelog', rel=True)
        self.control_path       = self._path_absrel('control')
        self.control_path_rel   = self._path_absrel('control', rel=True)
        self.mets_path          = self._path_absrel('mets.xml')
        self.mets_path_rel      = self._path_absrel('mets.xml', rel=True)
        self.lock_path          = self._path_absrel('lock')
        self._file_objects = []
    
    def __repr__(self):
        return "<Entity %s>" % (self.id)
    
    @staticmethod
    def create(path):
        """Creates a new entity with the specified entity ID.
        @param path: Absolute path to entity; must end in valid DDR entity id.
        """
        entity = Entity(path)
        for f in entitymodule.FIELDS:
            if hasattr(f, 'name') and hasattr(f, 'initial'):
                setattr(entity, f['name'], f['initial'])
        return entity
    
    @staticmethod
    def from_json(entity_abs):
        """Creates a Entity and populates with data from JSON file.
        
        @param entity_abs: Absolute path to entity dir.
        @returns: Entity
        """
        return from_json(Entity, os.path.join(entity_abs, 'entity.json'))
    
    def model_def_commits( self ):
        return Module(entitymodule).cmp_model_definition_commits(self)
    
    def model_def_fields( self ):
        return Module(entitymodule).cmp_model_definition_fields(fileio.read_raw(self.json_path))
    
    def labels_values(self):
        """Apply display_{field} functions to prep object data for the UI.
        """
        return Module(entitymodule).labels_values(self)

    def inheritable_fields( self ):
        return Inheritance.inheritable_fields(entitymodule.FIELDS)
    
    def selected_inheritables(self, cleaned_data ):
        """Returns names of fields marked as inheritable in cleaned_data.
        
        Fields are considered selected if dict contains key/value pairs in the form
        'FIELD_inherit':True.
        
        @param cleaned_data: dict Fieldname:value pairs.
        @returns: list
        """
        return Inheritance.selected_inheritables(self.inheritable_fields(), cleaned_data)
    
    def update_inheritables( self, inheritables, cleaned_data ):
        """Update specified fields of child objects.
        
        @param inheritables: list Names of fields that shall be inherited.
        @param cleaned_data: dict Fieldname:value pairs.
        @returns: tuple [changed object Ids],[changed objects' JSON files]
        """
        return Inheritance.update_inheritables(self, 'entity', inheritables, cleaned_data)
    
    def inherit( self, parent ):
        Inheritance.inherit( parent, self )
    
    def lock( self, text ): return Locking.lock(self.lock_path, text)
    def unlock( self, text ): return Locking.unlock(self.lock_path, text)
    def locked( self ): return Locking.locked(self.lock_path)

    def load_json(self, json_text):
        """Populate Entity data from JSON-formatted text.
        
        @param json_text: JSON-formatted text
        """
        load_json(self, entitymodule, json_text)
        # special cases
        def parsedt(txt):
            d = datetime.now()
            try:
                d = datetime.strptime(txt, DATETIME_FORMAT)
            except:
                try:
                    d = datetime.strptime(txt, TIME_FORMAT)
                except:
                    pass
            return d
        if hasattr(self, 'record_created') and self.record_created: self.record_created = parsedt(self.record_created)
        if hasattr(self, 'record_lastmod') and self.record_lastmod: self.record_lastmod = parsedt(self.record_lastmod)
        self.rm_file_duplicates()

    def dump_json(self, template=False, doc_metadata=False):
        """Dump Entity data to JSON-formatted text.
        
        @param template: [optional] Boolean. If true, write default values for fields.
        @param doc_metadata: boolean. Insert document_metadata().
        @returns: JSON-formatted text
        """
        data = prep_json(self, entitymodule,
                         exceptions=['files', 'filemeta'],
                         template=template,)
        if doc_metadata:
            data.insert(0, document_metadata(entitymodule, self.parent_path))
        files = []
        if not template:
            for f in self.files:
                fd = {}
                for key in ENTITY_FILE_KEYS:
                    val = None
                    if hasattr(f, key):
                        val = getattr(f, key, None)
                    elif f.get(key,None):
                        val = f[key]
                    if val != None:
                        fd[key] = val
                files.append(fd)
        data.append( {'files':files} )
        return format_json(data)

    def write_json(self):
        """Write JSON file to disk.
        """
        fileio.write_raw(self.dump_json(doc_metadata=True), self.json_path)
    
    def changelog( self ):
        if os.path.exists(self.changelog_path):
            return open(self.changelog_path, 'r').read()
        return '%s is empty or missing' % self.changelog_path
    
    def control( self ):
        if not os.path.exists(self.control_path):
            EntityControlFile.create(self.control_path, self.parent_uid, self.uid)
        return EntityControlFile(self.control_path)

    def mets( self ):
        if not os.path.exists(self.mets_path):
            METS.create(self.mets_path)
        return METS(self)
    
    def dump_mets(self):
        """Dump Entity data to mets.xml file.
        
        TODO render a Django/Jinja template instead of using lxml
        TODO This should not actually write the XML! It should return XML to the code that calls it.
        """
        NAMESPACES = {
            'mets':  'http://www.loc.gov/METS/',
            'mix':   'http://www.loc.gov/mix/v10',
            'mods':  'http://www.loc.gov/mods/v3',
            'rts':   'http://cosimo.stanford.edu/sdr/metsrights/',
            'xlink': 'http://www.w3.org/1999/xlink',
            'xsi':   'http://www.w3.org/2001/XMLSchema-instance',
        }
        NAMESPACES_TAGPREFIX = {}
        for k,v in NAMESPACES.iteritems():
            NAMESPACES_TAGPREFIX[k] = '{%s}' % v
        NAMESPACES_XPATH = {'mets': NAMESPACES['mets'],}
        NSMAP = {None : NAMESPACES['mets'],}
        NS = NAMESPACES_TAGPREFIX
        ns = NAMESPACES_XPATH
        tree = etree.parse(StringIO(self.mets().xml))
        for f in entitymodule.FIELDS:
            key = f['name']
            value = ''
            if hasattr(self, f['name']):
                value = getattr(self, f['name'])
                # run mets_* functions on field data if present
                tree = Module(entitymodule).xml_function(
                    'mets_%s' % key,
                    tree, NAMESPACES, f,
                    value
                )
        xml_pretty = etree.tostring(tree, pretty_print=True)
        with open(self.mets_path, 'w') as f:
            f.write(xml_pretty)
    
    @staticmethod
    def checksum_algorithms():
        return ['md5', 'sha1', 'sha256']
    
    def checksums( self, algo ):
        """Calculates hash checksums for the Entity's files.
        
        Gets hashes from FILE.json metadata if the file(s) are absent
        from the filesystem (i.e. git-annex file symlinks).
        Overrides DDR.models.Entity.checksums.
        """
        checksums = []
        if algo not in self.checksum_algorithms():
            raise Error('BAD ALGORITHM CHOICE: {}'.format(algo))
        for f in self.file_paths():
            cs = None
            fpath = os.path.join(self.files_path, f)
            # git-annex files are present
            if os.path.exists(fpath) and not os.path.islink(fpath):
                cs = file_hash(fpath, algo)
            # git-annex files NOT present - get checksum from entity._files
            # WARNING: THIS MODULE SHOULD NOT KNOW ANYTHING ABOUT HIGHER-LEVEL CODE!
            elif os.path.islink(fpath) and hasattr(self, '_files'):
                for fdict in self._files:
                    if os.path.basename(fdict['path_rel']) == os.path.basename(fpath):
                        cs = fdict[algo]
            if cs:
                checksums.append( (cs, fpath) )
        return checksums
    
    def file_paths( self ):
        """Returns relative paths to payload files.
        """
        paths = []
        prefix_path = self.files_path
        if prefix_path[-1] != '/':
            prefix_path = '{}/'.format(prefix_path)
        if os.path.exists(self.files_path):
            for f in os.listdir(self.files_path):
                paths.append(f.replace(prefix_path, ''))
        paths = sorted(paths, key=lambda f: natural_order_string(f))
        return paths
    
    def load_file_objects( self ):
        """Replaces list of file info dicts with list of File objects
        
        TODO Don't call in loop - causes all file .JSONs to be loaded!
        """
        self._file_objects = []
        for f in self.files:
            if f and f.get('path_rel',None):
                path_abs = os.path.join(self.files_path, f['path_rel'])
                file_ = File(path_abs=path_abs)
                file_.load_json(fileio.read_raw(file_.json_path))
                self._file_objects.append(file_)
        # keep track of how many times this gets loaded...
        self._file_objects_loaded = self._file_objects_loaded + 1
    
    def files_master( self ):
        self.load_file_objects()
        files = [f for f in self._file_objects if hasattr(f,'role') and (f.role == 'master')]
        return sorted(files, key=lambda f: f.sort)
    
    def files_mezzanine( self ):
        self.load_file_objects()
        files = [f for f in self._file_objects if hasattr(f,'role') and (f.role == 'mezzanine')]
        return sorted(files, key=lambda f: f.sort)
    
    def detect_file_duplicates( self, role ):
        """Returns list of file dicts that appear in Entity.files more than once
        
        NOTE: This function looks only at the list of file dicts in entity.json;
        it does not examine the filesystem.
        """
        duplicates = []
        for x,f in enumerate(self.files):
            for y,f2 in enumerate(self.files):
                if (f != f2) and (f['path_rel'] == f2['path_rel']) and (f2 not in duplicates):
                    duplicates.append(f)
        return duplicates
    
    def rm_file_duplicates( self ):
        """Remove duplicates from the Entity.files (._files) list of dicts.
        
        Technically, it rebuilds the last without the duplicates.
        NOTE: See note for detect_file_duplicates().
        """
        # regenerate files list
        new_files = []
        for f in self.files:
            if f not in new_files:
                new_files.append(f)
        self.files = new_files
        # reload objects
        self.load_file_objects()
    
    def file( self, repo, org, cid, eid, role, sha1, newfile=None ):
        """Given a SHA1 hash, get the corresponding file dict.
        
        @param sha1
        @param newfile (optional) If present, updates existing file or appends new one.
        @returns 'added', 'updated', File, or None
        """
        self.load_file_objects()
        # update existing file or append
        if sha1 and newfile:
            for f in self.files:
                if sha1 in f.sha1:
                    f = newfile
                    return 'updated'
            self.files.append(newfile)
            return 'added'
        # get a file
        for f in self._file_objects:
            if (f.sha1[:10] == sha1[:10]) and (f.role == role):
                return f
        # just do nothing
        return None
    
    def _addfile_log_path( self ):
        """Generates path to collection addfiles.log.
        
        Previously each entity had its own addfile.log.
        Going forward each collection will have a single log file.
            /STORE/log/REPO-ORG-CID-addfile.log
        
        @returns: absolute path to logfile
        """
        logpath = os.path.join(
            LOG_DIR, 'addfile', self.parent_uid, '%s.log' % self.id)
        if not os.path.exists(os.path.dirname(logpath)):
            os.makedirs(os.path.dirname(logpath))
        return logpath
    
    def addfile_logger( self ):
        log = EntityAddFileLogger()
        log.logpath = self._addfile_log_path()
        return log
    
    def add_file( self, src_path, role, data, git_name, git_mail, agent='' ):
        """Add file to entity
        
        This method breaks out of OOP and manipulates entity.json directly.
        Thus it needs to lock to prevent other edits while it does its thing.
        Writes a log to ${entity}/addfile.log, formatted in pseudo-TAP.
        This log is returned along with a File object.
        
        IMPORTANT: Files are only staged! Be sure to commit!
        
        @param src_path: Absolute path to an uploadable file.
        @param role: Keyword of a file role.
        @param data: 
        @param git_name: Username of git committer.
        @param git_mail: Email of git committer.
        @param agent: (optional) Name of software making the change.
        @return File,repo,log
        """
        f = None
        repo = None
        log = self.addfile_logger()
        
        def crash(msg):
            """Write to addfile log and raise an exception."""
            log.not_ok(msg)
            raise Exception(msg)

        log.ok('------------------------------------------------------------------------')
        log.ok('DDR.models.Entity.add_file: START')
        log.ok('entity: %s' % self.id)
        log.ok('data: %s' % data)
        
        tmp_dir = os.path.join(
            MEDIA_BASE, 'tmp', 'file-add', self.parent_uid, self.id)
        dest_dir = self.files_path
        
        log.ok('Checking files/dirs')
        def check_dir(label, path, mkdir=False, perm=os.W_OK):
            log.ok('%s: %s' % (label, path))
            if mkdir and not os.path.exists(path):
                os.makedirs(path)
            if not os.path.exists(path): crash('%s does not exist' % label)
            if not os.access(path, perm): crash('%s not has permission %s' % (label, permission))
        check_dir('src_path', src_path, mkdir=False, perm=os.R_OK)
        check_dir('tmp_dir', tmp_dir, mkdir=True, perm=os.W_OK)
        check_dir('dest_dir', dest_dir, mkdir=True, perm=os.W_OK)
        
        log.ok('Checksumming')
        sha1   = file_hash(src_path, 'sha1');   log.ok('sha1: %s' % sha1)
        md5    = file_hash(src_path, 'md5');    log.ok('md5: %s' % md5)
        sha256 = file_hash(src_path, 'sha256'); log.ok('sha256: %s' % sha256)
        if not sha1 and md5 and sha256:
            crash('Could not calculate checksums')
        
        # final basename
        dest_basename = File.file_name(
            self, src_path, role, sha1)  # NOTE: runs checksum if no sha1 arg!
        dest_path = os.path.join(dest_dir, dest_basename)
        
        # file object
        f = File(path_abs=dest_path)
        f.basename_orig = os.path.basename(src_path)
        f.size = os.path.getsize(src_path)
        f.role = role
        f.sha1 = sha1
        f.md5 = md5
        f.sha256 = sha256
        log.ok('Created File: %s' % f)
        log.ok('f.path_abs: %s' % f.path_abs)
        log.ok('f.basename_orig: %s' % f.basename_orig)
        log.ok('f.size: %s' % f.size)
        # form data
        for field in data:
            setattr(f, field, data[field])
        
        log.ok('Copying to work dir')
        tmp_path = os.path.join(tmp_dir, f.basename_orig)
        log.ok('cp %s %s' % (src_path, tmp_path))
        shutil.copy(src_path, tmp_path)
        os.chmod(tmp_path, 0644)
        if not os.path.exists(tmp_path):
            crash('Copy to work dir failed %s %s' % (src_path, tmp_path))
        
        # rename file
        tmp_path_renamed = os.path.join(os.path.dirname(tmp_path), dest_basename)
        log.ok('Renaming %s -> %s' % (os.path.basename(tmp_path), dest_basename))
        os.rename(tmp_path, tmp_path_renamed)
        if not os.path.exists(tmp_path_renamed) and not os.path.exists(tmp_path):
            crash('File rename failed: %s -> %s' % (tmp_path, tmp_path_renamed))
        
        log.ok('Extracting XMP data')
        f.xmp = imaging.extract_xmp(src_path)
        
        log.ok('Making access file')
        access_filename = File.access_filename(tmp_path_renamed)
        tmp_access_path = None
        try:
            tmp_access_path = imaging.thumbnail(
                src_path,
                os.path.join(tmp_dir, os.path.basename(access_filename)),
                geometry=ACCESS_FILE_GEOMETRY)
        except:
            # write traceback to log and continue on
            log.not_ok(traceback.format_exc().strip())
        if tmp_access_path and os.path.exists(tmp_access_path):
            log.ok('Attaching access file')
            #dest_access_path = os.path.join('files', os.path.basename(tmp_access_path))
            #log.ok('dest_access_path: %s' % dest_access_path)
            f.set_access(tmp_access_path, self)
            log.ok('f.access_rel: %s' % f.access_rel)
            log.ok('f.access_abs: %s' % f.access_abs)
        else:
            log.not_ok('no access file')
        
        log.ok('Attaching file to entity')
        self.files.append(f)
        
        log.ok('Writing file metadata')
        tmp_file_json = os.path.join(tmp_dir, os.path.basename(f.json_path))
        log.ok(tmp_file_json)
        fileio.write_raw(f.dump_json(), tmp_file_json)
        if not os.path.exists(tmp_file_json):
            crash('Could not write file metadata %s' % tmp_file_json)
        log.ok('Writing entity metadata')
        tmp_entity_json = os.path.join(tmp_dir, os.path.basename(self.json_path))
        log.ok(tmp_entity_json)
        fileio.write_raw(self.dump_json(), tmp_entity_json)
        if not os.path.exists(tmp_entity_json):
            crash('Could not write entity metadata %s' % tmp_entity_json)
        
        # WE ARE NOW MAKING CHANGES TO THE REPO ------------------------
        
        log.ok('Moving files to dest_dir')
        new_files = [
            [tmp_path_renamed, f.path_abs],
            [tmp_file_json, f.json_path],
        ]
        if tmp_access_path and os.path.exists(tmp_access_path):
            new_files.append([tmp_access_path, f.access_abs])
        mvfiles_failures = []
        for tmp,dest in new_files:
            log.ok('mv %s %s' % (tmp,dest))
            os.rename(tmp,dest)
            if not os.path.exists(dest):
                log.not_ok('FAIL')
                mvfiles_failures.append(tmp)
                break
        # one of new_files failed to copy, so move all back to tmp
        if mvfiles_failures:
            log.not_ok('%s failures: %s' % (len(mvfiles_failures), mvfiles_failures))
            log.not_ok('moving files back to tmp_dir')
            try:
                for tmp,dest in new_files:
                    log.ok('mv %s %s' % (dest,tmp))
                    os.rename(dest,tmp)
                    if not os.path.exists(tmp) and not os.path.exists(dest):
                        log.not_ok('FAIL')
            except:
                msg = "Unexpected error:", sys.exc_info()[0]
                log.not_ok(msg)
                raise
            finally:
                crash('Failed to place one or more files to destination repo')
        # entity metadata will only be copied if everything else was moved
        log.ok('mv %s %s' % (tmp_entity_json, self.json_path))
        os.rename(tmp_entity_json, self.json_path)
        if not os.path.exists(self.json_path):
            crash('Failed to place entity.json in destination repo')
        
        # stage files
        git_files = [self.json_path_rel, f.json_path_rel]
        annex_files = [f.path_abs.replace('%s/' % f.collection_path, '')]
        if f.access_abs:
            annex_files.append(f.access_abs.replace('%s/' % f.collection_path, ''))
        repo = dvcs.repository(f.collection_path)
        log.ok(repo)
        # These vars will be used to determine if stage operation is successful.
        # If called in batch operation there may already be staged files.
        # stage_planned   Files added/modified by this function call
        # stage_already   Files that were already staged
        # stage_predicted List of staged files that should result from this operation.
        # stage_new       Files that are being added.
        stage_planned = git_files + annex_files
        stage_already = dvcs.list_staged(repo)
        stage_predicted = self._addfile_predict_staged(stage_already, stage_planned)
        stage_new = [x for x in stage_planned if x not in stage_already]
        log.ok('Staging %s files' % len(stage_planned))
        stage_ok = False
        staged = []
        try:
            dvcs.stage(repo, git_files, annex_files)
            staged = dvcs.list_staged(repo)
        except:
            # FAILED! print traceback to addfile log
            entrails = traceback.format_exc().strip()
            log.not_ok(entrails)
            with open(self._addfile_log_path(), 'a') as f:
                f.write(entrails)
        finally:
            if len(staged) == len(stage_predicted):
                log.ok('%s files staged (%s new, %s modified)' % (
                    len(staged), len(stage_new), len(stage_already)))
                stage_ok = True
            else:
                log.not_ok('%s new files staged (should be %s)' % (
                    len(staged), len(stage_predicted)))
            if not stage_ok:
                log.not_ok('File staging aborted. Cleaning up...')
                # try to pick up the pieces
                # mv files back to tmp_dir
                # TODO Properly clean up git-annex-added files.
                #      This clause moves the *symlinks* to annex files but leaves
                #      the actual binaries in the .git/annex objects dir.
                for tmp,dest in new_files:
                    log.not_ok('mv %s %s' % (dest,tmp))
                    os.rename(dest,tmp)
                log.not_ok('finished cleanup. good luck...')
                raise crash('Add file aborted, see log file for details.')
        
        # IMPORTANT: Files are only staged! Be sure to commit!
        # IMPORTANT: changelog is not staged!
        return f,repo,log
    
    def _addfile_predict_staged(self, already, planned):
        """Predict which files will be staged, accounting for modifications
        
        When running a batch import there will already be staged files when this function is called.
        Some files to be staged will be modifications (e.g. entity.json).
        Predicts the list of files that will be staged if this round of add_file succeeds.
        how many files SHOULD be staged after we run this?
        
        @param already: list Files already staged.
        @param planned: list Files to be added/modified in this operation.
        @returns: list
        """
        additions = [path for path in planned if path not in already]
        total = already + additions
        return total
    
    def add_file_commit(self, file_, repo, log, git_name, git_mail, agent):
        staged = dvcs.list_staged(repo)
        modified = dvcs.list_modified(repo)
        if staged and not modified:
            log.ok('All files staged.')
            
            log.ok('Updating changelog')
            path = file_.path_abs.replace('{}/'.format(self.path), '')
            changelog_messages = ['Added entity file {}'.format(path)]
            if agent:
                changelog_messages.append('@agent: %s' % agent)
            changelog.write_changelog_entry(
                self.changelog_path, changelog_messages, git_name, git_mail)
            log.ok('git add %s' % self.changelog_path_rel)
            git_files = [self.changelog_path_rel]
            dvcs.stage(repo, git_files)
            
            log.ok('Committing')
            commit = dvcs.commit(repo, 'Added entity file(s)', agent)
            log.ok('commit: {}'.format(commit.hexsha))
            committed = dvcs.list_committed(repo, commit)
            committed.sort()
            log.ok('files committed:     {}'.format(committed))
            
        else:
            log.not_ok('%s files staged, %s files modified' % (len(staged),len(modified)))
            log.not_ok('staged %s' % staged)
            log.not_ok('modified %s' % modified)
            log.not_ok('Can not commit!')
            raise Exception()
        return file_,repo,log
    
    def add_access( self, ddrfile, git_name, git_mail, agent='' ):
        """Generate new access file for entity
        
        This method breaks out of OOP and manipulates entity.json directly.
        Thus it needs to lock to prevent other edits while it does its thing.
        Writes a log to ${entity}/addfile.log, formatted in pseudo-TAP.
        This log is returned along with a File object.
        
        TODO Refactor this function! It is waaay too long!
        
        @param ddrfile: File object
        @param git_name: Username of git committer.
        @param git_mail: Email of git committer.
        @param agent: (optional) Name of software making the change.
        @return file_ File object
        """
        from DDR.commands import entity_annex_add
        
        f = ddrfile
        repo = None
        log = self.addfile_logger()
        
        def crash(msg):
            """Write to addfile log and raise an exception."""
            log.not_ok(msg)
            raise Exception(msg)
        
        log.ok('DDR.models.Entity.add_access: START')
        log.ok('entity: %s' % self.id)
        log.ok('ddrfile: %s' % ddrfile)
        
        src_path = ddrfile.path_abs
        tmp_dir = os.path.join(
            MEDIA_BASE, 'tmp', 'file-add',
            self.parent_uid, self.id)
        dest_dir = self.files_path

        log.ok('Checking files/dirs')
        def check_dir(label, path, mkdir=False, perm=os.W_OK):
            log.ok('%s: %s' % (label, path))
            if mkdir and not os.path.exists(path):
                os.makedirs(path)
            if not os.path.exists(path): crash('%s does not exist' % label)
            if not os.access(path, perm): crash('%s not has permission %s' % (label, permission))
        check_dir('src_path', src_path, mkdir=False, perm=os.R_OK)
        check_dir('tmp_dir', tmp_dir, mkdir=True, perm=os.W_OK)
        check_dir('dest_dir', dest_dir, mkdir=True, perm=os.W_OK)
        
        log.ok('Making access file')
        access_filename = File.access_filename(src_path)
        tmp_access_path = None
        try:
            tmp_access_path = imaging.thumbnail(
                src_path,
                os.path.join(tmp_dir, os.path.basename(access_filename)),
                geometry=ACCESS_FILE_GEOMETRY)
        except:
            # write traceback to log and continue on
            log.not_ok(traceback.format_exc().strip())
        if tmp_access_path and os.path.exists(tmp_access_path):
            log.ok('Attaching access file')
            #dest_access_path = os.path.join('files', os.path.basename(tmp_access_path))
            #log.ok('dest_access_path: %s' % dest_access_path)
            f.set_access(tmp_access_path, self)
            log.ok('f.access_rel: %s' % f.access_rel)
            log.ok('f.access_abs: %s' % f.access_abs)
        else:
            crash('Failed to make an access file from %s' % src_path)
        
        log.ok('Writing file metadata')
        tmp_file_json = os.path.join(tmp_dir, os.path.basename(f.json_path))
        log.ok(tmp_file_json)
        fileio.write_raw(f.dump_json(), tmp_file_json)
        if not os.path.exists(tmp_file_json):
            crash('Could not write file metadata %s' % tmp_file_json)
        
        # WE ARE NOW MAKING CHANGES TO THE REPO ------------------------
        
        log.ok('Moving files to dest_dir')
        new_files = []
        new_files.append([tmp_access_path, f.access_abs])
        mvfiles_failures = []
        for tmp,dest in new_files:
            log.ok('mv %s %s' % (tmp,dest))
            os.rename(tmp,dest)
            if not os.path.exists(dest):
                log.not_ok('FAIL')
                mvfiles_failures.append(tmp)
                break
        # one of new_files failed to copy, so move all back to tmp
        if mvfiles_failures:
            log.not_ok('%s failures: %s' % (len(mvfiles_failures), mvfiles_failures))
            log.not_ok('moving files back to tmp_dir')
            try:
                for tmp,dest in new_files:
                    log.ok('mv %s %s' % (dest,tmp))
                    os.rename(dest,tmp)
                    if not os.path.exists(tmp) and not os.path.exists(dest):
                        log.not_ok('FAIL')
            except:
                msg = "Unexpected error:", sys.exc_info()[0]
                log.not_ok(msg)
                raise
            finally:
                crash('Failed to place one or more files to destination repo')
        # file metadata will only be copied if everything else was moved
        log.ok('mv %s %s' % (tmp_file_json, f.json_path))
        os.rename(tmp_file_json, f.json_path)
        if not os.path.exists(f.json_path):
            crash('Failed to place file metadata in destination repo')
        
        # commit
        git_files = [f.json_path_rel]
        annex_files = [f.access_rel]
        log.ok('entity_annex_add(%s, %s, %s, %s, %s, %s, %s, %s)' % (
            git_name, git_mail,
            self.parent_path, self.id,
            git_files, annex_files,
            agent, self))
        try:
            exit,status = entity_annex_add(
                git_name, git_mail,
                self.parent_path, self.id, git_files, annex_files,
                agent=agent, entity=self)
            log.ok('status: %s' % status)
            log.ok('DDR.models.Entity.add_file: FINISHED')
        except:
            # COMMIT FAILED! try to pick up the pieces
            # print traceback to addfile log
            with open(self._addfile_log_path(), 'a') as f:
                traceback.print_exc(file=f)
            # mv files back to tmp_dir
            log.not_ok('status: %s' % status)
            log.not_ok('Cleaning up...')
            for tmp,dest in new_files:
                log.not_ok('mv %s %s' % (dest,tmp))
                os.rename(dest,tmp)
            # restore backup of original file metadata
            log.not_ok('cp %s %s' % (file_json_backup, f.json_path))
            shutil.copy(file_json_backup, f.json_path)
            log.not_ok('finished cleanup. good luck...')
            raise
        
        return f,repo,log



FILE_KEYS = ['path_rel',
             'basename', 
             'size', 
             'role', 
             'sha1', 
             'sha256', 
             'md5',
             'basename_orig',
             'public',
             'sort',
             'label',
             'thumb',
             'access_rel',
             'xmp',]

class File( object ):
    id = 'whatever'
    # path relative to /
    # (ex: /var/www/media/base/ddr-testing-71/files/ddr-testing-71-6/files/ddr-testing-71-6-dd9ec4305d.jpg)
    # not saved; constructed on instantiation
    path = None
    path_abs = None
    # files
    # path relative to entity files directory
    # (ex: ddr-testing-71-6-dd9ec4305d.jpg)
    # (ex: subdir/ddr-testing-71-6-dd9ec4305d.jpg)
    path_rel = None
    json_path = None
    json_path_rel = None
    basename = None
    basename_orig = ''
    size = None
    role = None
    sha1 = None
    sha256 = None
    md5 = None
    public = 0
    sort = 1
    label = ''
    thumb = -1
    # access file path relative to entity
    access_rel = None
    # access file path relative to /
    # not saved; constructed on instantiation
    access_abs = None
    access_size = None
    xmp = ''
    # entity
    src = None
    repo = None
    org = None
    cid = None
    eid = None
    collection_path = None
    entity_path = None
    entity_files_path = None
    links = None
    
    def __init__(self, *args, **kwargs):
        """
        IMPORTANT: If at all possible, use the "path_abs" kwarg!!
        You *can* just pass in an absolute path. It will *appear* to work.
        This horrible function will attempt to infer the path but will
        probably get it wrong and fail silently!
        TODO refactor and simplify this horrible code!
        """
        # accept either path_abs or path_rel
        if kwargs and kwargs.get('path_abs',None):
            self.path_abs = kwargs['path_abs']
        elif kwargs and kwargs.get('path_rel',None):
            self.path_rel = kwargs['path_rel']
        else:
            if args and args[0]:
                s = os.path.splitext(args[0])
                if os.path.exists(args[0]):  # <<< Causes problems with missing git-annex files
                    self.path_abs = args[0]  #     Use path_abs arg!!!
                elif (len(s) == 2) and s[0] and s[1]:
                    self.path_rel = args[0]
        if self.path_abs:
            self.basename = os.path.basename(self.path_abs)
        elif self.path_rel:
            self.basename = os.path.basename(self.path_rel)
        # IMPORTANT: path_rel is the link between Entity and File
        # It MUST be present in entity.json and file.json or lots of
        # things will break!
        # NOTE: path_rel is basically the same as basename
        if self.path_abs and not self.path_rel:
            self.path_rel = self.basename
        # much info is encoded in filename
        if self.basename:
            parts = os.path.splitext(self.basename)[0].split('-')
            self.repo = parts[0]
            self.org = parts[1]
            self.cid = parts[2]
            self.eid = parts[3]
            # NOTE: we get role from filename and also from JSON data, if available
            self.role = parts[4]
            self.sha1 = parts[5]
            self.id = '-'.join([self.repo,self.org,self.cid,self.eid,self.role,self.sha1])
        # get one path if the other not present
        if self.entity_path and self.path_rel and not self.path_abs:
            self.path_abs = os.path.join(self.entity_files_path, self.path_rel)
        elif self.entity_path and self.path_abs and not self.path_rel:
            self.path_rel = self.path_abs.replace(self.entity_files_path, '')
        # clean up path_rel if necessary
        if self.path_rel and (self.path_rel[0] == '/'):
            self.path_rel = self.path_rel[1:]
        # load JSON
        if self.path_abs:
            self.path = self.path_abs
            p = Identity.dissect_path(self.path_abs)
            self.collection_path = p.collection_path
            self.entity_path = p.entity_path
            self.entity_files_path = os.path.join(self.entity_path, ENTITY_FILES_PREFIX)
            # file JSON
            self.json_path = os.path.join(os.path.splitext(self.path_abs)[0], '.json')
            self.json_path = self.json_path.replace('/.json', '.json')
            self.json_path_rel = self.json_path.replace(self.collection_path, '')
            if self.json_path_rel[0] == '/':
                self.json_path_rel = self.json_path_rel[1:]
            ## TODO seriously, do we need this?
            #with open(self.json_path, 'r') as f:
            #    self.load_json(f.read())
            access_abs = None
            if self.access_rel and self.entity_path:
                access_abs = os.path.join(self.entity_files_path, self.access_rel)
                if os.path.exists(access_abs):
                    self.access_abs = os.path.join(self.entity_files_path, self.access_rel)
    
    def __repr__(self):
        return "<File %s (%s)>" % (self.basename, self.basename_orig)
    
    # _lockfile
    # lock
    # unlock
    # locked
    
    # create(path)
    
    # entities/files/???
    
    def model_def_commits( self ):
        return Module(filemodule).cmp_model_definition_commits(self)
    
    def model_def_fields( self ):
        return Module(filemodule).cmp_model_definition_fields(fileio.read_raw(self.json_path))
    
    def labels_values(self):
        """Apply display_{field} functions to prep object data for the UI.
        """
        return Module(filemodule).labels_values(self)
    
    def files_rel( self, collection_path ):
        """Returns list of the file, its metadata JSON, and access file, relative to collection.
        
        @param collection_path
        @returns: list of relative file paths
        """
        if collection_path[-1] != '/':
            collection_path = '%s/' % collection_path
        paths = [ ]
        if self.path_abs and os.path.exists(self.path_abs) and (collection_path in self.path_abs):
            paths.append(self.path_abs.replace(collection_path, ''))
        if self.json_path and os.path.exists(self.json_path) and (collection_path in self.json_path):
            paths.append(self.json_path.replace(collection_path, ''))
        if self.access_abs and os.path.exists(self.access_abs) and (collection_path in self.access_abs):
            paths.append(self.access_abs.replace(collection_path, ''))
        return paths
    
    def present( self ):
        """Indicates whether or not the original file is currently present in the filesystem.
        """
        if self.path_abs and os.path.exists(self.path_abs):
            return True
        return False
    
    def access_present( self ):
        """Indicates whether or not the access file is currently present in the filesystem.
        """
        if self.access_abs and os.path.exists(self.access_abs):
            return True
        return False
    
    def inherit( self, parent ):
        Inheritance.inherit( parent, self )
    
    @staticmethod
    def from_json(file_json):
        """Creates a File and populates with data from JSON file.
        
        @param file_json: Absolute path to JSON file.
        @returns: File
        """
        # This is complicated: The file object has to be created with
        # the path to the file to which the JSON metadata file refers.
        file_abs = None
        fid = os.path.splitext(os.path.basename(file_json))[0]
        fstub = '%s.' % fid
        for filename in os.listdir(os.path.dirname(file_json)):
            if (fstub in filename) and not ('json' in filename):
                file_abs = os.path.join(os.path.dirname(file_json), filename)
        # Now load the object
        file_ = None
        if os.path.exists(file_abs) or os.path.islink(file_abs):
            file_ = File(path_abs=file_abs)
            file_.load_json(fileio.read_raw(file_.json_path))
        return file_
    
    def load_json(self, json_text):
        """Populate File data from JSON-formatted text.
        
        @param json_text: JSON-formatted text
        """
        json_data = load_json(self, filemodule, json_text)
        # fill in the blanks
        if self.access_rel:
            access_abs = os.path.join(self.entity_files_path, self.access_rel)
            if os.path.exists(access_abs):
                self.access_abs = access_abs
    
    def dump_json(self, doc_metadata=False):
        """Dump File data to JSON-formatted text.
        
        @param doc_metadata: boolean. Insert document_metadata().
        @returns: JSON-formatted text
        """
        data = prep_json(self, filemodule)
        if doc_metadata:
            data.insert(0, document_metadata(filemodule, self.collection_path))
        data.insert(1, {'path_rel': self.path_rel})
        return format_json(data)

    def write_json(self):
        """Write JSON file to disk.
        """
        fileio.write_raw(self.dump_json(doc_metadata=True), self.json_path)
    
    @staticmethod
    def file_name( entity, path_abs, role, sha1=None ):
        """Generate a new name for the specified file; Use only when ingesting a file!
        
        rename files to standard names on ingest:
        %{repo}-%{org}-%{cid}-%{eid}-%{role}%{sha1}.%{ext}
        example: ddr-testing-56-101-master-fb73f9de29.jpg
        
        SHA1 is optional so it can be passed in by a calling process that has already
        generated it.
        
        @param entity
        @param path_abs: Absolute path to the file.
        @param role
        @param sha1: SHA1 hash (optional)
        """
        if os.path.exists and os.access(path_abs, os.R_OK):
            ext = os.path.splitext(path_abs)[1]
            if not sha1:
                sha1 = file_hash(path_abs, 'sha1')
            if sha1:
                base = '-'.join([
                    entity.repo, entity.org, entity.cid, entity.eid,
                    role,
                    sha1[:10]
                ])
                name = '{}{}'.format(base, ext)
                return name
        return None
    
    def set_path( self, path_rel, entity=None ):
        """
        Reminder:
        self.path_rel is relative to entity
        self.path_abs is relative to filesystem root
        """
        self.path_rel = path_rel
        if entity:
            self.path_rel = self.path_rel.replace(entity.files_path, '')
        if self.path_rel and (self.path_rel[0] == '/'):
            # remove initial slash (ex: '/files/...')
            self.path_rel = self.path_rel[1:]
        if entity:
            self.path_abs = os.path.join(entity.files_path, self.path_rel)
            self.src = os.path.join('base', entity.files_path, self.path_rel)
        if self.path_abs and os.path.exists(self.path_abs):
            self.size = os.path.getsize(self.path_abs)
        self.basename = os.path.basename(self.path_rel)
    
    def set_access( self, access_rel, entity=None ):
        """
        @param access_rel: path relative to entity files dir (ex: 'thisfile.ext')
        @param entity: A Entity object (optional)
        """
        self.access_rel = os.path.basename(access_rel)
        if entity:
            self.access_abs = os.path.join(entity.files_path, self.access_rel)
        if self.access_abs and os.path.exists(self.access_abs):
            self.access_size = os.path.getsize(self.access_abs)
    
    def file( self ):
        """Simulates an entity['files'] dict used to construct file"""
        f = {}
        for key in FILE_KEYS:
            if hasattr(self, key):
                f[key] = getattr(self, key, None)
        return f
        
    def dict( self ):
        return self.__dict__
        
    @staticmethod
    def access_filename( src_abs ):
        """Generate access filename base on source filename.
        
        @param src_abs: Absolute path to source file.
        @returns: Absolute path to access file
        """
        return '%s%s.%s' % (
            os.path.splitext(src_abs)[0],
            ACCESS_FILE_APPEND,
            'jpg')
    
    def links_incoming( self ):
        """List of path_rels of files that link to this file.
        """
        incoming = []
        cmd = 'find {} -name "*.json" -print'.format(self.entity_files_path)
        r = envoy.run(cmd)
        jsons = []
        if r.std_out:
            jsons = r.std_out.strip().split('\n')
        for filename in jsons:
            data = json.loads(fileio.read_raw(filename))
            path_rel = None
            for field in data:
                if field.get('path_rel',None):
                    path_rel = field['path_rel']
            for field in data:
                linksraw = field.get('links', None)
                if linksraw:
                    for link in linksraw.strip().split(';'):
                        link = link.strip()
                        if self.basename in link:
                            incoming.append(path_rel)
        return incoming
    
    def links_outgoing( self ):
        """List of path_rels of files this file links to.
        """
        if self.links:
            return [link.strip() for link in self.links.strip().split(';')]
        return []
    
    def links_all( self ):
        """List of path_rels of files that link to this file or are linked to from this file.
        """
        links = self.links_outgoing()
        for l in self.links_incoming():
            if l not in links:
                links.append(l)
        return links
