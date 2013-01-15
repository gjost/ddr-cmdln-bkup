#!/usr/bin/env python



description="""Create, edit, delete entities"""

epilog="""
More than you thought you wanted to know about the entity command.
"""



import argparse
import configparser
from datetime import datetime
import hashlib
import os
import shutil
import sys



class Error( Exception ):
    def __init__( self, value ):
        self.value = value
    def __str__( self ):
        return repr(self.value)



ENTITY_OPERATIONS = ['init', 'add', 'rm', 'validate']

class Entity( object ):
    uid = None
    path = None
    parent = None
    
    def __init__( self, path, uid=None ):
        self.path = path
        if not uid:
            uid = os.path.basename(self.path)
        self.uid = uid

    def __str__(self):
        return self.__unicode__()
    def __unicode__(self):
        return '<Entity: {}>'.format(self.uid)
    
    def payload_path( self ):
        return os.path.join(self.path, 'files')
    
    def files( self ):
        """Returns relative paths to payload files."""
        files = []
        entity_path = self.path
        if entity_path[-1] != '/':
            entity_path = '{}/'.format(entity_path)
        for f in os.listdir(self.payload_path()):
            files.append(f.replace(entity_path, ''))
        return files

    CHECKSUM_ALGORITHMS = ['md5', 'sha1', 'sha256']
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
        if algo not in CHECKSUM_ALGORITHMS:
            raise Error('BAD ALGORITHM CHOICE: {}'.format(algo))
        for f in self.files():
            fpath = os.path.join(self.payload_path(), f)
            cs = file_checksum(fpath, algo)
            if cs:
                checksums.append( (cs, fpath) )
        return checksums

    def initialize( self, debug=False ):
        """Create the file structure for a new Entity.
        
        @param entity_path String Absolute path to entity dir.
        """
        # create directory if doesn't exist
        if not os.path.exists(self.path):
            os.makedirs(self.path)
            if debug:
                print('Created directory {}'.format(self.path))
        # make payload dir if doesn't exist
        if not os.path.exists(self.payload_path()):
            os.makedirs(self.payload_path())
            if debug:
                print('Created payload directory {}'.format(self.payload_path()))
        # update metadata
        controlfile = ControlFile(self, debug=debug)
        controlfile.write()
        changelog = Changelog(self, debug=debug)
        msg = 'Initialized entity {}'.format(self.uid)
        changelog.write([msg], 'username', 'user@example.com')
    
    def add( self, file_path, debug=False ):
        """Add a file to the Entity.
        
        @param file_path String Absolute path to file.
        @returns None for success, or String error message
        """
        controlfile = ControlFile(self)
        # check all the things!
        dest_path = os.path.join(self.payload_path(), os.path.basename(file_path))
        if not os.path.exists(self.path):
            raise Error('Entity does not seem to exist: {}'.format(self.path))
        if not os.path.exists(file_path):
            raise Error('File does not exist: {}'.format(file_path))
        if not os.path.exists(self.payload_path()):
            raise Error('Files directory does not exist: {}'.format(self.payload_path()))
        # TODO add force overwrite option
        #if os.path.exists(dest_path):
        #    raise Error('File already copied: {}'.format(dest_path))
        # copy the file already!
        # TODO hand off to background task? show progress bar?
        if debug:
            print('copying {}'.format(file_path)) 
            print('     -> {}'.format(dest_path)) 
        shutil.copyfile(file_path, dest_path)
        if not os.path.exists(dest_path):
            raise Error('File not copied: {}'.format(dest_path))
        else:
            if debug:
                print('OK')
        # update metadata
        controlfile.update_checksums(debug=debug)
        controlfile.write(debug=debug)
        changelog = Changelog(self, debug=debug)
        msg = 'Added file: {}'.format(file_path)
        changelog.write([msg], 'username', 'user@example.com')
    
    def rm( self, file_path=None, debug=False ):
        """Remove a file from the Entity.
        
        @param file_path String Path to file, relative to Entity root.
        @returns None for success, or String error message
        """
        controlfile = ControlFile(self)
        # error checking
        if not file_path:
            raise Error('No file path.')
        rm_path = os.path.join(self.payload_path(), file_path)
        if debug:
            print("rm {}".format(rm_path))
        if not os.path.exists(file_path):
            raise Error('File does not exist: {}'.format(file_path))
        # remove file
        if debug:
            print('removing {}'.format(rm_path))
        os.remove(rm_path)
        if os.path.exists(rm_path):
            raise Error('File not removed: {}'.format(rm_path))
        else:
            if debug:
                print('OK')
        # update metadata
        controlfile.update_checksums(debug=debug)
        controlfile.write(debug=debug)
        changelog = Changelog(self, debug=debug)
        msg = 'Removed file: {}'.format(file_path)
        changelog.write([msg], 'username', 'user@example.com')

    def validate( self, debug=False ):
        """Run validator tool on this Entity, return results.
        """
        if debug:
            print("validate('{}')".format(self.path))
        # error checking
        if not os.path.exists(self.path):
            raise Error('Entity does not seem to exist: {}'.format(self.path))
        # OK GO
        # validate entity
        # write to log



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
    entity = None
    entity_path = None
    filename = None
    _config = None
    CHECKSUMS = ['sha1', 'sha256', 'files']
    
    def __init__( self, entity, debug=False ):
        self.entity = entity
        self.entity_path = self.entity.path
        self.filename = os.path.join(self.entity_path, 'control')
        if not os.path.exists(self.filename):
            if debug:
                print('Initializing control file {} ...'.format(self.filename))
            f = open(self.filename, 'w')
            txt = CONTROL_TEMPLATE.format(uid=self.entity.uid)
            f.write(txt)
            f.close()
            if debug:
                print('OK')
        self.read(debug=debug)
    
    def read( self, debug=False ):
        if debug:
            print('Reading control file {} ...'.format(self.filename))
        self._config = configparser.ConfigParser()
        self._config.read([self.filename])
    
    def write( self, debug=False ):
        if debug:
            print('Writing control file {} ...'.format(self.filename))
        with open(self.filename, 'w') as cfile:
            self._config.write(cfile)
    
    def update_checksums( self, debug=False ):
        files = self.entity.files()
        payload_path = self.entity.payload_path()

        # return relative path to payload
        def relative_path(entity_path, payload_file):
            if entity_path[-1] != '/':
                entity_path = '{}/'.format(entity_path)
            return payload_file.replace(entity_path, '')
        
        self._config['Checksums-SHA1'] = {}
        for sha1,path in self.entity.checksums('sha1', debug=debug):
            path = relative_path(self.entity.path, path)
            self._config['Checksums-SHA1'][sha1] = path
        #
        self._config['Checksums-SHA256'] = {}
        for sha256,path in self.entity.checksums('sha256', debug=debug):
            path = relative_path(self.entity.path, path)
            self._config['Checksums-SHA256'][sha256] = path
        #
        self._config['Files'] = {}
        for md5,path in self.entity.checksums('md5', debug=debug):
            size = os.path.getsize(path)
            path = relative_path(self.entity.path, path)
            self._config['Files'][md5] = '{} ; {}'.format(size,path)



CHANGELOG_TEMPLATE = """{changes}
-- {user} <{email}>  {date}
"""
CHANGELOG_DATE_FORMAT = "%a, %d %b %Y %H:%M:%S %z"

class Changelog( object ):
    """changelog inspired by Debian package changelog file.
    """
    entity = None
    filename = None
    
    def __init__( self, entity, debug=False ):
        self.entity = entity
        self.filename = os.path.join(self.entity.path, 'changelog')
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

        

# command-line interface

def main():
    parser = argparse.ArgumentParser(description=description, epilog=epilog)
    # no positional arguments
    parser.add_argument('-o', '--operation', choices=ENTITY_OPERATIONS,
                        help='Operation to perform (init, add, remove, validate).')
    parser.add_argument('-e', '--entity',
                        help='Path to an entity')
    parser.add_argument('-f', '--file',
                        help='File to be added/removed to/from an entity.')
    parser.add_argument('-u', '--user',
                        help='User who is performing the change.')
    parser.add_argument('-m', '--mail',
                        help='Email of user.')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Debug; prints lots of debug info.')
    args = parser.parse_args()

    if args.debug:
        print(args)
    if not args.operation:
        raise Error('Choose an operation!')
    
    # do something
    e = Entity(args.entity)
    if   args.operation == 'init':     e.initialize(debug=args.debug)
    elif args.operation == 'add':      e.add(file_path=args.file, debug=args.debug)
    elif args.operation == 'rm':       e.rm(file_path=args.file, debug=args.debug)
    elif args.operation == 'validate': e.validate(debug=args.debug)
    else:
        raise Error('We fell through!')

if __name__ == '__main__':
    main()
