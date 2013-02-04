description="""Create, edit, delete entities"""

epilog="""
More than you thought you wanted to know about the entity command.
"""



import ConfigParser
from datetime import datetime
import hashlib
import os
import shutil
import subprocess
import sys

from bs4 import BeautifulSoup
import git



class Error( Exception ):
    def __init__( self, value ):
        self.value = value
    def __str__( self ):
        return repr(self.value)



CONTROL_TEMPLATE = """[Basic]
standards-version = DDR0.1
entity = {uid}
parent = PARENT_TYPE
maintainer = MAINTAINER
uploaders = UPLOADERS
changed-by = CHANGED_BY
organization = ORGANIZATION
format = MIMETYPE

[Description]
short = DESCRIPTION_SINGLELINE
extended = DESCRIPTION_EXTENDED
	DESCRIPTION_EXTENDED_CONTINUED

[Checksums-SHA1]

[Checksums-SHA256]

[Files]"""

class ControlFile( object ):
    """control file inspired by Debian package control file but using INI syntax.
    """
    entity_path = None
    filename = None
    _config = None
    CHECKSUMS = ['sha1', 'sha256', 'files']
    
    def __init__( self, entity_path, entity_uid, debug=False ):
        self.entity_path = entity_path
        self.filename = os.path.join(self.entity_path, 'control')
        if not os.path.exists(self.filename):
            if debug:
                print('Initializing control file {} ...'.format(self.filename))
            f = open(self.filename, 'w')
            txt = CONTROL_TEMPLATE.format(uid=entity_uid)
            f.write(txt)
            f.close()
            if debug:
                print('OK')
        self.read(debug=debug)
    
    def read( self, debug=False ):
        if debug:
            print('Reading control file {} ...'.format(self.filename))
        self._config = ConfigParser.ConfigParser()
        self._config.read([self.filename])
    
    def write( self, debug=False ):
        if debug:
            print('Writing control file {} ...'.format(self.filename))
        with open(self.filename, 'w') as cfile:
            self._config.write(cfile)
    
    def update_checksums( self, entity, debug=False ):
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



METS_TEMPLATE = """<mets>
  <metsHdr></metsHdr>
  <dmdSec></dmdSec>
  <amdSec></amdSec>
  <fileSec></fileSec>
  <structMap></structMap>
  <structLink></structLink>
  <behaviorSec></behaviorSec>
</mets>"""

class METS( object ):
    """Metadata Encoding and Transmission Standard (METS) file.
    """
    entity_path = None
    filename = None
    soup = None
    
    def __init__( self, entity_path, entity_uid, debug=False ):
        self.entity_path = entity_path
        self.filename = os.path.join(self.entity_path, 'mets.xml')
        if not os.path.exists(self.filename):
            if debug:
                print('Initializing METS file {}'.format(self.filename))
            # start fresh
            now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            soup = BeautifulSoup(METS_TEMPLATE, 'xml')
            soup.mets['OBJID'] = entity_uid
            soup.mets['LABEL'] = entity_uid
            soup.mets['TYPE'] = 'unknown'
            soup.mets.metsHdr['CREATEDATE'] = now
            soup.mets.metsHdr['LASTMODDATE'] = now
            # insert mets:agent
            with open(self.filename, 'w') as mfile:
                mfile.write(soup.prettify())
            if debug:
                print('OK')
        self.read(debug=debug)
    
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




CHANGELOG_TEMPLATE = """{changes}
-- {user} <{email}>  {date}
"""
CHANGELOG_DATE_FORMAT = "%a, %d %b %Y %H:%M:%S %z"

class Changelog( object ):
    """changelog inspired by Debian package changelog file.
    """
    filename = None
    
    def __init__( self, entity_path, debug=False ):
        self.filename = os.path.join(entity_path, 'changelog')
        if not os.path.exists(self.filename):
            if debug:
                print('Initializing changelog {} ...'.format(self.filename))
            f = open(self.filename, 'w')
            f.close()
            if debug:
                print('OK')

    def write(self, messages, user, email, debug=False):
        # TODO indent multi-line messages
        msgs = []
        for m in messages:
            msgs.append('* {}'.format(m))
        changes = '\n'.join(msgs)
        entry = CHANGELOG_TEMPLATE.format(
            changes=changes, user=user, email=email,
            date=datetime.now().strftime(CHANGELOG_DATE_FORMAT))
        if os.path.getsize(self.filename):
            entry = '\n{}'.format(entry)
        with open(self.filename, 'a') as f:
            f.write(entry)



GITIGNORE = """*~
*.pyc"""

class Repo( object ):
    """
    NOTES:
    - Multiple people may work with the same repo, so author is specified on every
      commit, using the username and email from the command.
    """
    entity_path = None
    gitignore = None
    repo = None

    def __init__( self, entity_path, debug=False ):
        self.entity_path = entity_path
        self.gitignore = os.path.join(self.entity_path, '.gitignore')
        #if not os.path.exists(self.gitignore):
        #    with open(self.gitignore, 'w') as gi:
        #        gi.write(self.gitignore)
        if debug:
            print('Initializing git repo: {}'.format(self.entity_path))
        #self.repo = git.Repo(self.entity_path)

    def clone( self, entity, debug=False ):
        """Clone the git repo from Gitolite.
        """
        if debug:
            print('Repo.clone({})'.format(entity.path))
        url = 'git@mits:{}.git'.format(entity.uid)
        if debug:
            print('cloning: {}'.format(url))
        self.repo = git.Repo.clone_from(url, entity.path)
        if debug:
            print('Repo.clone() DONE')
    
    def setup( self, entity, debug=False ):
        """Add entity files and git annex to newly-initialized entity repo.
        """
        if debug:
            print('Repo.setup({})'.format(entity.path))
        # git init
        self.repo = git.Repo(entity.path)
        # there is no master branch at this point
        g = self.repo.git
        g.config('user.name', entity.user)
        g.config('user.email', entity.mail)
        # git add
        index = self.repo.index
        index.add(['control', 'mets.xml', 'changelog',])
        commit = index.commit('Initialized {}'.format(entity.uid))
        # master branch should be created by now
        os.chdir(entity.path)
        if debug:
            print(os.system('git branch'))
        os.system('git annex init')
        if debug:
            print('Repo.setup() DONE')

    def add( self, entity, payload_path, msg, debug=False ):
        """git annex add specified file, update metadata.
        
        NOTE: This method does not copy files to the entity directory!
              It adds files already in $ENTITY/files to git annex!
        @param entity Entity object
        @param payload_path Path to file inside $ENTITY, NOT INCLUDING 'files/'.
        @param msg Git commit message.
        """
        if debug:
            print('Repo.add({}, {}, "{}")'.format(entity.path, payload_path, msg))
        self.repo = git.Repo(entity.path)
        g = self.repo.git
        g.config('user.name', entity.user)
        g.config('user.email', entity.mail)
        # file path
        fpath = os.path.join('files', payload_path)
        # git annex add
        os.chdir(entity.path)
        cmd = 'git annex add {}'.format(fpath)
        if debug:
            print(cmd)
        os.system(cmd)
        # git add
        index = self.repo.index
        index.add(['control', 'mets.xml', 'changelog',])
        commit = index.commit(msg)
        if debug:
            print('Repo.add() DONE')

    def rm( self, entity, payload_path, msg, debug=False ):
        """remove specified file, update metadata.
        
        NOTES:
        - Uses regular git rm, not git annex.
        - This actually DELETES the file!
        @param entity Entity object
        @param payload_path Path to file inside $ENTITY, not including 'files/'.
        @param msg Git commit message.
        """
        if debug:
            print('Repo.rm({}, {}, "{}")'.format(entity.path, payload_path, msg))
        self.repo = git.Repo(entity.path)
        g = self.repo.git
        g.config('user.name', entity.user)
        g.config('user.email', entity.mail)
        # file path
        fpath = os.path.join('files', payload_path)
        # git rm (no annex)
        index = self.repo.index
        index.remove([fpath])
        index.add(['control', 'mets.xml', 'changelog',])
        commit = index.commit(msg)
        if debug:
            print('Repo.rm() DONE')

    def sync(self, entity, debug=False ):
        """Fetches metadata, syncs annex media data, uploads updates.
        
        NOTE: Does not pull or push git-annex media files.
        """
        os.chdir(entity.path)
        # git co master
        print( subprocess.check_output('pwd') )
        print( subprocess.check_output('cd {} && git checkout master'.format(entity.path)) )
        print( subprocess.check_output('cd {} && git fetch origin'.format(entity.path)) )
        print( subprocess.check_output('git pull origin master') )
        print( subprocess.check_output('git checkout git-annex') )
        print( subprocess.check_output('git pull origin git-annex') )
        #print( subprocess.check_output('git checkout master') )




class Entity( object ):
    user = None
    mail = None
    uid = None
    path = None
    parent = None
    control = None
    mets = None
    changelog = None
    repo = None
    
    def __init__( self, path, user, mail, uid=None, debug=False ):
        self.path = path
        if not uid:
            uid = os.path.basename(self.path)
        self.uid  = uid
        self.user = user
        self.mail = mail
        ## create directory if doesn't exist
        #if not os.path.exists(self.path):
        #    os.makedirs(self.path)
        #    if debug:
        #        print('Created directory {}'.format(self.path))
        if os.path.exists(self.path):
            self.control   = ControlFile(self.path, self.uid)
            self.mets      = METS(self.path, self.uid)
            self.changelog = Changelog(self.path)
            self.repo      = Repo(self.path, debug=debug)

    def __str__(self):
        return self.__unicode__()
    def __unicode__(self):
        return '<Entity: {}>'.format(self.uid)
    
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

    # operations exposed to the command-line tool ------------------------------
    
    @staticmethod
    def operations():
        return ['init', 'add', 'rm',]

    def initialize( self, debug=False ):
        """Create the file structure for a new Entity.
        
        @param entity_path String Absolute path to entity dir.
        """
        if debug:
            print('Initializing {}'.format(self.uid))
        # clone repo from Gitolite
        self.repo      = Repo(self.path, debug=debug)
        self.repo.clone(self, debug=debug)
        if os.path.exists(self.path):
            self.control   = ControlFile(self.path, self.uid)
            self.mets      = METS(self.path, self.uid)
            self.changelog = Changelog(self.path)
        # update metadata
        self.control.write()
        self.mets.write()
        msg = 'Initialized entity {}'.format(self.uid)
        self.changelog.write([msg], self.user, self.mail)
        self.repo.setup(self, debug=debug)
        if debug:
            print('DONE')
        
    
    def add( self, file_path, debug=False ):
        """Add a file to the Entity.
        
        @param file_path String Absolute path to file.
        @returns None for success, or String error message
        """
        if debug:
            print('Entity.add({})'.format(file_path))
        # check all the things!
        dest_path = os.path.join(self.payload_path(), os.path.basename(file_path))
        if not os.path.exists(self.path):
            raise Error('Entity does not seem to exist: {}'.format(self.path))
        if not os.path.exists(file_path):
            raise Error('File does not exist: {}'.format(file_path))
        # make payload dir if doesn't exist
        if not os.path.exists(self.payload_path()):
            os.makedirs(self.payload_path())
            if debug:
                print('Created payload directory {}'.format(self.payload_path()))
        # TODO add force overwrite option
        #if os.path.exists(dest_path):
        #    raise Error('File already copied: {}'.format(dest_path))
        # copy the file already!
        # TODO hand off to background task? show progress bar?
        if debug:
            print('copying {}'.format(file_path)) 
            print('     -> {}'.format(dest_path))
        # copy file into payload dir
        shutil.copyfile(file_path, dest_path)
        if not os.path.exists(dest_path):
            raise Error('File not copied: {}'.format(dest_path))
        else:
            if debug:
                print('Copy OK')
        # update metadata
        self.control.update_checksums(self, debug=debug)
        self.mets.update_filesec(self, debug=debug)
        self.control.write()
        self.mets.write()
        git_add_path = dest_path.replace(self.payload_path(trailing_slash=True), '')
        msg = 'Added file: {}'.format(git_add_path)
        self.changelog.write([msg], self.user, self.mail)
        # git add,commit
        self.repo.add(self, git_add_path, msg, debug=debug)
    
    def rm( self, file_path, debug=False ):
        """Remove a file from the Entity.
        
        IMPORTANT: This actually deletes the file -- there is no undo!
        @param file_path Path to file inside $ENTITY, not including 'files/'.
        @returns None for success, or String error message
        """
        if debug:
            print('Entity.rm({})'.format(file_path))
        # error checking
        if not file_path:
            raise Error('No file path.')
        rm_path = os.path.join(self.payload_path(), file_path)
        if debug:
            print("rm {}".format(rm_path))
#        if not os.path.exists(file_path):
#            raise Error('File does not exist: {}'.format(file_path))
        # remove file
        if debug:
            print('removing {}'.format(rm_path))
        os.remove(rm_path)
        # update metadata
        self.control.update_checksums(self, debug=debug)
        self.mets.update_filesec(self, debug=debug)
        self.control.write()
        self.mets.write()
        relpath = file_path.replace('{}/'.format(self.path), '')
        msg = 'Removed file: {}'.format(relpath)
        self.changelog.write([msg], self.user, self.mail)
        # git rm,commit
        self.repo.rm(self, file_path, msg, debug=debug)
        #
        if os.path.exists(rm_path):
            raise Error('File not removed: {}'.format(rm_path))
        else:
            if debug:
                print('OK')
