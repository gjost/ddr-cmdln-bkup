import hashlib
import os
import re
import StringIO
import unittest

from lxml import etree



class TestDDRCollection(unittest.TestCase):
    path = ''
    ead_path = ''
    changelog_path = ''
    files_path = ''

    def test00_collection_directory_exists(self):
        """The collection directory does not exist."""
        self.assertEqual(True, os.path.exists(self.path))

    # ead.xml
    
    def test010_ead_exists(self):
        """The collection directory does not contain an ead.xml file."""
        self.assertEqual(True, os.path.exists(self.ead_path))

    def test011_ead_readable(self):
        """The ead.xml file is not readable."""
        readable = False
        with open(self.ead_path, 'r') as f:
            raw = f.read()
        if raw:
            readable = True
        self.assertEqual(True, readable)

    def test012_ead_parsable(self):
        """The ead.xml file is not parsable."""
        parsable = False
        with open(self.ead_path, 'r') as f:
            raw = f.read()
        xml = StringIO.StringIO(raw)
        tree = etree.parse(xml)
        if tree:
            parsable = True
        self.assertEqual(True, parsable)

    def test013_ead_valid(self):
        """The ead.xml file is not a valid EAD file."""
        pass
    
    # files directory

    def test020_filesdir_exists(self):
        """The collection directory does not contain a files directory."""
        path = os.path.join(TestDDRCollection.path, 'files')
        self.assertEqual(True, os.path.exists(path))
        self.assertEqual(True, os.path.isdir(path))

    # changelog file

    def test030_changelog_exists(self):
        """The collection directory does not contain a changelog file."""
        path = os.path.join(TestDDRCollection.path, 'changelog')
        self.assertEqual(True, os.path.exists(path))

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
    setattr(TestDDRCollection, 'path', collection_path)
    setattr(TestDDRCollection, 'ead_path', os.path.join(TestDDRCollection.path, 'ead.xml'))
    setattr(TestDDRCollection, 'changelog_path', os.path.join(TestDDRCollection.path, 'changelog'))
    setattr(TestDDRCollection, 'files_path', os.path.join(TestDDRCollection.path, 'files'))
    return unittest.TestLoader().loadTestsFromTestCase(TestDDRCollection)


if __name__ == '__main__':
    #unittest.main()
    collection_path = './ddr_samples/testcollection'
    suite = bagit_test_suite(collection_path)
    unittest.TextTestRunner(verbosity=2).run(suite)
