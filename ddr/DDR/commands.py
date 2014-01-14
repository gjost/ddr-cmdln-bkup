import ConfigParser
from datetime import datetime
from functools import wraps
import logging
import os
import re
import shutil
import sys

import envoy
import git

from DDR import CONFIG_FILE
from DDR import storage
from DDR import dvcs
from DDR.models import Collection as DDRCollection, Entity as DDREntity
from DDR.changelog import write_changelog_entry
from DDR.organization import group_repo_level, repo_level, repo_annex_get, read_group_file


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
ACCESS_FILE_APPEND = config.get('local','access_file_append')
ACCESS_FILE_EXTENSION = config.get('local','access_file_extension')

MODULE_PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(MODULE_PATH, 'templates')
GITIGNORE_TEMPLATE = os.path.join(TEMPLATE_PATH, 'gitignore.tpl')



def requires_network(f):
    """Indicate that function requires network access; check if can connect to gitolite server.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not dvcs.gitolite_connect_ok(GITOLITE):
            logging.error('Cannot connect to git server {}'.format(GITOLITE))
            return 1,'cannot connect to git server {}'.format(GITOLITE)
        return f(*args, **kwargs)
    return wrapper

def local_only(f):
    """Indicate that function requires no network access.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    return wrapper

def command(f):
    """Indicate that function is a command-line command.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        logging.debug('------------------------------------------------------------------------')
        logging.debug('{}.{}({}, {})'.format(f.__module__, f.__name__, args, kwargs))
        return f(*args, **kwargs)
    return wrapper


description="""Various commands for manipulating DDR collections and entities."""

epilog="""
More than you thought you wanted to know about the collection command.
"""

OPERATIONS = [
    'clocal',
    'create',
    'clone',
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



def commit_files(repo, message, git_files=[], annex_files=[]):
    """git-add and git-annex-add files and commit them
    
    @param repo: GitPython Repo object
    @param message: String
    @param git_files: List of filenames relative to repo root.
    @param annex_files: List of filenames relative to repo root.
    @return: GitPython Repo object
    """
    added = annex_files + git_files
    added.sort()
    logging.debug('    files added:         {}'.format(added))
    
    if annex_files:
        repo.git.annex('add', annex_files)
    if git_files:
        repo.index.add(git_files)
    
    staged = dvcs.list_staged(repo)
    staged.sort()
    logging.debug('    files staged:        {}'.format(staged))
    # TODO cancel commit if list of staged doesn't match list of files added?
    
    commit = repo.index.commit(message)
    logging.debug('    commit: {}'.format(commit.hexsha))
    
    committed = dvcs.list_committed(repo, commit)
    committed.sort()
    logging.debug('    files committed:     {}'.format(committed))
    # TODO complain if list of committed files doesn't match lists of added and staged files?
    
    return repo



#@command
@local_only
def removables():
    return 0,storage.removables()

#@command
@local_only
def removables_mounted():
    return 0,storage.removables_mounted()

@command
@local_only
def mount( device_file, label ):
    """Command-line function for mounting specified device on local system.
    """
    return 0,storage.mount(device_file, label)

@command
@local_only
def umount( device_file ):
    """Command-line function for UNmounting specified device on local system.
    """
    return 0,storage.umount(device_file)

@command
@local_only
def remount( device_file, label ):
    """Command-line function for unmounting and remounting specified device on local system.
    """
    return 0,storage.remount(device_file, label)

@command
@local_only
def mount_point( path ):
    return 0,storage.mount_point(path)

@command
@local_only
def storage_status( path ):
    return 0,storage.storage_status(path)



#@command
@local_only
def collections_local(collections_root, repository, organization):
    """Command-line function for listing collections on the local system.
    
    Looks for directories under collection_root with names matching the
    "{repository}-{organization}-*" pattern and containing ead.xml files.
    Doesn't check validity beyond that.
    
    @param collections_root: Absolute path of dir in which collections are located.
    @param repository: Repository keyword.
    @param organization: Organization keyword.
    @return: list of collection UIDs
    """
    if not (os.path.exists(collections_root) and os.path.isdir(collections_root)):
        message = '{} does not exist or is not a directory'.format(collections_root)
        raise Exception(message)
    return DDRCollection.collections(collections_root, repository, organization)


@command
@requires_network
def clone(user_name, user_mail, collection_uid, alt_collection_path):
    """Command-line function for cloning an existing collection.
    
    Clones existing collection object from workbench server.
    
    @param user_name: Username for use in changelog, git log
    @param user_mail: User email address for use in changelog, git log
    @param collection_uid: A valid DDR collection UID
    @param alt_collection_path: Absolute path to which repo will be cloned (includes collection UID)
    @return: message ('ok' if successful)
    """
    collection = DDRCollection(alt_collection_path)
    url = '{}:{}.git'.format(GITOLITE, collection_uid)
    
    repo = git.Repo.clone_from(url, alt_collection_path)
    logging.debug('    git clone {}'.format(url))
    if repo:
        logging.debug('    OK')
    else:
        logging.error('    COULD NOT CLONE!')
        return 1,'could not clone'
    if os.path.exists(os.path.join(alt_collection_path, '.git')):
        logging.debug('    .git/ is present')
    else:
        logging.error('    .git/ IS MISSING!')
        return 1,'.git/ is missing'
    # git annex init if not already existing
    if not os.path.exists(os.path.join(alt_collection_path, '.git', 'annex')):
        logging.debug('    git annex init')
        repo.git.annex('init')
    #
    repo.git.checkout('master')
    repo = dvcs.set_git_configs(repo, user_name, user_mail)
    dvcs.set_annex_description(repo)
    if not GIT_REMOTE_NAME in [r.name for r in repo.remotes]:
        repo.create_remote(GIT_REMOTE_NAME, collection.git_url)
    return 0,'ok'


@command
@requires_network
def create(user_name, user_mail, collection_path, templates, agent=''):
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
    
    @param user_name: Username for use in changelog, git log
    @param user_mail: User email address for use in changelog, git log
    @param collection_path: Absolute path to collection repo.
    @param templates: List of metadata templates (absolute paths).
    @param agent: (optional) Name of software making the change.
    @return: message ('ok' if successful)
    """
    collection = DDRCollection(collection_path)
    
    url = '{}:{}.git'.format(GITOLITE, collection.uid)
    
    repo = git.Repo.clone_from(url, collection.path)
    logging.debug('    git clone {}'.format(url))
    if repo:
        logging.debug('    OK')
    else:
        logging.error('    COULD NOT CLONE!')
    if os.path.exists(os.path.join(collection.path, '.git')):
        logging.debug('    .git/ is present')
    else:
        logging.error('    .git/ IS MISSING!')
    # there is no master branch at this point
    repo.create_remote(GIT_REMOTE_NAME, collection.git_url)
    repo = dvcs.set_git_configs(repo, user_name, user_mail)
    git_files = []
    
    # copy template files to collection
    for src in templates:
        if os.path.exists(src):
            dst = os.path.join(collection.path, os.path.basename(src))
            logging.debug('cp %s, %s' % (src, dst))
            shutil.copy(src, dst)
            if os.path.exists(dst):
                git_files.append(dst)
            else:
                logging.error('COULD NOT COPY %s' % src)
    
    # add control, .gitignore, changelog
    control   = collection.control()
    gitignore = collection.gitignore()
    
    # prep log entries
    changelog_messages = ['Initialized collection {}'.format(collection.uid)]
    if agent:
        changelog_messages.append('@agent: %s' % agent)
    commit_message = dvcs.compose_commit_message(changelog_messages[0], agent=agent)
    
    write_changelog_entry(collection.changelog_path,
                          changelog_messages,
                          user_name, user_mail)
    if os.path.exists(control.path):
        git_files.append(control.path_rel)
    else:
        logging.error('    COULD NOT CREATE control')
    if os.path.exists(collection.gitignore_path):
        git_files.append(collection.gitignore_path_rel)
    else:
        logging.error('    COULD NOT CREATE .gitignore')
    if os.path.exists(collection.changelog_path):
        git_files.append(collection.changelog_path_rel)
    else:
        logging.error('    COULD NOT CREATE changelog')
    
    # add files and commit
    repo = commit_files(repo, commit_message, git_files, [])
    # master branch should be created by this point
    # git annex init
    logging.debug('    git annex init')
    repo.git.annex('init')
    if os.path.exists(os.path.join(collection.path, '.git', 'annex')):
        logging.debug('    .git/annex/ OK')
    else:
        logging.error('    .git/annex/ IS MISSING!')
    
    # this little dance is necessary for some reason -- see notes
    logging.debug('    pushing master')
    repo.git.push('origin', 'master')
    logging.debug('    OK')
    repo.git.checkout('git-annex')
    logging.debug('    pushing git-annex')
    repo.git.push('origin', 'git-annex')
    logging.debug('    OK')
    repo.git.checkout('master')
    dvcs.set_annex_description(repo)
    return 0,'ok'


@command
@local_only
def destroy(agent=''):
    """Command-line function for removing  an entire collection's files from the local system.
    
    Does not remove files from the server!  That will remain a manual operation.
    
    @param agent: (optional) Name of software making the change.
    @return: message ('ok' if successful)
    """
    return 1,'not implemented yet'


#@command
@local_only
def status(collection_path, short=False):
    """Command-line function for running git status on collection repository.
    
    @param collection_path: Absolute path to collection repo.
    @return: message ('ok' if successful)
    """
    return dvcs.repo_status(collection_path)


@command
#@requires_network
def annex_status(collection_path):
    """Command-line function for running git annex status on collection repository.
    
    @param collection_path: Absolute path to collection repo.
    @return: message ('ok' if successful)
    """
    return dvcs.annex_status(collection_path)


@command
#@requires_network
def fetch(collection_path):
    """Command-line function for fetching latest changes to git repo from origin/master.
    
    @param collection_path: Absolute path to collection repo.
    @return: message ('ok' if successful)
    """
    return dvcs.fetch(collection_path)


@command
@local_only
def update(user_name, user_mail, collection_path, updated_files, agent=''):
    """Command-line function for commiting changes to the specified file.
    
    NOTE: Does not push to the workbench server.
    @param user_name: Username for use in changelog, git log
    @param user_mail: User email address for use in changelog, git log
    @param collection_path: Absolute path to collection repo.
    @param updated_files: List of relative paths to updated file(s).
    @param agent: (optional) Name of software making the change.
    @return: message ('ok' if successful)
    """
    collection = DDRCollection(collection_path)
    
    repo = dvcs.repository(collection.path, user_name, user_mail)
    if repo:
        logging.debug('    git repo {}'.format(collection.path))
    repo.git.checkout('master')
    if not GIT_REMOTE_NAME in [r.name for r in repo.remotes]:
        repo.create_remote(GIT_REMOTE_NAME, collection.git_url)
    
    # prep log entries
    changelog_messages = []
    for f in updated_files:
        changelog_messages.append('Updated collection file(s) {}'.format(f))
    if agent:
        changelog_messages.append('@agent: %s' % agent)
    commit_message = dvcs.compose_commit_message('Updated metadata file(s)', agent=agent)
    
    # write changelog
    write_changelog_entry(collection.changelog_path,
                          changelog_messages,
                          user_name, user_mail)
    if os.path.exists(collection.changelog_path):
        updated_files.append(collection.changelog_path)
    else:
        logging.error('    COULD NOT UPDATE changelog')
    
    # add files and commit
    repo = commit_files(repo, commit_message, updated_files, [])
    return 0,'ok'


@command
@requires_network
def sync(user_name, user_mail, collection_path):
    """Command-line function for git pull/push to workbench server, git-annex sync
    
    Pulls changes from and pushes changes to the workbench server.

    For this to work properly with Gitolite, it's necessary to push/pull
    on both the master AND git-annex branches.
    Sequence:
    - fetch
    - pull on master,git-annex branches
    - push on git-annex,master branches
    
    TODO This assumes that origin is the workbench server...
    
    @param user_name: Username for use in changelog, git log
    @param user_mail: User email address for use in changelog, git log
    @param collection_path: Absolute path to collection repo.
    @return: message ('ok' if successful)
    """
    collection = DDRCollection(collection_path)
    
    repo = dvcs.repository(collection.path, user_name, user_mail)
    repo.git.checkout('master')
    dvcs.set_annex_description(repo)
    if not GIT_REMOTE_NAME in [r.name for r in repo.remotes]:
        repo.create_remote(GIT_REMOTE_NAME, collection.git_url)
    # fetch
    repo.git.fetch('origin')
    # pull on master,git-annex branches 
    logging.debug('    git pull origin master')
    repo.git.checkout('master')
    repo.git.pull('origin', 'master')
    logging.debug('    OK')
    logging.debug('    git pull origin git-annex')
    repo.git.checkout('git-annex')
    repo.git.pull('origin', 'git-annex')
    logging.debug('    OK')
    # push on git-annex,master branches
    logging.debug('    git push origin git-annex')
    repo.git.checkout('git-annex')
    repo.git.push('origin', 'git-annex')
    logging.debug('    OK')
    logging.debug('    git push origin master')
    repo.git.checkout('master')
    repo.git.push('origin', 'master')
    logging.debug('    OK')
    # git annex sync
    logging.debug('    git annex sync')
    repo.git.annex('sync')
    logging.debug('    OK')
    return 0,'ok'


@command
@local_only
def entity_create(user_name, user_mail, collection_path, entity_uid, updated_files, templates, agent=''):
    """Command-line function for creating an entity and adding it to the collection.
    
    @param user_name: Username for use in changelog, git log
    @param user_mail: User email address for use in changelog, git log
    @param collection_path: Absolute path to collection repo.
    @param entity_uid: A valid DDR entity UID
    @param updated_files: List of updated files (relative to collection root).
    @param templates: List of entity metadata templates (absolute paths).
    @param agent: (optional) Name of software making the change.
    @return: message ('ok' if successful)
    """
    collection = DDRCollection(collection_path)
    entity = DDREntity(collection.entity_path(entity_uid))
    
    repo = dvcs.repository(collection.path, user_name, user_mail)
    repo.git.checkout('master')
    if not GIT_REMOTE_NAME in [r.name for r in repo.remotes]:
        repo.create_remote(GIT_REMOTE_NAME, collection.git_url)
    git_files = []
    
    # entity dir
    if not os.path.exists(entity.path):
        os.makedirs(entity.path)
    
    # copy template files to entity
    for src in templates:
        if os.path.exists(src):
            dst = os.path.join(entity.path, os.path.basename(src))
            logging.debug('cp %s, %s' % (src, dst))
            shutil.copy(src, dst)
            if os.path.exists(dst):
                git_files.append(dst)
            else:
                logging.error('COULD NOT COPY %s' % src)
    
    # entity control, changelog
    econtrol = entity.control()
    entity_changelog_messages = ['Initialized entity {}'.format(entity.uid),]
    write_changelog_entry(entity.changelog_path,
                          entity_changelog_messages,
                          user=user_name, email=user_mail)
    if os.path.exists(econtrol.path):
        git_files.append(econtrol.path)
    else:
        logging.error('    COULD NOT CREATE control')
    if os.path.exists(entity.changelog_path):
        git_files.append(entity.changelog_path)
    else:
        logging.error('    COULD NOT CREATE changelog')
    
    # add updated collection files
    for src in updated_files:
        git_files.append(src)
    
    # update collection control
    ccontrol = collection.control()
    ccontrol.update_checksums(collection)
    ccontrol.write()
    
    # prep log entries
    changelog_messages = ['Initialized entity {}'.format(entity.uid),]
    if agent:
        changelog_messages.append('@agent: %s' % agent)
    commit_message = dvcs.compose_commit_message(changelog_messages[0], agent=agent)
    
    # write changelog
    write_changelog_entry(collection.changelog_path,
                          changelog_messages,
                          user=user_name, email=user_mail)
    git_files.append(ccontrol.path)
    git_files.append(collection.changelog_path)
    
    # add files and commit
    repo = commit_files(repo, commit_message, git_files, [])
    return 0,'ok'


@command
@local_only
def entity_destroy(agent=''):
    """Command-line function for removing the specified entity from the collection.
    
    @param agent: (optional) Name of software making the change.
    @return: message ('ok' if successful)
    """
    return 1,'not implemented yet'


@command
@local_only
def entity_update(user_name, user_mail, collection_path, entity_uid, updated_files, agent=''):
    """Command-line function for committing changes to the specified entity file.
    
    NOTE: Does not push to the workbench server.
    Updates entity changelog but NOT in collection changelog.
    Makes an entry in git log.
    
    @param user_name: Username for use in changelog, git log
    @param user_mail: User email address for use in changelog, git log
    @param collection_path: Absolute path to collection repo.
    @param entity_uid: A valid DDR entity UID
    @param updated_files: List of paths to updated file(s), relative to entitys.
    @param agent: (optional) Name of software making the change.
    @return: message ('ok' if successful)
    """
    collection = DDRCollection(collection_path)
    entity = DDREntity(collection.entity_path(entity_uid))
    
    repo = dvcs.repository(collection.path, user_name, user_mail)
    repo.git.checkout('master')
    if not GIT_REMOTE_NAME in [r.name for r in repo.remotes]:
        repo.create_remote(GIT_REMOTE_NAME, collection.git_url)
    
    # entity file paths are relative to collection root
    git_files = []
    for f in updated_files:
        git_files.append( os.path.join( 'files', entity.uid, f) )
    
    # entity changelog
    entity_changelog_messages = []
    for f in updated_files:
        p = os.path.join(entity.uid, f)
        entity_changelog_messages.append('Updated entity file {}'.format(p))

    # prep log entries
    if agent:
        entity_changelog_messages.append('@agent: %s' % agent)
    commit_message = dvcs.compose_commit_message('Updated entity file(s)', agent=agent)
    
    write_changelog_entry(entity.changelog_path,
                          entity_changelog_messages,
                          user=user_name, email=user_mail)
    git_files.append(entity.changelog_path_rel)
    # add files and commit
    repo = commit_files(repo, commit_message, git_files, [])
    return 0,'ok'


@command
@local_only
def entity_annex_add(user_name, user_mail, collection_path, entity_uid, updated_files, new_annex_files, agent=''):
    """Command-line function for git annex add-ing a file and updating metadata.
    
    All this function does is git annex add the file, update changelog and
    mets.xml, and commit.
    It does not copy the file into the entity dir.
    It does not mark the file as master/mezzanine/access/etc or edit any metadata.
    It does not perform any background processing on the file.
    
    @param user_name: Username for use in changelog, git log
    @param user_mail: User email address for use in changelog, git log
    @param collection_path: Absolute path to collection repo.
    @param entity_uid: A valid DDR entity UID
    @param updated_files: list of paths to updated files (relative to collection repo).
    @param new_annex_files: List of paths to new files (relative to entity files dir).
    @param agent: (optional) Name of software making the change.
    @return: message ('ok' if successful)
    """
    collection = DDRCollection(collection_path)
    entity = DDREntity(collection.entity_path(entity_uid))
    
    repo = dvcs.repository(collection.path, user_name, user_mail)
    repo.git.checkout('master')
    if not GIT_REMOTE_NAME in [r.name for r in repo.remotes]:
        repo.create_remote(GIT_REMOTE_NAME, collection.git_url)
    git_files = []
    annex_files = []
    
    if not os.path.exists(collection.annex_path):
        logging.error('    .git/annex IS MISSING!')
        return 1,'.git/annex IS MISSING!'
    if not os.path.exists(entity.path):
        logging.error('    Entity does not exist: {}'.format(entity.uid))
        return 1,'entity does not exist: {}'.format(entity.uid)
    if not os.path.exists(entity.files_path):
        logging.error('    Entity files_path does not exist: {}'.format(entity.uid))
        return 1,'entity files_path does not exist: {}'.format(entity.uid)
    
    # new annex files
    new_files_rel_entity = []
    for new_file in new_annex_files:
        # paths: absolute, relative to collection repo, relative to entity_dir
        new_file_abs = os.path.join(entity.files_path, new_file)
        if not os.path.exists(new_file_abs):
            logging.error('    File does not exist: {}'.format(new_file_abs))
            return 1,'File does not exist: {}'.format(new_file_abs)
        new_file_rel = os.path.join(entity.files_path_rel, new_file)
        new_file_rel_entity = new_file_abs.replace('{}/'.format(entity.path), '')
        new_files_rel_entity.append(new_file_rel_entity)
        annex_files.append(new_file_rel)
    
    # updated files
    [git_files.append(updated_file) for updated_file in updated_files]
    
    # update entity control
    econtrol = entity.control()
    econtrol.update_checksums(entity)
    econtrol.write()
    git_files.append(econtrol.path_rel)
    
    # prep log entries
    changelog_messages = ['Added entity file {}'.format(f) for f in new_files_rel_entity]
    if agent:
        changelog_messages.append('@agent: %s' % agent)
    commit_message = dvcs.compose_commit_message('Added entity file(s)', agent=agent)
    
    # update entity changelog
    write_changelog_entry(entity.changelog_path,
                          changelog_messages,
                          user_name, user_mail)
    git_files.append(entity.changelog_path_rel)
    
    # add files and commit
    repo = commit_files(repo, commit_message, git_files, annex_files)
    return 0,'ok'


@command
@requires_network
def annex_push(collection_path, file_path_rel):
    """Push a git-annex file to workbench.

    Example file_paths:
        ddr-densho-1-1/files/video1.mov
        ddr-densho-42-17/files/image35.jpg
        ddr-one-35-248/files/newspaper.pdf
    
    $ git annex copy PATH --to=REMOTE
    
    @param collection_path: Absolute path to collection repo.
    @param file_path_rel: Path to file relative to collection root
    @return: message ('ok' if successful)
    """
    collection = DDRCollection(collection_path)
    file_path_abs = os.path.join(collection.path, file_path_rel)
    logging.debug('    collection.path {}'.format(collection.path))
    logging.debug('    file_path_rel {}'.format(file_path_rel))
    logging.debug('    file_path_abs {}'.format(file_path_abs))
    if not os.path.exists(collection.path):
        logging.error('    NO COLLECTION AT {}'.format(collection.path))
        return 1,'no collection'
    if not os.path.exists(collection.annex_path):
        logging.error('    NO GIT ANNEX AT {}'.format(collection.annex_path))
        return 1,'no annex'
    if not os.path.exists(file_path_abs):
        logging.error('    NO FILE AT {}'.format(file_path_abs))
        return 1,'no file'
    # let's do this thing
    repo = dvcs.repository(collection.path, user_name, user_mail)
    repo.git.checkout('master')
    if not GIT_REMOTE_NAME in [r.name for r in repo.remotes]:
        repo.create_remote(GIT_REMOTE_NAME, collection.git_url)
    logging.debug('    git annex copy -t {} {}'.format(GIT_REMOTE_NAME, file_path_rel))
    stdout = repo.git.annex('copy', '-t', GIT_REMOTE_NAME, file_path_rel)
    logging.debug('\n{}'.format(stdout))
    # confirm that it worked
    remotes = dvcs.annex_whereis_file(repo, file_path_rel)
    logging.debug('    present in remotes {}'.format(remotes))
    logging.debug('    it worked: {}'.format(GIT_REMOTE_NAME in remotes))
    logging.debug('    DONE')
    return 0,'ok'


@command
@requires_network
def annex_pull(collection_path, file_path_rel):
    """git-annex copy a file from workbench.

    Example file_paths:
        ddr-densho-1-1/files/video1.mov
        ddr-densho-42-17/files/image35.jpg
        ddr-one-35-248/files/newspaper.pdf
        
    @param collection_path: Absolute path to collection repo.
    @param file_path_rel: Path to file relative to collection root.
    @return: message ('ok' if successful)
    """
    collection = DDRCollection(collection_path)
    file_path_abs = os.path.join(collection.path, file_path_rel)
    logging.debug('    collection.path {}'.format(collection.path))
    logging.debug('    file_path_rel {}'.format(file_path_rel))
    logging.debug('    file_path_abs {}'.format(file_path_abs))
    if not os.path.exists(collection.path):
        logging.error('    NO COLLECTION AT {}'.format(collection.path))
        return 1,'no collection'
    if not os.path.exists(collection.annex_path):
        logging.error('    NO GIT ANNEX AT {}'.format(collection.annex_path))
        return 1,'no annex'
    # let's do this thing
    repo = dvcs.repository(collection.path, user_name, user_mail)
    repo.git.checkout('master')
    if not GIT_REMOTE_NAME in [r.name for r in repo.remotes]:
        repo.create_remote(GIT_REMOTE_NAME, collection.git_url)
    logging.debug('    git annex copy -t {} {}'.format(GIT_REMOTE_NAME, file_path_rel))
    stdout = repo.git.annex('copy', '-f', GIT_REMOTE_NAME, file_path_rel)
    logging.debug('\n{}'.format(stdout))
    # confirm that it worked
    exists = os.path.exists(file_path_abs)
    lexists = os.path.lexists(file_path_abs)
    islink = os.path.islink(file_path_abs)
    itworked = (exists and lexists and islink)
    logging.debug('    it worked: {}'.format(itworked))
    logging.debug('    DONE')
    return 0,'ok'


@command
@local_only
def sync_group(groupfile, local_base, local_name, remote_base, remote_name):
    """
    """
    logging.debug('reading group file: %s' % groupfile)
    repos = read_group_file(groupfile)
    ACCESS_SUFFIX = ACCESS_FILE_APPEND + ACCESS_FILE_EXTENSION
    
    def logif(txt):
        t = txt.strip()
        if t:
            logging.debug(t)
    
    for r in repos:
        repo_path = os.path.join(local_base, r['id'])
        logging.debug('- - - - - - - - - - - - - - - - - - - - - - - - - - - - - -')
        logging.debug('repo_path: %s' % repo_path)
        
        # clone/update
        if os.path.exists(repo_path):
            logging.debug('updating %s' % repo_path)
            repo = dvcs.repository(repo_path)
            repo.git.fetch('origin')
            repo.git.checkout('master')
            repo.git.pull('origin', 'master')
            repo.git.checkout('git-annex')
            repo.git.pull('origin', 'git-annex')
            repo.git.checkout('master')
            logging.debug('ok')
        else:
            url = '%s:%s.git' % (GITOLITE, r['id'])
            logging.debug('cloning %s' % url)
            repo = git.Repo.clone_from(url, r['id'])
            repo.git.config('annex.sshcaching', 'false')
            logging.debug('ok')
        
        # add/update remotes
        def add_remote(repo_path, remote_name, remote_path):
            repo = git.Repo(repo_path)
            if remote_name in [rem.name for rem in repo.remotes]:
                logging.debug('remote exists: %s %s' % (remote_name, remote_path))
            else:
                logging.debug(repo_path)
                logging.debug('remote add %s %s' % (remote_name, remote_path))
                repo.create_remote(remote_name, remote_path)
                logging.debug('ok')
        remote_path = os.path.join(remote_base, r['id'])
        add_remote(repo_path, remote_name, remote_path) # local -> remote
        add_remote(remote_path, local_name, repo_path)  # remote -> local
        
        # annex sync
        logging.debug('annex sync')
        response = repo.git.annex('sync')
        logif(response)
        
        # annex get
        level = r['level']
        logging.debug('level: %s' % level)
        if level == 'access':
            for root, dirs, files in os.walk(repo_path):
                if '.git' in dirs: # exclude .git dir
                    dirs.remove('.git')
                for f in files:
                    if f.endswith(ACCESS_SUFFIX):
                        path_rel = os.path.join(root, f).replace(repo_path, '')[1:]
                        response = repo.git.annex('get', path_rel)
                        logif(response)
        elif level == 'all':
            logging.debug('git annex get .')
            response = repo.git.annex('get', '.')
            logif(response)
        logging.debug('DONE')
        
    return 0,'ok'
