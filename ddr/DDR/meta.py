from datetime import datetime
import json
import logging
import os

MODULE_PATH   = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(MODULE_PATH, 'templates')
ENTITY_JSON_TEMPLATE = os.path.join(TEMPLATE_PATH, 'entity.json.tpl' )

def load_template(filename):
    template = ''
    with open(filename, 'r') as f:
        template = f.read()
    return template

class EntityJSON():
    entity_path = None
    filename = None
    data = None
    
    def __init__( self, entity ):
        self.entity_path = entity.path
        self.filename = os.path.join(self.entity_path, 'entity.json')
        self.read()
    
    @staticmethod
    def create( path ):
        logging.debug('    EntityJSON.create({})'.format(path))
        tpl = load_template(ENTITY_JSON_TEMPLATE)
        with open(path, 'w') as f:
            f.write(tpl)
    
    def read( self ):
        logging.debug('    EntityJSON.read({})'.format(self.filename))
        with open(self.filename, 'r') as f:
            self.data = json.loads(f.read())
     
    def write( self ):
        logging.debug('    EntityJSON.write({})'.format(self.filename))
        js = json.dumps(self.data)
        with open(self.filename, 'w') as f:
            f.write(js)
    
    CHECKSUMS = ['sha1', 'sha256', 'files']
    def update_checksums( self, entity ):
        """Returns file info in sorted list.
        """
        logging.debug('    EntityJSON.update_checksums({})'.format(entity))
        
        def relative_path(entity_path, payload_file):
            # relative path to payload
            if entity_path[-1] != '/':
                entity_path = '{}/'.format(entity_path)
            return payload_file.replace(entity_path, '')
        
        fdict = {}
        for sha1,path in entity.checksums('sha1'):
            relpath = relative_path(entity.path, path)
            size = os.path.getsize(path)
            fdict[relpath] = {'sha1':sha1, 'size':size,}
        for sha256,path in entity.checksums('sha256'):
            relpath = relative_path(entity.path, path)
            fdict[relpath]['sha256'] = sha256
        for md5,path in entity.checksums('md5'):
            relpath = relative_path(entity.path, path)
            fdict[relpath]['md5'] = md5
        
        # has to be sorted list so can meaningfully version
        files = []
        fkeys = fdict.keys()
        fkeys.sort()
        for key in fkeys:
            files.append(fdict[key])

        data = self.data

        # add files if absent
        present = False
        for field in self.data:
            for key in field.keys():
                if key == 'files':
                    present = True
        if not present:
            self.data.append( {'files':[]} )
        
        for field in self.data:
            for key in field.keys():
                if key == 'files':
                    field[key] = files
