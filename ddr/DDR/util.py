import hashlib
import os
import re


def find_meta_files( basedir, recursive=False, model=None, files_first=False, force_read=False, testing=False ):
    """Lists absolute paths to .json files in basedir; saves copy if requested.
    
    Skips/excludes .git directories.
    TODO depth (go down N levels from basedir)
    
    @param basedir: Absolute path
    @param recursive: Whether or not to recurse into subdirectories.
    @param model: list Restrict to the named model ('collection','entity','file').
    @param files_first: If True, list files,entities,collections; otherwise sort.
    @param force_read: If True, always searches for files instead of using cache.
    @param testing: boolean Allow 'tmp' in paths.
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
        excludes = ['.git', '*~']
        if not testing:
            excludes.append('tmp')
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
