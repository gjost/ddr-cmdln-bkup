from datetime import datetime
import os
import shutil
import subprocess
import sys
import unittest

import requests



DEBUG = False
#DEBUG = True


TEST_CID       = 'ddr-testing-{}'.format(datetime.now().strftime('%Y%m%d%H%M'))
TEST_EIDS      = []
for n in [1,2]:
    TEST_EIDS.append('{}-{}'.format(TEST_CID, n))

CMD_PATH = 'collection'

TEST_TMP_PATH  = '/tmp/'
TEST_USER_NAME = 'gjost'
TEST_USER_MAIL = 'geoffrey.jost@densho.org'

TEST_COLLECTION      = os.path.join(TEST_TMP_PATH,TEST_CID)
COLLECTION_CHANGELOG = os.path.join(TEST_COLLECTION, 'changelog')
COLLECTION_CONTROL   = os.path.join(TEST_COLLECTION, 'control')
COLLECTION_EAD       = os.path.join(TEST_COLLECTION, 'ead.xml')
COLLECTION_FILES     = os.path.join(TEST_COLLECTION, 'files')
COLLECTION_GIT       = os.path.join(TEST_COLLECTION, '.git')
COLLECTION_GITIGNORE = os.path.join(TEST_COLLECTION, '.gitignore')

MODULE_PATH = os.path.dirname(os.path.abspath(__file__))
TEST_FILES_DIR = os.path.join(MODULE_PATH, 'files')
TEST_MEDIA_DIR = os.path.join(MODULE_PATH, '..', 'files', 'entity')

GITWEB_URL = 'http://partner.densho.org/gitweb'



def last_local_commit(path, branch, debug=False):
    """Gets hash of last LOCAL commit on specified branch.
    
    $ git log <branch> -1
    commit 891c0f2f56a59dcd68ccf04392193be4b075fb2c
    Author: gjost <geoffrey.jost@densho.org>
    Date:   Fri Feb 8 15:29:07 2013 -0700
    """
    h = ''
    os.chdir(path)
    # get last commit
    log1 = subprocess.check_output('git log {} -1'.format(branch), shell=True)
    # 'commit 925315a29179c63f0849c0149451f1dd30010c02\nAuthor: gjost <geoffrey.jost@densho.org>\nDate:   Fri Feb 8 15:50:31 2013 -0700\n\n    Initialized entity ddr-testing-3-2\n'
    h = log1.split('\n')[0].split(' ')[1]
    return h

def last_remote_commit(path, branch, debug=False):
    """Gets hash of last REMOTE commit on specified branch.
    
    $ git ls-remote --heads
    From git@mits:ddr-testing-3.git
    7174bbd2a628bd2979e05c507c599937de22d2c9        refs/heads/git-annex
    925315a29179c63f0849c0149451f1dd30010c02        refs/heads/master
    d11f9258d0d34c4f0d6bfa3f8a9c7dcb1b64ef53        refs/heads/synced/master
    """
    h = ''
    os.chdir(path)
    ref_head = 'refs/heads/{}'.format(branch)
    out = subprocess.check_output('git ls-remote --heads', shell=True)
    for line in out.split('\n'):
        if ref_head in line:
            h = line.split('\t')[0]
    return h    

def file_in_local_commit(path, branch, commit, filename, debug=False):
    """Tells whether specified filename appears in specified commit message.
    
    IMPORTANT: We're not really checking to see if an actual file was in an
    actual commit here.  We're really just checking if a particular string
    (the filename) appears inside another string (the commit message).
    
    $ git log -1 --stat -p f6e877856b3f0536b6df42cafe3a369917950242 master|grep \|
    changelog                       |    2 ++
    files/ddr-testing-3-2/changelog |    2 ++
    """
    if debug:
        print('file_in_local_commit({}, {}, {}, {})'.format(
            path, branch, commit, filename))
    present = None
    os.chdir(path)
    log = subprocess.check_output('git log -1 --stat -p {} {}|grep \|'.format(commit, branch), shell=True)
    if debug:
        print(log)
    for line in log.split('\n'):
        linefile = line.split('|')[0].strip()
        if linefile == filename:
            present = True
    if debug:
        print('file_in_local_commit() {}'.format(present))
    return present

def file_in_remote_commit(collection_cid, commit, filename, debug=False):
    """
    Could do HTTP request:
    http://partner.densho.org/gitweb/?a=commitdiff_plain;p={repo}.git;h={hash}
    http://partner.densho.org/gitweb/?a=commitdiff_plain;p=ddr-testing-3.git;h=b0174f500b9235b7adbd799421294865fe374a13
    
    @return True if present, False if not present, or None if could not contact workbench.
    """
    if debug:
        print('file_in_remote_commit({}, {}, {})'.format(collection_cid, commit, filename))
    # TODO
    url = '{gitweb}/?a=commitdiff_plain;p={repo}.git;h={hash}'.format(
        gitweb=GITWEB_URL, repo=collection_cid, hash=commit)
    if debug:
        print(url)
    try:
        r = requests.get(url)
    except:
        return None
    if debug:
        print(r.status_code)
    if r and r.status_code == 200:
        for line in r.text.split('\n'):
            print(line)
            match = '+++ b/{}'.format(filename)
            if line == match:
                return True
    return False
    



class TestCollection( unittest.TestCase ):

    def setUp( self ):
        pass

    # initialize -------------------------------------------------------
    
    def test_00_create( self ):
        """Create a collection.
        """
        debug = ''
        if DEBUG:
            debug = ' --debug'
            print('\n----------------------------------------------------------------------')
            print('test_00_create')
        if os.path.exists(TEST_COLLECTION):
            shutil.rmtree(TEST_COLLECTION, ignore_errors=True)
        #
        cmd = '{} create {} --user {} --mail {} --collection {}'.format(CMD_PATH, debug, TEST_USER_NAME, TEST_USER_MAIL, TEST_COLLECTION)
        if DEBUG:
            print(cmd)
        out = subprocess.check_output(cmd, shell=True)
        if DEBUG:
            print(out)
        
        # directories exist
        self.assertTrue(os.path.exists(TEST_COLLECTION))
        self.assertTrue(os.path.exists(COLLECTION_CHANGELOG))
        self.assertTrue(os.path.exists(COLLECTION_CONTROL))
        self.assertTrue(os.path.exists(COLLECTION_EAD))
        # git, git-annex
        git   = os.path.join(TEST_COLLECTION, '.git')
        annex = os.path.join(git, 'annex')
        self.assertTrue(os.path.exists(git))
        self.assertTrue(os.path.exists(annex))
        # check that local,remote commits exist and are equal
        # indicates that local changes made it up to workbench
        remote_hash_master   = last_remote_commit(TEST_COLLECTION, 'master')
        remote_hash_gitannex = last_remote_commit(TEST_COLLECTION, 'git-annex')
        local_hash_master   = last_local_commit(TEST_COLLECTION, 'master')
        local_hash_gitannex = last_local_commit(TEST_COLLECTION, 'git-annex')
        self.assertTrue(remote_hash_master)
        self.assertTrue(remote_hash_gitannex)
        self.assertTrue(local_hash_master)
        self.assertTrue(local_hash_gitannex)
        self.assertEqual(remote_hash_master, local_hash_master)
        self.assertEqual(remote_hash_gitannex, local_hash_gitannex)

    def test_01_destroy( self ):
        """Destroy a collection.
        """
        debug = ''
        if DEBUG:
            debug = ' --debug'
            print('\n----------------------------------------------------------------------')
            print('test_01_destroy')
        # tests
        #self.assertTrue(...)

    def test_02_status( self ):
        """Get status info for collection.
        """
        debug = ''
        if DEBUG:
            debug = ' --debug'
            print('\n----------------------------------------------------------------------')
            print('test_02_status')
        # tests
        #self.assertTrue(...)
    
    def test_03_update( self ):
        """Register changes to specified file; does not push.
        """
        debug = ''
        if DEBUG:
            debug = ' --debug'
            print('\n----------------------------------------------------------------------')
            print('test_03_update')
        # simulate making changes to a file
        srcfile = os.path.join(TEST_FILES_DIR, 'collection', 'update_control')
        destfile = COLLECTION_CONTROL
        shutil.copy(srcfile, destfile)
        # run update
        cmd = '{} update {} --user {} --mail {} --collection {} --file {}'.format(
            CMD_PATH, debug, TEST_USER_NAME, TEST_USER_MAIL, TEST_COLLECTION, 'control')
        if DEBUG:
            print(cmd)
        out = subprocess.check_output(cmd, shell=True)
        if DEBUG:
            print(out)
        # tests
        # TODO we need to test status, that modified file was actually committed
        commit = last_local_commit(TEST_COLLECTION, 'master')
        self.assertTrue(file_in_local_commit(TEST_COLLECTION, 'master', commit, 'control', debug=debug))
    
    def test_04_sync( self ):
        """git pull/push to workbench server, git-annex sync
        """
        debug = ''
        if DEBUG:
            debug = ' --debug'
            print('\n----------------------------------------------------------------------')
            print('test_04_sync')
        cmd = '{} sync {} --user {} --mail {} --collection {}'.format(
            CMD_PATH, debug, TEST_USER_NAME, TEST_USER_MAIL, TEST_COLLECTION)
        if DEBUG:
            print('CMD: {}'.format(cmd))
        out = subprocess.check_output(cmd, shell=True)
        if DEBUG:
            print('OUT: {}'.format(out))
        # tests
        # check that local,remote commits exist and are equal
        # indicates that local changes made it up to workbench
        remote_hash_master   = last_remote_commit(TEST_COLLECTION, 'master')
        remote_hash_gitannex = last_remote_commit(TEST_COLLECTION, 'git-annex')
        local_hash_master   = last_local_commit(TEST_COLLECTION, 'master')
        local_hash_gitannex = last_local_commit(TEST_COLLECTION, 'git-annex')
        self.assertTrue(remote_hash_master)
        self.assertTrue(remote_hash_gitannex)
        self.assertTrue(local_hash_master)
        self.assertTrue(local_hash_gitannex)
        self.assertEqual(remote_hash_master, local_hash_master)
        self.assertEqual(remote_hash_gitannex, local_hash_gitannex)
    
    def test_10_entity_create( self ):
        """Create new entity in the collection
        """
        debug = ''
        if DEBUG:
            debug = ' --debug'
            print('\n----------------------------------------------------------------------')
            print('test_10_entity_create')
        
        # add the entity
        for eid in TEST_EIDS:
            cmd = '{} ecreate {} --user {} --mail {} --collection {} --entity {}'.format(
                CMD_PATH, debug, TEST_USER_NAME, TEST_USER_MAIL, TEST_COLLECTION, eid)
            if DEBUG:
                print('CMD: {}'.format(cmd))
            out = subprocess.check_output(cmd, shell=True)
            if DEBUG:
                print('OUT: {}'.format(out))
        
        # confirm entity files exist
        self.assertTrue(os.path.exists(COLLECTION_FILES))
        for eid in TEST_EIDS:
            entity_path = os.path.join(COLLECTION_FILES,eid)
            self.assertTrue(os.path.exists(entity_path))
            self.assertTrue(os.path.exists(os.path.join(entity_path,'changelog')))
            self.assertTrue(os.path.exists(os.path.join(entity_path,'control')))
            self.assertTrue(os.path.exists(os.path.join(entity_path,'mets.xml')))
        # TODO test contents of entity files
        
        # confirm entities in changelog
        changelog_entries = []
        for eid in TEST_EIDS:
            changelog_entries.append('* Initialized entity {}'.format(eid))
        changelog = None
        with open(COLLECTION_CHANGELOG,'r') as cl:
            changelog = cl.read()
        for entry in changelog_entries:
            self.assertTrue(entry in changelog)
        
        # confirm entities in control
        self.assertTrue(os.path.exists(COLLECTION_CONTROL))
        control = None
        with open(COLLECTION_CONTROL, 'r') as cn:
            control = cn.read()
        for eid in TEST_EIDS:
            self.assertTrue(eid in control)
        
        # confirm entities in ead.xml
        self.assertTrue(os.path.exists(COLLECTION_EAD))
        ead = None
        with open(COLLECTION_EAD, 'r') as ec:
            ead = ec.read()
        for eid in TEST_EIDS:
            entry = '<unittitle eid="{}">'.format(eid)
            self.assertTrue(entry in ead)
        
    def test_11_entity_destroy( self ):
        """Remove entity from the collection
        """
        debug = ''
        if DEBUG:
            debug = ' --debug'
            print('\n----------------------------------------------------------------------')
            print('test_11_entity_destroy')
        # tests
        # TODO confirm entity files gone
        # TODO confirm entity destruction mentioned in changelog
        # TODO confirm entity no longer in control
        # TODO confirm entity no longer in ead.xml <dsc>
        # TODO confirm entity desctruction properly recorded for posterity
    
    def test_12_entity_update( self ):
        """Register changes to specified file; does not push.
        """
        debug = ''
        if DEBUG:
            debug = ' --debug'
            print('\n----------------------------------------------------------------------')
            print('test_12_entity_update')
        # simulate making changes to a file for each entity
        eid_files = [[TEST_EIDS[0], 'update_control', 'control'],
                     [TEST_EIDS[1], 'update_mets', 'mets.xml'],]
        for eid,srcfilename,destfilename in eid_files:
            entity_path = os.path.join(COLLECTION_FILES,eid)
            srcfile  = os.path.join(TEST_FILES_DIR, 'entity', srcfilename)
            destfile = os.path.join(entity_path,              destfilename)
            shutil.copy(srcfile, destfile)
            # run update
            cmd = '{} eupdate {} --user {} --mail {} --collection {} --entity {} --file {}'.format(
                CMD_PATH, debug, TEST_USER_NAME, TEST_USER_MAIL, TEST_COLLECTION, eid, destfilename)
            if DEBUG:
                print(cmd)
            out = subprocess.check_output(cmd, shell=True)
            if DEBUG:
                print(out)
            # test that modified file appears in local commit
            commit = last_local_commit(TEST_COLLECTION, 'master')
            # entity files will appear in local commits as "files/ddr-testing-X-Y/FILENAME"
            destfilerelpath = os.path.join('files', eid, destfilename)
            self.assertTrue(
                file_in_local_commit(
                    TEST_COLLECTION, 'master', commit, destfilerelpath, debug=debug))
    
    def test_13_entity_add( self ):
        """git annex add file to entity, push it, and confirm that in remote repo
        """
        debug = ''
        if DEBUG:
            debug = ' --debug'
            print('\n----------------------------------------------------------------------')
            print('test_13_entity_add')
        eid = TEST_EIDS[0]
        for f in os.listdir(TEST_MEDIA_DIR):
            entity_path = os.path.join(COLLECTION_FILES,eid)
            entity_files_dir = os.path.join(entity_path, 'files')
            if not os.path.exists(entity_files_dir):
                os.mkdir(entity_files_dir)
            srcfile  = os.path.join(TEST_MEDIA_DIR, f)
            destfile = os.path.join(entity_files_dir, f)
            shutil.copy(srcfile, destfile)
            # run update
            cmd = '{} eadd {} --user {} --mail {} --collection {} --entity {} --file {}'.format(
                CMD_PATH, debug, TEST_USER_NAME, TEST_USER_MAIL, TEST_COLLECTION, eid, f)
            if DEBUG:
                print(cmd)
            out = subprocess.check_output(cmd, shell=True)
            if DEBUG:
                print(out)
        
        # test file checksums in control
        control_checksums = ['a58d0c947a747a9bce655938b5c251f72a377c00 = files/6a00e55055.png',
                             'c07a01ce976885e56138e821b3063a5ba2e97078 = files/20121205.jpg',
                             'fadfbcd8ceb71b9cfc765b9710db8c2c = 6539 ; files/6a00e55055.png',
                             '42d55eb5ac104c86655b3382213deef1 = 12457 ; files/20121205.jpg',]
        with open(os.path.join(COLLECTION_FILES,eid,'control'), 'r') as ecf:
            control = ecf.read()
            for cs in control_checksums:
                self.assertTrue(cs in control)
        # test file checksums in mets.xml
        mets_checksums = [
            '<file CHECKSUM="fadfbcd8ceb71b9cfc765b9710db8c2c" CHECKSUMTYPE="md5">',
            '<Flocat href="files/6a00e55055.png"/>',
            '<file CHECKSUM="42d55eb5ac104c86655b3382213deef1" CHECKSUMTYPE="md5">',
            '<Flocat href="files/20121205.jpg"/>',
        ]
        with open(os.path.join(COLLECTION_FILES,eid,'mets.xml'), 'r') as mf:
            mets = mf.read()
            for cs in mets_checksums:
                self.assertTrue(cs in mets)
        # TODO test 20121205.jpg,6a00e55055.png in local commit
        # TODO test 20121205.jpg,6a00e55055.png in remote commit

    def test_20_pull( self ):
        """
        """
        debug = ''
        if DEBUG:
            debug = ' --debug'
            print('\n----------------------------------------------------------------------')
            print('test_20_pull')
        # tests
        #self.assertTrue(...)
    
    def test_21_push( self ):
        """
        """
        debug = ''
        if DEBUG:
            debug = ' --debug'
            print('\n----------------------------------------------------------------------')
            print('test_21_push')
        # tests
        #self.assertTrue(...)



if __name__ == '__main__':
    unittest.main()
