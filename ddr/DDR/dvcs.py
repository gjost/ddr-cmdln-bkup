# git and git-annex code

import logging
logger = logging.getLogger(__name__)
import os
import re

import envoy
import git


def repo_status(path, short=False):
    """Retrieve git status on repository.
    
    @param collection_path: Absolute path to collection repo.
    @return: message ('ok' if successful)
    """
    status = 'unknown'
    repo = git.Repo(path)
    if short:
        status = repo.git.status(short=True, branch=True)
    else:
        status = repo.git.status()
    #logging.debug('\n{}'.format(status))
    return status

def annex_status(path):
    """Retrieve git annex status on repository.
    
    @param collection_path: Absolute path to collection repo.
    @return: message ('ok' if successful)
    """
    repo = git.Repo(collection_path)
    status = repo.git.annex('status')
    logging.debug('\n{}'.format(status))
    return status

def annex_whereis_file(repo, file_path_rel):
    """Show remotes that the file appears in
    
    $ git annex whereis files/ddr-testing-201303051120-1/files/20121205.jpg
    whereis files/ddr-testing-201303051120-1/files/20121205.jpg (2 copies)
            0bbf5638-85c9-11e2-aefc-3f0e9a230915 -- workbench
            c1b41078-85c9-11e2-bad2-17e365f14d89 -- here
    ok
    
    @param repo: A GitPython Repo object
    @param collection_uid: A valid DDR collection UID
    @return: List of names of remote repositories.
    """
    remotes = []
    stdout = repo.git.annex('whereis', file_path_rel)
    logging.debug('\n{}'.format(stdout))
    lines = stdout.split('\n')
    if ('whereis' in lines[0]) and ('ok' in lines[-1]):
        num_copies = int(lines[0].split(' ')[2].replace('(',''))
        logging.debug('    {} copies'.format(num_copies))
        remotes = [line.split('--')[1].strip() for line in lines[1:-1]]
        logging.debug('    remotes: {}'.format(remotes))
    return remotes

def gitolite_connect_ok(server):
    """See if we can connect to gitolite server.
    
    We should do some lightweight operation, just enough to make sure we can connect.
    But we can't ping.
    
    http://gitolite.com/gitolite/user.html#info
    "The only command that is always available to every user is the info command
    (run ssh git@host info -h for help), which tells you what version of gitolite
    and git are on the server, and what repositories you have access to. The list
    of repos is very useful if you have doubts about the spelling of some new repo
    that you know was setup."
    Sample output:
        hello gjost, this is git@mits running gitolite3 v3.2-19-gb9bbb78 on git 1.7.2.5
        
         R W C  ddr-densho-[0-9]+
         R W C  ddr-densho-[0-9]+-[0-9]+
         R W C  ddr-dev-[0-9]+
        ...
    
    @param server: USERNAME@DOMAIN
    @return: True or False
    """
    logging.debug('    DDR.commands.gitolite_connect_ok()')
    status,lines = gitolite_info(server)
    if status == 0 and lines:
        if len(lines) and ('this is git' in lines[0]) and ('running gitolite' in lines[0]):
            logging.debug('        OK ')
            return True
    logging.debug('        NO CONNECTION')
    return False

def gitolite_info(server):
    """
    @param server: USERNAME@DOMAIN
    @return: status,lines
    """
    status = None; lines = []
    cmd = 'ssh {} info'.format(server)
    logging.debug('        {}'.format(cmd))
    r = envoy.run(cmd, timeout=30)
    logging.debug('        {}'.format(r.status_code))
    status = r.status_code
    if r.status_code == 0:
        lines = r.std_out.split('\n')
    return status,lines

def list_staged(repo):
    """Returns list of currently staged files
    
    Works for git-annex files just like for regular files.
    
    @param repo: A Gitpython Repo object
    @return: List of filenames
    """
    return repo.git.diff('--cached', '--name-only').split('\n')

def list_committed(repo, commit):
    """Returns list of all files in the commit

    $ git log -1 --stat 0a1b2c3d4e...|grep \|

    @param repo: A Gitpython Repo object
    @param commit: A Gitpython Commit object
    @return: list of filenames
    """
    # return just the files from the specific commit's log entry
    entry = repo.git.log('-1', '--stat', commit.hexsha).split('\n')
    entrylines = [line for line in entry if '|' in line]
    files = [line.split('|')[0].strip() for line in entrylines]
    return files

def list_conflicted(repo):
    """Returns list of unmerged files in path; presence of files indicates merge conflict.
    
    @param repo: A Gitpython Repo object
    @return: List of filenames
    """
    lines = repo.git.ls_files('--unmerged').split('\n')
    files = []
    for line in lines:
        f = line.split('\t')[1]
        if f not in files:
            files.append(f)
    return files

def _status_analyzer(text, progs):
    """Helper function for running lists of compiled regexes on texts.
    
    @param text: The text to be analyzed.
    @param progs: List of compiled regex patterns.
    """
    stat = -1
    for prog in progs:
        if prog.search(text):
            stat = 1
        else:
            stat = 0
    return stat
    
"""
CONFLICTED
    $ git st
    # On branch master
>>> # Your branch and 'origin/master' have diverged,
>>> # and have 3 and 5 different commits each, respectively.
    #
    # Changes to be committed:
    #
    #	modified:   files/ddr-testing-160-1/changelog
    #	modified:   files/ddr-testing-160-1/entity.json
    #	modified:   files/ddr-testing-160-1/files/ddr-testing-160-1-master-c703e5ece1.json
    #
>>> # Unmerged paths:
    #   (use "git add/rm <file>..." as appropriate to mark resolution)
    #
    #	both modified:      ead.xml
    #
    # Untracked files:
    #   (use "git add <file>..." to include in what will be committed)
    #
    #	collection.json.conflict
    #	files/ddr-testing-160-1/addfile.log
    #	lock

AHEAD
    $ git st
    # On branch master
>>> # Your branch is ahead of 'origin/master' by 1 commit, and can be fast-forwarded.
    #
    nothing to commit (working directory clean)

BEHIND
    $ git st
    # On branch master
>>> # Your branch is behind 'origin/master' by 125 commits, and can be fast-forwarded.
    #
    nothing to commit (working directory clean)
"""
CONFLICTED = ["Your branch and ([a-zA-z0-9/']+) have diverged",
              "[0-9]+ and [0-9]+ different commits each",
              "Unmerged paths:",]

AHEAD = ["Your branch is behind ([a-zA-z0-9/']+) by ([0-9]+) commit",]

BEHIND = ["Your branch is behind ([a-zA-z0-9/']+) by ([0-9]+) commit",]

CONFLICTED_PROGS = [re.compile(pattern) for pattern in CONFLICTED]
AHEAD_PROGS = [re.compile(pattern) for pattern in AHEAD]
BEHIND_PROGS = [re.compile(pattern) for pattern in BEHIND]

def conflicted(status):
    """Indicates whether repo has a merge conflict.
    
    NOTE: Use list_conflicted if you have a repo object.
    @param status: A Git status message string.
    @returns 1 (conflicted), 0 (not conflicted), -1 (error)
    """
    return _status_analyzer(status, CONFLICTED_PROGS)

def ahead(status):
    """Indicates whether repo is ahead of remote repos.
    
    @param status: A Git status message string.
    @returns 1 (behind), 0 (not behind), -1 (error)
    """
    return _status_analyzer(status, AHEAD_PROGS)

def behind(status):
    """Indicates whether repo is behind remote repos.

    @param status: A Git status message string.
    @returns 1 (behind), 0 (not behind), -1 (error)
    """
    return _status_analyzer(status, BEHIND_PROGS)


# backup/sync -----------------------------------------------------

def repos(path):
    """Lists all the repositories in the path directory.
    Duplicate of collections list?
    
    >>> from DDR import dvcs
    >>> p = '/media/WD5000BMV-2/ddr'
    >>> dvcs.repos(p)
    ['/media/WD5000BMV-2/ddr/ddr-testing-130', '/media/WD5000BMV-2/ddr/ddr-testing-131', ...]
    """
    repos = []
    for d in os.listdir(path):
        dpath = os.path.join(path, d)
        if os.path.isdir(dpath) and ('.git' in os.listdir(dpath)):
            repos.append(dpath)
    return repos

def is_local(url):
    """Indicates whether or not the git URL is local.
    
    Currently very crude: just checks if there's an ampersand and a colon.
    
    @returns 1 (is local), 0 (not local), or -1 (unknown)
    """
    if url:
        if ('@' in url) and (':' in url):
            return 0 # remote
        return 1     # local
    return -1        # unknown

def local_exists(path):
    """Indicates whether a local remote can be found in the filesystem.
    """
    if os.path.exists(path):
        return 1
    return 0

def is_clone(path1, path2, n=5):
    """Indicates whether two repos at the specified paths are clones of each other.
    
    Compares the first N hashes
    TODO What if repo has less than N commits?
    
    @param path1
    @param path2
    @param n
    @returns 1 (is a clone), 0 (not a clone), or -1 (unknown)
    """
    print('is_clone(%s, %s, %s)' % (path1, path2, n))
    if is_local(path2):
        def get(path):
            try:
                repo = git.Repo(path)
            except:
                repo = None
            if repo:
                log = repo.git.log('--reverse', '-%s' % n, pretty="format:'%H'").split('\n')
                if log and (type(log) == type([])):
                    return log
            return None
        log1 = get(path1)
        log2 = get(path2)
        if log1 and log2:
            print('len(log1) %s' % len(log1))
            print('len(log2) %s' % len(log2))
            if (log1 == log2):
                return 1
            else:
                return 0
    return -1

def remotes(path, paths=None, clone_log_n=1):
    """Lists remotes for the repository at path.
    
    For each remote lists info you'd find in REPO/.git/config plus a bit more:
    - name
    - url
    - annex-uuid
    - fetch
    - push
    - local or remote
    - if local, whether the remote is a clone
    
    $ git remote -v
    memex	gjost@memex:~/music (fetch)
    memex	gjost@memex:~/music (push)
    origin	/media/WD5000BMV-2/music/ (fetch)
    origin	/media/WD5000BMV-2/music/ (push)
    seagate596-2010	gjost@memex:/media/seagate596-2010/Music (fetch)
    seagate596-2010	gjost@memex:/media/seagate596-2010/Music (push)
    serenity	gjost@jostwebwerks.com:~/git/music.git (fetch)
    serenity	gjost@jostwebwerks.com:~/git/music.git (push)
    wd5000bmv-2	/media/WD5000BMV-2/music/ (fetch)
    wd5000bmv-2	/media/WD5000BMV-2/music/ (push)
    
    >>> import git
    >>> repo = git.Repo(path)
    >>> repo.remotes
    [<git.Remote "origin">, <git.Remote "serenity">, <git.Remote "wd5000bmv-2">, <git.Remote "memex">, <git.Remote "seagate596-2010">]
    >>> cr = repo.config_reader()
    >>> cr.items('remote "serenity"')
[('url', 'gjost@jostwebwerks.com:~/git/music.git'), ('fetch', '+refs/heads/*:refs/remotes/serenity/*'), ('annex-uuid', 'e7e4c020-9335-11
e2-8184-835f755b29c5')]
    """
    remotes = []
    repo = git.Repo(path)
    for remote in repo.remotes:
        r = {'name':remote.name}
        for key,val in repo.config_reader().items('remote "%s"' % remote.name):
            r[key] = val
        r['local'] = is_local(r.get('url', None))
        r['local_exists'] = local_exists(r.get('url', None))
        r['clone'] = is_clone(path, r['url'], clone_log_n)
        remotes.append(r)
    return remotes

def repos_remotes(path):
    """Gets list of remotes for each repo in path.
    @returns list of dicts {'path':..., 'remotes':[...]}
    """
    return [{'path':p, 'remotes':remotes(p),} for p in repos(path)]
