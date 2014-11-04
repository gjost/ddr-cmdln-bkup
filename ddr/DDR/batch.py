import ConfigParser
from copy import deepcopy
from datetime import datetime
import csv
import json
import logging
import os
import sys

from DDR import CONFIG_FILES, NoConfigError
from DDR import natural_sort
from DDR import changelog
from DDR import commands
from DDR import dvcs
from DDR import models

config = ConfigParser.ConfigParser()
configs_read = config.read(CONFIG_FILES)
if not configs_read:
    raise NoConfigError('No config file!')

TEMPLATE_EJSON = config.get('local','template_ejson')
TEMPLATE_METS = config.get('local','template_mets')

COLLECTION_FILES_PREFIX = 'files'

# Some files' XMP data is wayyyyyy too big
csv.field_size_limit(sys.maxsize)
CSV_DELIMITER = ','
CSV_QUOTECHAR = '"'
CSV_QUOTING = csv.QUOTE_ALL


def dtfmt(dt, fmt='%Y-%m-%dT%H:%M:%S.%f'):
    """Format dates in consistent format.
    
    >>> dtfmt(datetime.fromtimestamp(0), fmt='%Y-%m-%dT%H:%M:%S.%f')
    '1969-12-31T16:00:00.000000'
    
    @param dt: datetime
    @param fmt: str Format string (default: '%Y-%m-%dT%H:%M:%S.%f')
    @returns: str
    """
    return dt.strftime(fmt)

def csv_writer(csvfile):
    """Get a csv.writer object for the file.
    
    @param csvfile: A file object.
    """
    writer = csv.writer(
        csvfile,
        delimiter=CSV_DELIMITER,
        quoting=CSV_QUOTING,
        quotechar=CSV_QUOTECHAR,
    )
    return writer

def csv_reader(csvfile):
    """Get a csv.reader object for the file.
    
    @param csvfile: A file object.
    """
    reader = csv.reader(
        csvfile,
        delimiter=CSV_DELIMITER,
        quoting=CSV_QUOTING,
        quotechar=CSV_QUOTECHAR,
    )
    return reader

def make_entity_path(collection_path, entity_id):
    """
    >>> cpath0 = '/var/www/media/base/ddr-test-123'
    >>> eid0 = 'ddr-test-123-456'
    >>> make_entity_path(cpath0, eid0)
    '/var/www/media/base/ddr-test-123/files/ddr-test-123-456'
    """
    return os.path.join(collection_path, COLLECTION_FILES_PREFIX, entity_id)

def make_entity_json_path(collection_path, entity_id):
    """
    >>> cpath0 = '/var/www/media/base/ddr-test-123'
    >>> eid0 = 'ddr-test-123-456'
    >>> make_entity_json_path(cpath0, eid0)
    '/var/www/media/base/ddr-test-123/files/ddr-test-123-456/entity.json'
    """
    return os.path.join(collection_path, COLLECTION_FILES_PREFIX, entity_id, 'entity.json')


# export ---------------------------------------------------------------

def make_tmpdir(tmpdir):
    """Make tmp dir if doesn't exist.
    
    @param tmpdir: Absolute path to dir
    """
    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)

def write_csv(path, headers, rows):
    with open(path, 'wb') as f:
        writer = csv_writer(f)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)

def module_field_names(module):
    """Manipulates list of fieldnames to include/exclude columns from CSV.
    """
    if hasattr(module, 'FIELDS_CSV_EXCLUDED'):
        excluded = module.FIELDS_CSV_EXCLUDED
    else:
        excluded = []
    fields = []
    for field in module.FIELDS:
        if not field['name'] in excluded:
            fields.append(field['name'])
    if module.MODEL == 'collection':
        pass
    elif module.MODEL == 'entity':
        pass
    elif module.MODEL == 'file':
        fields.insert(0, 'file_id')
    return fields

def dump_object(obj, module, field_names):
    """Dump object field values to list.
    
    Note: Autogenerated and non-user-editable fields
    (SHA1 and other hashes, file size, etc) should be excluded
    from the CSV file.
    Note: For files these are replaced by File.id which contains
    the role and a fragment of the SHA1 hash.
    
    @param obj_
    @param module: 
    @param field_names: 
    @returns: list of values
    """
    # seealso ddrlocal.models.__init__.module_function()
    values = []
    for field_name in field_names:
        value = ''
        # insert file_id as first column
        if (module.MODEL == 'file') and (field_name == 'file_id'):
            val = obj.id
        elif hasattr(obj, field_name):
            # run csvdump_* functions on field data if present
            val = models.module_function(
                module,
                'csvdump_%s' % field_name,
                getattr(obj, field_name)
            )
            if val == None:
                val = ''
        # clean values
        if not (isinstance(val, str) or isinstance(val, unicode)):
            val = unicode(val)
        if val:
            value = val.encode('utf-8')
        value = value.strip()
        value = value.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '\\n')
        values.append(value)
    return values

def export(json_paths, class_, module, csv_path):
    """Write the specified objects' data to CSV.
    
    # entities
    collection_path = '/var/www/media/base/ddr-test-123'
    entity_paths = []
    for path in models.metadata_files(basedir=collection_path, recursive=True):
        if os.path.basename(path) == 'entity.json':
            entity_paths.append(path)
    csv_path = '/tmp/ddr-test-123-entities.csv'
    export(entity_paths, entity_module, csv_path)
    
    # files
    collection_path = '/var/www/media/base/ddr-test-123'
    file_paths = []
    for path in models.metadata_files(basedir=collection_path, recursive=True):
        if ('master' in path) or ('mezzanine' in path):
            file_paths.append(path)
    csv_path = '/tmp/ddr-test-123-files.csv'
    export(file_paths, files_module, csv_path)

    @param json_paths: list of .json files
    @param class_: subclass of Entity or File
    @param module: entity_module or files_module
    @param csv_path: Absolute path to CSV data file.
    """
    if module.MODEL == 'file':
        json_paths = models.sort_file_paths(json_paths)
    else:
        json_paths = natural_sort(json_paths)
    make_tmpdir(os.path.dirname(csv_path))
    field_names = module_field_names(module)
    with open(csv_path, 'wb') as csvfile:
        writer = csv_writer(csvfile)
        writer.writerow(field_names)
        for n,path in enumerate(json_paths):
            logging.info('%s/%s - %s' % (n+1, len(json_paths), path))
            if module.MODEL == 'entity':
                obj = class_.from_json(os.path.dirname(path))
            elif module.MODEL == 'file':
                obj = class_.from_json(path)
            writer.writerow(dump_object(obj, module, field_names))
    return csv_path


# update entities ------------------------------------------------------

def read_csv(path):
    """Read specified file, return list of rows.
    
    @param path: Absolute path to CSV file
    @returns list of rows
    """
    rows = []
    with open(path, 'rU') as f:  # the 'U' is for universal-newline mode
        reader = csv_reader(f)
        for row in reader:
            rows.append(row)
    return rows

def get_required_fields(fields, exceptions):
    """Picks out the required fields.
    
    @param fields: module.FIELDS
    @param exceptions: list of field names
    @returns: list of field names
    """
    required_fields = []
    for field in fields:
        if field.get('form', None) and field['form']['required'] and (field['name'] not in exceptions):
            required_fields.append(field['name'])
    return required_fields

def prep_valid_values(vocabs_path):
    """Packages dict of acceptable values for controlled-vocab fields.
    
    Loads choice values from FIELD.json files in the 'ddr' repository
    into a dict:
    {
        'FIELD': ['VALID', 'VALUES', ...],
        'status': ['inprocess', 'completed'],
        'rights': ['cc', 'nocc', 'pdm'],
        ...
    }
    
    @param vocabs_path: Absolute path to dir containing vocab .json files.
    @returns: dict
    """
    valid_values = {}
    json_paths = []
    for p in os.listdir(vocabs_path):
        path = os.path.join(vocabs_path, p)
        if os.path.splitext(path)[1] == '.json':
            json_paths.append(path)
    for path in json_paths:
        with open(path, 'r') as f:
            data = json.loads(f.read())
        field = data['id']
        values = [term['id'] for term in data['terms']]
        if values:
            valid_values[field] = values
    return valid_values

def make_row_dict(headers, row):
    """Turns the row into a dict with the headers as keys
    
    >>> headers0 = ['id', 'created', 'lastmod', 'title', 'description']
    >>> row0 = ['id', 'then', 'now', 'title', 'descr']
    {'title': 'title', 'description': 'descr', 'lastmod': 'now', 'id': 'id', 'created': 'then'}

    @param headers: List of header field names
    @param row: A single row (list of fields, not dict)
    @returns dict
    """
    if len(headers) != len(row):
        logging.error(headers)
        logging.error(row)
        raise Exception('Row and header have different number of fields.')
    d = {}
    for n in range(0, len(row)):
        d[headers[n]] = row[n]
    return d

def replace_variant_cv_field_values(headers, alt_indexes, rowd):
    """Tries to replace variants of controlled-vocab with official values
    
    NOTE: This was a cool idea but we're not using it.
    
    @param headers: List of field names
    @param alt_indexes: list
    @param rowd: A single row (dict, not list of fields)
    @returns: list rows
    """
    for field_name, alt_index in alt_indexes.iteritems():
        value = rowd.get(fieldname, None)
        # if value appears in index, it is a variant
        if value and index.get(value, None):
            rowd[fieldname] = index[value]
    return rowd

def validate_headers(model, headers, field_names, exceptions):
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
    
    @param model: 'entity' or 'file'
    @param headers: List of field names
    @param field_names: List of field names
    @param exceptions: List of nonrequired field names
    """
    headers = deepcopy(headers)
    # validate
    missing_headers = []
    for field in field_names:
        if (field not in exceptions) and (field not in headers):
            missing_headers.append(field)
    if missing_headers:
        raise Exception('MISSING HEADER(S): %s' % missing_headers)
    bad_headers = []
    for header in headers:
        if header not in field_names:
            bad_headers.append(header)
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
    missing = []
    for f in required_fields:
        if (f not in rowd.keys()) or (not rowd.get(f,None)):
            missing.append(f)
    return missing

def validate_row(module, headers, valid_values, rowd):
    """Examines row values and returns names of invalid fields.
    
    TODO refers to lots of globals!!!
    
    @param module: entity_module or files_module
    @param headers: List of field names
    @param valid_values:
    @param rowd: A single row (dict, not list of fields)
    @returns: list of invalid values
    """
    invalid = []
    for field in headers:
        value = models.module_function(
            module,
            'csvload_%s' % field,
            rowd[field]
        )
        valid = models.module_function(
            module,
            'csvvalidate_%s' % field,
            [valid_values, value]
        )
        if not valid:
            invalid.append(field)
    return invalid

def validate_rows(module, headers, required_fields, valid_values, rows):
    """Examines rows and crashes if problems.
    
    @param module: entity_module or files_module
    @param headers: List of field names
    @param required_fields: List of required field names
    @param valid_values:
    @param rows: List of rows (each with list of fields, not dict)
    """
    for n,row in enumerate(rows):
        rowd = make_row_dict(headers, row)
        missing_required = account_row(required_fields, rowd)
        invalid_fields = validate_row(module, headers, valid_values, rowd)
        # print feedback and die
        if missing_required or invalid_fields:
            if missing_required:
                raise Exception('MISSING REQUIRED FIELDS: %s' % missing_required)
            if invalid_fields:
                raise Exception('INVALID VALUES: %s' % invalid_fields)

def load_entity(collection_path, class_, rowd):
    """Get new or existing Entity object
    
    @param collection_path: Absolute path to collection
    @param class_: subclass of Entity
    @param rowd:
    @returns: entity
    """
    entity_uid = rowd['id']
    entity_path = make_entity_path(collection_path, entity_uid)
    # update an existing entity
    if os.path.exists(entity_path):
        entity = class_.from_json(entity_path)
        entity.new = False
    else:
        entity = class_(entity_path)
        entity.id = entity_uid
        entity.record_created = datetime.now()
        entity.record_lastmod = datetime.now()
        entity.new = True
    return entity

def csvload_entity(entity, module, field_names, rowd):
    """Update entity with values from CSV row.
    
    TODO Populates entity attribs EXCEPT FOR .files!!!
    
    @param entity:
    @param module: entity_module
    @param field_names:
    @param rowd:
    @returns: entity,modified
    """
    # run csvload_* functions on row data, set values
    entity.modified = 0
    for field in field_names:
        oldvalue = getattr(entity, field, '')
        value = models.module_function(
            module,
            'csvload_%s' % field,
            rowd[field]
        )
        try:
            value = value.strip()
            value = value.replace('\\n', '\n')
        except AttributeError:
            pass # doesn't work on ints and lists :P
        if value != oldvalue:
            entity.modified += 1
        setattr(entity, field, value)
    if entity.modified:
        entity.record_lastmod = datetime.now()
    return entity

def write_entity_changelog(entity, git_name, git_mail, agent):
    # write entity changelogs
    messages = [
        'Updated entity file {}'.format(entity.json_path),
        '@agent: %s' % agent,
    ]
    changelog.write_changelog_entry(
        entity.changelog_path, messages,
        user=git_name, email=git_mail)

def update_entities(csv_path, collection_path, class_, module, vocabs_path, git_name, git_mail, agent):
    """Reads a CSV file, checks for errors, and writes entity.json files
    
    This function writes and stages files but does not commit them!
    That is left to the user or to another function.
    
    TODO What if entities already exist???
    TODO do we overwrite fields?
    TODO how to handle excluded fields like XMP???
    
    @param csv_path: Absolute path to CSV data file.
    @param collection_path: Absolute path to collection repo.
    @param class_: subclass of Entity
    @param module: entity_module
    @param vocabs_path: Absolute path to vocab dir
    @param git_name:
    @param git_mail:
    @param agent:
    """
    field_names = module_field_names(module)
    nonrequired_fields = module.REQUIRED_FIELDS_EXCEPTIONS
    required_fields = get_required_fields(module.FIELDS, nonrequired_fields)
    valid_values = prep_valid_values(vocabs_path)
    # read entire file into memory
    rows = read_csv(csv_path)
    headers = rows.pop(0)
    # check for errors
    logging.info('Validating headers')
    validate_headers('entity', headers, field_names, nonrequired_fields)
    logging.info('Validating rows')
    validate_rows(module, headers, required_fields, valid_values, rows)
    # ok go
    git_files = []
    annex_files = []
    for n,row in enumerate(rows):
        rowd = make_row_dict(headers, row)
        logging.info('%s/%s - %s' % (n+1, len(rows), rowd['id']))
        #rowd = replace_variant_cv_field_values(headers, rowd, alt_indexes)
        entity = load_entity(collection_path, class_, rowd)
        entity = csvload_entity(entity, module, field_names, rowd)
        if entity.new or entity.modified:
            logging.debug('    wrote %s' % entity.json_path)
            with open(entity.json_path, 'w') as f:
                f.write(entity.dump_json())
            write_entity_changelog(entity, git_name, git_mail, agent)
            git_files.append(entity.json_path_rel)
            git_files.append(entity.changelog_path_rel)
    # stage modified files
    logging.info('Staging changes to the repo')
    repo = dvcs.repository(collection_path)
    logging.debug(repo)
    for path in git_files:
        logging.debug('git add %s' % path)
        repo.git.add(path)

# update files ---------------------------------------------------------

def test_entities(collection_path, class_, rowds):
    """Test-loads Entities mentioned in rows; crashes if any are missing.
    
    @param collection_path:
    @param rowds: List of rowds
    @param class_: subclass of Entity
    @returns: ok,bad
    """
    basedir = os.path.dirname(os.path.dirname(collection_path))
    # get unique entity_ids
    paths = []
    for rowd in rowds:
        model,repo,org,cid,eid,role,sha1 = models.split_object_id(rowd['file_id'])
        entity_id = models.make_object_id('entity', repo,org,cid,eid)
        path = models.path_from_id(entity_id, basedir)
        if path not in paths:
            paths.append(path)
    # test-load the Entities
    entities = {}
    bad = []
    for path in paths:
        print(path)
        entity = class_.from_json(path)
        try:
            entity = class_.from_json(path)
            entities[entity.id] = entity
        except:
            broken.append(models.id_from_path(path))
    return entities,bad

def load_file(collection_path, file_class, rowd):
    """
    @param collection_path: Absolute path to collection
    @param file_class: subclass of DDRFile
    @param rowd:
    @returns: file_ object
    """
    file_path = models.path_from_id(
        rowd['file_id'],
        os.path.dirname(os.path.dirname(collection_path))
    ) + '.json'
    # update an existing entity
    if os.path.exists(file_path):
        file_ = file_class.from_json(file_path)
        file_.new = False
    else:
        file_ = file_class(file_path)
        file_.new = True
    return file_

def csvload_file(file_, module, field_names, rowd):
    """Write new file .json file, return new File object
    
    @param file_:
    @param module: file_module
    @param field_names:
    @param rowd:
    @returns: file_
    """
    # run csvload_* functions on row data, set values
    file_.modified = 0
    for field in field_names:
        oldvalue = getattr(file_, field, '')
        value = models.module_function(
            module,
            'csvload_%s' % field,
            rowd[field]
        )
        try:
            value = value.strip()
            value = value.replace('\\n', '\n')
        except AttributeError:
            pass # doesn't work on ints and lists :P
        if value != oldvalue:
            file_.modified += 1
        setattr(file_, field, value)
    return file_

def write_file_changelog(entity, files, git_name, git_mail, agent):
    # write entity changelogs
    messages = []
    for f in files:
        messages.append('Updated entity file {}'.format(f.json_path))
    messages.append('@agent: %s' % agent)
    changelog.write_changelog_entry(
        entity.changelog_path, messages,
        user=git_name, email=git_mail)

def update_files(csv_path, collection_path, entity_class, file_class, module, vocabs_path, git_name, git_mail, agent):
    """Updates metadata for files in csv_path.
    
    TODO Commit .json files in a big batch.
    
    TODO What if files already exist???
    TODO do we overwrite fields?
    TODO how to handle excluded fields like XMP???
    
    @param csv_path: Absolute path to CSV data file.
    @param collection_path: Absolute path to collection repo.
    @param entity_class: subclass of Entity
    @param file_class: subclass of DDRFile
    @param module: file_module
    @param vocabs_path: Absolute path to vocab dir
    @param git_name:
    @param git_mail:
    @param agent:
    """
    csv_dir = os.path.dirname(csv_path)
    field_names = module_field_names(module)
    nonrequired_fields = module.REQUIRED_FIELDS_EXCEPTIONS
    required_fields = get_required_fields(module.FIELDS, nonrequired_fields)
    valid_values = prep_valid_values(vocabs_path)
    # read entire file into memory
    rows = read_csv(csv_path)
    headers = rows.pop(0)
    # check for errors
    logging.info('Validating headers')
    validate_headers('file', headers, field_names, nonrequired_fields)
    logging.info('Validating rows')
    validate_rows(module, headers, required_fields, valid_values, rows)
    # make list-of-dicts
    rowds = []
    while rows:
        rowd = rows.pop(0)
        rowds.append(make_row_dict(headers, rowd))
    # more checks
    logging.info('Validating parent entities')
    entities,bad_entities = test_entities(collection_path, entity_class, rowds)
    if bad_entities:
        logging.error('One or more entities could not be loaded! - IMPORT CANCELLED!')
        for f in bad_entities:
            logging.error('    %s' % f)
    else:
        logging.info('ok')
    if bad_entities:
        raise Exception('Cannot continue!')
    # ok go
    git_files = []
    annex_files = []
    for n,rowd in enumerate(rowds):
        logging.info('%s/%s - %s' % (n+1, len(rowds), rowd['file_id']))
        file_ = load_file(collection_path, file_class, rowd)
        file_ = csvload_file(file_, module, field_names, rowd)
        if file_.new or file_.modified:
            with open(file_.json_path, 'w') as f:
                f.write(file_.dump_json())
            git_files.append(file_.json_path_rel)
            entity_id = models.id_from_path(os.path.join(file_.entity_path, 'entity.json'))
            entity = entities[entity_id]
            if not hasattr(entity, 'files_updated'):
                entity.files_updated = []
            entity.files_updated.append(file_)
    logging.info('Writing entity changelogs')
    for eid,entity in entities.iteritems():
        if hasattr(entity, 'files_updated') and getattr(entity, 'files_updated', None):
            write_file_changelog(entity, entity.files_updated, git_name, git_mail, agent)
            git_files.append(entity.changelog_path_rel)
    # stage modified files
    logging.info('Staging changes to the repo')
    repo = dvcs.repository(collection_path)
    logging.debug(repo)
    for path in git_files:
        logging.debug('git add %s' % path)
        repo.git.add(path)

def find_missing_files(csv_dir, headers, rowds):
    """checks for missing files
    
    @param csv_dir: Absolute path to dir
    @param headers: List of field names
    @param rowds: List of rowds
    @returns list of missing files
    """
    paths = []
    for rowd in rowds:
        path = os.path.join(csv_dir, rowd.pop('basename_orig'))
        if not os.path.exists(path):
            paths.append(path)
    return paths

def find_unreadable_files(csv_dir, headers, rowds):
    """checks for unreadable files
    
    @param csv_dir: Absolute path to dir
    @param headers: List of field names
    @param rowds: List of rowds
    @returns list of unreadable files
    """
    paths = []
    for rowd in rowds:
        print(rowd)
        path = os.path.join(csv_dir, rowd.pop('basename_orig'))
        try:
            f = open(path, 'r')
            f.close()
        except:
            paths.append(path)
    return paths

#def import_files(csv_path, collection_path, entity_class, file_class, module, vocabs_path, git_name, git_mail, agent):
#    """imports new files
#    
#    If you only want to update file metadata, use update_files.
#    
#    TODO Commit .json files in a big batch.
#    
#    TODO What if files already exist???
#    TODO do we overwrite fields?
#    TODO how to handle excluded fields like XMP???
#    
#    @param csv_path: Absolute path to CSV data file.
#    @param collection_path: Absolute path to collection repo.
#    @param entity_class: subclass of Entity
#    @param file_class: subclass of DDRFile
#    @param module: file_module
#    @param vocabs_path: Absolute path to vocab dir
#    @param git_name:
#    @param git_mail:
#    @param agent:
#    """
#    csv_dir = os.path.dirname(csv_path)
#    field_names = module_field_names(module)
#    nonrequired_fields = module.REQUIRED_FIELDS_EXCEPTIONS
#    required_fields = get_required_fields(module.FIELDS, nonrequired_fields)
#    valid_values = prep_valid_values(vocabs_path)
#    # read file into memory
#    rows = read_csv(csv_path)
#    headers = rows.pop(0)
#    # check for errors
#    validate_headers('file', headers, field_names, nonrequired_fields)
#    validate_rows(module, headers, required_fields, valid_values, rows)
#    # make list-of-dicts
#    rowds = []
#    while rows:
#        rowd = rows.pop(0)
#        rowds.append(make_row_dict(headers, rowd))
#    # more checks
#    print('Checking entities')
#    bad_entities = test_entities(collection_path, entity_class, rowds)
#    if bad_entities:
#        print('One or more objects (entities) could not be loaded! - IMPORT CANCELLED!')
#        for f in bad_entities:
#            print('    %s' % f)
#    else:
#        print('ok')
#    print('Looking for missing files')
#    missing_files = find_missing_files(csv_dir, headers, rowds)
#    if missing_files:
#        print('One or more source files are missing! - IMPORT CANCELLED!')
#        for f in missing_files:
#            print('    %s' % f)
#    else:
#        print('ok')
#    print('Looking for unreadable files')
#    unreadable_files = find_unreadable_files(csv_dir, headers, rowds)
#    if unreadable_files:
#        print('One or more source files were unreadable! - IMPORT CANCELLED!')
#        for f in unreadable_files:
#            print('    %s' % f)
#        print('Files must be readable to the user running this script (probably ddr).')
#    else:
#        print('ok')
#    if bad_entities or missing_files or unreadable_files:
#        raise Exception('Cannot continue!')
#    # ok go
#    for n,rowd in enumerate(rowds):
#        file_ = load_file(csv_dir, rowd, file_class)
#        assert False
#        
#        if file_exists():
#            update_file(file_)
#        else:
#            new_file(file_)
