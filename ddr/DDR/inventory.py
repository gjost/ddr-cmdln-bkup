"""
# Create an Organization
git_name = 'gjost'; git_mail = 'gjost@densho.org'
from DDR.inventory import Organization, Store
o = Organization.create(path='/tmp/repo/ddr-testing', id='ddr-testing', repo='ddr', org='testing')
o.save()
o.commit(git_name, git_mail, 'Set up organization: %s' % o.id)

# Load an existing Organization
from DDR.inventory import Organization, Store
o = Organization.load('/tmp/repo/ddr-testing')

# Add a new Store
git_name = 'gjost'; git_mail = 'gjost@densho.org'
import datetime
from DDR.inventory import Organization, Store
o = Organization.load('/tmp/repo/ddr-testing')
today = datetime.date.today().strftime('%Y-%m-%d')
s = Store(repo=o.repo, org=o.org,
          label='WHATEVER', location='HMWF',
          purchase_date=today)
o.stores.append(s)
o.save()
o.commit(git_name, git_mail, 'Added store: %s' % s.label)

# Add another Store
s = Store(repo=o.repo, org=o.org,
          label='BLAHBLAH', location='JANM',
          purchase_date=today)
o.stores.append(s)
o.save()
o.commit(git_name, git_mail, 'Added a store: %s' % s.label)

# Update a Store
git_name = 'gjost'; git_mail = 'gjost@densho.org'
from DDR.inventory import Organization, Store
o = Organization.load('/tmp/repo/ddr-testing')
s = o.store('WHATEVER')
s.location = 'Densho HQ'
o.save()
o.commit(git_name, git_mail, 'Updated store: %s' % s.label)

# Remove a Store
git_name = 'gjost'; git_mail = 'gjost@densho.org'
from DDR.inventory import Organization, Store
o = Organization.load('/tmp/repo/ddr-testing')
s = o.store('BLAHBLAH')
o.remove_store(s)
o.save()
o.commit(git_name, git_mail, 'Removed store: %s' % s.label)

# Add a collection
git_name = 'gjost'; git_mail = 'gjost@densho.org'
from DDR.inventory import Organization, Store
o = Organization.load('/tmp/repo/ddr-testing')
s = o.store('WHATEVER')
c = {'uuid':'2ca8e0aa-1cc1-11e3-8867-3fd4c84eb655', 'cid':'ddr-testing-123', 'level':'full'}
s.collections.append(c)
o.save()
o.commit(git_name, git_mail, 'Added collection %s %s' % (s.label, c['cid']))

# Add more collections
git_name = 'gjost'; git_mail = 'gjost@densho.org'
from DDR.inventory import Organization, Store
o = Organization.load('/tmp/repo/ddr-testing')
s = o.store('WHATEVER')
s.collections.append({'uuid':'a8e0aa2c-c1c1-e311-6788-d4c84eb6553f', 'cid':'ddr-testing-124', 'level':'full'})
s.collections.append({'uuid':'c8e0aaa2-1c1c-1e31-8678-fd4c84eb6553', 'cid':'ddr-testing-125', 'level':'full'})
s.collections.append({'uuid':'8e0aaa2c-cc11-1e31-8678-fd4c84eb6553', 'cid':'ddr-testing-126', 'level':'full'})
o.save()
o.commit(git_name, git_mail, 'Added multiple collections')

# Update a collection
git_name = 'gjost'; git_mail = 'gjost@densho.org'
from DDR.inventory import Organization, Store
o = Organization.load('/tmp/repo/ddr-testing')
s = o.store('WHATEVER')
c = s.collection(uuid='c8e0aaa2-1c1c-1e31-8678-fd4c84eb6553')
c['level'] = 'metadata'
o.save()
o.commit(git_name, git_mail, 'Updated collection %s %s' % (s.label, c['cid']))

# Remove a collection
git_name = 'gjost'; git_mail = 'gjost@densho.org'
from DDR.inventory import Organization, Store
o = Organization.load('/tmp/repo/ddr-testing')
s = o.store('WHATEVER')
c = s.collection(uuid='8e0aaa2c-cc11-1e31-8678-fd4c84eb6553')
s.collections.remove(c)
o.save()
o.commit(git_name, git_mail, 'Removed collection %s %s' % (s.label, c['cid']))

# Sync
from DDR.inventory import Organization, Store
o = Organization.load('/tmp/repo/ddr-testing')
o.sync()
"""

import ConfigParser
import json
import logging
logger = logging.getLogger(__name__)
import os
import re

import envoy
import git

from DDR import dvcs, storage


DRIVE_FILE_FIELDS = 'id,level'

LEVELS = ['meta', 'access', 'all']



def _write_json(data, path):
    """Write JSON using consistent formatting and sorting.
    
    For versioning and history to be useful we need data fields to be written
    in a format that is easy to edit by hand and in which values can be compared
    from one commit to the next.  This function prints JSON with nice spacing
    and indentation and with sorted keys, so fields will be in the same relative
    position across commits.
    
    >>> data = {'a':1, 'b':2}
    >>> path = '/tmp/ddrlocal.models.write_json.json'
    >>> _write_json(data, path)
    >>> with open(path, 'r') as f:
    ...     print(f.readlines())
    ...
    ['{\n', '    "a": 1,\n', '    "b": 2\n', '}']
    """
    json_pretty = json.dumps(data, indent=4, separators=(',', ': '), sort_keys=True)
    with open(path, 'w') as f:
        f.write(json_pretty)

def guess_collection_level(cpath):
    """Try to guess a collection's level by looking at git-annex-find
    
    If git-annex-find lists no files it's probably a metadata-only repo.
    If there are only files ending with the access suffix, probably access.
    If mixture of access and others, probably master.
    """
    annex_files = dvcs.annex_find(cpath)
    if len(annex_files) == 0:
        return 'metadata'
    # tally up the access and master copies
    access = 0
    master = 0
    for f in annex_files:
        # access files end in '-a'
        if os.path.splitext(f)[0][-2:] == '-a':
            access = access + 1
        else:
            master = master + 1
    if access and not master:
        return 'access'
    elif access and master:
        return 'master'
    return None



class Repository( object ):
    id = None
    keyword = None
    title = None
    description = None
    organizations = {}
    
    def __init__( self, path=None ):
        if path:
            self.read(path)
    
    def read( self, path ):
        with open(path, 'r') as f:
            data = json.loads(f.read())
        self.id = data['id']
        self.keyword = data['keyword']
        self.title = data['title']
        self.description = data['description']
    
    def json( self ):
        return {'id': self.id,
                'keyword': self.keyword,
                'title': self.title,
                'description': self.description,}
        
    def write( self, path ):
        _write_json(self.json(), path)



ORGANIZATION_FIELDS = ['id', 'repo', 'org',]

class Organization( object ):
    path = None
    id = None
    keyword = None
    stores = []
    filename = 'organization.json'
    
    def __init__(self, **kwargs):
        self.path = kwargs.get('path', None)
        for k in kwargs.keys():
            if k in ORGANIZATION_FIELDS:
                self.__setattr__(k, kwargs[k])
        if self.path:
            self.stores = self._stores()
    
    def json( self ):
        data = {}
        for f in ORGANIZATION_FIELDS:
            data[f] = getattr(self, f)
        return data
    
    @staticmethod
    def create(path, id, org, repo):
        if os.path.exists(path):
            raise Exception
        o = Organization(path=path, id=id, org=org, repo=repo)
        os.mkdir(o.path)
        # initialize Git repo
        os.chdir(o.path)
        repo = git.Repo.init(o.path)
        commit = repo.index.commit('initial commit')
        return o
    
    @staticmethod
    def load(path):
        o = Organization(path=path)
        opath = os.path.join(path, o.filename)
        with open(opath, 'r') as f:
            data = json.loads(f.read())
        for k in data.keys():
            if k in ORGANIZATION_FIELDS:
                o.__setattr__(k, data[k])
        return o
    
    def commit( self, git_name, git_mail, message ):
        repo = dvcs.repository(self.path)
        repo.git.add(self.filename)
        for store in self.stores:
            spath = os.path.join(self.path, store.filename())
            repo.git.add(spath)
        repo.git.commit('--author=%s <%s>' % (git_name, git_mail), '-m', message)
    
    def save( self ):
        opath = os.path.join(self.path, self.filename)
        _write_json(self.json(), opath)
        for store in self.stores:
            spath = os.path.join(self.path, store.filename())
            store.save(spath)
    
    def _store_files( self ):
        """Gets list of paths to store files in the repo.
        """
        if self.path and os.path.exists(self.path):
            excludes = ['.git', 'organization.json']
            pattern = re.compile('.json$')
            return [f for f in os.listdir(self.path) if (f not in excludes) and pattern.search(f)]
        return []
    
    def _stores( self ):
        self.stores = []
        for f in self._store_files():
            spath = os.path.join(self.path, f)
            s = Store.load(spath)
            self.stores.append(s)
        return self.stores
    
    def store( self, label ):
        for s in self.stores:
            if s.label == label:
                return s
        return None
    
    def remove_store( self, store ):
        """NOTE: Does not do the commit!"""
        repo = dvcs.repository(self.path)
        spath = os.path.join(self.path, store.filename())
        repo.git.rm(spath)
        self.stores.remove(store)
    
    def collection( self, cid ):
        """Lists the stores that contain collection and level
        """
        instances = []
        for store in self.stores:
            for c in store.collections:
                if c['id'] == cid:
                    c['label'] = store.label
                    instances.append(c)
        return instances
    
    def collections( self ):
        """Builds a data structure of all the repo remotes keyed to their UUIDs
        
        This function loads each of the store records for the organization.
        For each collection record it adds the location field and store label
        from the store record.  This is suitable for loading into a search engine.
        
        >> from DDR.inventory import Organization
        >> org = Organization('/var/www/media/base/ddr-testing')
        >> collections = org.collections()
        >> for c in collections:
        >>     print(c)
        {'uuid':'43935...', 'id':'ddr-testing-141', 'label':'HMWF1TB2013', 'location':'Heart Mountain, WY'},
        {'uuid':'64393...', 'id':'ddr-testing-141', 'label':'pnr_tmp-ddr', 'location':'Pasadena, CA'},
        {'uuid':'36493...', 'id':'ddr-testing-141', 'label':'WD5000BMV-2', 'location':'Pasadena, CA'},
        {'uuid':'35ea6...', 'id':'ddr-testing-141', 'label':'mits.densho.org', 'location':'Seattle, WA'},
        ...
        
        @returns list of dicts.
        """
        repos = []
        for s in self.stores:
            store = self.store(s)
            for c in store.collections:
                c['store'] = store.label
                c['location'] = store.location
                repos.append(c)
        return repos
    
    def collections_dict( self, fieldname ):
        """Similar to Organization.collections except returns collections in dict.
        
        >> from DDR.inventory import Organization
        >> org = Organization('/var/www/media/base/ddr-testing')
        >> collections = org.collections(key='uuid')
        >> for c in collections:
        >>     print(c)
        {'uuid':'43935...', 'id':'ddr-testing-141', 'label':'HMWF1TB2013', 'location':'Heart Mountain, WY'},
        {'uuid':'64393...', 'id':'ddr-testing-141', 'label':'pnr_tmp-ddr', 'location':'Pasadena, CA'},
        {'uuid':'36493...', 'id':'ddr-testing-141', 'label':'WD5000BMV-2', 'location':'Pasadena, CA'},
        {'uuid':'35ea6...', 'id':'ddr-testing-141', 'label':'mits.densho.org', 'location':'Seattle, WA'},
        ...
        
        @param fieldname: Name of field to use as dictionary key.
        @returns dict.
        """
        repos = {}
        for s in self.stores:
            store = self.store(s)
            for c in store.collections:
                c['store'] = store.label
                c['location'] = store.location
                if c.get(fieldname, None):
                    key = c.pop(fieldname)
                    repos[key] = c
        return repos
    
    @staticmethod
    def analyze_collections( path ):
        label = storage.drive_label(path)
        
        def looks_like_a_collection(path):
            git_dir = os.path.join(path, '.git')
            cjson = os.path.join(path, 'collection.json')
            if os.path.exists(git_dir) and os.path.exists(cjson):
                return True
            return False
        def get_cid(cpath):
            cjson = os.path.join(cpath, 'collection.json')
            with open(cjson, 'r') as f:
                data = json.loads(f.read())
            for field in data:
                cid = field.get('id', None)
                if cid:
                    return cid
            return None
        def get_uuid(cpath):
            repo = dvcs.repository(cpath)
            if repo:
                return repo.git.config('annex.uuid')
            return None
        
        # collections:
        dirs = os.listdir(path)
        dirs.sort()
        for d in dirs:
            cpath = os.path.join(path, d)
            print(cpath)
            if looks_like_a_collection(cpath):
                cid = get_cid(cpath)
                uuid = get_uuid(cpath)
                level = guess_collection_level(cpath)
                print('    %s %s %s' % (uuid, cid, level))
        pass


STORE_FIELDS = ['repo', 'org', 'label', 'location', 'purchase_date', 'collections',]

class Store( object ):
    path = None
    repo = None
    org = None
    label = None
    location = None
    purchase_date = None
    collections = []
    
    def __init__(self, **kwargs):
        self.path = kwargs.get('path', None)
        for k in kwargs.keys():
            if k in STORE_FIELDS:
                self.__setattr__(k, kwargs[k])
    
    def json( self ):
        data = {}
        for f in STORE_FIELDS:
            data[f] = getattr(self, str(f))
        return data
    
    @staticmethod
    def load(path):
        """
        @param path: Path including basename
        """
        s = Store(path=path)
        with open(path, 'r') as f:
            data = json.loads(f.read())
        for k in data.keys():
            if k in STORE_FIELDS:
                s.__setattr__(k, data[k])
        return s
    
    def save( self, path ):
        _write_json(self.json(), path)
    
    def filename( self ):
        return '%s.json' % self.label
    
    def collection( self, uuid=None, cid=None ):
        if uuid or cid:
            for c in self.collections:
                if uuid and (c['uuid'] == uuid):
                    return c
                elif cid and (c['cid'] == cid):
                    return c
        return None



def file_instances(collections_dict, annex_whereis_file):
    """Adds location field to file instance metadata.
    
    Takes location from each collection in the Organization's Store records and adds it to file instance records from git-annex.

    >> from DDR import dvcs, inventory
    >> repo = dvcs.repository('/tmp/ddr/ddr-testing-141')
    >> org = inventory.Organization('/var/www/media/base/ddr-testing')
    >> collections_dict = org.collections_dict('uuid')
    >> path_rel = 'files/ddr-testing-141-1/files/ddr-testing-141-1-master-96c048001e.pdf'
    >> instances = dvcs.annex_whereis_file(repo, path_rel)
    >> instances = inventory.file_locations(collections_dict, repo, path)
    >> for i in instances:
    >>     print(i)
    {'location': u'Pasadena', 'uuid': '643935ea-1cbe-11e3-afb5-3fb5a8f2a937', 'label': 'WD5000BMV-2'}
    {'location': u'Pasadena', 'uuid': 'a311a84a-4e48-11e3-ba9f-2fc2ce00326e', 'label': 'pnr_tmp-ddr'}
    
    @param collections_dict
    @param annex_whereis_file: Output of dvcs.annex_whereis_file
    """
    for i in annex_whereis_file:
        c = collections_dict[i['uuid']]
        i['location'] = c['location']
    return annex_whereis_file

def files_instances(collections_dict, repo, annex_whereis):
    """Adds location field to file instance metadata for specified repository.
    
    Takes location from each collection in the Organization's Store records and adds it to file instance records from git-annex.

from DDR import dvcs, inventory
repo = dvcs.repository('/tmp/ddr/ddr-testing-141')
org = inventory.Organization('/var/www/media/base/ddr-testing')
collections_dict = org.collections_dict('uuid')
instances = dvcs.annex_whereis(repo)
instances = inventory.files_instances(collections_dict, repo, instances)
for i in instances:
    print(i)

    {'location': u'Pasadena', 'uuid': '643935ea-1cbe-11e3-afb5-3fb5a8f2a937', 'label': 'WD5000BMV-2'}
    {'location': u'Pasadena', 'uuid': 'a311a84a-4e48-11e3-ba9f-2fc2ce00326e', 'label': 'pnr_tmp-ddr'}
    
    @param collections_dict
    @param annex_whereis_file: Output of dvcs.annex_whereis_file
    """
    for f in annex_whereis:
        for r in f['remotes']:
            rem = collections_dict.get(r['uuid'], None)
            if rem:
                r['location'] = rem['location']
    return annex_whereis



def group_files( path ):
    """Gets list of paths to group files in the repo.
    
    >>> from DDR import inventory
    >>> p = '/var/www/media/base/ddr-testing'
    >>> inventory.group_files(p)
    ['/var/www/media/base/ddr-testing/TS11TB2013.json', '/var/www/media/base/ddr-testing/WD5000BMV-2.json']
    
    @param path: Abs path to org repo
    """
    excludes = ['.git', 'organization.json']
    pattern = re.compile('.json$')
    return [f for f in os.listdir(path) if (f not in excludes) and pattern.search(f)]

def groups( path ):
    """Gets list of groups for which there are CSV files.
    
    >>> from DDR import inventory
    >>> p = '/var/www/media/base/ddr-testing'
    >>> inventory.groups(p)
    ['TS11TB2013', 'WD5000BMV-2']
    
    @param path: Abs path to org repo
    @returns drives: List of group labels
    """
    return [os.path.splitext(f)[0] for f in group_files(path)]
 
def group_file_path( path ):
    """Gets path to JSON file for the specified group based on orgrepo's location.
    
    DANGER! This function makes assumptions about file paths!
    This is a holdover from when group files were called "drive files"
    and when the group label was always assumed to match a drive label.
    The label is assumed to be the block of \w following '/media'.
    
    >>> from DDR import inventory
    >>> r = '/media/DRIVELABEL/ddr/REPOORGID'
    >>> inventory.group_file_path(r)
    '/media/DRIVELABEL/ddr/REPOORG/DRIVELABEL.json'
    
    @param path: Abs path to org repo (drive label extracted from this)
    """
    path = os.path.realpath(path)
    parts = path.split(os.sep)
    drivelabel = parts[2]
    repo,org,id = parts[4].split('-')
    repoorg = '-'.join([repo,org])
    jfile = '%s.json' % drivelabel
    return '/%s' % os.path.join(parts[1], drivelabel, parts[3], repoorg, jfile)

def read_group_file( path ):
    """Reads group file, returns list of repos and their levels
    
    Group file is a JSON file containing a list of DDR collection repo IDs and
    and indicator of which binaries should be present (see LEVELS).
    
    >>> from DDR import inventory
    >>> p = '/var/www/media/base/ddr-testing/WD5000BMV-2.json'
    >>> inventory.read_group_file(p)
    [{'id': 'ddr-testing-100', 'level': 'full'}, {'id': 'ddr-testing-101', 'level': 'access'}, ...]
    
    @param path: Absolute path to group file.
    @returns: List of dicts (id, level)
    """
    with open(path, 'rb') as f:
        return json.loads(f.read())

def write_group_file( repos, path ):
    """
    @param repos: List of dicts (id, level)
    @param path: (optional) Absolute path to group file.
    """
    data = {'repositories':repos}
    _write_json(data, path)

def group_repo_level( path, repo_basename ):
    """Get level for the specified repo from group file.
    
    @param path: Absolute path to group file.
    @param repo_basename: Collection repo directory.
    @return level
    """
    level = 'unknown'
    with open(path,'r') as f:
        for line in f.readlines():
            if repo_basename in line:
                level = line.split(',')[1].strip()
    return level

def repo_level( repo_path, level=None ):
    """Gets or sets level for specified repo.
    
    @param path: Absolute path to repo.
    @param level: If present, sets ddr.level to value.
    @returns level
    """
    logging.debug('repo_level(%s, %s)' % (repo_path,level))
    repo = git.Repo(repo_path)
    if level:
        logging.debug('level -> %s' % level)
        repo.git.config('--local', 'ddr.level', level)
    try:
        level = repo.git.config('--get', 'ddr.level')
    except:
        pass
    return level

def read_mrconfig( path ):
    """Reads .mrconfig file
    
    @param path: Absolute path to .mrconfig file.
    @returns: ConfigParser object
    """
    config = ConfigParser.ConfigParser()
    config.readfp(open(path))
    return config

def make_mrconfig( defaults, repos, server, base_path='' ):
    """Makes an .mrconfig file.
    
    import inventory
    p = '/media/WD5000BMV-2/ddr/ddr-testing/WD5000BMV-2.csv'
    repos = inventory.read_drive_file(p)
    defaults = {'ddrstatus': 'ddr status "$@"', 'ddrsync': 'ddr sync "$@"'}
    base_path = '/media/WD5000BMV-2/ddr'
    server = 'git@mits.densho.org'
    mrconfig = inventory.mrconfig(defaults, base_path, server, repos)
    inventory.write_mrconfig(mrconfig, '/tmp/mrconfig')
 
    @param defaults: dict of settings.
    @param repos: List of dicts (id, level)
    @param server: USERNAME@DOMAIN for Gitolite server.
    @param base_path: Absolute path to the directory in which the repos are located.
    @returns mrconfig: A ConfigParser object
    """
    mrconfig = ConfigParser.ConfigParser(defaults)
    for r in repos:
        section = os.path.join(base_path, r['id'])
        mrconfig.add_section(section)
        mrconfig.set(section, 'checkout', "git clone '%s:%s.git' '%s'" % (server, r['id'], r['id']))
    return mrconfig

def write_mrconfig( mrconfig, path ):
    """Writes an .mrconfig file to the specified path.
    
    @param mrconfig: A ConfigParser object
    @param path: Absolute path to write.
    """
    with open(path, 'wb') as f:
        mrconfig.write(f)

def repo_annex_get(repo_path, level):
    """Runs annex-get commands appropriate to this repo's level.
    
    metadata: does nothing
    access: git-annex-gets files ending with ACCESS_SUFFIX
    all: git annex get .
    """
    logger.debug('repo_annex_get(%s)' % repo_path)
    ACCESS_SUFFIX = '-a.jpg'
    #level = repo_level(repo_path)
    logger.debug('level: %s' % level)
    repo = git.Repo(repo_path)
    if level == 'access':
        r = envoy.run('find . -name "*%s" -print' % ACCESS_SUFFIX)
        for accessfile in r.std_out.strip().split('\n'):
            logger.debug('git annex get %s' % accessfile)
            repo.git.annex('get', accessfile)
    elif level == 'all':
        logger.debug('git annex get .')
        repo.git.annex('get', '.')
    logger.debug('DONE')

def load_organization_data(path):
    """Loads inventory data into single data structure.
    """
    orgfile = os.path.join(path, 'organization.json')
    with open(orgfile, 'rb') as f:
        org = json.loads(f.read())
    org['drives'] = {}
    for f in group_files(path):
        fn = os.path.join(path, f)
        data = read_group_file(fn)
        label = data['drive info']['label']
        try:
            org['drives'][label] = data
        except:
            org['drives'][f] = {}
    return org

"""
UUID	Label	Location	Level	Trust
faf5b548-4285-11e3-877e-33872002bf67	WD5000BMV-2	Pasadena, here	master	semitrusted
2c5e9652-4283-11e3-ba24-6f28c7ec0c50	workbench	Seattle, mits.densho.org	metadata	semitrusted
affb5584-2485-1e13-87e7-33827020b6f7	TS1TB201301	Seattle, Densho HQ	master	semitrusted
62a9c710-4718-11e3-ac94-87227a8b2c2c	pub	Seattle, Densho Colo	access	

from DDR import dvcs, inventory
repo = dvcs.repository('/var/www/media/base/ddr-testing-196')
stat = dvcs.annex_status(repo)
path = '/var/www/media/base/ddr-testing'
inventory.repo_inventory_remotes(repo, stat, path)
"""
