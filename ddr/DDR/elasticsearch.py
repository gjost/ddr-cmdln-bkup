import json
import logging
logger = logging.getLogger(__name__)
import os

import envoy
import requests

from DDR.models import MODELS, MODELS_DIR

MAX_SIZE = 1000000

HARD_CODED_MAPPINGS_PATH = '/usr/local/src/ddr-cmdln/ddr/DDR/es-mappings.json'


def _metadata_files(dirname, recursive=False):
    """Lists absolute paths to .json files in dirname.
    
    Skips/excludes .git directories.
    
    @param dirname: Absolute path
    @param recursive: Whether or not to recurse into subdirectories.
    """
    paths = []
    excludes = ['.git', 'tmp']
    if recursive:
        for root, dirs, files in os.walk(dirname):
            # don't go down into .git directory
            if '.git' in dirs:
                dirs.remove('.git')
            for f in files:
                if f.endswith('.json'):
                    path = os.path.join(root, f)
                    exclude = [1 for x in excludes if x in path]
                    if not exclude:
                        paths.append(path)
    else:
        for f in os.listdir(dirname):
            if f.endswith('.json'):
                path = os.path.join(dirname, f)
                exclude = [1 for x in excludes if x in path]
                if not exclude:
                    paths.append(path)
    return paths


def settings(host):
    """Get Elasticsearch's current settings.
    
    curl -XGET 'http://localhost:9200/twitter/_settings'
    
    @param host: Hostname and port (HOST:PORT).
    """
    url = 'http://%s/_settings' % (host)
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

def model_fields():
    models = {}
    for model in MODELS:
        json_path = os.path.join(MODELS_DIR, '%s.json' % model)
        with open(json_path, 'r') as f:
            data = json.loads(f.read())
        models[model] = data
    return models

def _public_fields():
    """Lists public fields for each model
    
    IMPORTANT: Adds certain dynamically-created fields
    
    @param models: Output of model_fields()
    @returns: dict
    """
    public_fields = {}
    models =  model_fields()
    for model in MODELS:
        modelfields = []
        for field in models[model]:
            if field['elasticsearch'].get('public',None):
                modelfields.append(field['name'])
        public_fields[model] = modelfields
    # add dynamically created fields
    public_fields['file'].append('path_rel')
    return public_fields

def mappings(host, index):
    """Get mappings for index.
    
    curl -XGET 'http://localhost:9200/twitter/_mappings?pretty=1'
    
    @param host: Hostname and port (HOST:PORT).
    """
    url = 'http://%s/_mapping?pretty=1' % (host)
    r = requests.get(url)
    return r.text
    #return json.dumps(mapping, indent=4, separators=(',', ': '), sort_keys=True))
    #return json.loads(r.text)


# Each item in this list is a mapping dict in the format ElasticSearch requires.
# Mappings for each type have to be uploaded individually (I think).
MAPPINGS = [
    {
        'collection': {
            '_source': {'enabled': True},
            'date_detection':0,
            'properties': {}
        }
    },
    {
        'entity': {
            '_source': {'enabled': True},
            'date_detection':0,
            'properties': {}
        }
    },
    {
        'file': {
            '_source': {'enabled': True},
            'date_detection':0,
            'properties': {}
        }
    }
]

def _make_mappings():
    """Takes MAPPINGS and adds field properties from MODEL_FIELDS
    Returns a nice list of mapping dicts.
    
    Expects MODEL.json to be formatted thusly:
        [
            {
                "name": "FIELD NAME",
                ...
                "elasticsearch": {
                    "properties": {
                        ...
                    }
                }
            }
        ]
    """
    mappings = MAPPINGS
    for mapping in mappings:
        model = mapping.keys()[0]
        json_path = os.path.join(MODELS_DIR, '%s.json' % model)
        with open(json_path, 'r') as f:
            data = json.loads(f.read())
        for field in data:
            fname = field['name']
            mapping[model]['properties'][fname] = field['elasticsearch']['properties']
    return mappings

def _mapping(mappings, model):
    """Get mapping for the specified model
    """
    for m in mappings:
        if m.keys()[0] == model:
            return m
    return None

def _create_index(host, index):
    """Create the specified index.
    
    curl -XPOST 'http://localhost:9200/twitter/' -d @mappings.json
    
    @param host: Hostname and port (HOST:PORT).
    @param index: Name of the target index.
    @returns: JSON dict with status codes and responses
    """
    status = {}
    
    # create the index
    logger.debug('_create_index(%s, %s)' % (host, index))
    url = 'http://%s/%s/' % (host, index)
    headers = {'content-type': 'application/json'}
    r = requests.put(url, headers=headers)
    logger.debug('%s %s' % (r.status_code, r.text))
    status['create'] = {'status':r.status_code, 'response':r.text}
    
    # mappings
    status['mappings'] = {}
    for mapping in _make_mappings():
        model = mapping.keys()[0]
        logger.debug(model)
        logger.debug(json.dumps(mapping, indent=4, separators=(',', ': '), sort_keys=True))
        payload = json.dumps(mapping)
        url = 'http://%s/%s/%s/_mapping' % (host, index, model)
        headers = {'content-type': 'application/json'}
        r = requests.put(url, data=payload, headers=headers)
        logger.debug('%s %s' % (r.status_code, r.text))
        status['mappings'][model] = {'status':r.status_code, 'response':r.text}
    return status

def _delete_index(host, index):
    """Delete the specified index.
    
    curl -XDELETE 'http://localhost:9200/twitter/'
    
    @param host: Hostname and port (HOST:PORT).
    @param index: Name of the target index.
    @returns: JSON dict with status code and response
    """
    logger.debug('_delete_index(%s, %s)' % (host, index))
    url = 'http://%s/%s/' % (host, index)
    r = requests.delete(url)
    logger.debug('%s %s' % (r.status_code, r.text))
    return {'status':r.status_code, 'response':r.text}


def _filter_payload(data, public_fields):
    """If requested, removes non-public fields from document before sending to ElasticSearch.
    
    @param data: Standard DDR list-of-dicts data structure.
    @param public_fields: List of field names; if present, fields not in list will be removed.
    """
    if public_fields and data and isinstance(data, list):
        for field in data[1:]:
            fieldname = field.keys()[0]
            if fieldname not in public_fields:
                data.remove(field)
                print('removed %s' % fieldname)

def _clean_dict(data):
    """Remove null or empty fields; ElasticSearch chokes on them.
    """
    if data and isinstance(data, dict):
        for key in data.keys():
            if not data[key]:
                del(data[key])

def _clean_creators(data):
    """Normalizes contents of 'creators' field.
    There are lots of weird variations on this field.
    We want all of them to end up as simple lists of strings.
    """
    # turn strings into lists
    if isinstance(data, basestring):
        if data == '[]':
            data = []
        elif data == '':
            data = []
        elif ';' in data:
            # ex: "Preliminary Hearing Board"; "YMCA";
            data = [x.strip() for x in data.strip().split(';')]
        elif '\r\n' in data:
            data = [x.strip() for x in data.strip().split('\r\n')]
        elif '\n' in data:
            data = [x.strip() for x in data.strip().split('\n')]
        else:
            # ex: Greenwood, Jonny:composer
            # ex: Snead, John
            data = [data]
    # Get just the name. Don't add a role if none selected.
    # 'Author' was default role so ignore.
    # ex: [u'Ninomiya, L.A.']
    # ex: [u'Mitsuoka, Norio: photographer']
    # ex: [{u'namepart': u'', u'role': u'author'}]
    # ex: [{u'namepart': u'Boyle, Rob:editor', u'role': u'author'}, {u'namepart': u'Cross, Brian:editor', u'role': u'author'}]
    # ex: [{u'namepart': u'"YMCA:publisher"', u'role': u'author'}]
    # ex: [{u'namepart': u'Heart Mountain YMCA', u'role': u'author'}]
    names = []
    for element in data:
        name = None
        # make everything into a string
        if isinstance(element, basestring):
            name = element
        elif isinstance(element, dict):
            # only keep the 'namepart' of a dict
            if element.get('namepart', None) and element['namepart']:
                name = element['namepart']
        if name:
            names.append(name)
    return names

def _clean_payload(data):
    """Remove null or empty fields; ElasticSearch chokes on them.
    """
    # remove info about DDR release, git-annex version, etc
    if data and isinstance(data, list):
        # skip the initial metadata field
        data = data[1:]
        # remove empty fields
        for field in data:
            for key in field.keys():
                if key == 'creators':
                    field[key] = _clean_creators(field[key])
            # rm null or empty fields
            _clean_dict(field)

def post(path, host, index, model, newstyle=False, public_fields=[]):
    """Add a new document to an index or update an existing one.
    
    This function can produce ElasticSearch documents in two formats:
    - old-style list-of-dicts used in the DDR JSON files.
    - normal dicts used by ddr-public.
    
    DDR metadata JSON files are structured as a list of fieldname:value dicts.
    This is done so that the fields are always in the same order, making it
    possible to easily see the difference between versions of a file.
    
    In ElasticSearch, documents are structured in a normal dict so that faceting
    works properly.
    
    curl -XPUT 'http://localhost:9200/ddr/collection/ddr-testing-141' -d '{ ... }'
    
    @param path: Absolute path to the JSON file.
    @param host: Hostname and port (HOST:PORT).
    @param index: Name of the target index.
    @param model: Type of object ('collection', 'entity', 'file')
    @param newstyle: Use new ddr-public ES document format.
    @param public_fields: List of field names; if present, fields not in list will be removed.
    @returns: JSON dict with status code and response
    """
    logger.debug('post(%s, %s, %s, %s, newstyle=%s, public=%s)' % (path, index, model, path, newstyle, public_fields))
    if not os.path.exists(path):
        return {'status':1, 'response':'path does not exist'}
    with open(path, 'r') as f:
        filedata = json.loads(f.read())
    
    # TODO die if document is public=False or status=incomplete
    
    # remove non-public fields
    _filter_payload(filedata, public_fields)
    # normalize field contents
    _clean_payload(filedata)
    
    if newstyle:
        # restructure from list-of-fields dict to straight dict used by ddr-public
        data = {}
        for field in filedata:
            for k,v in field.iteritems():
                data[k] = v
        
        if model in ['collection', 'entity']:
            if not (data and data.get('id', None)):
                return {'status':2, 'response':'no id'}
            cid = data['id']
            url = 'http://%s/%s/%s/%s' % (host, index, model, cid)
        elif model in ['file']:
            if not (data and data.get('path_rel', None)):
                return {'status':3, 'response':'no path_rel'}
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
        payload = json.dumps(data)
        
    else:
        # old-style list-of-fields dict used by ddr-local
        data = filedata
        
        if model in ['collection', 'entity']:
            if not (data and data[1].get('id', None)):
                return {'status':2, 'response':'no id'}
            cid = None
            for field in data:
                if field.get('id',None):
                    cid = field['id']
            url = 'http://%s/%s/%s/%s' % (host, index, model, cid)
        elif model in ['file']:
            if not (data and data[1].get('path_rel', None)):
                return {'status':3, 'response':'no path_rel'}
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
        payload = json.dumps({'d': data})

    if url:
        logger.debug(url)
        #logger.debug(payload)
        headers = {'content-type': 'application/json'}
        r = requests.put(url, data=payload, headers=headers)
        #logger.debug('%s %s' % (r.status_code, r.text))
        return {'status':r.status_code, 'response':r.text}
    return {'status':4, 'response':'unknown problem'}

def get(host, index, model, id):
    """GET a single document.
    
    GET http://192.168.56.101:9200/ddr/collection/{repo}-{org}-{cid}
    
    @param host: Hostname and port (HOST:PORT).
    @param index: Name of the target index.
    @param model: Type of object ('collection', 'entity', 'file')
    @param id: object ID
    @returns: document, or JSON dict with status code and response
    """
    url = 'http://%s/%s/%s/%s' % (host, index, model, id)
    headers = {'content-type': 'application/json'}
    r = requests.get(url, headers=headers)
    return {'status':r.status_code, 'response':r.text}

def delete(host, index, model, id):
    """Delete specified document from the index.
    
    curl -XDELETE 'http://localhost:9200/twitter/tweet/1'
    
    @param host: Hostname and port (HOST:PORT).
    @param index: Name of index.
    @param model: Type of object ('collection', 'entity', 'file')
    @param id: object ID
    @returns: JSON dict with status code and response
    """
    url = 'http://%s/%s/%s/%s' % (host, index, model, id)
    r = requests.delete(url)
    return {'status':r.status_code, 'response':r.text}


def index(host, index, path, recursive=False, newstyle=False, public=True, paths=None):
    """(Re)index with data from the specified directory.
    
    @param host: Hostname and port (HOST:PORT).
    @param index: Name of the target index.
    @param path: Absolute path to metadata file or directory containing metadata files.
    @param recursive: Whether or not to recurse into subdirectories.
    @param newstyle: Use new ddr-public ES document format.
    @param public: For publication (fields not marked public will be ommitted).
    @param paths: Absolute paths to directory containing collections.
    @returns: number successful,list of paths that didn't work out
    """
    logger.debug('index(%s, %s, %s)' % (host, index, path))
    
    public_fields = _public_fields()
    
    # process a single file if requested
    if os.path.isfile(path):
        paths = [path]
    
    if not paths:
        paths = _metadata_files(path, recursive)
    
    SUCCESS_STATUSES = [200, 201]
    successful = 0
    bad_paths = []
    for path in paths:
        model = None
        if 'organization.json' in path:
            pass
        elif 'collection.json' in path:
            model = 'collection'
        elif 'entity.json' in path:
            model = 'entity'
        elif ('master' in path) or ('mezzanine' in path):
            model = 'file'
        publicfields = []
        if public and model:
            publicfields = public_fields[model]
        if path and index and model:
            print('adding %s' % path)
            result = post(path, host, index, model, newstyle, publicfields)
            status_code = result['status']
            response = result['response']
            if status_code in SUCCESS_STATUSES:
                successful += 1
            else:
                bad_paths.append((path,status_code,response))
            #print(status_code)
        else:
            logger.error('missing information!: %s' % path)
    logger.debug('INDEXING COMPLETED')
    return {'total':len(paths), 'successful':successful, 'bad':bad_paths}

def query(host, index, model=None, query='', filters={}, sort='', fields='', size=MAX_SIZE):
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
