README = """ddr-cmdln Flask API

------------------------------------------------------------------------

GET  /storage/removables
GET  /storage/removables-mounted
GET  /storage/active-device
GET  /storage/status
GET  /storage/mount-point
POST /storage/mount
POST /storage/unmount

GET  dvcs/git-version
GET  dvcs/latest-commit
GET  dvcs/status

GET  inventory/repository
GET  inventory/organizations
GET  inventory/collections
POST inventory/sync-group

POST collection/create
POST collection/delete
POST collection/update
POST collection/clone
POST collection/sync
GET  collection/changelog
GET  collection/control
GET  collection/json
GET  collection/status
GET  collection/annex-status

POST entity/create
POST entity/update
POST entity/delete
POST entity/add-file
GET  entity/changelog
GET  entity/control
GET  entity/json

POST file/delete

GET  search/indexes
GET  search/mappings
GET  search/facets
GET  search/facet/{facet}
POST search/index
GET  search/exists/{object-id}
GET  search/get/{object-id}
GET  search/query

------------------------------------------------------------------------

INSTALL
    sudo pip install flask flask-script

RUN
    $ cd /usr/local/src/ddr-cmdln/ddr/DDR
    $ python ./api.py runserver -h 0.0.0.0 -p 5000 -dr

HELP
    $ python ./api.py runserver --help
"""

import json

from flask import Flask
from flask.ext.script import Manager

app = Flask(__name__)
manager = Manager(app)

import commands
import dvcs
import storage


@app.route('/')
@app.route('/index')
def index():
    return "<pre>%s</pre>" % README

# ----------------------------------------------------------------------

@app.route('/storage/removables')
def removables():
    data = json.dumps(storage.removables())
    return data

@app.route('/storage/removables-mounted')
def removables_mounted():
    data = json.dumps(storage.removables_mounted())
    return data

# ----------------------------------------------------------------------

@app.route('/dvcs/git-version')
def git_version():
    path = '/var/www/media/base/ddr-testing-141'
    commit = dvcs.git_version()
    return commit

@app.route('/dvcs/latest-commit')
def latest_commit():
    path = '/var/www/media/base/ddr-testing-141'
    repo = dvcs.repository(path)
    commit = dvcs.latest_commit(repo)
    return commit

@app.route('/dvcs/status')
def status():
    path = '/var/www/media/base/ddr-testing-141'
    status = dvcs.repo_status(path)
    return status

@app.route('/dvcs/annex-status')
def annex_status():
    path = '/var/www/media/base/ddr-testing-141'
    status = dvcs.annex_status(path)
    return status

# ----------------------------------------------------------------------

@app.route('/collections')
def collections():
    collections = commands.collections_local('/var/www/media/base', 'ddr', 'testing')
    data = json.dumps(collections)
    return data


if __name__ == '__main__':
    manager.run()
