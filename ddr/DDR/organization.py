"""
Conventions:
- Local remotes are named after the drive label
- Network remotes are named: 
- Drive files are named 'LABEL.csv'
- 

When add/rm local collection, add/rm repo to local drive file.

New drive:

"""


import ConfigParser
import csv
import os
import re



DRIVE_FILE_FIELDS = 'id,level'

DELIMITER = ','
QUOTECHAR = '"'
QUOTING = csv.QUOTE_MINIMAL

LEVELS = ['meta', 'access', 'all']



def drives(path):
    """Gets list of drives for which there are CSV files.
    
    @param path: Abs path to org repo (drive label extracted from this)
    @returns drives: List of drive labels
    """
    pattern = re.compile('.csv$')
    return [os.path.splitext(f)[0] for f in os.listdir(path) if pattern.search(f)]

def drive_files(path):
    """Gets list of paths to drive files in the repo.
    
    @param path: Abs path to org repo (drive label extracted from this)
    """
    return [os.path.join(path, '%s.csv' % drive) for drive in drives(path)]

def read_drive_file(path):
    """Reads drive file, returns list of repos and their levels
    
    @param path: Absolute path to drive file.
    @returns: List of dicts (id, level)
    """
    if not os.path.exists(path):
        return None
    repos = []
    with open(path, 'rb') as f:
        reader = csv.reader(f, delimiter=DELIMITER, quotechar=QUOTECHAR)
        for id,level in reader:
            repos.append({'id':id, 'level':level})
    return repos

def write_drive_file(repos, path):
    """
    @param repos: List of dicts (id, level)
    @param path: Absolute path to drive file.
    """
    with open(path, 'wb') as f:
        writer = csv.writer(f, delimiter=DELIMITER, quotechar=QUOTECHAR, quoting=QUOTING)
        for r in repos:
            writer.writerow(r['id'], r['level'])

def read_mrconfig(path):
    """
    @param path: Absolute path to .mrconfig file.
    @returns default,repos: Dict of defaults, list of repository IDs.
    """
    config = ConfigParser.ConfigParser()
    config.readfp(open(path))
    repos = [os.path.basename(s) for s in config.sections()]
    return config.defaults(),repos

def make_mrconfig(defaults, base_path, server, repos, output_file=None):
    """Makes an .mrconfig file.
    
    import organization
    p = '/media/WD5000BMV-2/ddr/ddr-testing/WD5000BMV-2.csv'
    repos = organization.read_drive_file(p)
    defaults = {'ddrstatus': 'ddr status "$@"', 'ddrsync': 'ddr sync "$@"'}
    base_path = '/media/WD5000BMV-2/ddr'
    server = 'git@mits.densho.org'
    mrconfig = organization.mrconfig(defaults, base_path, server, repos)
    with open('/tmp/mrconfig', 'wb') as cf:
        mrconfig.write(cf)

    @param defaults: dict of settings.
    @param base_path: Absolute path to the directory in which the repos are located.
    @param server: USERNAME@DOMAIN for Gitolite server.
    @param repos: List of dicts (id, level)
    @returns mrconfig: A ConfigParser object
    """
    c = ConfigParser.ConfigParser(defaults)
    for r in repos:
        section = os.path.join(base_path, r['id'])
        c.add_section(section)
        c.set(section, 'checkout', "git clone '%s:%s.git' '%s'" % (server, r['id'], r['id']))
    if output_file:
        output_file
    return c

def drive_file_path(orgrepo_path):
    """Gets path to CSV file for the specified drive.
    
    @param orgrepo_path: Abs path to org repo (drive label extracted from this)
    """
    label = orgrepo_path.split(os.sep)[2]
    filename = '%s.csv' % label
    path = os.path.join(orgrepo_path, filename)
    return path
