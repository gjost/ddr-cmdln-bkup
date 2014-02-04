import json
import logging
logger = logging.getLogger(__name__)
import os

import envoy
import requests

MAX_SIZE = 1000000


def _clean_dict(data):
    """Remove null or empty fields; ElasticSearch chokes on them.
    """
    if data and isinstance(data, dict):
        for key in data.keys():
            if not data[key]:
                del(data[key])

def _clean_payload(data):
    """Remove null or empty fields; ElasticSearch chokes on them.
    """
    # remove info about DDR release, git-annex version, etc
    if data and isinstance(data, list):
        data = data[1:]
        # remove empty fields
        for field in data:
            _clean_dict(field)

def _metadata_files(dirname):
    """Lists absolute paths to .json files in dirname.
    
    Skips/excludes .git directories.
    
    @param path: Absolute path
    """
    paths = []
    excludes = ['tmp']
    for root, dirs, files in os.walk(dirname):
        if '.git' in dirs:
            dirs.remove('.git')
        for f in files:
            if f.endswith('.json'):
                path = os.path.join(root, f)
                exclude = [1 for x in excludes if x in path]
                if not exclude:
                    paths.append(path)
    return paths


def settings(host):
    """Get Elasticsearch's current settings.
    
    curl -XGET 'http://localhost:9200/twitter/_settings'
    
    @param host: Hostname and port (HOST:PORT).
    """
    url = 'http://%s/_status' % (host)
    r = requests.get(url)
    return json.loads(r.text)

def status(host):
    """Get Elasticsearch's current settings.
    
    curl -XGET 'http://localhost:9200/_status'

    @param host: Hostname and port (HOST:PORT).
    """
    url = 'http://%s/_status' % (host)
    r = requests.get(url)
    return json.loads(r.text)

def index_exists(host, index):
    """Indicates whether the given ElasticSearch index exists.
    
    curl -XHEAD 'http://localhost:9200/ddr/collection'
    
    @param host: Hostname and port (HOST:PORT).
    @param index: Name of the target index.
    @return True/False
    """
    url = 'http://%s/%s' % (host, index)
    r = requests.head(url)
    if r.status_code == 200:
        return True
    return False

def model_exists(host, index, model):
    """Indicates whether an ElasticSearch 'type' exists for the given model.
    
    curl -XHEAD 'http://localhost:9200/ddr/collection'
    
    @param host: Hostname and port (HOST:PORT).
    @param index: Name of the target index.
    @param model: Type of object ('collection', 'entity', 'file')
    @return True/False
    """
    url = 'http://%s/%s/%s' % (host, index, model)
    r = requests.head(url)
    if r.status_code == 200:
        return True
    return False

def document_exists(host, index, model, id):
    """Indicates whether a given document exists.
    
    curl -XHEAD 'http://localhost:9200/ddr/collection/ddr-testing-123'
    
    @param host: Hostname and port (HOST:PORT).
    @param index: Name of the target index.
    @param model: Type of object ('collection', 'entity', 'file')
    @param id: object ID
    @return True/False
    """
    url = 'http://%s/%s/%s/%s' % (host, index, model, id)
    r = requests.head(url)
    if r.status_code == 200:
        return True
    return False

def add_document(path, host, index, model):
    """Add a new document to an index or update an existing one.
    
    curl -XPUT 'http://localhost:9200/ddr/collection/ddr-testing-141' -d '{ ... }'
    
    @param path: Absolute path to the JSON file.
    @param host: Hostname and port (HOST:PORT).
    @param index: Name of the target index.
    @param model: Type of object ('collection', 'entity', 'file')
    @return 0 if successful, status code if not.
    """
    logger.debug('add_document(%s, %s, %s, %s)' % (path, index, model, path))
    if not os.path.exists(path):
        return 1
    headers = {'content-type': 'application/json'}
    with open(path, 'r') as f:
        data = json.loads(f.read())
    _clean_payload(data)
    
    if model in ['collection', 'entity']:
        if not (data and data[1].get('id', None)):
            return 2
        cid = None
        for field in data:
            if field.get('id',None):
                cid = field['id']
        url = 'http://%s/%s/%s/%s' % (host, index, model, cid)
        
    elif model in ['file']:
        if not (data and data[1].get('path_rel', None)):
            return 2
        filename = None
        basename_orig = None
        label = None
        for field in data:
            if field.get('path_rel',None):
                filename,extension = os.path.splitext(field['path_rel'])
            if field.get('basename_orig', None):
                basename_orig = field['basename_orig']
            if field.get('label', None):
                label = field['label']
        if basename_orig and not label:
            label = basename_orig
        elif filename and not label:
            label = filename
        data.append({'id': filename})
        data.append({'title': label})
        url = 'http://%s/%s/%s/%s' % (host, index, model, filename)
        
    else:
        url = None
        
    if url:
        payload = json.dumps({'d': data})
        logger.debug(url)
        logger.debug(payload)
        r = requests.put(url, data=payload, headers=headers)
        return r.status_code
    return 3

def delete_document(host, index, model, id):
    """Delete specified document from the index.
    
    curl -XDELETE 'http://localhost:9200/twitter/tweet/1'
    
    @param host: Hostname and port (HOST:PORT).
    @param index: Name of index.
    @param model: Type of object ('collection', 'entity', 'file')
    @param id: object ID
    """
    url = 'http://%s/%s/%s/%s' % (host, index, model, id)
    r = requests.delete(url)
    return r.status_code

def index(dirname, host, index, paths=None):
    """(Re)index with data from the specified directory.
    
    @param paths: Absolute paths to directory containing collections.
    @param host: Hostname and port (HOST:PORT).
    @param index: Name of the target index.
    """
    logger.debug('index(%s, %s)' % (host, index))
    if not paths:
        paths = _metadata_files(dirname)
    for path in paths:
        model = None
        if 'collection.json' in path:
            model = 'collection'
        elif 'entity.json' in path:
            model = 'entity'
        elif ('master' in path) or ('mezzanine' in path):
            model = 'file'
        if path and index and model:
            print('adding %s' % path)
            status = add_document(path, host, index, model)
            print(status)
            logger.debug('%s: %s' % (model, path))
        else:
            logger.error('missing information!: %s' % path)
    logger.debug('INDEXING COMPLETED')

def delete_index(host, index):
    """Delete the specified index.
    
    curl -XDELETE 'http://localhost:9200/twitter/'
    
    @param host: Hostname and port (HOST:PORT).
    @param index: Name of the target index.
    @return status code
    """
    url = 'http://%s/%s/' % (host, index)
    r = requests.delete(url)
    return r.status_code

def get(host, index, model, id):
    """GET a single document.
    
    GET http://192.168.56.101:9200/ddr/collection/{repo}-{org}-{cid}
    
    @param host: Hostname and port (HOST:PORT).
    @param index: Name of the target index.
    @param model: Type of object ('collection', 'entity', 'file')
    @param id: object ID
    """
    url = 'http://%s/%s/%s/%s' % (host, index, model, id)
    headers = {'content-type': 'application/json'}
    r = requests.get(url, headers=headers)
    data = json.loads(r.text)
    if data.get('exists', False):
        hits = []
        if data and data.get('_source', None) and data['_source'].get('d', None):
            hits = data['_source']['d']
        return hits
    return None

def query(host, index='ddr', model=None, query='', filters={}, sort='', fields='', size=MAX_SIZE):
    """Run a query, get a list of zero or more hits.
    
    curl -XGET 'http://localhost:9200/twitter/tweet/_search?q=user:kimchy&pretty=true'
    
    @param host: Hostname and port (HOST:PORT).
    @param index: Name of the target index.
    @param model: Type of object ('collection', 'entity', 'file')
    @param query: User's search text
    @param filters: dict
    @param sort: dict
    @param fields: str
    @param size: int Number of results to return
    @returns list of hits (dicts)
    """
    _clean_dict(filters)
    _clean_dict(sort)
    
    if model and query:
        url = 'http://%s/%s/%s/_search?q=%s&pretty=true' % (host, index, model, query)
    else:
        url = 'http://%s/%s/_search?q=%s&pretty=true' % (host, index, query)
    
    payload = {'size':size,}
    if fields:  payload['fields'] = fields
    if filters: payload['filter'] = {'term':filters}
    if sort:    payload['sort'  ] = sort
    logger.debug(str(payload))
    
    headers = {'content-type': 'application/json'}
    r = requests.post(url, data=json.dumps(payload), headers=headers)
    data = json.loads(r.text)
    hits = []
    if data and data.get('hits', None):
        hits = data['hits']['hits']
    return hits
