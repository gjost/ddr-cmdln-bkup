from datetime import datetime
import os
import subprocess
import sys

import git



GIT_USER = 'git'
GIT_SERVER = 'mits'

MODULE_PATH = os.path.join(sys.path[0])

TEMPLATE_PATH = os.path.join(MODULE_PATH, 'templates')
GITIGNORE_TEMPLATE          = os.path.join(TEMPLATE_PATH, 'gitignore.template')
CHANGELOG_TEMPLATE          = os.path.join(TEMPLATE_PATH, 'changelog.template')
CHANGELOG_DATE_FORMAT       = os.path.join(TEMPLATE_PATH, 'changelog-date.template')
COLLECTION_CONTROL_TEMPLATE = os.path.join(TEMPLATE_PATH, 'collection/control.template')
COLLECTION_EAD_TEMPLATE     = os.path.join(TEMPLATE_PATH, 'collection/ead.xml.template')
ENTITY_CONTROL_TEMPLATE     = os.path.join(TEMPLATE_PATH, 'entity/control.template' )
ENTITY_METS_TEMPLATE        = os.path.join(TEMPLATE_PATH, 'entity/mets.xml.template' )

def load_template(filename):
    template = ''
    with open(filename, 'r') as f:
        template = f.read()
    return template

def write_changelog_entry(path, messages, user, email, debug=False):
    if debug:
        print('Updating changelog {} ...'.format(path))
    template = load_template(CHANGELOG_TEMPLATE)
    date_format = load_template(CHANGELOG_DATE_FORMAT)
    # one line per message
    lines = []
    [lines.append('* {}'.format(m)) for m in messages]
    changes = '\n'.join(lines)
    # render
    entry = template.format(
        changes=changes,
        user=user,
        email=email,
        date=datetime.now().strftime(date_format)
        )
    with open(path, 'a') as changelog:
        changelog.write(entry)



description="""Create, edit, delete collections"""

epilog="""
More than you thought you wanted to know about the collection command.
"""

OPERATIONS = [
    'create',
    'destroy',
    'status',
    'update',
    'sync',
    'ecreate',
    'edestroy',
    'eupdate',
    'pull',
    'push',
    ]


def create(user_name, user_mail, collection_path, debug=False):
    """Create a new collection

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
    # TODO always start on master branch
    if debug:
        print('cloned')
    # there is no master branch at this point
    g = repo.git
    g.config('user.name', user_name)
    g.config('user.email', user_mail)
    
    g.config('gitweb.owner', '{} <{}>'.format(user_name, user_mail))
    git_files = []

    # control
    control_path_rel = 'control'
    control_path_abs = os.path.join(collection_path, control_path_rel)
    if debug:
        print('Creating control {} ...'.format(control_path_abs))
    control_template = load_template(COLLECTION_CONTROL_TEMPLATE)
    with open(control_path_abs, 'w') as control:
        control.write(control_template.format(cid=collection_uid))
    git_files.append(control_path_rel)

    # ead.xml
    ead_path_rel = 'ead.xml'
    ead_path_abs = os.path.join(collection_path, ead_path_rel)
    if debug:
        print('Creating ead.xml {} ...'.format(ead_path_abs))
    ead_template = load_template(COLLECTION_EAD_TEMPLATE)
    with open(ead_path_abs, 'w') as ead:
        ead.write(ead_template)
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
    if debug:
        print('Creating .gitignore {} ...'.format(gitignore_path_abs))
    gitignore_template = load_template(GITIGNORE_TEMPLATE)
    with open(gitignore_path_abs, 'w') as gitignore:
        gitignore.write(gitignore_template)
    git_files.append(gitignore_path_rel)
    
    # git add
    index = repo.index
    index.add(git_files)
    commit = index.commit(changelog_messages[0])
    # master branch should be created by now
    os.chdir(collection_path)
    if debug:
        print(os.system('git branch'))
    def run(cmd, debug=False):
        out = subprocess.check_output(cmd, shell=True)
        if debug:
            print(out)
    run('git annex init', debug)
    run('git push origin master', debug)
    run('git checkout git-annex', debug)
    run('git push origin git-annex', debug)
    run('git checkout master', debug)
    if debug:
        print('collection.create DONE')


def destroy():
    """
    Removes an entire collection's files from the local system.  Does not remove files from the server!  That will remain a manual operation.
    """
    pass


def status(collection_path, debug=False):
    """
    Gathers information about the status of the collection.
    """
    pass


def update(user_name, user_mail, collection_path, updated_files, debug=False):
    """
    Commits changes to the specified file.  NOTE: Does not push to the workbench server.
    @param updated_files List of relative paths to updated file(s).
    """
    if debug:
        print('update({}, {}, {}, {})'.format(
            user_name, user_mail, collection_path, updated_files, debug=False))
    
    repo = git.Repo(collection_path)
    # TODO always start on master branch
    g = repo.git
    g.config('user.name', user_name)
    g.config('user.email', user_mail)
    
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
    index = repo.index
    index.add(updated_files)
    commit = index.commit('Updated collection file(s)')
    if debug:
        print('commit {}'.format(commit))


def sync(user_name, user_mail, collection_path, debug=False):
    """git pull/push to workbench server, git-annex sync

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
        print('update({}, {}, {})'.format(
            user_name, user_mail, collection_path, debug=False))
    
    repo = git.Repo(collection_path)
    # TODO always start on master branch
    g = repo.git
    g.config('user.name', user_name)
    g.config('user.email', user_mail)
    
    def run(cmd, debug=False):
        if debug:
            print('kura.collection.sync: {}'.format(cmd))
        out = subprocess.check_output(cmd, shell=True)
        if debug:
            print(out)
    os.chdir(collection_path)
    run('pwd', debug=debug)
    # TODO git checkout master
    run('git branch', debug=debug)
    # fetch
    run('git fetch origin', debug=debug)
    # pull on master,git-annex branches
    run('git checkout master', debug=debug)
    run('git pull origin master', debug=debug)
    run('git checkout git-annex', debug=debug)
    run('git pull origin git-annex', debug=debug)
    # push on git-annex,master branches
    run('git checkout git-annex', debug=debug)
    run('git push origin git-annex', debug=debug)
    run('git checkout master', debug=debug)
    run('git push origin master', debug=debug)
    # git annex sync
    run('git annex sync', debug=debug)



def entity_create(user_name, user_mail, collection_path, entity_uid, debug=False):
    """Create an entity and add it to the collection.
    """
    repo = git.Repo(collection_path)
    # TODO always start on master branch
    g = repo.git
    g.config('user.name', user_name)
    g.config('user.email', user_mail)
    
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
    if debug:
        print('Creating control {} ...'.format(control_path_abs))
    with open(control_path_abs, 'w') as control:
        control.write(ENTITY_CONTROL_TEMPLATE.format(cid=collection_uid, eid=entity_uid))
    git_files.append(control_path_rel)

    # entity mets.xml
    mets_path_rel = os.path.join(entity_path_rel, 'mets.xml')
    mets_path_abs = os.path.join(collection_path, mets_path_rel)
    if debug:
        print('Creating mets.xml {} ...'.format(mets_path_abs))
    with open(mets_path_abs, 'w') as mets:
        mets.write(ENTITY_METS_TEMPLATE)
    git_files.append(mets_path_rel)

    # entity changelog
    entity_changelog_path_rel = os.path.join(entity_path_rel, 'changelog')
    entity_changelog_messages = ['Initialized entity {}'.format(entity_uid),]
    write_changelog_entry(
        os.path.join(collection_path, entity_changelog_path_rel),
        entity_changelog_messages,
        user=user_name, email=user_mail, debug=debug)
    git_files.append(entity_changelog_path_rel)

    # collection ead.xml

    # collection changelog
    changelog_path_rel = 'changelog'
    changelog_messages = ['Initialized entity {}'.format(entity_uid),]
    write_changelog_entry(
        os.path.join(collection_path, changelog_path_rel),
        changelog_messages,
        user=user_name, email=user_mail, debug=debug)
    git_files.append(changelog_path_rel)
    
    # git add
    index = repo.index
    index.add(git_files)
    commit = index.commit(changelog_messages[0])
    # master branch should be created by now
    os.chdir(collection_path)
    if debug:
        print(os.system('git branch'))
    def run(cmd, debug=False):
        out = subprocess.check_output(cmd, shell=True)
        if debug:
            print(out)
    run('git annex init', debug)
    run('git push origin master', debug)
    run('git checkout git-annex', debug)
    run('git push origin git-annex', debug)
    run('git checkout master', debug)
    if debug:
        print('collection.entity_create DONE')


def entity_destroy():
    """Remove the specified entity from the collection.
    """
    pass


def entity_update(user_name, user_mail, collection_path, entity_uid, updated_files, debug=False):
    """
    Commits changes to the specified file in the entity.  NOTE: Does not push to the workbench server.
    Updates entity changelog but NOT in collection changelog.
    Makes an entry in git log.
    @param updated_files List of paths to updated file(s), relative to entity/files.
    """
    repo = git.Repo(collection_path)
    # TODO always start on master branch
    g = repo.git
    g.config('user.name', user_name)
    g.config('user.email', user_mail)

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
    index = repo.index
    index.add(git_files)
    commit = index.commit('Updated entity file(s)')


def annex_pull(collection_path, entity_file_path, debug=False):
    """Pull a git-annex file from workbench.

    Example file_paths:
        ddr-densho-1-1/files/video1.mov
        ddr-densho-42-17/files/image35.jpg
        ddr-one-35-248/files/newspaper.pdf
        
    @param entity_file_path Relative path to collection files dir.
    """
    pass


def annex_push(collection_path, entity_file_path, debug=False):
    """Push a git-annex file to workbench.

    Example file_paths:
        ddr-densho-1-1/files/video1.mov
        ddr-densho-42-17/files/image35.jpg
        ddr-one-35-248/files/newspaper.pdf
        
    @param entity_file_path Relative path to collection files dir.
    """
    pass
