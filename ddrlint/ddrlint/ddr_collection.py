from datetime import datetime
import hashlib
import os
import re
import StringIO
import unittest

from dateutil.parser import parse
from lxml import etree


def _read_xml(path):
    """Just see if we can get a string from the file
    """
    with open(path, 'r') as f:
        raw = f.read()
    return raw

def _parse_xml(path):
    """See if we the file can be parsed as XML.
    """
    return etree.parse(StringIO.StringIO(_read_xml(path)))

def _entity_eids(ead_path):
    """Get a list of entity EIDs from the EAD.xml.
    """
    tree = _parse_xml(ead_path)
    return tree.xpath('/ead/dsc/c01/did/unittitle/@eid')

def _entity_paths(files_path, eids):
    """Make list of entity directory paths.
    """
    return [os.path.join(files_path, eid) for eid in eids if files_path and eids]

def _entity_dirs(entity_paths):
    """Return list of entity dirs that exist.
    """
    return [path for path in entity_paths if os.path.exists(path)]

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


class TestDDRCollection(unittest.TestCase):
    path = ''
    ead_path = ''
    changelog_path = ''
    files_path = ''

    def test00_collection_directory_exists(self):
        """Collection directory does not exist.
        """
        self.assertEqual(True, os.path.exists(self.path))
    
    # ead.xml
    
    def test010_ead_exists(self):
        """Collection directory does not contain an ead.xml file.
        """
        self.assertEqual(True, os.path.exists(self.ead_path))
    
    def test011_ead_readable(self):
        """Collection ead.xml file is not readable.
        """
        readable = False
        raw = _read_xml(self.ead_path)
        if raw:
            readable = True
        self.assertEqual(True, readable)
    
    def test012_ead_parsable(self):
        """Collection ead.xml file is not parsable.
        """
        parsable = False
        tree = _parse_xml(self.ead_path)
        if tree:
            parsable = True
        self.assertEqual(True, parsable)
    
    def test013_ead_valid(self):
        """Collection ead.xml file is not a valid EAD file.
        """
        valid = False
        self.assertEqual(True, valid)
    
    # changelog file
    
    def test020_changelog_exists(self):
        """Collection directory does not contain a changelog file.
        """
        self.assertEqual(True, os.path.exists(self.changelog_path))
    
    def test021_changelog_valid(self):
        """Collection changelog file is invalid.
        """
        valid = _changelog_valid(self.changelog_path)
        self.assertEqual(True, valid)
    
    # control file
    
    def test030_control_exists(self):
        """Collection directory does not contain a control file.
        """
        self.assertEqual(True, os.path.exists(self.control_path))
    
    def test031_control_valid(self):
        """Collection control file is invalid.
        """
        valid = _control_valid(self.control_path)
        self.assertEqual(True, valid)
    
    # entities
    
    def test040_entities_dir_exists(self):
        """Collection directory does not contain a files directory.
        """
        if self.entity_eids:
            self.assertEqual(True, os.path.exists(self.files_path))
            self.assertEqual(True, os.path.isdir(self.files_path))
    
    def test041_entity_dirs_exist(self):
        """One or more entities listed in manifest do not exist.
        """
        self.assertEqual(len(self.entity_eids), len(self.entity_dirs))
    
    # manifest
    
    #def test030_manifests_exist(self):
    #    """The bag directory must contain at least one manifest file. (2.1.3)"""
    #    manifests = get_manifests(TestDDRCollection.path)
    #    self.assertTrue(len(manifests) >= 1)
    # 
    #def test031_manifests_readable(self):
    #    """One or more manifest files could not be read. (2.1.3)"""
    #    path = os.path.join(TestDDRCollection.path, 'manifest-md5.txt')
    #    self.assertEqual(True, manifests_readable(path))
    # 
    #def test032_manifest_files_exist(self):
    #    """One or more files listed in the manifest do not exist. (2.1.3)"""
    #    self.assertEqual(True, manifest_files_exist(TestDDRCollection.path))
    # 
    #def test032_manifest_files_match(self):
    #    """Checksums for one or more files in the manifest do not match. (2.1.3)"""
    #    self.assertEqual(True, manifest_files_match(TestDDRCollection.path))


def ddr_test_suite(collection_path):
    setattr(TestDDRCollection, 'path',           collection_path)
    setattr(TestDDRCollection, 'changelog_path', os.path.join(TestDDRCollection.path, 'changelog'))
    setattr(TestDDRCollection, 'control_path',   os.path.join(TestDDRCollection.path, 'control'))
    setattr(TestDDRCollection, 'ead_path',       os.path.join(TestDDRCollection.path, 'ead.xml'))
    setattr(TestDDRCollection, 'files_path',     os.path.join(TestDDRCollection.path, 'files'))
    entity_eids = _entity_eids(TestDDRCollection.ead_path)
    entity_paths = _entity_paths(TestDDRCollection.files_path, entity_eids)
    entity_dirs = _entity_dirs(entity_paths)
    setattr(TestDDRCollection, 'entity_eids',    entity_eids)
    setattr(TestDDRCollection, 'entity_paths',   entity_paths)
    setattr(TestDDRCollection, 'entity_dirs',    entity_dirs)
    return unittest.TestLoader().loadTestsFromTestCase(TestDDRCollection)


if __name__ == '__main__':
    #unittest.main()
    collection_path = './ddr_samples/testcollection'
    suite = bagit_test_suite(collection_path)
    unittest.TextTestRunner(verbosity=2).run(suite)
