# git and git-annex code

import json
import logging
logger = logging.getLogger(__name__)
import os
import re
import socket

import envoy
import git

from DDR import storage


def set_git_configs(repo, user_name=None, user_mail=None):
    if user_name and user_mail:
        repo.git.config('user.name', user_name)
        repo.git.config('user.email', user_mail)
        # we're not actually using gitweb any more...
        repo.git.config('gitweb.owner', '{} <{}>'.format(user_name, user_mail))
    # ignore file permissions
    repo.git.config('core.fileMode', 'false')
    # earlier versions of git-annex have problems with ssh caching on NTFS
    repo.git.config('annex.sshcaching', 'false')
    return repo

def repository(path, user_name=None, user_mail=None):
    """
    @param collection_path: Absolute path to collection repo.
    @return: GitPython repo object
    """
    repo = git.Repo(path)
    return set_git_configs(repo, user_name, user_mail)

def latest_commit(repo_or_path=None):
    """Returns latest commit for the specified repository
    
    This function prefers a GitPython Repository object but will also accept an
    absolute path to a repository.  If no argument is provided it will use CWD.
    
    >>> repo = repository('/path/to/repo')
    >>> latest_commit(repo)
    '8ad396324cc4a9ce6b9c0bce1cc8b78cc8e82859 (HEAD, master) 2013-07-11 11:03:19 -0700'
    
    @param repo_or_path: GitPython Repository object or repo path
    """
    if not repo_or_path:
        repo_or_path = os.getcwd()
    repo = None
    if isinstance(repo_or_path, git.Repo):
        repo = repo_or_path
    elif isinstance(repo_or_path, basestring) and os.path.exists(repo_or_path):
        repo = git.Repo(repo_or_path)
    if repo:
        return repo.git.log('--pretty=format:%H %d %ad', '--date=iso', '-1')
    return None

def compose_commit_message(title, body='', agent=''):
    """Composes a Git commit message.
    
    TODO wrap body text at 72 chars
    
    @param title: (required) 50 chars or less
    @param body: (optional) Freeform body text.
    @param agent: (optional) Do not include the word 'agent'.
    """
    # force to str
    if not body: body = ''
    if not agent: agent = ''
    # formatting
    if body:  body = '\n\n%s' % body
    if agent: agent = '\n\n@agent: %s' % agent
    return '%s%s%s' % (title, body, agent)

def _parse_annex_description(annex_status, uuid):
    """
    @param annex_status: output of git-annex-status
    @param uuid: UUID of repository to extract
    """
    DESCR_REGEX = '\((?P<description>[\w\d ._-]+)\)'
    description = None
    for line in annex_status.split('\n'):
        if (uuid in line) and ('here' in line):
            match = re.search(DESCR_REGEX, line)
            if match and match.groupdict():
                description = match.groupdict().get('description', None)
    return description

def get_annex_description( repo, annex_status=None ):
    """Get description of the current repo, if any.
    
    Parses the output of "git annex status" and extracts the current repos description.
    If annex_status is provided, it will search that.
    This is a timesaver, as git-annex-status takes time to run if a repo has any remotes
    that are accessible only via a network.
    
    Sample status (repo has description):
        $ git annex status
        ...
        semitrusted repositories: 8
                00000000-0000-0000-0000-000000000001 -- web
         	371931a0-34f6-11e3-bdb4-93c90d5c4311
         	5ee6f3c0-2ae2-11e3-91a3-938a9cc1e3e5 -- TS1TB2013
         	6367a2b4-34f6-11e3-b0c7-675d7fe6384c
         	86fd75d0-32c8-11e3-af91-1bdd76d780f0
         	9bcda696-2ae0-11e3-8c55-eb0b7dddd863 -- here (WD5000BMV-2)
         	a1a0923a-2ae6-11e3-89ec-d3f4e727eeaf -- int_var-ddr
         	b84dc8fc-2ade-11e3-88a3-1f33b5e6b986 -- workbench
        untrusted repositories: 0
        dead repositories: 0
        ...
    
    Sample status (no description):
        $ git annex status
        ...
        semitrusted repositories: 8
                00000000-0000-0000-0000-000000000001 -- web
                8792a1aa-2a08-11e3-9f20-3331e21c94e3 -- here
         	b84dc8fc-2ade-11e3-88a3-1f33b5e6b986 -- workbench
        untrusted repositories: 0
        dead repositories: 0
        ...

    @param repo: A GitPython Repo object
    @param annex_status: (optional) Output of "git annex status" (saves some time).
    @return String description or None
    """
    uuid = repo.git.config('annex.uuid')
    if not annex_status:
        annex_status = repo.git.annex('status')
    return _parse_annex_description(annex_status, uuid)

def _make_annex_description( drive_label=None, hostname=None, partner_host=None, mail=None ):
    description = None
    if drive_label:
        description = drive_label
    elif hostname and (hostname == partner_host) and mail:
        description = ':'.join([ hostname, mail.split('@')[1] ])
    elif hostname and (hostname != partner_host):
        description = hostname
    return description

def set_annex_description( repo, annex_status=None, description=None, force=False ):
    """Sets repo's git annex description if not already set.

    NOTE: This needs to run git annex status, which takes some time.
     
    New repo: git annex init "REPONAME"
    Existing repo: git annex describe here "REPONAME"
     
    Descriptions should be chosen/generated base on the following heuristic:
    - Input to description argument of function.
    - If on USB device, the drive label of the device.
    - Hostname of machine, unless it is pnr (used by partner VMs).
    - If hostname is pnr, pnr:DOMAIN where DOMAIN is the domain portion of the git config user.email
    
    @param repo: A GitPython Repo object
    @param annex_status: (optional) Output of "git annex status" (saves some time).
    @param description: Manually supply a new description.
    @param force: Boolean Apply a new description even if one already exists.
    @return String description if new one was created/applied or None
    """
    desc = None
    PARTNER_HOSTNAME = 'pnr'
    annex_description = get_annex_description(repo, annex_status)
    # keep existing description unless forced
    if (not annex_description) or (force == True):
        if description:
            desc = description
        else:
            # gather information
            drive_label = storage.drive_label(repo.working_dir)
            hostname = socket.gethostname()
            user_mail = repo.git.config('user.email')
            # generate description
            desc = _make_annex_description(
                drive_label=drive_label,
                hostname=hostname, partner_host=PARTNER_HOSTNAME,
                mail=user_mail)
        if desc:
            # apply description
            logging.debug('git annex describe here %s' % desc)
            repo.git.annex('describe', 'here', desc)
    return desc

def fetch(path):
    """run git fetch; fetches from origin.
    
    @param collection_path: Absolute path to collection repo.
    @return: message ('ok' if successful)
    """
    repo = git.Repo(path)
    return repo.git.fetch()

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
    repo = git.Repo(path)
    status = repo.git.annex('status')
    logging.debug('\n{}'.format(status))
    return status

def _parse_annex_whereis( annex_whereis_stdout ):
    lines = annex_whereis_stdout.strip().split('\n')
    # chop off anything before whereis line
    startline = -1
    for n,line in enumerate(lines):
        if 'whereis' in line:
            startline = n
    lines = lines[startline:]
    remotes = []
    if ('whereis' in lines[0]) and ('ok' in lines[-1]):
        num_copies = int(lines[0].split(' ')[2].replace('(',''))
        logging.debug('    {} copies'.format(num_copies))
        remotes = [line.split('--')[1].strip() for line in lines[1:-1]]
    return remotes

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
    stdout = repo.git.annex('whereis', file_path_rel)
    print('----------')
    print(stdout)
    print('----------')
    return _parse_annex_whereis(stdout)

def _gitolite_info_authorized( status, lines ):
    if status == 0 and lines:
        if len(lines) and ('this is git' in lines[0]) and ('running gitolite' in lines[0]):
            logging.debug('        OK ')
            return True
    logging.debug('        NO CONNECTION')
    return False
    
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
    return _gitolite_info_authorized(status, lines)

def gitolite_orgs( gitoliteinfo ):
    """Returns list of orgs to which user has access
    
    @param gitoliteinfo: lines part of gitolite_info() output
    @returns: list of organization IDs
    """
    repos_orgs = []
    for line in gitoliteinfo:
        if 'R W C' in line:
            parts = line.replace('R W C', '').strip().split('-')
            repo_org = '-'.join([parts[0], parts[1]])
            if repo_org not in repos_orgs:
                repos_orgs.append(repo_org)
    return repos_orgs

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

def _parse_list_staged( diff ):
    staged = []
    if diff:
        staged = diff.strip().split('\n')
    return staged
    
def list_staged(repo):
    """Returns list of currently staged files
    
    Works for git-annex files just like for regular files.
    
    @param repo: A Gitpython Repo object
    @return: List of filenames
    """
    stdout = repo.git.diff('--cached', '--name-only')
    return _parse_list_staged(stdout)

def _parse_list_committed( entry ):
    entrylines = [line for line in entry.split('\n') if '|' in line]
    files = [line.split('|')[0].strip() for line in entrylines]
    return files
    
def list_committed(repo, commit):
    """Returns list of all files in the commit

    $ git log -1 --stat 0a1b2c3d4e...|grep \|

    @param repo: A Gitpython Repo object
    @param commit: A Gitpython Commit object
    @return: list of filenames
    """
    # return just the files from the specific commit's log entry
    entry = repo.git.log('-1', '--stat', commit.hexsha)
    return _parse_list_committed(entry)

def _parse_list_conflicted( ls_unmerged ):
    files = []
    for line in ls_unmerged.strip().split('\n'):
        if line:
            f = line.split('\t')[1]
            if f not in files:
                files.append(f)
    return files
    
def list_conflicted(repo):
    """Returns list of unmerged files in path; presence of files indicates merge conflict.
    
    @param repo: A Gitpython Repo object
    @return: List of filenames
    """
    stdout = repo.git.ls_files('--unmerged')
    return _parse_list_conflicted(stdout)

# merge tools ------------------------------------------------------------

MERGE_MARKER_START = '<<<<<<<'
MERGE_MARKER_MID   = '======='
MERGE_MARKER_END   = '>>>>>>>'

def load_conflicted_json(text):
    """Reads DDR JSON file, extracts conflicting fields; arranges in left-right pairs.
    
    Takes JSON like this:
        ...
            {
                "record_created": "2013-09-30T12:43:11"
            },
            {
        <<<<<<< HEAD
                "record_lastmod": "2013-10-02T12:59:30"
        =======
                "record_lastmod": "2013-10-02T12:59:30"
        >>>>>>> 0b9d669da8295fc05e092d7abdce22d4ffb50f45
            },
            {
                "status": "completed"
            },
        ...

    Outputs like this:
        ...
        {u'record_created': u'2013-09-30T12:43:11'}
        {u'record_lastmod': {'right': u'2013-10-02T12:59:30', 'left': u'2013-10-02T12:59:30'}}
        {u'status': u'completed'}
        ...
    """
    def make_dict(line):
        """
        Sample inputs:
            '    "application": "https://github.com/densho/ddr-local.git",'
            '    "release": "0.20130711"'
        Sample outputs:
            {"application": "https://github.com/densho/ddr-local.git"}
            {"release": "0.20130711"}
        """
        txt = line.strip()
        if txt[-1] == ',':
            txt = txt[:-1]
        txt = '{%s}' % txt
        return json.loads(txt)
    fieldlines = []
    l = ' '; r = ' '
    for line in text.split('\n'):
        KEYVAL_SEP = '": "'  # only keep lines with keyval pairs
        mrk = ' ';  sep = ' '
        if MERGE_MARKER_START in line: mrk='M'; l='L'; r=' ' # <<<<<<<<
        elif MERGE_MARKER_MID in line: mrk='M'; l=' '; r='R' # ========
        elif MERGE_MARKER_END in line: mrk='M'; l=' '; r=' ' # >>>>>>>>
        elif KEYVAL_SEP in line: sep='S'               # normal field
        flags = '%s%s%s%s' % (sep, mrk, l, r)
        fieldlines.append((flags, line))
    fields = []
    for flags,line in fieldlines:
        if   flags == 'S   ': fields.append(make_dict(line)) # normal field
        elif flags == ' ML ': left = []; right = []          # <<<<<<<<
        elif flags == 'S L ': left.append(make_dict(line))   # left
        elif flags == 'S  R': right.append(make_dict(line))  # right
        elif flags == ' M  ':                                # >>>>>>>>
            if len(left) == len(right):
                for n in range(0, len(left)):
                    key = left[n].keys()[0]
                    val = {'left': left[n].values()[0],
                           'right': right[n].values()[0],}
                    fields.append( {key:val} )
    return fields

def automerge_conflicted(text, which='left'):
    """Automatically accept left or right conflicted changes in a file.
    
    Works on any kind of file.
    Does not actually understand the file contents!
    
    Used for files like ead.xml, mets.xml that are autogenerated
    We'll just accept whatever change and then it'll get fixed
    next time the file is edited.
    These really shouldn't be in Git anyway...
    """
    lines = []
    l = 0; r = 0
    for line in text.split('\n'):
        marker = 0
        if MERGE_MARKER_START in line: l = 1; r = 0; marker = 1
        elif MERGE_MARKER_MID in line: l = 0; r = 1; marker = 1
        elif MERGE_MARKER_END in line: l = 0; r = 0; marker = 1
        flags = '%s%s%s' % (l, r, marker)
        add = 0
        if ( flags == '000'): add = 1
        if ((flags == '100') and (which == 'left')): add = 1
        if ((flags == '010') and (which == 'right')): add = 1
        if add:
            lines.append(line)
    return '\n'.join(lines)

def merge_add( repo, file_path_rel ):
    """Adds file unless contains conflict markers
    """
    # check for merge conflict markers
    file_path_abs = os.path.join(repo_path, file_path_rel)
    with open(file_path_abs, 'r') as f:
        txt = f.read()
    if (MERGE_MARKER_START in txt) or (MERGE_MARKER_MID in txt) or (MERGE_MARKER_END in txt):
        return 'ERROR: file still contains merge conflict markers'
    repo.git.add(file_path_rel)
    return 'ok'

def merge_commit( repo ):
    """Performs the final commit on a merge.
    
    Assumes files have already been added; quits if it finds unmerged files.
    """
    unmerged = list_conflicted(path)
    if unmerged:
        return 'ERROR: unmerged files exist!'
    commit = repo.git.commit('--message', 'merge conflicts resolved using DDR web UI.')

def diverge_commit( repo ):
    """Performs the final commit on diverged repo.
    
    Assumes files have already been added; quits if it finds unmerged files.
    """
    unmerged = list_conflicted(path)
    if unmerged:
        return 'ERROR: unmerged files exist!'
    commit = repo.git.commit('--message', 'divergent commits resolved using DDR web UI.')

# ------------------------------------------------------------------------
    
"""
IMPORTANT:
Indicators for SYNCED,AHEAD,BEHIND,DIVERGED
are found in the FIRST LINE
of "git status --short --branch".

SYNCED
$ git status --short --branch
## master

AHEAD
$ git status --short --branch
## master...origin/master [ahead 1]
---
$ git status --short --branch
## master...origin/master [ahead 2]

BEHIND
$ git status --short --branch
## master...origin/master [behind 1]

DIVERGED
$ git status --short --branch
## master...origin/master [ahead 1, behind 2]
"""

def synced(status):
    """Indicates whether repo is synced with remote repo.
    
    @param status: Output of "git status --short --branch"
    @returns 1 (behind), 0 (not behind), -1 (error)
    """
    if status == '## master':
        return 1
    return 0

AHEAD = "(ahead [0-9]+)"
AHEAD_PROG = re.compile(AHEAD)
BEHIND = "(behind [0-9]+)"
BEHIND_PROG = re.compile(BEHIND)

def ahead(status):
    """Indicates whether repo is ahead of remote repos.
    
    @param status: Output of "git status --short --branch"
    @returns 1 (behind), 0 (not behind), -1 (error)
    """
    if AHEAD_PROG.search(status) and not BEHIND_PROG.search(status):
        return 1
    return 0

def behind(status):
    """Indicates whether repo is behind remote repos.

    @param status: Output of "git status --short --branch"
    @returns 1 (behind), 0 (not behind), -1 (error)
    """
    if BEHIND_PROG.search(status) and not AHEAD_PROG.search(status):
        return 1
    return 0

DIVERGED = [AHEAD, BEHIND]
DIVERGED_PROGS = [re.compile(pattern) for pattern in DIVERGED]

def diverged(status):
    """
    @param status: Output of "git status --short --branch"
    @returns 1 (diverged), 0 (not conflicted), -1 (error)
    """
    matches = [1 for prog in DIVERGED_PROGS if prog.search(status)]
    if len(matches) == 2: # both ahead and behind
        return 1
    return 0

"""
IMPORTANT:
Indicators for CONFLICTED,PARTIAL_RESOLVED,RESOLVED
are found AFTER the first line
of "git status --short --branch".

CONFLICTED
$ git status --short --branch
## master...origin/master [ahead 1, behind 2]
UU changelog
UU collection.json

PARTIAL_RESOLVED
$ git status --short --branch
## master...origin/master [ahead 1, behind 2]
M  changelog
UU collection.json

RESOLVED
$ git status --short --branch
## master...origin/master [ahead 1, behind 2]
M  changelog
M  collection.json
"""

CONFLICTED_PROG = re.compile("(UU )")

def conflicted(status):
    """Indicates whether repo has a merge conflict.
    
    NOTE: Use list_conflicted if you have a repo object.
    @param status: Output of "git status --short --branch"
    @returns 1 (conflicted), 0 (not conflicted), -1 (error)
    """
    matches = [1 for line in status if CONFLICTED_PROG.match(line)]
    if matches:
        return 1
    return 0


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
