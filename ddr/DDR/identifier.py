# coding: utf-8

from collections import OrderedDict
import importlib
import os
import re
import string
from urlparse import urlparse


# Models in this Repository
MODELS = [
    'file',
    'file-role',
    'entity',
    'collection',   # required
    'organization', # required
    'repository',   # required
]

# map model names to DDR python classes
MODEL_CLASSES = {
    'file':         {'module': 'DDR.models', 'class':'File'},
    'file-role':    {'module': 'DDR.models', 'class':'Stub'},
    'entity':       {'module': 'DDR.models', 'class':'Entity'},
    'collection':   {'module': 'DDR.models', 'class':'Collection'},
    'organization': {'module': 'DDR.models', 'class':'Stub'},
    'repository':   {'module': 'DDR.models', 'class':'Stub'},
}

# TODO no hard-coding: import using os.listdir
MODULES = { key:None for key in MODELS }
try:
    from repo_models import collection as collectionmodule
    from repo_models import entity as entitymodule
    from repo_models import files as filemodule
    MODULES['collection'] = collectionmodule
    MODULES['entity'] = entitymodule
    MODULES['file'] = filemodule
except ImportError:
    raise Exception('Could not import repo_models modules!')

# map model names to module files in ddr repo's repo_models
MODEL_REPO_MODELS = {
    'file':         {'module': 'repo_models.files', 'class':'file', 'as':'filemodule'},
    'entity':       {'module': 'repo_models.entity', 'class':'entity', 'as':'entitymodule'},
    'collection':   {'module': 'repo_models.collection', 'class':'collection', 'as':'collectionmodule'},
}


# Models that are part of collection repositories. Repository and organizations
# are above the level of the collection and are thus excluded.
COLLECTION_MODELS = [
    'file',
    'file-role',
    'entity',
    'collection',   # required
]

# Models that can contain other models.
CONTAINERS = [
    'file-role',
    'entity',
    'collection',
    'organization',
    'repository',
]

# Pointers from models to their parent models
PARENTS = {
    'file': 'entity',
    'entity': 'collection',
    'collection': None,
}
# include Stubs
PARENTS_ALL = {
    #'file': 'entity',
    'file': 'file-role',
    'file-role': 'entity',
    'entity': 'collection',
    'collection': 'organization',
    'organization': 'repository',
    'repository': None,
}
CHILDREN = {val:key for key,val in PARENTS.iteritems() if val}
CHILDREN_ALL = {val:key for key,val in PARENTS_ALL.iteritems() if val}

# Keywords that can legally appear in IDs
ID_COMPONENTS = [
    'repo', 'org', 'cid', 'eid', 'role', 'sha1', 'ext'
]

# Components in VALID_COMPONENTS.keys() must appear in VALID_COMPONENTS[key] to be valid.
VALID_COMPONENTS = {
    'repo': [
        'ddr'
    ],
    'org': [
        'densho', 'hmwf', 'jamsj', 'janm', 'jcch', 'njpa', 'one', 'pc',
        'dev', 'test', 'testing',
    ],
    'role': [
        'master', 'mezzanine'
    ],
}

# Bits of file paths that uniquely identify file types.
# Suitable for use on command-line e.g. in git-annex-whereis.
FILETYPE_MATCH_ANNEX = {
    'access': '*-a.jpg',
    'master': '*-master-*',
    'mezzanine': '*-mezzanine-*',
}

# ----------------------------------------------------------------------
# Regex patterns used to match IDs, paths, and URLs and extract model and tokens
# Record format: (regex, memo, model)
# TODO compile regexes
#

def _compile_patterns(patterns):
    """Replace str regexes with compiled regular expression objects.
    """
    new = []
    for p in patterns:
        pattern = [x for x in p]
        pattern[0] = re.compile(p[0])
        new.append(pattern)
    return new

# (regex, memo, model) NOTE: 'memo' is not used for anything yet
ID_PATTERNS = _compile_patterns((
    (r'^(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[\w]+)-(?P<sha1>[\w]+)$', '', 'file'),
    (r'^(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[\w]+)$', '', 'file-role'),
    (r'^(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)$', '', 'entity'),
    (r'^(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)$', '', 'collection'),
    (r'^(?P<repo>[\w]+)-(?P<org>[\w]+)$', '', 'organization'),
    (r'^(?P<repo>[\w]+)$', '', 'repository'),
))

# In the current path scheme, collection and entity ID components are repeated.
# Fields can't appear multiple times in regexes so redundant fields have numbers.
# (regex, memo, model) NOTE: 'memo' is not used for anything yet
PATH_PATTERNS = _compile_patterns((
    # file-abs
    (r'(?P<basepath>[\w/-]+)/(?P<repo0>[\w]+)-(?P<org0>[\w]+)-(?P<cid0>[\d]+)/files/(?P<repo1>[\w]+)-(?P<org1>[\w]+)-(?P<cid1>[\d]+)-(?P<eid1>[\d]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[\w]+)-(?P<sha1>[\w\d]+)\.(?P<ext>[\w]+)$', 'file-ext-abs', 'file'),
    (r'(?P<basepath>[\w/-]+)/(?P<repo0>[\w]+)-(?P<org0>[\w]+)-(?P<cid0>[\d]+)/files/(?P<repo1>[\w]+)-(?P<org1>[\w]+)-(?P<cid1>[\d]+)-(?P<eid1>[\d]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[\w]+)-(?P<sha1>[\w\d]+)\.json$', 'file-meta-abs', 'file'),
    (r'(?P<basepath>[\w/-]+)/(?P<repo0>[\w]+)-(?P<org0>[\w]+)-(?P<cid0>[\d]+)/files/(?P<repo1>[\w]+)-(?P<org1>[\w]+)-(?P<cid1>[\d]+)-(?P<eid1>[\d]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[\w]+)-(?P<sha1>[\w\d]+)$', 'file-abs', 'file'),
    # file-rel
    (r'^files/(?P<repo0>[\w]+)-(?P<org0>[\w]+)-(?P<cid0>[\d]+)-(?P<eid0>[\d]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[\w]+)-(?P<sha1>[\w\d]+)\.(?P<ext>[\w]+)$', 'file-ext-rel', 'file'),
    (r'^files/(?P<repo0>[\w]+)-(?P<org0>[\w]+)-(?P<cid0>[\d]+)-(?P<eid0>[\d]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[\w]+)-(?P<sha1>[\w\d]+)\.json$', 'file-meta-rel', 'file'),
    (r'^files/(?P<repo0>[\w]+)-(?P<org0>[\w]+)-(?P<cid0>[\d]+)-(?P<eid0>[\d]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[\w]+)-(?P<sha1>[\w\d]+)$', 'file-rel', 'file'),
    # entity
    (r'(?P<basepath>[\w/-]+)/(?P<repo0>[\w]+)-(?P<org0>[\w]+)-(?P<cid0>[\d]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)', 'entity-abs', 'entity'),
    (r'^files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)$', 'entity-rel', 'entity'),
    # collection
    (r'(?P<basepath>[\w/-]+)/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)', 'collection-abs', 'collection'),
    (r'^collection.json$', 'collection-meta-rel', 'collection'),
    # organization
    (r'(?P<basepath>[\w/-]+)/(?P<repo>[\w]+)-(?P<org>[\w]+)$', 'organization-abs', 'organization'),
    (r'^organization.json$', 'organization-meta-rel', 'organization'),
    # repository
    (r'(?P<basepath>[\w/-]+)/(?P<repo>[\w]+)/repository.json$', 'repository-meta-abs', 'repository'),
    (r'(?P<basepath>[\w/-]+)/(?P<repo>[\w]+)$', 'repository-meta-abs', 'repository'),
    (r'^repository.json$', 'repository-meta-rel', 'repository'),
))

# Simple path regexes suitable for use inside for-loops
PATH_PATTERNS_LOOP = (
    (r'(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[\w]+)-(?P<sha1>[\w\d]+).json$', '' 'file-json'),
    (r'entity.json$', '' 'entity-json'),
    (r'collection.json$', '' 'collection-json'),
)

# (regex, memo, model) NOTE: 'memo' is not used for anything yet
URL_PATTERNS = _compile_patterns((
    # editor
    (r'/ui/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[\w]+)-(?P<sha1>[\w]+)$', 'editor-file', 'file'),
    (r'/ui/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[\w]+)$', 'editor-file-role', 'file-role'),
    (r'/ui/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)$', 'editor-entity', 'entity'),
    (r'/ui/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)$', 'editor-collection', 'collection'),
    (r'/ui/(?P<repo>[\w]+)-(?P<org>[\w]+)$', 'editor-organization', 'organization'),
    (r'/ui/(?P<repo>[\w]+)$', 'editor-repository', 'repository'),
    # public
    (r'^/(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)/(?P<eid>[\d]+)/(?P<role>[\w]+)/(?P<sha1>[\w]+)$', 'public-file', 'file'),
    (r'^/(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)/(?P<eid>[\d]+)/(?P<role>[\w]+)$', 'public-file-role', 'file-role'),
    (r'^/(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)/(?P<eid>[\d]+)$', 'public-entity', 'entity'),
    (r'^/(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)$', 'public-collection', 'collection'),
    (r'^/(?P<repo>[\w]+)/(?P<org>[\w]+)$', 'public-organization', 'organization'),
    (r'^/(?P<repo>[\w]+)$', 'public-repository', 'repository'),
))

# ----------------------------------------------------------------------
# Templates used to generate IDs, paths, and URLs from model and tokens
#

ID_TEMPLATES = {
    'file':         '{repo}-{org}-{cid}-{eid}-{role}-{sha1}',
    'file-role':    '{repo}-{org}-{cid}-{eid}-{role}',
    'entity':       '{repo}-{org}-{cid}-{eid}',
    'collection':   '{repo}-{org}-{cid}',
    'organization': '{repo}-{org}',
    'repository':   '{repo}',
}

PATH_TEMPLATES = {
    'file-rel':         'files/{repo}-{org}-{cid}-{eid}/files/{repo}-{org}-{cid}-{eid}-{role}-{sha1}',
    # file-role-rel
    'entity-rel':       'files/{repo}-{org}-{cid}-{eid}',
    'file-abs':         '{basepath}/{repo}-{org}-{cid}/files/{repo}-{org}-{cid}-{eid}/files/{repo}-{org}-{cid}-{eid}-{role}-{sha1}',
    # file-role-abs
    'entity-abs':       '{basepath}/{repo}-{org}-{cid}/files/{repo}-{org}-{cid}-{eid}',
    'collection-abs':   '{basepath}/{repo}-{org}-{cid}',
    'organization-abs': '{basepath}/{repo}-{org}',
    'repository-abs':   '{basepath}/{repo}',
    #'file-rel':         '{eid}/{repo}-{org}-{cid}-{eid}-{role}-{sha1}',
    #'entity-rel':       '{eid}',
    #'file-abs':         '{basepath}/{repo}-{org}-{cid}/{eid}/{repo}-{org}-{cid}-{eid}-{role}-{sha1}',
    #'entity-abs':       '{basepath}/{repo}-{org}-{cid}/{eid}',
    #'collection-abs':   '{basepath}/{repo}-{org}-{cid}',
    #'organization-abs': '{basepath}/{repo}-{org}',
    #'repository-abs':   '{basepath}/{repo}',
}

URL_TEMPLATES = {
    'editor': {
        'file':         '/ui/{repo}-{org}-{cid}-{eid}-{role}-{sha1}',
        'file-role':    '/ui/{repo}-{org}-{cid}-{eid}-{role}',
        'entity':       '/ui/{repo}-{org}-{cid}-{eid}',
        'collection':   '/ui/{repo}-{org}-{cid}',
        'organization': '/ui/{repo}-{org}',
        'repository':   '/ui/{repo}',
    },
    'public': {
        'file':         '/{repo}/{org}/{cid}/{eid}/{role}/{sha1}',
        'file-role':    '/{repo}/{org}/{cid}/{eid}/{role}',
        'entity':       '/{repo}/{org}/{cid}/{eid}',
        'collection':   '/{repo}/{org}/{cid}',
        'organization': '/{repo}/{org}',
        'repository':   '/{repo}',
    },
}

# Additional file types that may be present in a repo
ADDITIONAL_PATHS = {
    'file': {
        'access': '{id}-a.jpg',
        'json': '{id}.json',
    },
    'file-role': {
    },
    'entity': {
        'changelog': 'changelog',
        'control': 'control',
        'files': 'files',
        'json': 'entity.json',
        'lock': 'lock',
        'mets': 'mets.xml',
    },
    'collection': {
        'annex': '.git/annex',
        'changelog': 'changelog',
        'control': 'control',
        'ead': 'ead.xml',
        'files': 'files',
        'gitignore': '.gitignore',
        'git': '.git',
        'json': 'collection.json',
        'lock': 'lock',
    },
    'organization': {
        'json': 'organization.json',
    },
    'repository': {
        'json': 'repository.json',
    },
}


def identify_object(text, patterns):
    """Split ID, path, or URL into model and tokens and assign to Identifier
    
    Like Django URL router, look for pattern than matches the given text.
    Patterns match to a model and the fields correspond to components of
    a legal object ID.
    Component names and values are assigned as attributes of the object.
    
    @param i: Identifier object
    @param text: str Text string to look for
    @param patterns: list Patterns in which to look
    @returns: dict groupdict resulting from successful regex match
    """
    model = None
    memo = None
    groupdict = None
    for tpl in patterns:
        m = re.match(tpl[0], text)
        if m:
            pattern,memo,model = tpl
            groupdict = m.groupdict()
            break
    ## validate components
    #for key in VALID_COMPONENTS.keys():
    #    val = groupdict.get(key, None)
    #    if val and (val not in VALID_COMPONENTS[key]):
    #        raise Exception('Invalid ID keyword: "%s"' % val)
    return model,memo,groupdict

def identify_filepath(path):
    """Indicates file role or if path is an access file.
    
    TODO use VALID_COMPONENTS or similar rather than hard-coding
    Probably better to do the access file matching separately
    
    @param text: str Text string to look for
    @returns: str File type or None
    """
    ftype = None
    if   '-a.'    in path: ftype = 'access'
    elif 'mezzan' in path: ftype = 'mezzanine'
    elif 'master' in path: ftype = 'master'
    return ftype

def set_idparts(i, groupdict, components=ID_COMPONENTS):
    """Sets keys,values of groupdict as attributes of identifier.
    
    @param i: Identifier
    @param groupdict: dict
    @param components: list [optional]
    """
    i.basepath = groupdict.get('basepath', None)
    if i.basepath:
        i.basepath = os.path.normpath(i.basepath)
    # list of object ID components
    i.parts = OrderedDict([
        (key, groupdict[key])
        for key in components
        if groupdict.get(key)
    ])
    # set object attributes with numbers as ints
    for key,val in i.parts.items():
        if val.isdigit():
            i.parts[key] = int(val)

def format_id(i, model, templates=ID_TEMPLATES):
    """Format ID for the requested model using ID_TEMPLATES.
    
    Hint: you can get parent IDs from an Identifier.
    
    @param i: Identifier
    @param model: str A legal model keyword
    @param templates: [optional] dict of str templates keyed to models
    @returns: str
    """
    return templates[model].format(**i.parts)

def format_path(i, model, path_type, templates=PATH_TEMPLATES):
    """Format absolute or relative path using PATH_TEMPLATES.
    
    @param i: Identifier
    @param model: str A legal model keyword
    @param path_type: str 'abs' or 'rel'
    @param templates: [optional] dict of str templates keyed to models
    @returns: str or None
    """
    if path_type and (path_type == 'abs') and (not i.basepath):
        raise MissingBasepathException('%s basepath not set.'% i)
    key = '-'.join([model, path_type])
    template = templates.get(key, None)
    if template:
        kwargs = {key: val for key,val in i.parts.items()}
        kwargs['basepath'] = i.basepath
        return template.format(**kwargs)
    return None

def format_url(i, model, url_type, templates=URL_TEMPLATES):
    """Format URL using URL_TEMPLATES.
    
    @param i: Identifier
    @param model: str A legal model keyword
    @param url_type: str 'public' or 'editor'
    @param templates: [optional] dict of str templates keyed to models
    @returns: str
    """
    try:
        template = templates[url_type][model]
        return template.format(**i.parts)
    except KeyError:
        return None

def matches_pattern(text, patterns):
    """True if text matches one of patterns
    
    Used for telling what kind of pattern (id, path, url) an arg is.
    
    @param text: str
    @returns: dict of idparts including model
    """
    for tpl in patterns:
        pattern = tpl[0]
        model = tpl[-1]
        m = re.match(pattern, text)
        if m:
            idparts = {k:v for k,v in m.groupdict().iteritems()}
            idparts['model'] = model
            return idparts
    return {}

def _is_id(text):
    """
    @param text: str
    @returns: dict of idparts including model
    """
    return matches_pattern(text, ID_PATTERNS)

def _is_path(text):
    """
    @param text: str
    @returns: dict of idparts including model
    """
    return matches_pattern(text, PATH_PATTERNS)

def _is_url(text):
    """
    @param text: str
    @returns: dict of idparts including model
    """
    return matches_pattern(text, URL_PATTERNS)

def _is_abspath(text):
    if isinstance(text, basestring) and os.path.isabs(text):
        return True
    return False

def _parse_args_kwargs(keys, args, kwargs):
    """Attempts to convert Identifier.__init__ args to kwargs.
    
    @param keys: list Whitelist of accepted kwargs
    @param args: list
    @param kwargs: dict
    """
    # TODO there's probably something in stdlib for this...
    blargs = {key:None for key in keys}
    if args:
        arg = None
        if len(args) >= 2: blargs['base_path'] = args[1]
        if len(args) >= 1: arg = args[0]
        if arg:
            # TODO refactor: lots of regex that's duplicated in identify_object
            if isinstance(arg, dict): blargs['parts'] = arg
            elif _is_id(arg): blargs['id'] = arg
            elif _is_url(arg): blargs['url'] = arg
            elif _is_abspath(arg): blargs['path'] = arg
    # kwargs override args
    if kwargs:
        for key,val in kwargs.items():
            if val and (key in keys):
                blargs[key] = val
    return blargs

def module_for_name(module_name):
    """Returns specified module.
    
    @param module_name: str
    @returns: module
    """
    # load the module, will raise ImportError if module cannot be loaded
    return importlib.import_module(module_name)

def class_for_name(module_name, class_name):
    """Returns specified class from specified module.
    
    @param module_name: str
    @param class_name: str
    @returns: class
    """
    c = getattr(
        module_for_name(module_name),
        class_name
    )
    return c

def _field_names(template):
    """Extract field names from string formatting template.
    """
    return [v[1] for v in string.Formatter().parse(template)]

def first_id(i, model):
    """Returns first child Identifier in series
    
    No guarantee that it's a legal Identifier...
    
    @param i: Identifier
    @param model: str
    @returns: Identifier
    """
    parts = {k:v for k,v in i.parts.iteritems()}
    next_component = _field_names(ID_TEMPLATES[model]).pop()
    parts[next_component] = 1
    parts['model'] = model
    new = Identifier(parts=parts)
    return new

def max_id(model, identifiers):
    """Returns highest existing ID for the specied model
    """
    component = _field_names(ID_TEMPLATES[model]).pop()
    existing = [i.parts[component] for i in identifiers]
    existing.sort()
    return existing[-1] + 1

def available(num_new, model, identifiers, startwith=None):
    """Can {num} {model} IDs to {list} starting with {n}; complain if duplicates
    
    >>> model = 'entity'
    >>> c = Collection('/PATH/TO/ddr-test-123')
    >>> identifiers = [i.id for i in c.family(model=model)]
    >>> add_ids(10, model, identifiers, 42)
    [42, 43, 44, 45, 46, 47, 48, 49, 50, 51]
    
    @param num_new: int
    @param model: str
    @param identifiers: list
    @param startwith: int
    @returns: dict {'success', 'max_id', 'new', 'taken'}
    """
    # Get name of the ID component from the model's ID_TEMPLATE
    # e.g. for Entity we want 'eid'
    # This is the part we will increment
    component = _field_names(ID_TEMPLATES[model]).pop()
    # then get {component} from each Identifier.parts
    existing = [i.parts[component] for i in identifiers]
    existing.sort()
    max_id = existing[-1] + 1
    
    if startwith:
        start = startwith
    else:
        start = max_id + 1
    new = range(start, start + num_new)
    
    taken = [x for x in set(new).intersection(existing)]
    return {
        'max_id': max_id,
        'new': new,
        'taken': taken,
        'success': taken == [],
    }


class MissingBasepathException(Exception):
    pass

class BadPathException(Exception):
    pass

class MalformedIDException(Exception):
    pass

class MalformedPathException(Exception):
    pass

class MalformedURLException(Exception):
    pass

KWARG_KEYS = [
    'id',
    'parts',
    'path',
    'url',
    'base_path',
]

class Identifier(object):
    raw = None
    method = None
    model = None
    parts = OrderedDict()
    basepath = None
    id = None
    
    @staticmethod
    def wellformed(idtype, text, models=MODELS):
        """Checks if text is well-formed ID of specified type and (optionally) model.
        
        @param idtype: str one of ['id', 'path', 'url']
        @param text: str
        @param models: list
        @returns: dict (populated if well-formed)
        """
        idparts = None
        if idtype == 'id': idparts = _is_id(text)
        elif idtype == 'path': idparts = _is_path(text)
        elif idtype == 'url': idparts = _is_url(text)
        if idparts and (idparts['model'] in models):
            return idparts
        return {}

    #@staticmethod
    #def valid(idparts, components=VALID_COMPONENTS):
    #    """Checks if all non-int ID components are valid.
    #    
    #    @param idparts: dict
    #    @param components: dict 
    #    @returns: True or dict containing name of invalid component
    #    """
    #    invalid = [
    #        key for key in components.iterkeys()
    #        if idparts.get(key) and (idparts[key] not in components[key])
    #    ]
    #    if not invalid:
    #        return True
    #    return invalid
    
    def __init__(self, *args, **kwargs):
        """
        NOTE: You will get faster performance with kwargs
        """
        blargs = _parse_args_kwargs(KWARG_KEYS, args, kwargs)
        if blargs['id']: self._from_id(blargs['id'], blargs['base_path'])
        elif blargs['parts']: self._from_idparts(blargs['parts'], blargs['base_path'])
        elif blargs['path']: self._from_path(blargs['path'], blargs['base_path'])
        elif blargs['url']: self._from_url(blargs['url'], blargs['base_path'])

    def _from_id(self, object_id, base_path=None):
        """Make Identifier from object ID.
        
        >>> Identifier(id='ddr-testing-123-456')
        <Identifier ddr-testing-123-456>
        
        @param object_id: str
        @param base_path: str Absolute path to Store's parent dir
        @returns: Identifier
        """
        if base_path and not os.path.isabs(base_path):
            raise BadPathException('Base path is not absolute: %s' % base_path)
        if base_path:
            base_path = os.path.normpath(base_path)
        self.method = 'id'
        self.raw = object_id
        self.id = object_id
        model,memo,groupdict = identify_object(object_id, ID_PATTERNS)
        if not groupdict:
            raise MalformedIDException('Malformed ID: "%s"' % object_id)
        self.model = model
        set_idparts(self, groupdict)
        if base_path and not self.basepath:
            self.basepath = base_path
    
    def _from_idparts(self, idparts, base_path=None):
        """Make Identifier from dict of parts.
        
        >>> parts = {'model':'entity', 'repo':'ddr', 'org':'testing', 'cid':123, 'eid':456}
        >>> Identifier(parts=parts)
        <Identifier ddr-testing-123-456>
        
        @param parts: dict
        @param base_path: str Absolute path to Store's parent dir
        @returns: Identifier
        """
        if base_path and not os.path.isabs(base_path):
            raise BadPathException('Base path is not absolute: %s' % base_path)
        if base_path:
            base_path = os.path.normpath(base_path)
        self.method = 'parts'
        self.raw = idparts
        self.model = idparts['model']
        self.parts = OrderedDict([
            (key, idparts[key])
            for key in ID_COMPONENTS
            if idparts.get(key)
        ])
        self.id = format_id(self, self.model)
        if base_path and not self.basepath:
            self.basepath = base_path
    
    def _from_path(self, path_abs, base_path=None):
        """Make Identifier from absolute path.
        
        >>> path = '/tmp/ddr-testing-123/files/ddr-testing-123-456/entity.json
        >>> Identifier(path=path)
        <Identifier ddr-testing-123-456>
        
        @param path_abs: str
        @param base_path: str Absolute path to Store's parent dir
        @returns: Identifier
        """
        path_abs = os.path.normpath(path_abs)
        if not os.path.isabs(path_abs):
            raise BadPathException('Path is not absolute: %s' % path_abs)
        if base_path:
            base_path = os.path.normpath(base_path)
        self.method = 'path'
        self.raw = path_abs
        model,memo,groupdict = identify_object(path_abs, PATH_PATTERNS)
        if not groupdict:
            raise MalformedPathException('Malformed path: "%s"' % path_abs)
        self.model = model
        set_idparts(self, groupdict)
        self.id = format_id(self, self.model)
    
    def _from_url(self, url, base_path=None):
        """Make Identifier from URL or URI.
        
        >>> Identifier(url='http://ddr.densho.org/ddr/testing/123/456')
        <Identifier ddr-testing-123-456>
        >>> Identifier(url='http://ddr.densho.org/ddr/testing/123/456/')
        <Identifier ddr-testing-123-456>
        >>> Identifier(url='http://192.168.56.101/ui/ddr-testing-123-456')
        <Identifier ddr-testing-123-456>
        >>> Identifier(url='http://192.168.56.101/ui/ddr-testing-123-456/files/')
        <Identifier ddr-testing-123-456>
        
        @param path_abs: str
        @param base_path: str Absolute path to Store's parent dir
        @returns: Identifier
        """
        if base_path and not os.path.isabs(base_path):
            raise BadPathException('Base path is not absolute: %s' % base_path)
        if base_path:
            base_path = os.path.normpath(base_path)
        self.method = 'url'
        self.raw = url
        urlpath = urlparse(url).path  # ignore domain and queries
        urlpath = os.path.normpath(urlpath)
        model,memo,groupdict = identify_object(urlpath, URL_PATTERNS)
        if not groupdict:
            raise MalformedURLException('Malformed URL: "%s"' % url)
        self.model = model
        set_idparts(self, groupdict)
        self.id = format_id(self, self.model)
        if base_path and not self.basepath:
            self.basepath = base_path
    
    def __repr__(self):
        return "<%s.%s %s:%s>" % (self.__module__, self.__class__.__name__, self.model, self.id)
    
    def _key(self):
        """Key for Pythonic object sorting.
        Integer components are returned as ints, enabling natural sorting.
        """
        return self.parts.values()
    
    def __lt__(self, other):
        """Enables Pythonic sorting; see Identifier._key.
        """
        return self._key() < other._key()

    @staticmethod
    def nextable(model):
        NEXTABLE = [
            'collection',
            'entity',
        ]
        if model in NEXTABLE:
            return True
        return False
        
    def next(self):
        """Returns next Identifier if last ID component is numeric
        
        @returns: Identifier
        """
        partsd = {'model': self.model}
        for k,v in self.parts.iteritems():
            partsd[k] = v
        if not isinstance(v, int):
            raise Exception('Not a next-able model: %s' % (self.model))
        # increment the last component of the ID
        partsd[k] = v + 1
        return Identifier(parts=partsd, base_path=self.basepath)
    
    def components(self):
        """Model and parts of the ID as a list.
        """
        parts = [val for val in self.parts.itervalues()]
        parts.insert(0, self.model)
        return parts

    def fields_module(self, mappings=MODEL_REPO_MODELS):
        """Identifier's fields definitions module from repo_models.
        """
        return module_for_name(
            mappings[self.model]['module']
        )
        
    def object_class(self, mappings=MODEL_CLASSES):
        """Identifier's object class according to mappings.
        """
        return class_for_name(
            mappings[self.model]['module'],
            mappings[self.model]['class']
        )
    
    def object(self, mappings=MODEL_CLASSES):
        """The object identified by the Identifier.
        """
        return self.object_class(mappings).from_identifier(self)
    
    def collection_id(self):
        """ID of the collection to which the Identifier belongs, if any.
        """
        if not self.model in COLLECTION_MODELS:
            raise Exception('%s objects do not have collection IDs' % self.model.capitalize())
        return format_id(self, 'collection')
    
    def collection_path(self):
        """Absolute path of the collection to which the Identifier belongs, if any.
        """
        if not self.model in COLLECTION_MODELS:
            raise Exception('%s objects do not have collection paths' % self.model.capitalize())
        if not self.basepath:
            raise MissingBasepathException('%s basepath not set.'% self)
        return os.path.normpath(format_path(self, 'collection', 'abs'))
    
    def collection(self):
        """Collection object to which the Identifier belongs, if any.
        """
        return self.__class__(id=self.collection_id(), base_path=self.basepath)
    
    def parent_id(self, stubs=False):
        """ID of the Identifier's parent, if any.
        
        @param stubs: boolean Whether or not to include Stub objects.
        """
        if stubs:
            parent_model = PARENTS_ALL.get(self.model, None)
        else:
            parent_model = PARENTS.get(self.model, None)
        if not parent_model:
            return None
        return format_id(self, parent_model)
    
    def parent_path(self, stubs=False):
        """Absolute path to parent object
        
        @param stubs: boolean Whether or not to include Stub objects.
        """
        if stubs:
            parent_model = PARENTS_ALL.get(self.model, None)
        else:
            parent_model = PARENTS.get(self.model, None)
        if parent_model:
            path = format_path(self, parent_model, 'abs')
            if path:
                return os.path.normpath(path)
        return None
    
    def parent(self, stubs=False):
        """Parent of the Identifier
        
        @param stub: boolean An archival object not just a Stub
        """
        pid = self.parent_id(stubs)
        if pid:
            return self.__class__(id=pid, base_path=self.basepath)
        return None

    def child_models(self, stubs=False):
        if stubs:
            return CHILDREN_ALL.get(self.model, [])
        return CHILDREN.get(self.model, [])
        
    def child(self, model, idparts, base_path=None):
        """Returns a *new* child Identifier with specified properties.
        
        Does not return an existing child of the Identifier!
        Useful for when you need Identifier info before Object is created.
        
        @param model: str Model of the child object
        @param idparts: dict Additional idpart(s) to add.
        """
        if not model in CHILDREN[self.model]:
            raise Exception('%s can not have child of type %s.' % (self.model, model))
        child_parts = {key:val for key,val in self.parts.iteritems()}
        child_parts['model'] = model
        for key,val in idparts.iteritems():
            if key in ID_COMPONENTS:
                child_parts[key] = val
        return self.__class__(child_parts, base_path=base_path)
    
    def lineage(self, stubs=False):
        """Identifier's lineage, starting with the Identifier itself.
        
        @param stubs: boolean Whether or not to include Stub objects.
        """
        i = self
        identifiers = [i]
        while(i.parent(stubs=stubs)):
            i = i.parent(stubs=stubs)
            identifiers.append(i)
        return identifiers

    def path_abs(self, append=None):
        """Return absolute path to object with optional file appended.
        
        @param append: str File descriptor. Must be present in ADDITIONAL_PATHS!
        @returns: str
        """
        if not self.basepath:
            raise MissingBasepathException('%s basepath not set.'% self)
        path = format_path(self, self.model, 'abs')
        if append:
            filename = ADDITIONAL_PATHS.get(self.model,None).get(append,None)
            if filename and self.model == 'file':
                # For files, bits are appended to file ID using string formatter
                dirname,basename = os.path.split(path)
                filename = filename.format(id=self.id)
                path = os.path.join(dirname, filename)
            elif filename:
                # For everything else you just append the file or dirname
                # to the end of the path
                path = os.path.join(path, filename)
            else:
                return None
        return os.path.normpath(path)
    
    def path_rel(self, append=None):
        """Return relative path to object with optional file appended.
        
        Note: paths relative to repository, intended for use in Git commands.
        
        @param append: str Descriptor of file in ADDITIONAL_PATHS!
        @returns: str
        """
        path = format_path(self, self.model, 'rel')
        if append:
            if self.model == 'file':
                filename = ADDITIONAL_PATHS[self.model][append].format(id=self.id)
                path = os.path.dirname(path)
            else:
                filename = ADDITIONAL_PATHS[self.model][append]
            if path:
                path = os.path.join(path, filename)
            else:
                path = filename
        if path:
            path = os.path.normpath(path)
        return path
    
    def urlpath(self, url_type):
        """Return object URL or URI.
        
        @param url_type: str 'public' or 'editor'
        @returns: str
        """
        return format_url(self, self.model, url_type)
