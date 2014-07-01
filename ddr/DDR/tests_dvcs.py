from datetime import datetime
import os
import re

import git

import dvcs


def test_repository():
    # set_git_configs
    # repository
    path = '/tmp/test_dvcs.repository-%s' % datetime.now().strftime('%Y%m%d-%H%M%S')
    user = 'gjost'
    mail = 'gjost@densho.org'
    repo = git.Repo.init(path)
    dvcs.repository(path=path, user_name=user, user_mail=mail)
    reader = repo.config_reader()
    assert ('filemode','false') in reader.items('core')
    assert ('name',user) in reader.items('user')
    assert ('email',mail) in reader.items('user')
    assert ('sshcaching','false') in reader.items('annex')

def test_git_version():
    out = dvcs.git_version()
    assert 'git version' in out
    assert 'git-annex version' in out
    assert 'local repository version' in out

def test_latest_commit():
    repo = dvcs.latest_commit(git.Repo(os.getcwd()))
    path = dvcs.latest_commit(os.getcwd())
    nopath = dvcs.latest_commit()
    assert nopath == path == repo
    regex = r'(([0123456789abcdef]+) +\(([a-zA-Z ,/]+)\) [0-9-]+ [0-9:]+ -[0-9]+)'
    assert re.match(regex, repo)

def test_compose_commit_message():
    title = 'made-up title'
    body = 'freeform body text\nbody text line 2'
    agent = 'nosetests'
    expected = '%s\n\n%s\n\n@agent: %s' % (title, body, agent)
    msg = dvcs.compose_commit_message(title, body, agent)
    assert msg == expected

SAMPLE_ANNEX_STATUS = """
supported backends: SHA256 SHA1 SHA512 SHA224 SHA384 SHA256E SHA1E SHA51
supported remote types: git S3 bup directory rsync web hook
trusted repositories: FATAL: ddr-densho-10.git ddr DENIED

Command ssh ["git@mits.densho.org","git-annex-shell 'configlist' '/~/ddr
FATAL: bad git-annex-shell command: git-annex-shell 'configlist' '/~/' a

Command ssh ["git@mits.densho.org","git-annex-shell 'configlist' '/~/'"]
0
semitrusted repositories: 5
	00000000-0000-0000-0000-000000000001 -- web
 	a39a106a-e5c7-11e3-8996-bfa1bcf63a02 -- here (ddrworkstation)
 	a587a176-3dca-11e3-b491-9baacb8840e9
 	a5f4d94d-2073-4b59-8c98-9372012a6cbb -- qnfs
 	c52c412e-467d-11e3-b428-7fb930a6e21c
untrusted repositories: 0
dead repositories: 0
available local disk space: 128 gigabytes (+1 megabyte reserved)
local annex keys: 0
local annex size: 0 bytes
known annex keys: 60
known annex size: 212 megabytes
bloom filter size: 16 mebibytes (0% full)
backend usage: 
	SHA256E: 60
"""

def test_parse_annex_description():
    uuid0 = 'a5f4d94d-2073-4b59-8c98-9372012a6cbb'
    uuid1 = 'a39a106a-e5c7-11e3-8996-bfa1bcf63a02'
    assert dvcs._parse_annex_description(SAMPLE_ANNEX_STATUS, uuid0) == None
    assert dvcs._parse_annex_description(SAMPLE_ANNEX_STATUS, uuid1) == 'ddrworkstation'

# get_annex_description

def test_make_annex_description():
    dl = 'WD201405'
    hn = 'ddrworkstation'
    ph = 'testing'
    ml = 'gjost@densho.org'
    # drive label
    assert dvcs._make_annex_description(drive_label=dl, hostname=hn, partner_host=ph, mail=ml) == dl
    # hostname:domainname
    expected1 = 'ddrworkstation:densho.org'
    assert dvcs._make_annex_description(drive_label=None, hostname=hn, partner_host=hn, mail=ml) == expected1
    # hostname
    assert dvcs._make_annex_description(drive_label=None, hostname=hn, partner_host=ph, mail=ml) == hn
    # TODO Test doesn't cover all possibile combinations!!!

# set_annex_description
# fetch
# repo_status
# annex_status

GITANNEX_WHEREIS = """FATAL: ddr-testing-141.git ddr DENIED

Command ssh ["git@mits.densho.org","git-annex-shell 'configlist' '/~/ddr-testing-141.git'
FATAL: bad git-annex-shell command: git-annex-shell 'configlist' '/~/' at /home/git/gitol

Command ssh ["git@mits.densho.org","git-annex-shell 'configlist' '/~/'"] failed; exit cod
whereis files/ddr-testing-141-1/files/ddr-testing-141-1-master-96c048001e.pdf (2 copies) 
  	643935ea-1cbe-11e3-afb5-3fb5a8f2a937 -- WD5000BMV-2
   	a311a84a-4e48-11e3-ba9f-2fc2ce00326e -- pnr_tmp-ddr
ok
"""
GITANNEX_WHEREIS = """whereis files/ddr-testing-141-1/files/ddr-testing-141-1-master-96c048001e.pdf (2 copies) 
  	643935ea-1cbe-11e3-afb5-3fb5a8f2a937 -- WD5000BMV-2
   	a311a84a-4e48-11e3-ba9f-2fc2ce00326e -- pnr_tmp-ddr
ok
"""
GITANNEX_WHEREIS_EXPECTED = ['WD5000BMV-2', 'pnr_tmp-ddr']

def test_parse_annex_whereis():
    assert dvcs._parse_annex_whereis(GITANNEX_WHEREIS) == GITANNEX_WHEREIS_EXPECTED

# annex_whereis_file

GITOLITE_INFO_OK = """hello ddr, this is git@mits running gitolite3 v3.2-19-gb9bbb78 on git 1.7.2.5

 R W C	ddr-densho-[0-9]+
 R W C	ddr-densho-[0-9]+-[0-9]+
 R W C	ddr-testing-[0-9]+
 R W C	ddr-testing-[0-9]+-[0-9]+
 R W	ddr-densho
 R W	ddr-densho-1
 R W	ddr-testing
 R W	ddr-testing-101
"""
GITOLITE_ORGS_EXPECTED = ['ddr-densho', 'ddr-testing']

def test_gitolite_info_authorized():
    assert dvcs._gitolite_info_authorized(
        status=0, lines=GITOLITE_INFO_OK.split('\n')
    ) == True
    assert dvcs._gitolite_info_authorized(status=1, lines='') == False
    assert dvcs._gitolite_info_authorized(status=1, lines=[]) == False

# gitolite_connect_ok

def test_gitolite_orgs():
    assert dvcs.gitolite_orgs(GITOLITE_INFO_OK.split('\n')) == GITOLITE_ORGS_EXPECTED

# gitolite_info

GIT_DIFF_STAGED = """collection.json
files/ddr-densho-10-1/entity.json
files/ddr-densho-10-1/files/ddr-densho-10-1-master-c85f8d0f91.json
"""
GIT_DIFF_STAGED_EXPECTED = [
    'collection.json',
    'files/ddr-densho-10-1/entity.json',
    'files/ddr-densho-10-1/files/ddr-densho-10-1-master-c85f8d0f91.json',
]

def test_parse_list_staged():
    assert dvcs._parse_list_staged(GIT_DIFF_STAGED) == GIT_DIFF_STAGED_EXPECTED

SAMPLE_COMMIT_LOG = """
commit 4df7877f43a10873ced2c484cc9f65605ee4ca68
Author: DDRAdmin <kinkura@hq.densho.org>
Date:   Tue Apr 22 17:44:37 2014 -0700

    Manual fix for rights.

 collection.json                                                         |    2 +-
 files/ddr-densho-10-1/entity.json                                       |    2 +-
 files/ddr-densho-10-1/files/ddr-densho-10-1-master-c85f8d0f91.json      |    2 +-
"""
SAMPLE_COMMIT_LOG_PARSED = [
    'collection.json',
    'files/ddr-densho-10-1/entity.json',
    'files/ddr-densho-10-1/files/ddr-densho-10-1-master-c85f8d0f91.json',
]

def test_parse_list_committed():
    assert dvcs._parse_list_committed(SAMPLE_COMMIT_LOG) == SAMPLE_COMMIT_LOG_PARSED

# list_committed

SAMPLE_CONFLICTED_0 = """
100755 a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2 1\tpath/to/conflicted_file/01
100755 1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2a 2\tpath/to/conflicted_file/02
100755 ab2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b21 3\tpath/to/conflicted_file/03
"""
SAMPLE_CONFLICTED_1 = ""
SAMPLE_CONFLICTED_0_EXPECTED = [
    'path/to/conflicted_file/01',
    'path/to/conflicted_file/02',
    'path/to/conflicted_file/03',
]
SAMPLE_CONFLICTED_1_EXPECTED = []
def test_parse_list_conflicted():
    assert dvcs._parse_list_conflicted(SAMPLE_CONFLICTED_0) == SAMPLE_CONFLICTED_0_EXPECTED
    assert dvcs._parse_list_conflicted(SAMPLE_CONFLICTED_1) == SAMPLE_CONFLICTED_1_EXPECTED

CONFLICTED_JSON_TEXT = """{
    {
        "record_created": "2013-09-30T12:43:11"
    },
    {
<<<<<<< HEAD
        "record_lastmod": "2013-10-02T12:59:30"
=======
        "record_lastmod": "2013-10-02T12:59:30"
>>>>>>> 0b9d669da8295fc05e092d7abdce22d4ffb50f45
    },
    {
        "status": "completed"
    },
}"""
CONFLICTED_JSON_EXPECTED = [
    {u'record_created': u'2013-09-30T12:43:11'},
    {u'record_lastmod': {'right': u'2013-10-02T12:59:30', 'left': u'2013-10-02T12:59:30'}},
    {u'status': u'completed'},
]

def test_load_conflicted_json():
    assert dvcs.load_conflicted_json(CONFLICTED_JSON_TEXT) == CONFLICTED_JSON_EXPECTED

AUTOMERGE_TEXT = """
Next level meh sriracha, distillery Tonx actually Etsy sustainable Tumblr.
<<<<<<< HEAD
Art party meggings tote bag drinking vinegar distillery jean shorts, mumblecore
farm-to-table flexitarian. Pug small batch Thundercats mustache. Trust fund XOXO
=======
Polaroid blog Kickstarter. Ennui disrupt tote bag, you probably haven't heard of
them VHS food truck DIY 8-bit swag direct trade fingerstache. Cliche wayfarers
>>>>>>> 0a1b2c3d4e5f6a7b8c9d0a1b2c3d4e5f6a7b8c9d
hashtag pour-over, church-key tousled trust fund Tonx Intelligentsia vinyl
photo booth Vice Brooklyn seitan. Meggings irony Echo Park Pitchfork Thundercats.
"""
AUTOMERGE_LEFT_EXPECTED = """
Next level meh sriracha, distillery Tonx actually Etsy sustainable Tumblr.
Art party meggings tote bag drinking vinegar distillery jean shorts, mumblecore
farm-to-table flexitarian. Pug small batch Thundercats mustache. Trust fund XOXO
hashtag pour-over, church-key tousled trust fund Tonx Intelligentsia vinyl
photo booth Vice Brooklyn seitan. Meggings irony Echo Park Pitchfork Thundercats.
"""
AUTOMERGE_RIGHT_EXPECTED = """
Next level meh sriracha, distillery Tonx actually Etsy sustainable Tumblr.
Polaroid blog Kickstarter. Ennui disrupt tote bag, you probably haven't heard of
them VHS food truck DIY 8-bit swag direct trade fingerstache. Cliche wayfarers
hashtag pour-over, church-key tousled trust fund Tonx Intelligentsia vinyl
photo booth Vice Brooklyn seitan. Meggings irony Echo Park Pitchfork Thundercats.
"""

def test_automerge_conflicted():
    assert dvcs.automerge_conflicted(AUTOMERGE_TEXT) == AUTOMERGE_LEFT_EXPECTED
    assert dvcs.automerge_conflicted(AUTOMERGE_TEXT, which='left') == AUTOMERGE_LEFT_EXPECTED
    assert dvcs.automerge_conflicted(AUTOMERGE_TEXT, which='right') == AUTOMERGE_RIGHT_EXPECTED

# TODO merge_add
# TODO merge_commit
# TODO diverge_commit


GIT_STATUS_SYNCED = [
    """## master""",
    """## master\n?? .gitstatus""",
    """## master\n?? .gitstatus\n?? files/ddr-testing-233-1/addfile.log""",
]
GIT_STATUS_AHEAD = [
    """## master...origin/master [ahead 1]""",
    """## master...origin/master [ahead 2]""",
]
GIT_STATUS_BEHIND = [
    """## master...origin/master [behind 1]""",
]
GIT_STATUS_DIVERGED = [
    """## master...origin/master [ahead 1, behind 2]""",
]

def test_synced():
    for status in GIT_STATUS_SYNCED: assert dvcs.synced(status) == 1     # <<<
    for status in GIT_STATUS_AHEAD: assert dvcs.synced(status) == 0
    for status in GIT_STATUS_BEHIND: assert dvcs.synced(status) == 0
    for status in GIT_STATUS_DIVERGED: assert dvcs.synced(status) == 0

def test_ahead():
    for status in GIT_STATUS_SYNCED: assert dvcs.ahead(status) == 0
    for status in GIT_STATUS_AHEAD: assert dvcs.ahead(status) == 1       # <<<
    for status in GIT_STATUS_BEHIND: assert dvcs.ahead(status) == 0
    for status in GIT_STATUS_DIVERGED: assert dvcs.ahead(status) == 0

def test_behind():
    for status in GIT_STATUS_SYNCED: assert dvcs.behind(status) == 0
    for status in GIT_STATUS_AHEAD: assert dvcs.behind(status) == 0
    for status in GIT_STATUS_BEHIND: assert dvcs.behind(status) == 1     # <<<
    for status in GIT_STATUS_DIVERGED: assert dvcs.behind(status) == 0

def test_diverged():
    for status in GIT_STATUS_SYNCED: assert dvcs.diverged(status) == 0
    for status in GIT_STATUS_AHEAD: assert dvcs.diverged(status) == 0
    for status in GIT_STATUS_BEHIND: assert dvcs.diverged(status) == 0
    for status in GIT_STATUS_DIVERGED: assert dvcs.diverged(status) == 1 # <<<

GIT_STATUS_CONFLICTED = [
    ['## master...origin/master [ahead 1, behind 2]','UU changelog','UU collection.json'],
]
GIT_STATUS_PARTIAL_RESOLVED = [
    ['## master...origin/master [ahead 1, behind 2]', 'M  changelog', 'UU collection.json'],
]
GIT_STATUS_RESOLVED = [
    ['## master...origin/master [ahead 1, behind 2]', 'M  changelog', 'M  collection.json'],
]

def test_conflicted():
    for status in GIT_STATUS_SYNCED: assert dvcs.conflicted([status]) == 0
    for status in GIT_STATUS_AHEAD: assert dvcs.conflicted([status]) == 0
    for status in GIT_STATUS_BEHIND: assert dvcs.conflicted([status]) == 0
    for status in GIT_STATUS_DIVERGED: assert dvcs.conflicted([status]) == 0
    for status in GIT_STATUS_CONFLICTED: assert dvcs.conflicted(status) == 1 # <<<

# TODO test PARTIAL_RESOLVED
# TODO test RESOLVED

# TODO repos

def test_is_local():
    url0 = '/tmp/ddr-testing-141.git'
    url1 = 'git@mits.densho.org:ddr-testing-141.git'
    assert dvcs.is_local(url0) == 1
    assert dvcs.is_local(url1) == 0

# TODO local_exists
# TODO is_clone
# TODO remotes
# TODO repos_remotes
