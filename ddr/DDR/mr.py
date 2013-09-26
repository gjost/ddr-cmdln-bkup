import logging
logger = logging.getLogger(__name__)
import os

import envoy
import git



def mrtest():
    print(os.getcwd())

def update(path):
    """
    $ cd $PATH
    $ mr update
    """
    pass

def add_remote(repo_path, name, url):
    """Given the paths to two repos, add the latter as a remote to the former.
    
    @param repo_path: Absolute path to a repo.
    @param name: Name by which to refer to the remote.
    @param url: URL or file path by which to 
    """
    pass

def add_remotes(this_dir, name, url):
    """function for adding 
    
    $ cd $PATH
    $ mr run ddr add_remote -l NAME -u URL
    
    # load .mrconfig from this_dir
    # load .mrconfig from remotes_dir
    # for repo in path1:
    #     if no remote is found which has label and points to path:
    #         git remote add DRIVELABEL PATH
    
    @param repo_path: Absolute path to a repo.
    @param name: Name by which to refer to the remote.
    @param url: URL or file path by which to 
    """
    pass

def repo_level(repo_path, level=None):
    """Determine the "level" of the repo.
    
    Indicates which of the repo's binaries to git-annex-get when syncing.
    
    TODO WHERE TO STORE THIS SETTING???
    - set property in .git/config?
    - field in collection.json?
    - REPO/control?
    - some other file?
    
    >>> repo_level('/var/www/media/base/ddr-testing-123')
    None
    >>> repo_level('/var/www/media/base/ddr-testing-123', 'access')
    'access'
    >>> repo_level('/var/www/media/base/ddr-testing-123')
    'access'
    
    @param repo_path: Absolute path to a repo.
    @param level: If present, sets level.
    @returns level: "metadata", "access", "all", or None
    """
    return None

def sync_repo(repo_path, remote_name):
    """Sync between the repository and a named remote.
    
    Checks the level of "this" repo (path).
    'metadata': No git-annex files are synced.
    'all': A normal git-annex-sync is performed.
    'access': 

    @param path: Absolute path to a repo.
    @param remote_name: Name of remote.
    @return feedback
    """
    feedback = 'UNSPECIFIED ERROR'
    remote_exists = None
    if not remote_exists:
        return 'ERROR: remote does not exist %s' % name
    level = repo_level(path1)
    if level == 'metadata':
        # git pull
        pass
    elif level == 'all':
        # git annex sync
        pass
    elif level == 'access':
        # find all the access files
        # sync each one
        pass
    return feedback

def sync_repositories(orgrepo_path, remote_name):
    """Sync the 
    TODO return feedback for each repo as it completes.
    """
    # mr run ddr syncrepo -c PATH -r REMOTE_NAME
    pass
