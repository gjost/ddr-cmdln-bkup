"""

Gitolite setup
--------------

Before you can do anything else you have to modify `gitolite-admin` to all the local partner VMs to access and modify the inventory repos.::

    $ git clone git@mits:gitolite-admin.git ./gitolite-admin
    $ cd gitolite-admin
    $ nano conf/gitolite.conf

Add a record like this::

    + # new {REPO}-{ORGANIZATION} repo 2013-12-05 14:57
    + repo {REPO}-{ORGANIZATION}
    +   C     = @admins @densho @{ORGANIZATION}
    +   RW+   = @admins
    +   RW    = @{ORGANIZATION} @densho
    
    # collections
    repo ddr-testing-[0-9]+
    ...

Commit the change and push it to the Gitolite server.::

    $ git add -p conf/gitolite.conf
    $ git commit
    $ git push

For testing purposes it may be necessary to remove the organization repo several times.  The only way to remove a repo from a Gitolite server is to log in as the `git` user and `rm -Rf` the repository directory.  However, the Gitolite server process may still think the repo exists, or may not recreate it when you try to clone again.  To get around this, reset the datetime in `gitolite-admin/conf/gitolite.conf` and `git-push` up to the Gitolite server.  The organization repo will be regenerated.


Set up a new Organization
-------------------------

When first adding a new partner you need to create an organzation repo in which to store their metadata.

Create organization repo, add a store to it, push changes to the Gitolite server.  You can create this initial organization repo in your `/tmp` directory, then clone it to a Store after you've completed this step.::

    $ su ddr
    $ cd /usr/local/src/ddr-local/ddrlocal
    $ python
    >>> from DDR.models import Organization, Store
    >>> from DDR import inventory
    >>> inventory.create_organization('git@mits.densho.org', 'REPO', 'ORG', '/PATH/TO/BASE', 'GITNAME', 'GITMAIL')
    >>> inventory.add_store('/PATH/TO/BASE/ddr-testing', 'LABEL', 'LOCATION', 'YYYY-MM-DD', 'GITNAME', 'GITMAIL')
    >>> inventory.sync_organization('/PATH/TO/BASE/ddr-testing')


Set up Store on existing drive
------------------------------

This is a procedure for setting up an inventory on a drive that already contains collection repos.  As part of this procedure you will scan the drive for existing collections and use the list to populate the Store file.

Mount drive.

Clone the organization repo and add a store to it.::

    $ su ddr
    $ cd /usr/local/src/ddr-local/ddrlocal
    $ python
    >>> from DDR.models import Organization, Store
    >>> from DDR import inventory
    >>> inventory.clone_organization('git@mits.densho.org', 'REPO', 'ORG', '/PATH/TO/BASE')
    >>> inventory.add_store('/PATH/TO/BASE/ddr-testing', 'LABEL', 'LOCATION', 'YYYY-MM-DD', 'GITNAME', 'GITMAIL')

Get a list of collections present on the store and use that list to update Store.::

    $ python
    >>> label,collections = Store.analyze('/PATH/TO/BASE', force_level='access')
    >>> inventory.update_store('/PATH/TO/BASE/ddr-testing', 'LABEL', {'collections': collections}, 'GITNAME', 'GITMAIL')

Use the editor of your choice to confirm that the list of collections matches the collections in the store.

Push changes to the Gitolite server.::

    $ python
    >>> inventory.sync_organization('/PATH/TO/BASE/ddr-testing')


Set up new Store
----------------

This is a procedure for setting up an inventory on a drive does not contain any collection repos.

Mount drive.

Make a ddr/ directory.::

    $ mkdir /media/LABEL/ddr

Clone organization repo, add a store to it, push changes to Gitolite server.::

    $ su ddr
    $ cd /usr/local/src/ddr-local/ddrlocal
    $ python
    >>> from DDR.models import Organization, Store
    >>> from DDR import inventory
    >>> inventory.clone_organization('git@mits.densho.org', 'REPO', 'ORG', '/PATH/TO/BASE')
    >>> inventory.add_store('/PATH/TO/BASE/ddr-testing', 'LABEL', 'LOCATION', 'YYYY-MM-DD', 'GITNAME', 'GITMAIL')
    >>> inventory.sync_organization('/PATH/TO/BASE/ddr-testing')


Sync new Store with existing one
--------------------------------

This is the procedure for cloning the collection repos in one Store onto another Store.  At the end of this procedure, the destination store should contain all the repos from the source store.  The organization repos for both source and destination stores will have been synchronized with the Gitolite server.  NOTE: The organization repo must already be set up. The Store must have been added to organization repo.

Sync collection repos.::

    $ su ddr
    $ ddr syncgrp -i /PATH/TO/SOURCE/BASE/REPO-ORG -B /PATH/TO/SOURCE/BASE -b /PATH/TO/DEST/BASE -v LEVEL

Get list of collections and update the store record on the *destination* store.::

    $ su ddr
    $ cd /usr/local/src/ddr-local/ddrlocal
    $ python
    >>> from DDR.models import Organization, Store
    >>> from DDR import inventory
    >>> label,collections = Store.analyze('/PATH/TO/DEST/BASE', force_level='LEVEL')
    >>> inventory.update_store('/PATH/TO/DEST/BASE/REPO-ORG', 'LABEL', {'collections': collections}, 'GITNAME', 'GITMAIL')

Confirm list of collections matches.::

Push changes from the *destination* store to the Gitolite server.::

    $ python
    >>> inventory.sync_organization('/PATH/TO/DEST/BASE/REPO-ORG')

Pull changes to the *source* store.::

    $ python
    >>> inventory.sync_organization('/PATH/TO/SOURCE/BASE/REPO-ORG')

"""

from datetime import datetime, date
import ConfigParser
import json
import logging
logger = logging.getLogger(__name__)
import os
import re
import sys

import envoy
import git

from DDR import CONFIG_FILE
from DDR import dvcs, storage
from DDR.models import Repository, Organization, Store
from DDR.models import INVENTORY_LEVELS, ORGANIZATION_FIELDS, COLLECTION_FIELDS, STORE_FIELDS
from DDR.models import _write_json


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
GIT_REMOTE_NAME = config.get('workbench','remote')



DRIVE_FILE_FIELDS = 'id,level'



def create_organization( git_remote, repo, org, dest_dir, git_name, git_mail ):
    """Create a copy of Organization repo.
    
from DDR.inventory import clone_organization
clone_organization('git@mits.densho.org', 'ddr', 'testing', '/tmp/repo')
    
    @param git_remote: Address of Git server ('git@mits.densho.org').
    @param repo: Keyword of the Repository.
    @param org: keyword of the Organization.
    @param dest_dir: Absolute path to destination directory.
    @param git_name
    @param git_mail
    """
    org_id = '%s-%s' % (repo, org)
    git_url = '{}:{}.git'.format(GITOLITE, org_id)
    path = os.path.join(dest_dir, org_id)
    repository = git.Repo.clone_from(git_url, path)
    o = Organization(path=path, id=org_id, repo=repo, org=org, keyword=org,)
    o.save()
    o.commit(git_name, git_mail, 'Set up organization: %s' % o.id)
    repository.git.push('origin', 'master')

def clone_organization( git_remote, repo, org, dest_dir ):
    """Clone a copy of Organization repo.
    
from DDR.inventory import clone_organization
clone_organization('git@mits.densho.org', 'ddr', 'testing', '/tmp/repo')
    
    @param git_remote: Address of Git server ('git@mits.densho.org').
    @param repo: Keyword of the Repository.
    @param org: keyword of the Organization.
    @param dest_dir: Absolute path to destination directory.
    """
    org_id = '%s-%s' % (repo, org)
    git_url = '{}:{}.git'.format(GITOLITE, org_id)
    path = os.path.join(dest_dir, org_id)
    repository = git.Repo.clone_from(git_url, path)

def sync_organization( path, remote='origin' ):
    """Sync Organization with the specified remote.
    
from DDR.inventory import sync_organization
sync_organization('/tmp/repo/ddr-testing', 'origin')
    
    @param path: Absolute path to Organization directory.
    @param remote: Name of remote to sync to
    """
    repo = dvcs.repository(path)
    repo.git.fetch()
    repo.git.pull()
    repo.git.push(remote, 'master')

def add_store( path, label, location, purchase_date, git_name, git_mail ):
    """Create a new Store and add it to an existing Organization.
    
from DDR.inventory import add_store
add_store('/tmp/repo/ddr-testing', 'WD5000BMV-2', 'Pasadena', '2013-11-23', 'gjost', 'gjost@densho.org')
    
    @param path: Absolute path to Organization directory.
    @param label: Drive label for drive on which the Store resides.
    @param location: 
    @param purchase_date: String in the form 'YYYY-MM-DD'.
    @param git_name
    @param git_mail
    """
    o = Organization.load(path)
    s = Store(repo=o.repo, org=o.org,
              label=label, location=location,
              purchase_date=purchase_date)
    o.stores.append(s)
    o.save()
    o.commit(git_name, git_mail, 'Added store: %s' % label)

def update_store( path, label, kwargs, git_name, git_mail ):
    """Update an existing Store record.
    
    @param path: Absolute path to Organization directory.
    @param label: Drive label for drive on which the Store resides.
    @param kwargs
    @param git_name
    @param git_mail
    """
    o = Organization.load(path)
    s = o.store(label)
    # update values
    for key in kwargs.keys():
        if key in STORE_FIELDS:
            setattr(s, key, kwargs[key])
    o.save()
    o.commit(git_name, git_mail, 'Updated store: %s' % label)

def remove_store( path, label, git_name, git_mail ):
    """Remove Store from an Organization.
    
    @param path: Absolute path to Organization directory.
    @param label: Drive label for drive on which the Store resides.
    @param git_name
    @param git_mail
    """
    o = Organization.load(path)
    s = o.store(label)
    o.remove_store(s)
    o.save()
    o.commit(git_name, git_mail, 'Removed store: %s' % label)

def add_collection( path, label, collections, git_name, git_mail ):
    """Add a collection to the specified Store.
    
from DDR.inventory import add_collection
collections = [{}]
add_collection('gjost', 'gjost@densho.org', '/tmp/repo/ddr-testing', 'WD5000BMV-2', collections)
    
    @param path: Absolute path to Organization directory.
    @param label: Drive label for drive on which the Store resides.
    @param collections: List of dicts ({uuid, cid, level})
    @param git_name
    @param git_mail
    """
    o = Organization.load(path)
    s = o.store(label)
    for c in collections:
        ok = 0
        for key in c.keys():
            if key in COLLECTION_FIELDS:
                ok = ok + 1
        if (ok == len(c.keys())) and (c not in s.collections):
            s.collections.append(c)
    o.save()
    o.commit(git_name, git_mail, 'Added collection(s)')
    return 0

def update_collection( path, label, uuid, kwargs, git_name, git_mail ):
    """Update a collection.
    
    @param path: Absolute path to Organization directory.
    @param label: Drive label for drive on which the Store resides.
    @param uuid: UUID of collection to remove.
    @param kwargs: Dict of kwargs.
    @param git_name
    @param git_mail
    """
    o = Organization.load(path)
    s = o.store(label)
    c = s.collection(uuid=uuid)
    for key in kwargs:
        if key in COLLECTION_FIELDS:
            c[key] = kwargs[key]
    o.save()
    o.commit(git_name, git_mail, 'Updated collection %s %s' % (s.label, c['cid']))

def remove_collection( path, label, uuid, git_name, git_mail ):
    """Remove a collection from the specified Store.
    
    @param path: Absolute path to Organization directory.
    @param label: Drive label for drive on which the Store resides.
    @param uuid: UUID of collection to remove.
    @param git_name
    @param git_mail
    """
    o = Organization.load(path)
    s = o.store(label)
    c = s.collection(uuid=uuid)
    s.collections.remove(c)
    o.save()
    o.commit(git_name, git_mail, 'Removed collection %s %s' % (s.label, c['cid']))





def syncable_devices(mounted):
    """Lists mounted devices that are available to be synced.

    To be eligible, devices must contain a ddr/ directory in their root; the ddr/ directory must contain a valid inventory repo.  Each REPO-ORG combination must appear on at least two devices or there's no point in syncing.
    
    >> from DDR import storage
    >> from DDR import inventory
    >> inventory.syncable_devices(storage.removables_mounted())

    @param mounted: Output of storage.removables_mounted()
    @returns Dict of organization IDs and lists of device dicts for drives they appear on.
    """
    def ddr_path(path):
        return os.path.join(path, 'ddr')
    def looks_like_org_dir(dirname):
        if len(dirname.split('-')) == 2:
            return True
        return False
    tentative = {}
    for device in mounted:
        ddrpath = ddr_path(device['mountpath'])
        if os.path.exists(ddrpath):
            for d in os.listdir(ddrpath):
                orgdir = os.path.join(ddrpath, d)
                if looks_like_org_dir(d) and Organization.is_valid(orgdir):
                    orgdevices = tentative.get(d, [])
                    if device not in orgdevices:
                        orgdevices.append(device)
                    tentative[d] = orgdevices
    # only list inventories if there are at least two devices
    syncable = {}
    for key in tentative.keys():
        orgdevices = tentative.get(key, [])
        if orgdevices and (len(orgdevices) > 1):
            syncable[key] = orgdevices
    return syncable

def guess_drive_label(path):
    label = storage.drive_label(path)
    if not label:
        hostname = envoy.run('hostname').std_out.strip()
        ppath = path.replace(os.sep, '-')[1:]
        label = '%s_%s' % (hostname, ppath)
    return label

def init_store():
    """[DEPRECATED] Interactive command for initializing a new (blank) Store.
    
    * * * * * DEPRECATED - use inventory.add_store() * * * * *
    Asks user for values of the various fields.
    """
    print('')
    
    git_name = raw_input('Your name: ')
    git_mail = raw_input('Email address: ')
    
    path = raw_input("Path to Store's ddr/ dir (e.g. '/media/USBDRIVE/ddr'): ")
    if not os.path.exists(path):
        print('Nonexistant path: %s' % path)
        sys.exit(1)
    label = guess_drive_label(path)
    confirm = raw_input('Drive label: "%s" [y/n] ' % label)
    if confirm != 'y':
        label = raw_input('Drive label: ')
    
    location = raw_input("Location: ")
    level = raw_input("Annex level %s: " % INVENTORY_LEVELS)
    if level not in INVENTORY_LEVELS:
        print('Enter a valid level')
        sys.exit(1)
    raw_purchased = raw_input('Purchase date (YYYY-MM-DD): ')
    try:
        purchased = datetime.strptime(raw_purchased, '%Y-%m-%d').date()
    except:
        print('Enter a valid date')
        sys.exit(1)
    
    repo = raw_input('Repository (e.g. "ddr"): ')
    org = raw_input('Organization (e.g. "densho"): ')
    oid = '%s-%s' % (repo, org)
    gitolite = raw_input('Server (e.g. "%s"): ' % GITOLITE)
    url = '%s:%s-%s.git' % (gitolite, repo, org)
    url_confirm = raw_input('Organization repo URL: "%s" [y/n] ' % url)
    if url_confirm != 'y':
        sys.exit(1)
    
    print('')
    print('User name:  %s' % git_name)
    print('User mail:  %s' % git_mail)
    print('Path:       %s' % path)
    print('Label:      %s' % label)
    print('Purchased:  %s' % purchased)
    print('Location:   %s' % location)
    print('Level:      %s' % level)
    print('URL:        %s' % url)
    confirm = raw_input('Are the above values correct? [y/n] ')
    print('')
    if confirm != 'y':
        sys.exit(1)
    
    clone_organization( url, os.path.join(path, oid) )
    add_store( path, label, location, purchased, git_name, git_mail )
    #sync_organization( path, remote='origin' )




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
    repos = []
    with open(path, 'rb') as f:
        data = json.loads(f.read())
    return data['collections']

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





if __name__ == '__main__':
    #init_store()
    pass
