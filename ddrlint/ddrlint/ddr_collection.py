from datetime import datetime
import hashlib
import os
import re
import StringIO
import unittest

from dateutil.parser import parse
from lxml import etree


"""
TODO: Rethink XML readable/parsable/valid tests. How will these work on a collection with thousands of entities, each with multiple files?
"""

def _read_xml(path):
    """Just see if we can get a string from the file
    """
    raw = ''
    if os.path.exists(path):
        with open(path, 'r') as f:
            raw = f.read()
    return raw

def _parse_xml(path):
    """Indicate whether file can be parsed as XML.
    @return tree: lxml tree object
    """
    return etree.parse(StringIO.StringIO(_read_xml(path)))

def _validate_xml(path):
    """Indicate whether XML file is valid.
    @return boolean
    """
    return False

def _entity_eids(ead_path):
    """List of entity EIDs from the EAD.xml.
    """
    tree = _parse_xml(ead_path)
    return tree.xpath('/ead/dsc/c01/did/unittitle/@eid')

def _entity_paths(files_path, eids):
    """List of entity directory paths.
    """
    return [os.path.join(files_path, eid) for eid in eids if files_path and eids]

def _entity_dirs(entity_paths):
    """Return list of entity dirs that exist.
    """
    return [path for path in entity_paths if os.path.exists(path)]

def _entity_meta_files(entity_paths, filename):
    """File paths of entity files (single files) that exist.
    """
    existing = []
    for path in entity_paths:
        x = os.path.join(path, filename)
        if os.path.exists(x):
            existing.append(x)
    return existing

def _entity_xml_filter(entity_paths, filename, function):
    """File paths of entity XML files that pass the filter function.
    """
    passed = []
    for path in entity_paths:
        x = os.path.join(path, filename)
        if function(x):
            passed.append(x)
    return passed

def _changelog_valid(path):
    """Indicates whether changelog file is valid.

    Example:
    * Initialized collection ddr-testing-32
    -- Geoffrey Jost <geoffrey.jost@densho.org>  Thu, 23 May 2013 12:34:17 
     
    * Initialized entity ddr-testing-32-1
    -- Geoffrey Jost <geoffrey.jost@densho.org>  Thu, 23 May 2013 12:34:35 
     
    * Updated collection file(s) ead.xml
    -- Geoffrey Jost <geoffrey.jost@densho.org>  Thu, 23 May 2013 12:36:04

    Notes:
    - example is indented 4 spaces
    - space after datetime
    """
    valid = False
    with open(path, 'r') as f:
        changelog = f.read()
    num_valid = 0
    entries = changelog.split(' \n\n')
    pattern = '^-- ([\w ]+) <([\w_.-@]+)>$'
    for entry in entries:
        lines = entry.strip().split('\n')
        # signature
        sig = lines.pop().strip()
        # name, email formatted properly
        name = None; mail = None
        name_mail = sig.split('  ')[0]
        if name_mail:
            m = re.match(pattern, name_mail)
            name = m.group(1)
            mail = m.group(2)
        # timestamp can be parsed into datetime
        timestamp = None
        try:    tsraw = sig.split('  ')[1]
        except: tsraw = ''
        try:    ts = parse(tsraw)
        except: ts = None
        if ts and (type(ts) == type(datetime(1970,1,1,00,00,00))):
            timestamp = ts
        if name and mail and timestamp:
            num_valid = num_valid + 1
    if num_valid == len(entries):
        valid = True
    return valid

def _control_valid(path):
    """Indicates whether control file is valid.
    """
    valid = False
    return valid

def _entity_files_info(entity_mets_xmls):
    """List of file info from METS.xml.
    
    <mets>
      <metsHdr/>
        <dmdSec/>
          <amdSec/>
            <fileSec>
              <fileGrp USE="master">
                <file CHECKSUM="38b1886b239ceb54727cd977f6bf1223" CHECKSUMTYPE="md5">
                  <Flocat href="files/crunchbang-flames-full-by-omns.jpg"/>
    """
    entities = []
    for path in entity_mets_xmls:
        files = []
        d = os.path.dirname(path)
        eid = d.split(os.path.sep)[-1]
        tree = _parse_xml(path)
        for f in tree.xpath('/mets/fileSec/fileGrp/file'):
            checksum = None
            checksumtype = None
            href = None
            path_abs = None
            
            checksum = f.get('checksum')
            checksumtype = f.get('checksumtype')
            if not checksum:
                checksum = f.get('CHECKSUM')
            if not checksumtype:
                checksumtype = f.get('CHECKSUMTYPE')
            
            # TODO Can there be more than one <Flocat> in a <file>?
            for href in f.xpath('Flocat/@href'):
                path_abs = os.path.join(d, href)
            if href and path_abs and checksum and checksumtype:
                files.append({'eid': eid,
                              'href': href,
                              'abs': path_abs,
                              'checksum': checksum,
                              'checksumtype': checksumtype,})
        entities.append(files)
    return entities

def _entity_files_count(entity_files_info):
    """Takes output of entity_files_info and counts the total number of files.
    """
    c = 0
    for e in entity_files_info:
        for f in e:
            c = c + 1
    return c

def _entity_files_existing(entity_files_info):
    """Takes output of entity_files_info and lists files that exist.
    NOTE: result is a flat list of absolute file paths.
    """
    existing = []
    for e in entity_files_info:
        for f in e:
            if os.path.exists(f['abs']):
                existing.append(f)
    return existing

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

def _entity_files_verified(entity_files_info):
    """Takes output of entity_files_info and lists files that exist.
    NOTE: result is a flat list of absolute file paths.
    """
    verified = []
    for e in entity_files_info:
        for f in e:
            if os.path.exists(f['abs']):
                c = _checksum_for_file(f['abs'], f['checksumtype'])
                if c and (c == f['checksum']):
                    verified.append(f)
    return verified

    


class TestDDRCollection(unittest.TestCase):
    path = ''
    ead_path = ''
    changelog_path = ''
    files_path = ''

    def test00_collection_directory_exists(self):
        """Collection directory does not exist.
        """
        self.assertEqual(True, os.path.exists(self.path))
    
    # ead.xml ----------------------------------------------------------
    
    def test010_ead_exists(self):
        """Collection directory does not contain an ead.xml file.
        """
        self.assertEqual(True, os.path.exists(self.ead_path))
    
    def test011_ead_readable(self):
        """Collection ead.xml is not readable.
        """
        readable = False
        raw = _read_xml(self.ead_path)
        if raw:
            readable = True
        self.assertEqual(True, readable)
    
    def test012_ead_parsable(self):
        """Collection ead.xml is not parsable.
        """
        parsable = False
        tree = _parse_xml(self.ead_path)
        if tree:
            parsable = True
        self.assertEqual(True, parsable)
    
    def test013_ead_valid(self):
        """Collection ead.xml is not valid.
        """
        valid = False
        self.assertEqual(True, valid)
    
    # changelog file ---------------------------------------------------
    
    def test020_changelog_exists(self):
        """Collection directory does not contain a changelog file.
        """
        self.assertEqual(True, os.path.exists(self.changelog_path))
    
    def test021_changelog_valid(self):
        """Collection changelog file is not valid.
        """
        valid = _changelog_valid(self.changelog_path)
        self.assertEqual(True, valid)

    
    # control file -----------------------------------------------------
    
    def test030_control_exists(self):
        """Collection directory does not contain a control file.
        """
        self.assertEqual(True, os.path.exists(self.control_path))
    
    def test031_control_valid(self):
        """Collection control file is not valid.
        """
        valid = _control_valid(self.control_path)
        self.assertEqual(True, valid)
    
    # entities =========================================================
    
    def test040_entities_dir_exists(self):
        """Collection directory does not contain a files directory.
        """
        if self.entity_eids:
            self.assertEqual(True, os.path.exists(self.files_path))
            self.assertEqual(True, os.path.isdir(self.files_path))
    
    def test041_entity_dirs_exist(self):
        """Entities listed in manifest do not exist.
        """
        self.assertEqual(len(self.entity_eids),
                         len(self.entity_dirs))
    
    # entity changelogs ------------------------------------------------
    
    def test0420_entity_changelogs_exist(self):
        """Entity changelogs are missing.
        """
        self.assertEqual(len(self.entity_changelog_paths),
                         len(self.entity_paths))
    
    def test0421_entity_changelogs_valid(self):
        """Entity changelogs are not valid.
        """
        self.assertEqual(True, False)
    
    # entity control files ---------------------------------------------
    
    def test0430_entity_controls_exist(self):
        """Entity control files are missing.
        """
        self.assertEqual(len(self.entity_control_paths),
                         len(self.entity_paths))
    
    def test0431_entity_controls_valid(self):
        """Entity control files are not vald.
        """
        self.assertEqual(True, False)
    
    # entity mets.xml --------------------------------------------------
    
    def test0440_entity_mets_exist(self):
        """Entity mets.xml files are missing.
        """
        self.assertEqual(len(self.entity_metsxml_paths),
                         len(self.entity_paths))
    
    def test0441_entity_mets_readable(self):
        """Entity mets.xml files are not readable.
        """
        self.assertEqual(len(self.entity_metsxml_readable),
                         len(self.entity_paths))
    
    def test0442_entity_mets_parsable(self):
        """Entity mets.xml files are not parsable.
        """
        self.assertEqual(len(self.entity_metsxml_parsable),
                         len(self.entity_paths))
    
    def test0443_entity_mets_valid(self):
        """Entity mets.xml files are not valid.
        """
        self.assertEqual(len(self.entity_metsxml_valid),
                         len(self.entity_paths))


def ddr_test_suite(collection_path):
    
    changelog_path = os.path.join(collection_path, 'changelog')
    control_path   = os.path.join(collection_path, 'control')
    ead_path       = os.path.join(collection_path, 'ead.xml')
    files_path     = os.path.join(collection_path, 'files')
    setattr(TestDDRCollection, 'path',                    collection_path)
    setattr(TestDDRCollection, 'changelog_path',          changelog_path)
    setattr(TestDDRCollection, 'control_path',            control_path)
    setattr(TestDDRCollection, 'ead_path',                ead_path)
    setattr(TestDDRCollection, 'files_path',              files_path)

    # Read ead.xml and get list of entities
    entity_eids  = _entity_eids(ead_path)
    entity_paths = _entity_paths(files_path, entity_eids)
    entity_dirs  = _entity_dirs(entity_paths)
    setattr(TestDDRCollection, 'entity_eids',             entity_eids)
    setattr(TestDDRCollection, 'entity_paths',            entity_paths)
    setattr(TestDDRCollection, 'entity_dirs',             entity_dirs)
    
    # List paths of entity files found in ead.xml.
    # Each entity should have one of these files, so list lengths should match
    # length of entity_paths.
    entity_changelog_paths  = _entity_meta_files(entity_paths, 'changelog')
    entity_control_paths    = _entity_meta_files(entity_paths, 'control')
    entity_metsxml_paths    = _entity_meta_files(entity_paths, 'mets.xml')
    setattr(TestDDRCollection, 'entity_changelog_paths',  entity_changelog_paths)
    setattr(TestDDRCollection, 'entity_control_paths',    entity_control_paths)
    setattr(TestDDRCollection, 'entity_metsxml_paths',    entity_metsxml_paths)
    
    # List paths of entity mets.xml files that pass various tests
    entity_metsxml_readable = _entity_xml_filter(entity_paths, 'mets.xml', _read_xml)
    entity_metsxml_parsable = _entity_xml_filter(entity_paths, 'mets.xml', _parse_xml)
    entity_metsxml_valid    = _entity_xml_filter(entity_paths, 'mets.xml', _validate_xml)
    setattr(TestDDRCollection, 'entity_metsxml_readable', entity_metsxml_readable)
    setattr(TestDDRCollection, 'entity_metsxml_parsable', entity_metsxml_parsable)
    setattr(TestDDRCollection, 'entity_metsxml_valid',    entity_metsxml_valid)
    
    # List the files for each entity
    entity_files_info       = _entity_files_info(entity_metsxml_readable)
    entity_files_count      = _entity_files_count(entity_files_info)
    entity_files_existing   = _entity_files_existing(entity_files_info)
    entity_files_verified   = _entity_files_verified(entity_files_info)
    setattr(TestDDRCollection, 'entity_files_info',     entity_files_info)
    setattr(TestDDRCollection, 'entity_files_count',    entity_files_count)
    setattr(TestDDRCollection, 'entity_files_existing', entity_files_existing)
    setattr(TestDDRCollection, 'entity_files_verified', entity_files_verified)
    
    return unittest.TestLoader().loadTestsFromTestCase(TestDDRCollection)


if __name__ == '__main__':
    #unittest.main()
    collection_path = './ddr_samples/testcollection'
    suite = bagit_test_suite(collection_path)
    unittest.TextTestRunner(verbosity=2).run(suite)
