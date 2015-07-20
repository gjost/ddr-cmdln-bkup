# coding: utf-8

from collections import OrderedDict
import os
import re
import string
import urlparse


# Models in this Repository
MODELS = [
    'file',
    'file-role',
    'entity',
    'collection',   # required
    'organization', # required
    'repository',   # required
]

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
    'collection': 'organization',
    'organization': 'repository',
    'repository': None,
}

# Keywords that can legally appear in IDs
ID_COMPONENTS = [
    'repo', 'org', 'cid', 'eid', 'role', 'sha1', 'ext'
]

# ----------------------------------------------------------------------
# Regex patterns used to match IDs, paths, and URLs and extract model and tokens
# Record format: (regex, description, model)
#

ID_PATTERNS = (
    (r'^(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[\w]+)-(?P<sha1>[\w]+)$', '', 'file'),
    (r'^(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[\w]+)$', '', 'file-role'),
    (r'^(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)$', '', 'entity'),
    (r'^(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)$', '', 'collection'),
    (r'^(?P<repo>[\w]+)-(?P<org>[\w]+)$', '', 'organization'),
    (r'^(?P<repo>[\w]+)$', '', 'repository'),
)

# In the current path scheme, collection and entity ID components are repeated.
# Fields can't appear multiple times in regexes so redundant fields have numbers.
PATH_PATTERNS = (
    # file-abs
    (r'(?P<basepath>[\w/]+/ddr/)(?P<repo0>[\w]+)-(?P<org0>[\w]+)-(?P<cid0>[\d]+)/files/(?P<repo1>[\w]+)-(?P<org1>[\w]+)-(?P<cid1>[\d]+)-(?P<eid1>[\d]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[\w]+)-(?P<sha1>[\w\d]+)\.(?P<ext>[\w]+)$', 'file-ext-abs', 'file'),
    (r'(?P<basepath>[\w/]+/ddr/)(?P<repo0>[\w]+)-(?P<org0>[\w]+)-(?P<cid0>[\d]+)/files/(?P<repo1>[\w]+)-(?P<org1>[\w]+)-(?P<cid1>[\d]+)-(?P<eid1>[\d]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[\w]+)-(?P<sha1>[\w\d]+)\.json$', 'file-meta-abs'),
    (r'(?P<basepath>[\w/]+/ddr/)(?P<repo0>[\w]+)-(?P<org0>[\w]+)-(?P<cid0>[\d]+)/files/(?P<repo1>[\w]+)-(?P<org1>[\w]+)-(?P<cid1>[\d]+)-(?P<eid1>[\d]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[\w]+)-(?P<sha1>[\w\d]+)$', 'file-abs', 'file'),
    # file-rel
    (r'^files/(?P<repo0>[\w]+)-(?P<org0>[\w]+)-(?P<cid0>[\d]+)-(?P<eid0>[\d]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[\w]+)-(?P<sha1>[\w\d]+)\.(?P<ext>[\w]+)$', 'file-ext-rel', 'file'),
    (r'^files/(?P<repo0>[\w]+)-(?P<org0>[\w]+)-(?P<cid0>[\d]+)-(?P<eid0>[\d]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[\w]+)-(?P<sha1>[\w\d]+)\.json$', 'file-meta-rel', 'file'),
    (r'^files/(?P<repo0>[\w]+)-(?P<org0>[\w]+)-(?P<cid0>[\d]+)-(?P<eid0>[\d]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[\w]+)-(?P<sha1>[\w\d]+)$', 'file-rel', 'file'),
    # entity
    (r'(?P<basepath>[\w/]+/ddr/)(?P<repo0>[\w]+)-(?P<org0>[\w]+)-(?P<cid0>[\d]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)', 'entity-abs', 'entity'),
    (r'^files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)$', 'entity-rel', 'entity'),
    # collection
    (r'(?P<basepath>[\w/]+/ddr/)(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)', 'collection'),
    (r'^collection.json$', 'collection-meta-rel', 'collection'),
    # organization
    (r'(?P<basepath>[\w/]+/ddr/)(?P<repo>[\w]+)-(?P<org>[\w]+)$', 'organization-abs', 'organization'),
    (r'^organization.json$', 'organization-meta-rel', 'organization'),
    # repository
    (r'(?P<basepath>[\w/]+/ddr/)(?P<repo>[\w]+)/repository.json$', 'repository-meta-abs', 'repository'),
    (r'(?P<basepath>[\w/]+/ddr/)(?P<repo>[\w]+)$', 'repository-meta-abs', 'repository'),
    (r'^repository.json$', 'repository-meta-rel', 'repository'),
)

URL_PATTERNS = (
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
)

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
    'entity-rel':       'files/{repo}-{org}-{cid}-{eid}',
    'file-abs':         '{basepath}/{repo}-{org}-{cid}/files/{repo}-{org}-{cid}-{eid}/files/{repo}-{org}-{cid}-{eid}-{role}-{sha1}',
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
    'entity': {
        'changelog': 'changelog',
        'control': 'control',
        'files': 'files/',
        'json': 'entity.json',
    },
    'collection': {
        'annex': '.git/annex/',
        'control': 'control',
        'gitignore': '.gitignore',
        'git': '.git/',
        'json': 'collection.json',
    },
    'organization': {
        'json': 'organization.json',
    },
    'repository': {
        'json': 'repository.json',
    },
}


def identify_object(i, text, patterns):
    """split ID,path,url into model and tokens and assign to identifier
    
    Like Django URL router, look for pattern than matches the given text.
    Patterns match to a model and the fields correspond to components of
    a legal object ID.
    Component names and values are assigned as attributes of the object.
    
    @param i: Identifier object
    @param text: str Text string to look for
    @param patterns: list Patterns in which to look
    @returns: dict groupdict resulting from successful regex match
    """
    groupdict = {}
    for tpl in patterns:
        pattern = tpl[0]
        model = tpl[-1]
        m = re.match(pattern, text)
        if m:
            i.model = model
            groupdict = m.groupdict()
            break
    if not groupdict:
        raise Exception('Could not identify object: "%s"' % text)
    i.basepath = groupdict.get('basepath', None)
    i.basepath = os.path.normpath(i.basepath)
    # list of object ID components
    i.parts = OrderedDict([
        (key, groupdict[key])
        for key in ID_COMPONENTS
        if groupdict.get(key)
    ])
    # set object attributes with numbers as ints
    for key,val in i.parts.items():
        if val.isdigit():
            i.parts[key] = int(val)

def format_id(i, model):
    """
    @param i: Identifier
    @returns: str
    """
    return ID_TEMPLATES[model].format(**i.parts)

def format_path(i, model, which):
    """
    @param i: Identifier
    @param which: str 'abs' or 'rel'
    @returns: str
    """
    key = '-'.join([model, which])
    kwargs = {key: val for key,val in i.parts.items()}
    kwargs['basepath'] = i.basepath
    try:
        template = PATH_TEMPLATES[key]
        return template.format(**kwargs)
    except KeyError:
        return None

def format_url(i, model, which):
    """
    @param i: Identifier
    @param which: str 'public' or 'editor'
    @returns: str
    """
    try:
        template = URL_TEMPLATES[which][model]
        return template.format(**i.parts)
    except KeyError:
        return None


class Identifier(object):
    raw = None
    method = None
    model = None
    parts = OrderedDict()
    basepath = None
    id = None
    
    def __repr__(self):
        return "<Identifier %s:%s>" % (self.model, self.id)

    def components(self):
        """Model and parts of the ID as a list.
        """
        parts = [val for val in self.parts.itervalues()]
        parts.insert(0, self.model)
        return parts
    
    def collection_id(self):
        if not self.model in COLLECTION_MODELS:
            raise Exception('%s objects do not have collection IDs' % self.model.capitalize())
        return format_id(self, 'collection')
    
    def collection_path(self):
        if not self.model in COLLECTION_MODELS:
            raise Exception('%s objects do not have collection paths' % self.model.capitalize())
        if not self.basepath:
            raise Exception('%s basepath not set.'% self)
        return format_path(self, 'collection', 'abs')
    
    def parent_id(self):
        if not PARENTS.get(self.model, None):
            return None
        return format_id(self, PARENTS[self.model])
    
    def parent_path(self):
        """Absolute path to parent object
        """
        if not PARENTS.get(self.model, None):
            return None
        return format_path(self, PARENTS[self.model], 'abs')
    
    def path_abs(self, append=None):
        """Return absolute path to object with optional file appended.
        
        @param append: str File descriptor. Must be present in ADDITIONAL_PATHS!
        @returns: str
        """
        if not self.basepath:
            raise Exception('%s basepath not set.'% self)
        path = format_path(self, self.model, 'abs')
        if append:
            if self.model == 'file':
                filename = ADDITIONAL_PATHS[self.model][append].format(id=self.id)
            else:
                filename = ADDITIONAL_PATHS[self.model][append]
            path = os.path.join(path, filename)
        return path
    
    def path_rel(self, append=None):
        """Return relative path to object with optional file appended.
        
        Note: paths relative to repository, intended for use in Git commands.
        
        @param append: str File descriptor. Must be present in ADDITIONAL_PATHS!
        @returns: str
        """
        path = format_path(self, self.model, 'rel')
        if append:
            if self.model == 'file':
                filename = ADDITIONAL_PATHS[self.model][append].format(id=self.id)
            else:
                filename = ADDITIONAL_PATHS[self.model][append]
            if path:
                path = os.path.join(path, filename)
            else:
                path = filename
        return path
    
    def urlpath(self, which):
        """Return object URL or URI.
        """
        return format_url(self, self.model, which)
    
    @staticmethod
    def from_id(object_id, base_path=None):
        """Return Identified given object ID
        
        >>> Identifier.from_id('ddr-testing-123-456')
        <Identifier ddr-testing-123-456>
        
        @param object_id: str
        """
        if base_path and not os.path.isabs(base_path):
            raise Exception('Base path is not absolute: %s' % base_path)
        i = Identifier()
        i.method = 'id'
        i.raw = object_id
        i.id = object_id
        identify_object(i, object_id, ID_PATTERNS)
        if base_path and not i.basepath:
            i.basepath = base_path
        return i
    
    @staticmethod
    def from_idparts(partsdict, base_path=None):
        """Return Identified given dict of parts
        
        >>> parts = {'model':'entity', 'repo':'ddr', 'org':'testing', 'cid':123, 'eid':456}
        >>> Identifier.from_parts(parts)
        <Identifier ddr-testing-123-456>
        
        @param parts: dict
        """
        if base_path and not os.path.isabs(base_path):
            raise Exception('Base path is not absolute: %s' % base_path)
        i = Identifier()
        i.method = 'parts'
        i.raw = partsdict
        i.model = partsdict['model']
        i.parts = OrderedDict([
            (key, val)
            for key,val in partsdict.iteritems()
            if (key in ID_COMPONENTS) and val
        ])
        i.id = format_id(i, i.model)
        if base_path and not i.basepath:
            i.basepath = base_path
        return i
    
    @staticmethod
    def from_path(path_abs):
        """Return Identified given absolute path.
        
        >>> Identifier.from_id('ddr-testing-123-456')
        <Identifier ddr-testing-123-456>
        
        @param path_abs: str
        """
        if not os.path.isabs(path_abs):
            raise Exception('Path is not absolute: %s' % path_abs)
        i = Identifier()
        i.method = 'path'
        i.raw = path_abs
        identify_object(i, path_abs, PATH_PATTERNS)
        i.id = format_id(i, i.model)
        return i
    
    @staticmethod
    def from_url(url, base_path=None):
        """Return Identified given URL or URI.
        
        >>> Identifier.from_id('http://ddr.densho.org/ddr/testing/123/456')
        <Identifier ddr-testing-123-456>
        >>> Identifier.from_id('http://ddr.densho.org/ddr/testing/123/456/')
        <Identifier ddr-testing-123-456>
        >>> Identifier.from_id('http://192.168.56.101/ui/ddr-testing-123-456')
        <Identifier ddr-testing-123-456>
        >>> Identifier.from_id('http://192.168.56.101/ui/ddr-testing-123-456/files/')
        <Identifier ddr-testing-123-456>
        
        @param path_abs: str
        """
        if base_path and not os.path.isabs(base_path):
            raise Exception('Base path is not absolute: %s' % base_path)
        i = Identifier()
        i.method = 'url'
        i.raw = url
        path = urlparse.urlparse(url).path
        identify_object(i, path, URL_PATTERNS)
        i.id = format_id(i, i.model)
        if base_path and not i.basepath:
            i.basepath = base_path
        return i
