import json
import logging
logger = logging.getLogger(__name__)
import os

import envoy
import requests

MAX_SIZE = 1000000

HARD_CODED_MAPPINGS_PATH = '/usr/local/src/ddr-cmdln/ddr/DDR/es-mappings.json'


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

def create_index(host, index):
    """Create the specified index.
    
    curl -XPOST 'http://localhost:9200/twitter/' -d @mappings.json
    
    @param host: Hostname and port (HOST:PORT).
    @param index: Name of the target index.
    @return status code
    """
    logger.debug('delete_index(%s, %s)' % (host, index))
    url = 'http://%s/%s/' % (host, index)
    with open(HARD_CODED_MAPPINGS_PATH, 'r') as f:
        data = json.loads(f.read())
    logger.debug('mappings: %s' % data)
    payload = json.dumps({'d': data})
    headers = {'content-type': 'application/json'}
    r = requests.put(url, data=payload, headers=headers)
    logger.debug('%s %s' % (r.status_code, r.text))
    return r.status_code

def delete_index(host, index):
    """Delete the specified index.
    
    curl -XDELETE 'http://localhost:9200/twitter/'
    
    @param host: Hostname and port (HOST:PORT).
    @param index: Name of the target index.
    @return status code
    """
    logger.debug('delete_index(%s, %s)' % (host, index))
    url = 'http://%s/%s/' % (host, index)
    r = requests.delete(url)
    logger.debug('%s %s' % (r.status_code, r.text))
    return r.status_code

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

def put_document(path, host, index, model):
    """Add a new document to an index or update an existing one.
    
    curl -XPUT 'http://localhost:9200/ddr/collection/ddr-testing-141' -d '{ ... }'
    
    @param path: Absolute path to the JSON file.
    @param host: Hostname and port (HOST:PORT).
    @param index: Name of the target index.
    @param model: Type of object ('collection', 'entity', 'file')
    @return 0 if successful, status code if not.
    """
    logger.debug('put_document(%s, %s, %s, %s)' % (path, index, model, path))
    if not os.path.exists(path):
        return 1
    headers = {'content-type': 'application/json'}
    with open(path, 'r') as f:
        filedata = json.loads(f.read())
    _clean_payload(filedata)
    
    # restructure from list-of-fields dict to a straight dict
    data = {}
    for field in filedata:
        for k,v in field.iteritems():
            data[k] = v
    
    if model in ['collection', 'entity']:
        if not (data and data.get('id', None)):
            return 2
        cid = data['id']
        url = 'http://%s/%s/%s/%s' % (host, index, model, cid)
        
    elif model in ['file']:
        if not (data and data.get('path_rel', None)):
            return 2
        filename = None
        extension = None
        if data.get('path_rel',None):
            filename,extension = os.path.splitext(data['path_rel'])
        basename_orig = data.get('basename_orig', None)
        label = data.get('label', None)
        if basename_orig and not label:
            label = basename_orig
        elif filename and not label:
            label = filename
        data['id'] = filename
        data['title'] = label
        url = 'http://%s/%s/%s/%s' % (host, index, model, filename)
        
    else:
        url = None
    
    if url:
        payload = json.dumps({'d': data})
        logger.debug(url)
        #logger.debug(payload)
        r = requests.put(url, data=payload, headers=headers)
        logger.debug('%s %s' % (r.status_code, r.text))
        return r.status_code
    return 3

def get_document(host, index, model, id):
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
            status = put_document(path, host, index, model)
            print(status)
        else:
            logger.error('missing information!: %s' % path)
    logger.debug('INDEXING COMPLETED')

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
    @returns raw ElasticSearch query output
    """
    _clean_dict(filters)
    _clean_dict(sort)
    
    if model and query:
        url = 'http://%s/%s/%s/_search?q=%s' % (host, index, model, query)
    else:
        url = 'http://%s/%s/_search?q=%s' % (host, index, query)
    
    payload = {'size':size,}
    if fields:  payload['fields'] = fields
    if filters: payload['filter'] = {'term':filters}
    if sort:    payload['sort'  ] = sort
    logger.debug(str(payload))
    
    headers = {'content-type': 'application/json'}
    r = requests.post(url, data=json.dumps(payload), headers=headers)
    return json.loads(r.text)

def facet_terms( host, index, facet, order='term', all_terms=True, model=None ):
    """Gets list of terms for the facet.
    
    $ curl -XGET 'http://192.168.56.101:9200/ddr/entity/_search?format=yaml' -d '{
      "fields": ["id"],
      "query": { "match_all": {} },
      "facets": {
        "genre_facet_result": {
          "terms": {
            "order": "count",
            "field": "genre"
          }
        }
      }
    }'
    Sample results:
        {
          u'_type': u'terms',
          u'missing': 203,
          u'total': 49,
          u'other': 6,
          u'terms': [
            {u'term': u'photograph', u'count': 14},
            {u'term': u'ephemera', u'count': 6},
            {u'term': u'advertisement', u'count': 6},
            {u'term': u'book', u'count': 5},
            {u'term': u'architecture', u'count': 3},
            {u'term': u'illustration', u'count': 2},
            {u'term': u'fieldnotes', u'count': 2},
            {u'term': u'cityscape', u'count': 2},
            {u'term': u'blank_form', u'count': 2},
            {u'term': u'portrait, u'count': 1'}
          ]
        }

    @param host: Hostname and port (HOST:PORT).
    @param index: Name of the target index.
    @param facet: Name of field
    @param order: term, count, reverse_term, reverse_count
    @param model: (optional) Type of object ('collection', 'entity', 'file')
    @returns raw output of facet query
    """
    if model:
        url = 'http://%s/%s/%s/_search?' % (host, index, model)
    else:
        url = 'http://%s/%s/_search?format=pretty' % (host, index)
    payload = {
        "fields": ["id"],
        "query": { "match_all": {} },
        "facets": {
            "results": {
                "terms": {
                    "order": order,
                    "all_terms": all_terms,
                    "field": facet
                }
            }
        }
    }
    headers = {'content-type': 'application/json'}
    r = requests.post(url, data=json.dumps(payload), headers=headers)
    data = json.loads(r.text)
    return data['facets']['results']
