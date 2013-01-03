import hashlib
import os
import re
import unittest


MANIFEST_ALGORITHMS = ['md5', 'sha1']
def get_manifests(path):
    """Returns list of (filename,algo) tuples of manifest files in the path.
    """
    files = []
    for fn in os.listdir(path):
        for algo in MANIFEST_ALGORITHMS:
            if fn == 'manifest-%s.txt' % algo:
                files.append((fn,algo))
    return files

def manifest_files_readable(path):
    """Checks whether the manifest file(s) are readable.
    """
    readable = True
    try:
        for fn in os.listdir(path):
            for algo in MANIFEST_ALGORITHMS:
                if fn == 'manifest-%s.txt' % algo:
                    f = open(fn, 'r')
                    lines = f.readlines()
                    f.close()
    except:
        readable = False
    return readable

def manifest_files_exist(path):
    """Checks whether all the files listed in manifests exist.
    
    Checks all the lines in all the manifest files to see if files exist.
    @return True or False.
    """
    valid_manifests = []
    manifests = get_manifests(path)
    for manifest in manifests:
        mfn = manifest[0]
        mf = open(os.path.join(path, mfn), 'r')
        lines = mf.readlines()
        mf.close()
        existing_files = []
        for line in lines:
            line = line.strip().replace('\t', ' ')
            while line.find('  ') > -1:
                line = line.replace('  ', ' ')
            fpath = os.path.join(TestBagit.target_path, line.split(' ')[1])
            if os.path.exists(fpath):
                existing_files.append(fpath)
        if len(existing_files) == len(lines):
            valid_manifests.append(mfn)
    if len(valid_manifests) == len(manifests):
        return True
    return False

def checksum_for_file(path, algo, block_size=1024):
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

def manifest_files_match(target_path):
    """Checks whether all the files listed in manifests match their checksums.

    Checks all the lines in all the manifest files to see if the files
    match their checksums.
    @return True or False.
    """
    valid_manifests = []
    manifests = get_manifests(target_path)
    # each manifest file
    for manifest in manifests:
        algo = manifest[1]
        mfn = manifest[0]
        mf = open(os.path.join(target_path, mfn), 'r')
        mlines = mf.readlines()
        mf.close()
        matched_files = []
        # each file in manifest
        for mline in mlines:
            mline = mline.strip().replace('\t', ' ')
            while mline.find('  ') > -1:
                mline = mline.replace('  ', ' ')
            mchecksum = mline.split(' ')[0]
            fpath = os.path.join(target_path, mline.split(' ')[1])
            if os.path.exists(fpath):
                checksum = checksum_for_file(fpath, algo)
                if checksum == mchecksum:
                    matched_files.append(fpath)
        if len(matched_files) == len(mlines):
            valid_manifests.append(mfn)
    if len(valid_manifests) == len(manifests):
        return True
    return False
    

class TestBagit(unittest.TestCase):

    def test00_bag_directory_exists(self):
        """The bag directory does not exist."""
        path = TestBagit.target_path
        self.assertEqual(True, os.path.exists(path))

    # bagit.txt file

    def test010_bagittxt_exists(self):
        """The bag directory does not contain a bagit.txt file. (2.1.1)"""
        path = os.path.join(TestBagit.target_path, 'bagit.txt')
        self.assertEqual(True, os.path.exists(path))

    def test011_bagittxt_valid(self):
        """The bagit.txt file is incorrectly formatted. (2.1.1)"""
        path = os.path.join(TestBagit.target_path, 'bagit.txt')
        f = open(path, 'r')
        lines = f.readlines()
        f.close()
        self.assertEqual(2, len(lines), msg="The bagit.txt file must contain only 2 lines.")
        self.assertEqual('BagIt-version: 0.97', lines[0].strip())
        # match different versions
        #line0match = re.match('BagIt-version: ([0-9]+).([0-9]+)', lines[0].strip())
        #self.assertNotEqual(None, line0match)
        self.assertEqual('Tag-File-Character-Encoding: UTF-8', lines[1].strip())

    # data directory

    def test020_datadir_exists(self):
        """The bag directory does not contain a data directory. (2.1.2)"""
        path = os.path.join(TestBagit.target_path, 'data')
        self.assertEqual(True, os.path.exists(path))
        self.assertEqual(True, os.path.isdir(path))

    # manifest

    def test030_manifests_exist(self):
        """The bag directory must contain at least one manifest file. (2.1.3)"""
        manifests = get_manifests(TestBagit.target_path)
        self.assertTrue(len(manifests) >= 1)

    def test031_manifests_readable(self):
        """One or more manifest files could not be read. (2.1.3)"""
        path = os.path.join(TestBagit.target_path, 'manifest-md5.txt')
        self.assertEqual(True, manifests_readable(path))

    def test032_manifest_files_exist(self):
        """One or more files listed in the manifest do not exist. (2.1.3)"""
        self.assertEqual(True, manifest_files_exist(TestBagit.target_path))

    def test032_manifest_files_match(self):
        """Checksums for one or more files in the manifest do not match. (2.1.3)"""
        self.assertEqual(True, manifest_files_match(TestBagit.target_path))


def bagit_test_suite(target_path):
    setattr(TestBagit, 'target_path', target_path)
    return unittest.TestLoader().loadTestsFromTestCase(TestBagit)


if __name__ == '__main__':
    #unittest.main()
    target_path = './bagit_samples/testbag'
    suite = bagit_test_suite(target_path)
    unittest.TextTestRunner(verbosity=2).run(suite)
