import os

from bs4 import BeautifulSoup


MODULE_PATH   = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(MODULE_PATH, 'templates')
EAD_TEMPLATE  = os.path.join(TEMPLATE_PATH, 'collection_ead.xml.tpl')
METS_TEMPLATE = os.path.join(TEMPLATE_PATH, 'entity_mets.xml.tpl' )


def load_template(filename):
    template = ''
    with open(filename, 'r') as f:
        template = f.read()
    return template


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
    
    @staticmethod
    def create( path, ):
        if debug:
            print('Creating ead.xml {} ...'.format(path))
        t = load_template(EAD_TEMPLATE)
        with open(path, 'w') as f:
            f.write(t)

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
        # TODO Instead of creating a new <dsc>, read current data then recreate with additional files
        dsc = self.soup.new_tag('dsc')
        self.soup.dsc.replace_with(dsc)
        head = self.soup.new_tag('head')
        head.string = 'Inventory'
        self.soup.dsc.append(head)
        n = 0
        for entity in collection.entities(debug=debug):
            n = n + 1
            # add c01, did, unittitle
            c01 = self.soup.new_tag('c01')
            did = self.soup.new_tag('did')
            c01.append(did)
            unittitle = self.soup.new_tag('unittitle', eid=entity.uid)
            unittitle.string = 'Entity description goes here'
            did.append(unittitle)
            self.soup.dsc.append(c01)


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
    
    @staticmethod
    def create( path, ):
        if debug:
            print('Creating mets.xml {} ...'.format(path))
        t = load_template(METS_TEMPLATE)
        with open(path, 'w') as f:
            f.write(t)
    
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
            path = relative_path(entity.path, path)
            # add fileGrp, file, Floca
            fileGrp = self.soup.new_tag('fileGrp', USE='master')
            self.soup.fileSec.append(fileGrp)
            f = self.soup.new_tag('file', CHECKSUM=md5, CHECKSUMTYPE='md5')
            fileGrp.append(f)
            flocat = self.soup.new_tag('Flocat', href=path)
            f.append(flocat)
