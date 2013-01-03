import os
import unittest


class TestExample(unittest.TestCase):
    #entity_path = '/tmp/entity'  # this gets overridden in validator.run_tests()

    def test_path_exists(self):
        """The entity directory does not exist."""
        path = TestExample.entity_path
        self.assertEqual(True, os.path.exists(path))

    def test_manifest_exists(self):
        """The entity directory does not contain a manifest file."""
        path = os.path.join(TestExample.entity_path, 'manifest')
        self.assertEqual(True, os.path.exists(path))

    def test_manifest_readable(self):
        """The manifest file could not be read."""
        path = os.path.join(TestExample.entity_path, 'manifest')
        result = False
        f = open(path, 'r')
        for line in f.readlines():
            parts = line.split(' ')
            result = True
        self.assertEqual(True, result)

    def test_manifest_files_exist(self):
        """One or more files listed in the manifest do not exist."""
        path = os.path.join(TestExample.entity_path, 'manifest')
        f = open(path, 'r')
        listed_files = []
        existing_files = []
        for line in f.readlines():
            listed_files.append(True)
            parts = line.strip().split(' ')
            fpath = os.path.join(TestExample.entity_path, 'files', parts[2])
            if os.path.exists(fpath):
                existing_files.append(True)
        self.assertEqual(listed_files, existing_files)


def example_test_suite(entity_path):
    setattr(TestExample, 'entity_path', entity_path)
    return unittest.TestLoader().loadTestsFromTestCase(TestExample)


if __name__ == '__main__':
    #unittest.main()
    entity_path = './example_samples/entity'
    suite = example_test_suite(entity_path)
    unittest.TextTestRunner(verbosity=2).run(suite)
