import ConfigParser
import json
import logging
logger = logging.getLogger(__name__)
import os
import re

import envoy
import git

from DDR import dvcs


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


class Organization( object ):
    path = None
    id = None
    keyword = None
    title = None
    description = None
    stores = []
    
    def __init__( self, path=None ):
        if path:
            self.path = path
            self.read(os.path.join(path, 'organization.json'))
            self.stores = self._stores()
    
    def json( self ):
        return {'id': self.id,
                'keyword': self.keyword,
                'title': self.title,
                'description': self.description,}
    
    def read( self, path ):
        with open(path, 'r') as f:
            data = json.loads(f.read())
        self.id = data['id']
        self.keyword = data['keyword']
        self.title = data['title']
        self.description = data['description']
    
    def write( self, path ):
        _write_json(self.json(), path)
    
    def store_files( self ):
        """Gets list of paths to store files in the repo.
        """
        excludes = ['.git', 'organization.json']
        pattern = re.compile('.json$')
        return [f for f in os.listdir(self.path) if (f not in excludes) and pattern.search(f)]
    
    def _stores( self ):
        return [os.path.splitext(f)[0] for f in self.store_files()]
    
    def store( self, label ):
        filename = '%s.json' % label
        path = os.path.join(self.path, filename)
        store = Store(path)
        return store
    
    def collection( self, cid ):
        """Lists the stores that contain collection and level
        """
        instances = []
        for label in self.store_files():
            store = Store(os.path.join(self.path, label))
            for c in store.collections:
                if c['id'] == cid:
                    c['store'] = sf
                    instances.append(c)
        return instances


class Store( object ):
    path = None
    label = None
    org = None
    repo = None
    location = None
    purchase_date = None
    collections = {}
    
    def __init__( self, path=None ):
        if path:
            self.path = path
            self.read(path)
    
    def read( self, path ):
        with open(path, 'r') as f:
            data = json.loads(f.read())
        self.label = data['label']
        self.org = data['org']
        self.repo = data['repo']
        self.location = data['location']
        self.purchase_date = data['purchase_date']
        self.collections = data['collections']
    
    def json( self ):
        return {'label': self.label,
                'org': self.org,
                'repo': self.repo,
                'location': self.location,
                'purchase_date': self.purchase_date,
        }
    
    def write( self, path ):
        _write_json(self.json(), path)







def repos_by_uuid(organization, collection=None):
    """Builds a data structure of all the repo remotes keyed to their UUIDs
    
{
  '43935ea6-cbe1-1e31-fba5-fb5a8f2a9337': {'id':'ddr-testing-141', 'label':'HMWF1TB2013', 'location':'Heart Mountain, WY'},
  '643935ea-1cbe-11e3-afb5-3fb5a8f2a973': {'id':'ddr-testing-141', 'label':'pnr_tmp-ddr', 'location':'Pasadena, CA'},
  '364935ea-1cbe-11e3-afb5-38f2a937fb5a': {'id':'ddr-testing-141', 'label':'WD5000BMV-2', 'location':'Pasadena, CA'},
  '35ea6439-1cbe-11e3-afb5-3fb592a37a8f': {'id':'ddr-testing-141', 'label':'mits.densho.org', 'location':'Seattle, WA'}
}


from DDR import dvcs, organization
org = organization.Organization('/var/www/media/base/ddr-testing')
uuid_repos = organization.repos_by_uuid(org)

r = dvcs.repository('/tmp/ddr/ddr-testing-141')
file_remotes = dvcs.annex_whereis(r)
for f in file_remotes:
   for fr in f['remotes']:
       print(fr)
       uuid = fr.get('uuid',None)
       print(uuid)
       remote = uuid_repos.get(uuid,None)
       print(remote)
       if remote and (remote.get('location',None)):
           fr['location'] = remote['location']

for f in file_remotes:
   for fr in f['remotes']:
       print(fr)


    """
    repos = {}
    for s in organization.stores:
        store = organization.store(s)
        for c in store.collections:
            uuid = c.get('uuid',None)
            if uuid:
                c['location'] = store.location
                repos[uuid] = c
    return repos



def file_locations(repo, file_path_rel, organization):
    """
>>> dvcs.annex_whereis_file(r, 'files/ddr-testing-141-1/files/ddr-testing-141-1-master-96c048001e.pdf')
[{'uuid': '643935ea-1cbe-11e3-afb5-3fb5a8f2a937', 'label': 'WD5000BMV-2'}, {'uuid': 'a311a84a-4e48-11e3-ba9f-2fc2ce00326e', 'label': 'pn
r_tmp-ddr'}]

from DDR import dvcs, organization
repo = dvcs.repository('/tmp/ddr/ddr-testing-141')
org = organization.Organization('/var/www/media/base/ddr-testing')
path = 'files/ddr-testing-141-1/files/ddr-testing-141-1-master-96c048001e.pdf'
stores = organization.file_locations(repo, path, org)
for s in stores:
    print(s.location)

[{'uuid': '643935ea-1cbe-11e3-afb5-3fb5a8f2a937', 'label': 'WD5000BMV-2'}, {'uuid': 'a311a84a-4e48-11e3-ba9f-2fc2ce00326e', 'label': 'pn
r_tmp-ddr'}]
['HMWF1TB2013', 'pnr_tmp-ddr', 'WD5000BMV-2']

    """
    stores = []
    instances = dvcs.annex_whereis_file(repo, file_path_rel)
    for i in instances:
        if i.get('label',None):
            store = organization.store(i['label'])
            stores.append(store)
    return stores








def group_files( path ):
    """Gets list of paths to group files in the repo.
    
    >>> from DDR import organization
    >>> p = '/var/www/media/base/ddr-testing'
    >>> organization.group_files(p)
    ['/var/www/media/base/ddr-testing/TS11TB2013.json', '/var/www/media/base/ddr-testing/WD5000BMV-2.json']
    
    @param path: Abs path to org repo
    """
    excludes = ['.git', 'organization.json']
    pattern = re.compile('.json$')
    return [f for f in os.listdir(path) if (f not in excludes) and pattern.search(f)]

def groups( path ):
    """Gets list of groups for which there are CSV files.
    
    >>> from DDR import organization
    >>> p = '/var/www/media/base/ddr-testing'
    >>> organization.groups(p)
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
    
    >>> from DDR import organization
    >>> r = '/media/DRIVELABEL/ddr/REPOORGID'
    >>> organization.group_file_path(r)
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
    
    >>> from DDR import organization
    >>> p = '/var/www/media/base/ddr-testing/WD5000BMV-2.json'
    >>> organization.read_group_file(p)
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
    
    import organization
    p = '/media/WD5000BMV-2/ddr/ddr-testing/WD5000BMV-2.csv'
    repos = organization.read_drive_file(p)
    defaults = {'ddrstatus': 'ddr status "$@"', 'ddrsync': 'ddr sync "$@"'}
    base_path = '/media/WD5000BMV-2/ddr'
    server = 'git@mits.densho.org'
    mrconfig = organization.mrconfig(defaults, base_path, server, repos)
    organization.write_mrconfig(mrconfig, '/tmp/mrconfig')
 
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

from DDR import dvcs, organization
repo = dvcs.repository('/var/www/media/base/ddr-testing-196')
stat = dvcs.annex_status(repo)
path = '/var/www/media/base/ddr-testing'
organization.repo_inventory_remotes(repo, stat, path)
"""
