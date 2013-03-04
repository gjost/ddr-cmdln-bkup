import hashlib
import os


class Collection( object ):
    path = None
    uid = None
    
    def __init__( self, path, uid=None ):
        self.path = path
        if not uid:
            uid = os.path.basename(self.path)
        self.uid  = uid
    
    def payload_path( self, trailing_slash=False ):
        p = os.path.join(self.path, 'files')
        if trailing_slash:
            p = '{}/'.format(p)
        return p
    
    def entities( self ):
        """Returns relative paths to entities."""
        entities = []
        cpath = self.path
        if cpath[-1] != '/':
            cpath = '{}/'.format(cpath)
        for uid in os.listdir(self.payload_path()):
            epath = os.path.join(self.payload_path(), uid)
            e = Entity(epath)
            entities.append(e)
        return entities


class Entity( object ):
    path = None
    uid = None
    
    def __init__( self, path, uid=None ):
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
    
    def checksums( self, algo ):
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
