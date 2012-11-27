import ConfigParser
import hashlib
import logging
import os
import shutil

import config
conf = config.read_config(path='/etc/kura.conf')



class Error(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)



def _payload_path(entity_path):
    return os.path.join(entity_path, 'files')

def _payload_file_path(payload_file, entity_path):
    """Given absolute paths to payload file and entity, return relative path to payload
    """
    if entity_path[-1] != '/':
        entity_path = '%s/' % entity_path
    return payload_file.replace(entity_path, '')



METADATA_TEMPLATE = """[Basic]
standards-version = DDR0.1
entity = UID
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

def _metadata_filename(entity_path):
    return os.path.join(entity_path, 'control')

def _read_metadata_file(entity_path, debug=False):
    path = _metadata_filename(entity_path)
    c = ConfigParser.ConfigParser()
    c.read([path])
    if debug:
        for section in c.sections():
            print '[%s]' % section
            for item in c.items(section):
                print item
    return c

def _write_metadata_file(metadata, entity_path, debug=False):
    path = _metadata_filename(entity_path)
    with open(path, 'wb') as mfile:
        metadata.write(mfile)
    if debug:
        for section in metadata.sections():
            print '[%s]' % section
            for item in metadata.items(section):
                print item



def _checksum_for_file(path, algo, block_size=1024):
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

def _checksums(payload_path, algo, debug=False):
    if algo not in ['sha1', 'sha256', 'md5']:
        raise Error('BAD ALGORITHM: %s' % algo)
    checksums = []
    for f in os.listdir(payload_path):
        fpath = os.path.join(payload_path, f)
        cs = _checksum_for_file(fpath, algo)
        if cs:
            checksums.append( (cs, fpath) )
    return checksums

def _files_list(payload_path, debug=False):
    files = []
    checksums = _checksums(payload_path, 'md5', debug=debug)
    for md5,path in checksums:
        files.append((md5, os.path.getsize(path), path))
    return files



def init(entity_path, debug=False):
    """Create the file structure for a new Entity.
    
    @param entity_path String Absolute path to entity dir.
    """
    # create directory if doesn't exist
    if not os.path.exists(entity_path):
        os.makedirs(entity_path)
        if debug:
            print 'Created directory %s' % entity_path
    # make payload dir if doesn't exist
    payload_path = _payload_path(entity_path)
    if not os.path.exists(payload_path):
        os.makedirs(payload_path)
        if debug:
            print 'Created payload directory %s' % payload_path
    # write blank metadata file
    metadata_path = _metadata_filename(entity_path)
    if not os.path.exists(metadata_path):
        if debug:
            print 'Writing metadata file %s ...' % metadata_path
        metadata = open(metadata_path, 'w')
        metadata.write(METADATA_TEMPLATE)
        metadata.close()
        if debug:
            print 'OK'
    # TODO write to log

def add(entity_path, file_path, debug=False):
    """Add a file to the Entity.
    
    @param entity_path String Absolute path to entity dir.
    @param file_path String Absolute path to file.
    @returns None for success, or String error message
    """
    # check all the things!
    payload_path = _payload_path(entity_path)
    metadata_path = _metadata_filename(entity_path)
    dest_path = os.path.join(payload_path, os.path.basename(file_path))
    if not os.path.exists(entity_path):
        raise Error('Entity does not seem to exist: %s' % entity_path)
    if not os.path.exists(payload_path):
        raise Error('Files directory does not exist: %s' % payload_path)
    if not os.path.exists(metadata_path):
        raise Error('Metadata file does not exist: %s' % metadata_path)
    if not os.path.exists(file_path):
        raise Error('File does not exist: %s' % file_path)
    # TODO add force overwrite option
    #if os.path.exists(dest_path):
    #    raise Error('File already copied: %s' % dest_path)
    metadata = _read_metadata_file(entity_path, debug=debug)
    # copy the file already!
    # TODO hand off to background task? show progress bar?
    if debug:
        print 'copying %s' % file_path
        print '     -> %s' % dest_path
    shutil.copyfile(file_path, dest_path)
    if not os.path.exists(dest_path):
        raise Error('File not copied: %s' % dest_path)
    else:
        if debug:
            print 'OK'
    # update metadata
    for sha1,path in _checksums(payload_path, 'sha1', debug=debug):
        path = _payload_file_path(path, entity_path)
        metadata.set('Checksums-SHA1', sha1, path)
    for sha256,path in _checksums(payload_path, 'sha256', debug=debug):
        path = _payload_file_path(path, entity_path)
        metadata.set('Checksums-SHA256', sha256, path)
    for md5,size,path in _files_list(payload_path, debug=debug):
        path = _payload_file_path(path, entity_path)
        metadata.set('Files', md5, '%s ; %s' % (size,path))
    _write_metadata_file(metadata, entity_path, debug=debug)
    # TODO write to log

def rm(entity_path, file_path, debug=False):
    """Remove a file from the Entity.
    
    @param entity_path String Absolute path to entity dir.
    @param file_path String Path to file, relative to Entity root.
    @returns None for success, or String error message
    """
    # confirm that entity exists
    if not os.path.exists(entity_path):
        raise Error('Entity does not seem to exist: %s' % entity_path)
    # confirm that metadata file exists, read it
    metadata_path = _metadata_filename(entity_path)
    if not os.path.exists(metadata_path):
        raise Error('Metadata file does not exist: %s' % metadata_path)
    metadata = _read_metadata_file(entity_path)
    # confirm that file_path exists
    if not os.path.exists(file_path):
        raise Error('File does not exist: %s' % file_path)
    # OK GO
    # remove file
    # update metadata SHA1
    # update metadata SHA256
    # update metadata files
    # write to log
    pass

def validate(entity_path):
    """Run validator tool on this Entity, return results.
    
    @param entity_path String Absolute path to entity dir.
    """
    pass
