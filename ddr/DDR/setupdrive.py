import os

import envoy
import git

from DDR import commands
from DDR import organization


GROUPFILE='/media/WD5000BMV-2/ddr/ddr-testing/TS1TB2013.csv'
REMOTE_BASE='/media/WD5000BMV-2/ddr'
LABEL='WD5000BMV-2'
SERVER='git@mits.densho.org'
USER_NAME='gjost'
USER_MAIL='gjost@densho.org'

CWD = os.getcwd()
BASE = CWD

repos = organization.read_group_file(GROUPFILE)
for r in repos:
    print(r)

#mr update
for r in repos:
    print('')
    print('------------------------------------------------------------------------')
    repo_path = os.path.join(BASE, r['id'])
    
    print('[mr clone/update]')
    if os.path.exists(repo_path):
        print('updating %s' % repo_path)
        repo = git.Repo(repo_path)
        # fetch
        repo.git.fetch('origin')
        repo.git.checkout('master')
        repo.git.pull('origin', 'master')
        repo.git.checkout('git-annex')
        repo.git.pull('origin', 'git-annex')
        repo.git.checkout('master')
        print('ok')
    else:
        url = '%s:%s.git' % (SERVER, r['id'])
        print('cloning %s' % url)
        repo = git.Repo.clone_from(url, r['id'])
        print('ok')
    
    print('[add/update remotes]')
    remote_path = os.path.join(REMOTE_BASE, r['id'])
    if LABEL in [rem.name for rem in repo.remotes]:
        print('exists')
    else:
        repo.create_remote(LABEL, remote_path)
        print('added')
    
    print('[annex sync]')
    #cmd = 'cd %s ; git annex sync' % repo_path
    #print(cmd)
    #r = envoy.run(cmd)
    #print(r.status_code)
    #print(r.std_out)
    commands.sync(USER_NAME, USER_MAIL, repo_path)
    print('ok')
    
    print('[annex-get]')
    level = r['level']
    print('%s - %s' % (repo_path, level))
    #organization.repo_annex_get(repo_path, level)
    ACCESS_SUFFIX = '-a.jpg'
    print(level)
<<<<<<< HEAD
    
=======
>>>>>>> 57ed61ee0860f28e48034d9c3952b9fb3d1d0632
    if level == 'access':
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if file.endswith(ACCESS_SUFFIX):
<<<<<<< HEAD
                    path_rel = os.path.join(root, file).replace(repo_path, '')[1:]
                    response = repo.git.annex('get', path_rel)
                    print('    %s' % response)
    
=======
                    print('    git annex get %s' % file)
                    response = repo.git.annex('get', file)
                    print('    %s' % response)
>>>>>>> 57ed61ee0860f28e48034d9c3952b9fb3d1d0632
    elif level == 'all':
        print('git annex get .')
        response = repo.git.annex('get', '.')
        print('    %s' % response)
<<<<<<< HEAD
    
=======
>>>>>>> 57ed61ee0860f28e48034d9c3952b9fb3d1d0632
    print('ok')
