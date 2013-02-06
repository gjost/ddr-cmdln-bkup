from datetime import datetime
import os
import subprocess

import git



GIT_USER = 'git'
GIT_SERVER = 'mits'



CHANGELOG_TEMPLATE = """{changes}
-- {user} <{email}>  {date}
"""
CHANGELOG_DATE_FORMAT = "%a, %d %b %Y %H:%M:%S %z"


CONTROL_TEMPLATE = """[Basic]
standards-version = DDR0.1
organization = ORGANIZATION
collection = {cid}
maintainer = MAINTAINER
uploaders = UPLOADERS
changed-by = CHANGED_BY

[Description]
short = DESCRIPTION_SINGLELINE
extended = DESCRIPTION_EXTENDED
	DESCRIPTION_EXTENDED_CONTINUED

[Entities]"""


EAD_TEMPLATE = """<mets>
  <metsHdr></metsHdr>
  <dmdSec></dmdSec>
  <amdSec></amdSec>
  <fileSec></fileSec>
  <structMap></structMap>
  <structLink></structLink>
  <behaviorSec></behaviorSec>
</mets>"""


GITIGNORE_TEMPLATE = """*~
*.pyc"""


ENTITY_CONTROL_TEMPLATE = """[Basic]
standards-version = DDR0.1
organization = ORGANIZATION
parent = {cid}
entity = {eid}
maintainer = MAINTAINER
uploaders = UPLOADERS
changed-by = CHANGED_BY
format = MIMETYPE

[Description]
short = DESCRIPTION_SINGLELINE
extended = DESCRIPTION_EXTENDED
	DESCRIPTION_EXTENDED_CONTINUED

[Checksums-SHA1]

[Checksums-SHA256]

[Files]"""


ENTITY_METS_TEMPLATE = """<mets>
  <metsHdr></metsHdr>
  <dmdSec></dmdSec>
  <amdSec></amdSec>
  <fileSec></fileSec>
  <structMap></structMap>
  <structLink></structLink>
  <behaviorSec></behaviorSec>
</mets>"""




description="""Create, edit, delete collections"""

epilog="""
More than you thought you wanted to know about the collection command.
"""

OPERATIONS = [
    'create',
    'destroy',
    'update',
    'sync',
    'ecreate',
    'edestroy',
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
    if debug:
        print('cloned')
    # there is no master branch at this point
    g = repo.git
    g.config('user.name', user_name)
    g.config('user.email', user_mail)
    git_files = []

    # control
    control_path_rel = 'control'
    control_path_abs = os.path.join(collection_path, control_path_rel)
    if debug:
        print('Creating control {} ...'.format(control_path_abs))
    with open(control_path_abs, 'w') as control:
        control.write(CONTROL_TEMPLATE.format(cid=collection_uid))
    git_files.append(control_path_rel)

    # ead.xml
    ead_path_rel = 'ead.xml'
    ead_path_abs = os.path.join(collection_path, ead_path_rel)
    if debug:
        print('Creating ead.xml {} ...'.format(ead_path_abs))
    with open(ead_path_abs, 'w') as ead:
        ead.write(EAD_TEMPLATE)
    git_files.append(ead_path_rel)

    # changelog
    changelog_path_rel = 'changelog'
    changelog_path_abs = os.path.join(collection_path, changelog_path_rel)
    if debug:
        print('Creating changelog {} ...'.format(changelog_path_abs))
    changelog_messages = [
        'Initialized collection {}'.format(collection_uid),
        ]
    lines = []
    [lines.append('* {}'.format(m)) for m in changelog_messages]
    changes = '\n'.join(lines)
    entry = CHANGELOG_TEMPLATE.format(
        changes=changes, user=user_name, email=user_mail,
        date=datetime.now().strftime(CHANGELOG_DATE_FORMAT))
    with open(changelog_path_abs, 'a') as changelog:
        changelog.write(entry)
    git_files.append(changelog_path_rel)

    # .gitignore
    gitignore_path_rel = '.gitignore'
    gitignore_path_abs = os.path.join(collection_path, gitignore_path_rel)
    if debug:
        print('Creating .gitignore {} ...'.format(gitignore_path_abs))
    with open(gitignore_path_abs, 'w') as gitignore:
        gitignore.write(GITIGNORE_TEMPLATE)
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
    repo = git.Repo(collection_path)
    g = repo.git
    g.config('user.name', user_name)
    g.config('user.email', user_mail)
    # changelog
    changelog_path_rel = 'changelog'
    changelog_path_abs = os.path.join(collection_path, changelog_path_rel)
    if debug:
        print('Updating changelog {} ...'.format(changelog_path_abs))
    changelog_messages = []
    for f in updated_files:
        changelog_messages.append('Updated collection file(s) {}'.format(f))
    lines = []
    [lines.append('* {}'.format(m)) for m in changelog_messages]
    changes = '\n'.join(lines)
    entry = CHANGELOG_TEMPLATE.format(
        changes=changes, user=user_name, email=user_mail,
        date=datetime.now().strftime(CHANGELOG_DATE_FORMAT))
    with open(changelog_path_abs, 'a') as changelog:
        changelog.write('\n')
        changelog.write(entry)
    updated_files.append(changelog_path_rel)
    # git add
    index = repo.index
    index.add(updated_files)
    commit = index.commit('Updated collection file(s)')


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
    # git co master
    def run(cmd, debug=False):
        out = subprocess.check_output(cmd, shell=True)
        if debug:
            print(out)
    os.chdir(collection_path)
    run('pwd', debug=debug)
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
    entity_changelog_path_abs = os.path.join(collection_path, entity_changelog_path_rel)
    if debug:
        print('Creating entity changelog {} ...'.format(entity_changelog_path_abs))
    entity_changelog_messages = [
        'Initialized entity {}'.format(entity_uid),
        ]
    lines = []
    [lines.append('* {}'.format(m)) for m in entity_changelog_messages]
    changes = '\n'.join(lines)
    entry = CHANGELOG_TEMPLATE.format(
        changes=changes, user=user_name, email=user_mail,
        date=datetime.now().strftime(CHANGELOG_DATE_FORMAT))
    with open(entity_changelog_path_abs, 'a') as entity_changelog:
        entity_changelog.write(entry)
    git_files.append(entity_changelog_path_rel)

    # collection ead.xml

    # collection changelog
    changelog_path_rel = 'changelog'
    changelog_path_abs = os.path.join(collection_path, changelog_path_rel)
    if debug:
        print('Creating changelog {} ...'.format(changelog_path_abs))
    changelog_messages = [
        'Initialized entity {}'.format(entity_uid),
        ]
    lines = []
    [lines.append('* {}'.format(m)) for m in changelog_messages]
    changes = '\n'.join(lines)
    entry = CHANGELOG_TEMPLATE.format(
        changes=changes, user=user_name, email=user_mail,
        date=datetime.now().strftime(CHANGELOG_DATE_FORMAT))
    with open(changelog_path_abs, 'a') as changelog:
        changelog.write('\n')
        changelog.write(entry)
    git_files.append(changelog_path_rel)
    
    # git add
    repo = git.Repo(collection_path)
    g = repo.git
    g.config('user.name', user_name)
    g.config('user.email', user_mail)
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
