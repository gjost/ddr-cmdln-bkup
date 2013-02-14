import ConfigParser
from datetime import datetime
import hashlib
import os
import subprocess
import sys

from bs4 import BeautifulSoup
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
    try:
        preexisting = os.path.getsize(path)
    except:
        preexisting = False
    with open(path, 'a') as changelog:
        if preexisting:
            changelog.write('\n')
        changelog.write(entry)


class ControlFile( object ):
    """control file inspired by Debian package control file but using INI syntax.
    """
    path = None
    _config = None
    CHECKSUMS = ['sha1', 'sha256', 'files']
    
    def __init__( self, path, debug=False ):
        self.path = path
        if not os.path.exists(self.path):
            print('ERR: control file not initialized')
            sys.exit(1)
        self.read(debug=debug)
    
    def read( self, debug=False ):
        if debug:
            print('Reading control file {} ...'.format(self.path))
        self._config = ConfigParser.ConfigParser()
        self._config.read([self.path])
    
    def write( self, debug=False ):
        if debug:
            print('Writing control file {} ...'.format(self.path))
        with open(self.path, 'w') as cfile:
            self._config.write(cfile)
    
    def entity_update_checksums( self, entity, debug=False ):
        # return relative path to payload
        def relative_path(entity_path, payload_file):
            if entity_path[-1] != '/':
                entity_path = '{}/'.format(entity_path)
            return payload_file.replace(entity_path, '')
        
        self._config.remove_section('Checksums-SHA1')
        self._config.add_section('Checksums-SHA1')
        for sha1,path in entity.checksums('sha1', debug=debug):
            path = relative_path(entity.path, path)
            self._config.set('Checksums-SHA1', sha1, path)
        #
        self._config.remove_section('Checksums-SHA256')
        self._config.add_section('Checksums-SHA256')
        for sha256,path in entity.checksums('sha256', debug=debug):
            path = relative_path(entity.path, path)
            self._config.set('Checksums-SHA256', sha256, path)
        #
        self._config.remove_section('Files')
        self._config.add_section('Files')
        for md5,path in entity.checksums('md5', debug=debug):
            size = os.path.getsize(path)
            path = relative_path(entity.path, path)
            self._config.set('Files', md5, '{} ; {}'.format(size,path))


class EAD( object ):
    """Encoded Archival Description (EAD) file.
    """
    collection_path = None
    filename = None
    soup = None
    
    def __init__( self, collection, debug=False ):
        self.collection_path = collection.path
        self.filename = os.path.join(self.collection_path, 'ead.xml')
        self.read(debug=debug)
        if debug:
            print(self.soup.prettify())
    
    def read( self, debug=False ):
        if debug:
            print('Reading EAD file {}'.format(self.filename))
        with open(self.filename, 'r') as e:
            self.soup = BeautifulSoup(e, 'xml')
    
    def write( self, debug=False ):
        if debug:
            print('Writing EAD file {}'.format(self.filename))
        with open(self.filename, 'w') as e:
            e.write(self.soup.prettify())
    
    def update_dsc( self, collection, debug=False ):
        """
        <dsc type="combined">
          <head>Inventory</head>
          <c01>
            <did>
              <unittitle eid="{eid}">{title}</unittitle>
            </did>
          </c01>
        </dsc>
        """
        # TODO keep as much existing <dsc> data as possible!
        dsc = self.soup.new_tag('dsc')
        self.soup.dsc.replace_with(dsc)
        head = self.soup.new_tag('head', contents='Inventory')
        for entity in collection.entities(debug=debug):
            n = n + 1
            # add c01, did, unittitle
            c01 = self.soup.new_tag('c01')
            did = self.soup.new_tag('did')
            unittitle = self.soup.new_tag('unittitle', eid=entity.eid, contents=entity.description.short)
            self.soup.dsc.append(c01)
            self.soup.dsc.append(did)
            self.soup.dsc.append(unittitle)


class METS( object ):
    """Metadata Encoding and Transmission Standard (METS) file.
    """
    entity_path = None
    filename = None
    soup = None
    
    def __init__( self, entity, debug=False ):
        self.entity_path = entity.path
        self.filename = os.path.join(self.entity_path, 'mets.xml')
        self.read(debug=debug)
        if debug:
            print(self.soup.prettify())
    
    def read( self, debug=False ):
        if debug:
            print('Reading METS file {}'.format(self.filename))
        with open(self.filename, 'r') as mfile:
            self.soup = BeautifulSoup(mfile, 'xml')
    
    def write( self, debug=False ):
        if debug:
            print('Writing METS file {}'.format(self.filename))
        with open(self.filename, 'w') as mfile:
            mfile.write(self.soup.prettify())
    
    def update_filesec( self, entity, debug=False ):
        """
        <fileSec>
          <fileGrp USE="master">
            <file GROUPID="GID1" ID="FID1" ADMID="AMD1" SEQ="1" MIMETYPE="image/tiff" CHECKSUM="80172D87C6A762C0053CAD9215AE2535" CHECKSUMTYPE="MD5">
              <FLocat LOCTYPE="OTHER" OTHERLOCTYPE="fileid" xlink:href="1147733144860875.tiff"/>
            </file>
          </fileGrp>
          <fileGrp USE="usecopy">
            <file GROUPID="GID1" ID="FID2" ADMID="AMD2" SEQ="1" MIMETYPE="image/jpeg" CHECKSUM="4B02150574E1B321B526B095F82BBA0E" CHECKSUMTYPE="MD5">
              <FLocat LOCTYPE="OTHER" OTHERLOCTYPE="fileid" xlink:href="1147733144860875.jpg"/>
            </file>
          </fileGrp>
        </fileSec>
        """
        payload_path = entity.payload_path()
        
        # return relative path to payload
        def relative_path(entity_path, payload_file):
            if entity_path[-1] != '/':
                entity_path = '{}/'.format(entity_path)
            return payload_file.replace(entity_path, '')
        n = 0
        # remove existing files
        filesec = self.soup.new_tag('fileSec')
        self.soup.fileSec.replace_with(filesec)
        # add new ones
        for md5,path in entity.checksums('md5', debug=debug):
            n = n + 1
            use = 'unknown'
            seq = n
            gid = 'GID{}'.format(n)
            fid = 'FID{}'.format(n)
            aid = 'AMD{}'.format(n)
            mimetype = 'mimetype'
            path = relative_path(entity.path, path)
            # add fileGrp, file, Floca
            fileGrp = self.soup.new_tag('fileGrp', USE='master')
            self.soup.fileSec.append(fileGrp)
            f = self.soup.new_tag('file',
                                  GROUPID=gid, ID=fid, ADMID=aid, SEQ=seq, MIMETYPE=mimetype,
                                  CHECKSUM=md5, CHECKSUMTYPE='md5')
            fileGrp.append(f)
            flocat = self.soup.new_tag('Flocat',
                                       LOCTYPE='OTHER', OTHERLOCTYPE='fileid',
                                       href=path)
            f.append(flocat)


class Entity( object ):
    path = None
    
    def __init__( self, path, uid=None, debug=False ):
        self.path = path
        if not uid:
            uid = os.path.basename(self.path)
        self.uid  = uid
    
    def payload_path( self, trailing_slash=False ):
        p = os.path.join(self.path, 'files')
        if trailing_slash:
            p = '{}/'.format(p)
        return p
    
    def files( self ):
        """Returns relative paths to payload files."""
        files = []
        entity_path = self.path
        if entity_path[-1] != '/':
            entity_path = '{}/'.format(entity_path)
        for f in os.listdir(self.payload_path()):
            files.append(f.replace(entity_path, ''))
        return files

    @staticmethod
    def checksum_algorithms():
        return ['md5', 'sha1', 'sha256']
    
    def checksums( self, algo, debug=False ):
        checksums = []
        def file_checksum( path, algo, block_size=1024 ):
            if algo == 'md5':
                h = hashlib.md5()
            elif algo == 'sha1':
                h = hashlib.sha1()
            else:
                return None
            f = open(path, 'rb')
            while True:
                data = f.read(block_size)
                if not data:
                    break
                h.update(data)
            f.close()
            return h.hexdigest()
        if algo not in Entity.checksum_algorithms():
            raise Error('BAD ALGORITHM CHOICE: {}'.format(algo))
        for f in self.files():
            fpath = os.path.join(self.payload_path(), f)
            cs = file_checksum(fpath, algo)
            if cs:
                checksums.append( (cs, fpath) )
        return checksums



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
    'eadd',
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
    control_template = load_template(ENTITY_CONTROL_TEMPLATE)
    with open(control_path_abs, 'w') as control:
        control.write(control_template.format(cid=collection_uid, eid=entity_uid))
    git_files.append(control_path_rel)

    # entity mets.xml
    mets_path_rel = os.path.join(entity_path_rel, 'mets.xml')
    mets_path_abs = os.path.join(collection_path, mets_path_rel)
    if debug:
        print('Creating mets.xml {} ...'.format(mets_path_abs))
    mets_template = load_template(ENTITY_METS_TEMPLATE)
    with open(mets_path_abs, 'w') as mets:
        mets.write(mets_template)
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
    ead = EAD(e, debug)
    ead.update_dsc(e)
    ead.write()

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


def entity_annex_add(user_name, user_mail, collection_path, entity_uid, new_file, debug=False):
    """git annex add a file, update changelog and mets,xml.
    
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
    # TODO always start on master branch
    g = repo.git
    g.config('user.name', user_name)
    g.config('user.email', user_mail)
    
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
    
    def run(cmd, debug=False):
        out = subprocess.check_output(cmd, shell=True)
        if debug:
            print(out)
    os.chdir(collection_path)
    run('git checkout master', debug)
    
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
    c = ControlFile(os.path.join(entity_dir,'control'))
    c.entity_update_checksums(e)
    c.write()
    # update entity mets
    m = METS(e, debug)
    m.update_filesec(e)
    m.write()
    # git annex add
    #add_cmd = 'git annex add {}'.format(new_file_rel)
    #run(add_cmd, debug)
    # commit

def entity_add_master(user_name, user_mail, collection_path, entity_uid, file_path, debug=False):
    """Wrapper around entity_annex_add() that 
    """

def entity_add_mezzanine(user_name, user_mail, collection_path, entity_uid, file_path, debug=False):
    """
    """
    pass

def entity_add_access(user_name, user_mail, collection_path, entity_uid, file_path, debug=False):
    """
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
