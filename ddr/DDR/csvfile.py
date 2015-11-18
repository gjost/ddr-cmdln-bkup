from collections import OrderedDict
import logging

from DDR import identifier


def make_row_dict(headers, row):
    """Turns CSV row into a dict with the headers as keys
    
    >>> headers0 = ['id', 'created', 'lastmod', 'title', 'description']
    >>> row0 = ['id', 'then', 'now', 'title', 'descr']
    {'title': 'title', 'description': 'descr', 'lastmod': 'now', 'id': 'id', 'created': 'then'}

    @param headers: List of header field names
    @param row: A single row (list of fields, not dict)
    @returns: OrderedDict
    """
    d = OrderedDict()
    for n in range(0, len(row)):
        d[headers[n]] = row[n]
    return d

def make_rowds(rows):
    """Takes list of rows (from csv lib) and turns into list of rowds (dicts)
    
    @param rows: list
    @returns: (headers, list of OrderedDicts)
    """
    headers = rows.pop(0)
    return headers, [make_row_dict(headers, row) for row in rows]

def validate_headers(headers, field_names, exceptions):
    """Validates headers and crashes if problems.
    
    >>> model = 'entity'
    >>> field_names = ['id', 'title', 'notused']
    >>> exceptions = ['notused']
    >>> headers = ['id', 'title']
    >>> validate_headers(model, headers, field_names, exceptions)
    >>> headers = ['id', 'titl']
    >>> validate_headers(model, headers, field_names, exceptions)
    Traceback (most recent call last):
      File "<input>", line 1, in <module>
      File "/usr/local/lib/python2.7/dist-packages/DDR/batch.py", line 319, in validate_headers
        raise Exception('MISSING HEADER(S): %s' % missing_headers)
    Exception: MISSING HEADER(S): ['title']
    
    @param headers: List of field names
    @param field_names: List of field names
    @param exceptions: List of nonrequired field names
    """
    missing_headers = [
        field for field in field_names
        if (field not in exceptions)
        and (field not in headers)
    ]
    bad_headers = [
        header for header in headers
        if header not in field_names
    ]
    if missing_headers:
        raise Exception('MISSING HEADER(S): %s' % missing_headers)
    if bad_headers:
        raise Exception('BAD HEADER(S): %s' % bad_headers)
    
def account_row(required_fields, rowd):
    """Returns list of any required fields that are missing from rowd.
    
    >>> required_fields = ['id', 'title']
    >>> rowd = {'id': 123, 'title': 'title'}
    >>> account_row(required_fields, rowd)
    []
    >>> required_fields = ['id', 'title', 'description']
    >>> account_row(required_fields, rowd)
    ['description']
    
    @param required_fields: List of required field names
    @param rowd: A single row (dict, not list of fields)
    @returns: list of field names
    """
    return [
        f for f in required_fields
        if (f not in rowd.keys()) or (not rowd.get(f,None))
    ]

def validate_id(text):
    try:
        i = identifier.Identifier(id=text)
        return i
    except:
        pass
    return False
    
def check_row_values(module, headers, valid_values, rowd):
    """Examines row values and returns names of invalid fields.
    
    TODO refers to lots of globals!!!
    
    @param module: modules.Module object
    @param headers: List of field names
    @param valid_values:
    @param rowd: A single row (dict, not list of fields)
    @returns: list of invalid values
    """
    invalid = []
    if not validate_id(rowd['id']):
        invalid.append('id')
    for field in headers:
        value = module.function(
            'csvload_%s' % field,
            rowd[field]
        )
        valid = module.function(
            'csvvalidate_%s' % field,
            [valid_values, value]
        )
        if not valid:
            invalid.append(field)
    return invalid


def find_duplicate_ids(rowds):
    unique = []
    duplicates = []
    for rowd in rowds:
        if rowd['id'] not in unique:
            unique.append(rowd['id'])
        else:
            duplicates.append(rowd['id'])
    if duplicates:
        raise Exception('Duplicate IDs: %s' % duplicates)

def find_multiple_cids(rowds):
    cids = {}
    for rowd in rowds:
        oid = identifier.Identifier(rowd['id'])
        cid = oid.collection().id
        if cid in cids.keys():
            cids[cid].append(oid.id)
        else:
            cids[cid] = [oid.id]
    # all IDs must belong to same collection
    if cids and (len(cids.keys()) > 1):
        raise Exception('File contains IDs from multiple collections: %s' % cids.keys())

def find_missing_required(required_fields, rowds):
    ids = [
        rowd['id']
        for rowd in rowds
        if account_row(required_fields, rowd)
    ]
    if ids:
        raise Exception('Missing required fields for these IDs: %s' % ids)

def find_invalid_values(module, headers, valid_values, rowds):
    ids = [
        rowd['id']
        for rowd in rowds
        if check_row_values(module, headers, valid_values, rowd)
    ]
    if ids:
        raise Exception('Invalid values for these IDs: %s' % ids)
    
def validate_rowds(module, headers, required_fields, valid_values, rowds):
    """Examines rows and raises exceptions if problems.
    
    Looks for
    - missing required fields
    - invalid field values
    - duplicate IDs
    
    @param module: modules.Module object
    @param headers: List of field names
    @param required_fields: List of required field names
    @param valid_values:
    @param rowds: List of row dicts
    """
    find_duplicate_ids(rowds)
    find_multiple_cids(rowds)
    find_missing_required(required_fields, rowds)
    find_invalid_values(module, headers, valid_values, rowds)
    
