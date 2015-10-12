VERSION = '0.9.4-beta'

import ConfigParser
from datetime import datetime, timedelta
import json
import logging
logger = logging.getLogger(__name__)
import os
import re

class NoConfigError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

CONFIG_FILES = ['/etc/ddr/ddr.cfg', '/etc/ddr/local.cfg']
config = ConfigParser.ConfigParser()
configs_read = config.read(CONFIG_FILES)
if not configs_read:
    raise NoConfigError('No config file!')

INSTALL_PATH = config.get('cmdln','install_path')
REPO_MODELS_PATH = config.get('cmdln','repo_models_path')
MEDIA_BASE = config.get('cmdln','media_base')
LOG_DIR = config.get('local', 'log_dir')

TIME_FORMAT = config.get('cmdln','time_format')
DATETIME_FORMAT = config.get('cmdln','datetime_format')

ACCESS_FILE_APPEND = config.get('cmdln','access_file_append')
ACCESS_FILE_EXTENSION = config.get('cmdln','access_file_extension')
ACCESS_FILE_GEOMETRY = config.get('cmdln','access_file_geometry')
FACETS_PATH = config.get('cmdln','vocab_facets_path')
MAPPINGS_PATH = config.get('cmdln','vocab_mappings_path')
TEMPLATE_EJSON = config.get('cmdln','template_ejson')
TEMPLATE_EAD = config.get('cmdln','template_ead')
TEMPLATE_METS = config.get('cmdln','template_mets')

CGIT_URL = config.get('workbench','cgit_url')
GIT_REMOTE_NAME = config.get('workbench','remote')
GITOLITE = config.get('workbench','gitolite')
WORKBENCH_LOGIN_TEST = config.get('workbench','login_test_url')
WORKBENCH_LOGIN_URL = config.get('workbench','workbench_login_url')
WORKBENCH_LOGOUT_URL = config.get('workbench','workbench_logout_url')
WORKBENCH_NEWCOL_URL = config.get('workbench','workbench_newcol_url')
WORKBENCH_NEWENT_URL = config.get('workbench','workbench_newent_url')
WORKBENCH_REGISTER_EIDS_URL = config.get('workbench','workbench_register_eids_url')
WORKBENCH_URL = config.get('workbench','workbench_url')
WORKBENCH_USERINFO = config.get('workbench','workbench_userinfo_url')


def format_json(data):
    """Write JSON using consistent formatting and sorting.
    
    For versioning and history to be useful we need data fields to be written
    in a format that is easy to edit by hand and in which values can be compared
    from one commit to the next.  This function prints JSON with nice spacing
    and indentation and with sorted keys, so fields will be in the same relative
    position across commits.
    
    >>> data = {'a':1, 'b':2}
    >>> path = '/tmp/ddrlocal.models.write_json.json'
    >>> write_json(data, path)
    >>> with open(path, 'r') as f:
    ...     print(f.readlines())
    ...
    ['{\n', '    "a": 1,\n', '    "b": 2\n', '}']
    """
    return json.dumps(data, indent=4, separators=(',', ': '), sort_keys=True)

def find_meta_files( basedir, recursive=False, model=None, files_first=False, force_read=False ):
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
        # TODO pass in list of regexes to exclude instead of hard-coding
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

def natural_sort( l ):
    """Sort the given list in the way that humans expect.
    src: http://www.codinghorror.com/blog/2007/12/sorting-for-humans-natural-sort-order.html
    """
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    l.sort( key=alphanum_key )
    return l

def natural_order_string( id ):
    """Convert a collection/entity ID into form that can be sorted naturally.
    
    @param id: A valid format DDR ID
    """
    alnum = re.findall('\d+', id)
    if not alnum:
        raise Exception('Valid DDR ID required.')
    return alnum.pop()


class Timer( object ):
    """
    from DDR import Timer
    t = Timer()
    t.mark('start')
    ...YOUR CODE HERE...
    t.mark('did something')
    ...MORE CODE...
    t.mark('did something else')
    ...MORE CODE...
    t.display()
    """
    steps = []
    
    def mark( self, msg ):
        now = datetime.now()
        index = len(self.steps)
        if index:
            delta = now - self.steps[-1]['datetime']
        else:
            delta = timedelta(0)
        step = {'index':index, 'datetime':now, 'delta':delta, 'msg':msg}
        self.steps.append(step)
        logger.debug(msg)
    
    def display( self ):
        """Return list of steps arranged slowest first.
        """
        from operator import itemgetter
        ordered = sorted(self.steps, key=itemgetter('delta'))
        logger.debug('TIMER RESULTS -- SLOWEST-FASTEST -----------------------------------')
        for step in ordered:
            logger.debug('{:>10}: {:<14} | {}'.format(step['index'], step['delta'], step['msg']))
        return self.steps
