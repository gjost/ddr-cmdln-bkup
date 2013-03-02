from datetime import datetime
from functools import wraps
import os
import sys

import envoy
import git

from Kura.models import Collection, Entity
from Kura.changelog import write_changelog_entry
from Kura.control import CollectionControlFile, EntityControlFile
from Kura.xml import EAD, METS


GIT_USER = 'git'
GIT_SERVER = 'mits'

MODULE_PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(MODULE_PATH, 'templates')
GITIGNORE_TEMPLATE = os.path.join(TEMPLATE_PATH, 'gitignore.tpl')


def gitolite_connect_ok( debug=False ):
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
    """
    cmd = 'ssh {}@{} info'.format(GIT_USER, GIT_SERVER)
    if debug:
        print(cmd)
    r = envoy.run(cmd)
    if debug:
        print(r.status_code)
    if r.status_code == 0:
        lines = r.std_out.split('\n')
        if len(lines) and ('this is git@{} running gitolite'.format(GIT_SERVER) in lines[0]):
            return True
    return False

def requires_network(f):
    """Indicate that function requires network access; check if can connect to gitolite server.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not gitolite_connect_ok():
            print('ERR: Cannot connect to git server {}@{}'.format(GIT_USER,GIT_SERVER))
            sys.exit(1)
        return f(*args, **kwargs)
    return wrapper

def local_only(f):
    """Indicate that function requires no network access.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    return wrapper



description="""Create, edit, delete collections"""

epilog="""
More than you thought you wanted to know about the collection command.
"""

OPERATIONS = [
    'create',
    'destroy',
    'status',
    'astatus',
    'update',
    'sync',
    'ecreate',
    'edestroy',
    'eupdate',
    'eadd',
    'pull',
    'push',
    ]


@requires_network
def create(user_name, user_mail, collection_path, debug=False):
    """Command-line function for creating a new collection.
    
    Clones a blank collection object from workbench server, adds files, commits.
    
    - clones new repo from gitolite server
    # Easier to have Gitolite create repo then clone (http://sitaramc.github.com/gitolite/repos.html)
    # than to add existing to Gitolite (http://sitaramc.github.com/gitolite/rare.html#existing).
    local requests CID from workbench API
    background:collection init: $ collection -cCID -oinit]
    background:collection init: $ git clone git@mits:ddr-ORG-C
        $ git clone git@mits:ddr-densho-1
        Cloning into 'ddr-densho-1'...
        Initialized empty Git repository in /home/git/repositories/ddr-densho-1.git/
        warning: You appear to have cloned an empty repository.
    background:entity init: $ git annex init
    background:entity init: $ git add changelog control ead.xml .gitignore
    background:entity init: $ git commit
    """
    if debug:
        print('collection.create({})'.format(collection_path))
    collection_uid = os.path.basename(collection_path)
    url = '{}@{}:{}.git'.format(GIT_USER, GIT_SERVER, collection_uid)
    if debug:
        print('cloning: {}'.format(url))
    
    repo = git.Repo.clone_from(url, collection_path)
    # there is no master branch at this point
    if debug:
        print('cloned')
    repo.git.config('user.name', user_name)
    repo.git.config('user.email', user_mail)
    repo.git.config('gitweb.owner', '{} <{}>'.format(user_name, user_mail))
    git_files = []

    # control
    control_path_rel = 'control'
    control_path_abs = os.path.join(collection_path, control_path_rel)
    CollectionControlFile.create(control_path_abs, collection_uid)
    git_files.append(control_path_rel)

    # ead.xml
    ead_path_rel = 'ead.xml'
    ead_path_abs = os.path.join(collection_path, ead_path_rel)
    EAD.create(ead_path_abs)
    git_files.append(ead_path_rel)

    # changelog
    changelog_path_rel = 'changelog'
    changelog_messages = ['Initialized collection {}'.format(collection_uid)]
    write_changelog_entry(
        os.path.join(collection_path, changelog_path_rel),
        changelog_messages,
        user_name, user_mail, debug=debug)
    git_files.append(changelog_path_rel)

    # .gitignore
    gitignore_path_rel = '.gitignore'
    gitignore_path_abs = os.path.join(collection_path, gitignore_path_rel)
    with open(GITIGNORE_TEMPLATE, 'r') as f:
        gitignore_template = f.read()
    with open(gitignore_path_abs, 'w') as gitignore:
        gitignore.write(gitignore_template)
    git_files.append(gitignore_path_rel)
    
    # git add
    repo.index.add(git_files)
    commit = repo.index.commit(changelog_messages[0])
    # master branch should be created by this point
    
    # git annex init
    repo.git.annex('init')
    # this little dance is necessary for some reason -- see notes
    repo.git.push('origin', 'master')
    repo.git.checkout('git-annex')
    repo.git.push('origin', 'git-annex')
    repo.git.checkout('master')
    
    if debug:
        print('collection.create DONE')


@local_only
def destroy():
    """Command-line function for removing  an entire collection's files from the local system.
    
    Does not remove files from the server!  That will remain a manual operation.
    """
    if debug:
        print('destroy()')


@local_only
def status(collection_path , debug=False):
    """Command-line function for running git status on collection repository.
    """
    if debug:
        print('status({})'.format(collection_path))
    repo = git.Repo(collection_path)
    print(repo.git.status())


@local_only
def annex_status(collection_path , debug=False):
    """Command-line function for running git annex status on collection repository.
    """
    if debug:
        print('annex_status({})'.format(collection_path))
    repo = git.Repo(collection_path)
    print(repo.git.annex('status'))



@local_only
def update(user_name, user_mail, collection_path, updated_files, debug=False):
    """Command-line function for commiting changes to the specified file.
    
    NOTE: Does not push to the workbench server.
    @param updated_files List of relative paths to updated file(s).
    """
    if debug:
        print('update({}, {}, {}, {})'.format(
            user_name, user_mail, collection_path, updated_files, debug=False))
    
    repo = git.Repo(collection_path)
    repo.git.checkout('master')
    repo.git.config('user.name', user_name)
    repo.git.config('user.email', user_mail)
    
    # changelog
    changelog_path_rel = 'changelog'
    changelog_messages = []
    for f in updated_files:
        changelog_messages.append('Updated collection file(s) {}'.format(f))
    write_changelog_entry(
        os.path.join(collection_path, changelog_path_rel),
        changelog_messages,
        user_name, user_mail, debug=debug)
    updated_files.append(changelog_path_rel)
    
    # git add
    if debug:
        print('updated_files {}'.format(updated_files))
    repo.index.add(updated_files)
    commit = repo.index.commit('Updated collection file(s)')
    if debug:
        print('commit {}'.format(commit))


@requires_network
def sync(user_name, user_mail, collection_path, debug=False):
    """Command-line function for git pull/push to workbench server, git-annex sync
    
    Pulls changes from and pushes changes to the workbench server.

    For this to work properly with Gitolite, it's necessary to push/pull
    on both the master AND git-annex branches.
    Sequence:
    - fetch
    - pull on master,git-annex branches
    - push on git-annex,master branches
    
    TODO This assumes that origin is the workbench server...
    """
    if debug:
        print('sync({}, {}, {})'.format(
            user_name, user_mail, collection_path, debug=False))
    
    repo = git.Repo(collection_path)
    repo.git.checkout('master')
    repo.git.config('user.name', user_name)
    repo.git.config('user.email', user_mail)
    # fetch
    repo.git.fetch('origin')
    # pull on master,git-annex branches
    repo.git.checkout('master')
    repo.git.pull('origin', 'master')
    repo.git.checkout('git-annex')
    repo.git.pull('origin', 'git-annex')
    # push on git-annex,master branches
    repo.git.checkout('git-annex')
    repo.git.push('origin', 'git-annex')
    repo.git.checkout('master')
    repo.git.push('origin', 'master')
    # git annex sync
    repo.git.annex('sync')


@local_only
def entity_create(user_name, user_mail, collection_path, entity_uid, debug=False):
    """Command-line function for creating an entity and adding it to the collection.
    """
    if debug:
        print('entity_create({}, {})'.format(collection_path, entity_uid))
    
    collection = Collection(collection_path)
    repo = git.Repo(collection_path)
    repo.git.checkout('master')
    repo.git.config('user.name', user_name)
    repo.git.config('user.email', user_mail)
    
    # create collection files/ dir if not already present
    # mets.xml
    # control
    # changelog
    # commit
    # control
    collection_uid = os.path.basename(collection_path)

    entity_path_rel = os.path.join('files', entity_uid)
    entity_path_abs = os.path.join(collection_path, entity_path_rel)
        
    # entity dir
    if not os.path.exists(entity_path_abs):
        os.makedirs(entity_path_abs)
    
    git_files = []
    
    # entity control
    control_path_rel = os.path.join(entity_path_rel, 'control')
    control_path_abs = os.path.join(collection_path, control_path_rel)
    EntityControlFile.create(control_path_abs, collection_uid, entity_uid)
    git_files.append(control_path_rel)

    # entity mets.xml
    mets_path_rel = os.path.join(entity_path_rel, 'mets.xml')
    mets_path_abs = os.path.join(collection_path, mets_path_rel)
    METS.create(mets_path_abs)
    git_files.append(mets_path_rel)

    # entity changelog
    entity_changelog_path_rel = os.path.join(entity_path_rel, 'changelog')
    entity_changelog_messages = ['Initialized entity {}'.format(entity_uid),]
    write_changelog_entry(
        os.path.join(collection_path, entity_changelog_path_rel),
        entity_changelog_messages,
        user=user_name, email=user_mail, debug=debug)
    git_files.append(entity_changelog_path_rel)

    # update collection ead.xml
    ead = EAD(collection, debug)
    ead.update_dsc(collection)
    ead.write()
    git_files.append(ead.filename)

    # update collection changelog
    changelog_path_rel = 'changelog'
    changelog_messages = ['Initialized entity {}'.format(entity_uid),]
    write_changelog_entry(
        os.path.join(collection_path, changelog_path_rel),
        changelog_messages,
        user=user_name, email=user_mail, debug=debug)
    git_files.append(changelog_path_rel)

    # update collection control
    ctl = CollectionControlFile(os.path.join(collection.path,'control'))
    ctl.update_checksums(collection)
    ctl.write()
    git_files.append('control')
    
    # git add
    repo.index.add(git_files)
    commit = repo.index.commit(changelog_messages[0])


@local_only
def entity_destroy():
    """Command-line function for removing the specified entity from the collection.
    """
    if debug:
        print('entity_destroy()')


@local_only
def entity_update(user_name, user_mail, collection_path, entity_uid, updated_files, debug=False):
    """Command-line function for committing changes to the specified entity file.
    
    NOTE: Does not push to the workbench server.
    Updates entity changelog but NOT in collection changelog.
    Makes an entry in git log.
    @param updated_files List of paths to updated file(s), relative to entity/files.
    """
    if debug:
        print('entity_update({}, {}, {})'.format(collection_path, entity_uid, updated_files))
    
    repo = git.Repo(collection_path)
    repo.git.checkout('master')
    repo.git.config('user.name', user_name)
    repo.git.config('user.email', user_mail)

    entity_path_rel = os.path.join('files', entity_uid)
    entity_path_abs = os.path.join(collection_path, entity_path_rel)
    # entity file paths are relative to collection root
    git_files = []
    for f in updated_files:
        git_files.append( os.path.join( 'files', entity_uid, f) )
    
    # entity changelog
    entity_changelog_path_rel = os.path.join(entity_path_rel, 'changelog')
    entity_changelog_messages = []
    for f in updated_files:
        p = os.path.join(entity_uid, f)
        entity_changelog_messages.append('Updated entity file {}'.format(p))
    write_changelog_entry(
        os.path.join(collection_path, entity_changelog_path_rel),
        entity_changelog_messages,
        user=user_name, email=user_mail, debug=debug)
    git_files.append(entity_changelog_path_rel)
    
    # git add
    if debug:
        print('git_files {}'.format(git_files))
    repo.index.add(git_files)
    commit = repo.index.commit('Updated entity file(s)')


@local_only
def entity_annex_add(user_name, user_mail, collection_path, entity_uid, new_file, debug=False):
    """Command-line function for git annex add-ing a file and updating metadata.
    
    All this function does is git annex add the file, update changelog and
    mets.xml, and commit.
    It does not copy the file into the entity dir.
    It does not mark the file as master/mezzanine/access/etc or edit any metadata.
    It does not perform any background processing on the file.
    
    @param collection_path Absolute path to collection
    @param entity_uid Entity UID
    @param file_path Path to new file relative to entity files dir.
    """
    if debug:
        print('entity_annex_add({}, {}, {}, {}, {})'.format(
            user_name, user_mail, collection_path, entity_uid, new_file))
    
    repo = git.Repo(collection_path)
    repo.git.checkout('master')
    repo.git.config('user.name', user_name)
    repo.git.config('user.email', user_mail)
    
    entity_dir = os.path.join(collection_path, 'files', entity_uid)
    entity_files_dir = os.path.join(entity_dir, 'files')
    new_file_abs = os.path.join(entity_files_dir, new_file)
    # relative to collection repo
    new_file_rel = new_file_abs.replace(collection_path, '')
    # relative to entity_dir
    new_file_rel_entity = new_file_abs.replace('{}/'.format(entity_dir), '')
    if debug:
        print('new_file_abs {}'.format(new_file_abs))
        print('new_file_rel {}'.format(new_file_rel))
        print('new_file_rel_entity {}'.format(new_file_rel_entity))
    
    if not os.path.exists(entity_dir):
        print('ERR: Entity does not exist: {}'.format(entity_uid))
        sys.exit(1)
    if not os.path.exists(entity_files_dir):
        os.makedirs(entity_files_dir)
    if not os.path.exists(new_file_abs):
        print('ERR: File does not exist: {}'.format(new_file_abs))
        sys.exit(1)
    
    updated_files = []
    # update entity changelog
    entity_changelog_path_rel = os.path.join(entity_dir, 'changelog')
    changelog_messages = []
    for f in [new_file_rel_entity]:
        changelog_messages.append('Added entity file {}'.format(f))
    write_changelog_entry(
        os.path.join(collection_path, entity_changelog_path_rel),
        changelog_messages,
        user_name, user_mail, debug=debug)
    updated_files.append(entity_changelog_path_rel)
    # update entity control
    e = Entity(entity_dir)
    c = EntityControlFile(os.path.join(entity_dir,'control'))
    c.update_checksums(e)
    c.write()
    # update entity mets
    m = METS(e, debug)
    m.update_filesec(e)
    m.write()
#    # git annex add
#    repo.git.annex('add', new_file_rel)
#    # commit
#    commit = repo.index.commit('Updated entity file(s)')


@local_only
def entity_add_master(user_name, user_mail, collection_path, entity_uid, file_path, debug=False):
    """Wrapper around entity_annex_add() that 
    """
    if debug:
        print('entity_add_master()')


@local_only
def entity_add_mezzanine(user_name, user_mail, collection_path, entity_uid, file_path, debug=False):
    """
    """
    if debug:
        print('entity_add_mezzanine()')


@local_only
def entity_add_access(user_name, user_mail, collection_path, entity_uid, file_path, debug=False):
    """
    """
    if debug:
        print('entity_add_access()')


@requires_network
def annex_pull(collection_path, entity_file_path, debug=False):
    """Pull a git-annex file from workbench.

    Example file_paths:
        ddr-densho-1-1/files/video1.mov
        ddr-densho-42-17/files/image35.jpg
        ddr-one-35-248/files/newspaper.pdf
        
    @param entity_file_path Relative path to collection files dir.
    """
    pass


@requires_network
def annex_push(collection_path, entity_file_path, debug=False):
    """Push a git-annex file to workbench.

    Example file_paths:
        ddr-densho-1-1/files/video1.mov
        ddr-densho-42-17/files/image35.jpg
        ddr-one-35-248/files/newspaper.pdf
        
    @param entity_file_path Relative path to collection files dir.
    """
    pass
