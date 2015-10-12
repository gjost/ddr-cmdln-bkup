VERSION = '0.9.4-beta'

from datetime import datetime, timedelta
import json
import logging
logger = logging.getLogger(__name__)
import os
import re


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
