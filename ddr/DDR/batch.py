import ConfigParser
from datetime import datetime
import csv
import os
import sys

from DDR import CONFIG_FILES, NoConfigError
from DDR import commands
from DDR.models import metadata_files

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

def export_csv_path( collection_path, model ):
    collection_id = os.path.basename(collection_path)
    if model == 'entity':
        csv_filename = '%s-objects.csv' % collection_id
    elif model == 'file':
        csv_filename = '%s-files.csv' % collection_id
    csv_path = os.path.join(CSV_TMPDIR, csv_filename)
    return csv_path

def parse_ids(text):
    """Parses IDs arg and returns list of IDs.
    
    ddr-test-123-*            All entities in a collection
    ddr-test-123-1-*          All files in an entity
    ddr-test-123-*            All files in a collection
    ddr-test-123-(1-5,7-8,10) Ranges of entities
    
    """
    return []

def module_field_names(module):
    return [field['name'] for field in module.FIELDS]

def dump_entity(path, class_, module, field_names):
    """Dump entity field values to list.
    
    @param path: Absolute path to entity.json
    @param class_
    @param module: 
    @param field_names: 
    @returns: list of values
    """
    entity_dir = os.path.dirname(path)
    entity_id = os.path.basename(entity_dir)
    entity = class_.from_json(entity_dir)
    # seealso ddrlocal.models.__init__.module_function()
    values = []
    for field in module.FIELDS:
        value = ''
        if (field['name'] in field_names) \
                and hasattr(entity, field['name']) \
                and field.get('form',None):
            key = field['name']
            label = field['form']['label']
            # run csvexport_* functions on field data if present
            val = module_function(module,
                                  'csvexport_%s' % key,
                                  getattr(entity, field['name']))
            if not (isinstance(val, str) or isinstance(val, unicode)):
                val = unicode(val)
            if val:
                value = val.encode('utf-8')
        values.append(value)
    return values

def dump_file(path, class_, module, field_names):
    """Dump file field values to list.
    
    @param path: Absolute path to .json
    @param class_
    @param module: 
    @param field_names: 
    @returns: list of values
    """
    # load file object
    filename = os.path.basename(path)
    file_id = os.path.splitext(filename)[0]
    file_ = class_.from_json(path)
    # seealso ddrlocal.models.__init__.module_function()
    values = []
    for f in module.FIELDS:
        value = ''
        if hasattr(file_, f['name']):
            key = f['name']
            # run csvexport_* functions on field data if present
            val = module_function(module,
                                  'csvexport_%s' % key,
                                  getattr(file_, f['name']))
            if not (isinstance(val, str) or isinstance(val, unicode)):
                val = unicode(val)
            if val:
                value = val.encode('utf-8')
        values.append(value)
    return values

def export(json_paths, class_, module, csv_path):
    """Write the specified objects' data to CSV.
    
    # entities
    collection_path = '/var/www/media/base/ddr-test-123'
    entity_paths = []
    for path in metadata_files(basedir=collection_path, recursive=True):
        if os.path.basename(path) == 'entity.json':
            entity_paths.append(path)
    csv_path = '/tmp/ddr-test-123-entities.csv'
    export(entity_paths, entity_module, csv_path)
    
    # files
    collection_path = '/var/www/media/base/ddr-test-123'
    file_paths = []
    for path in metadata_files(basedir=collection_path, recursive=True):
        if ('master' in path) or ('mezzanine' in path):
            file_paths.append(path)
    csv_path = '/tmp/ddr-test-123-files.csv'
    export(file_paths, files_module, csv_path)

    @param json_paths: list of .json files
    @param class_: subclass of Entity or File
    @param module: entity_module or files_module
    @param csv_path: Absolute path to CSV data file.
    """
    make_tmpdir(os.path.dirname(csv_path))
    # exclude 'files' from entities bc hard to convert to CSV.
    field_names = module_field_names(module)
    if module.MODEL == 'entity':
        field_names.remove('files')
    with open(csv_path, 'wb') as csvfile:
        writer = csv_writer(csvfile)
        writer.writerow(field_names)
        for n,path in enumerate(json_paths):
            if module.MODEL == 'entity':
                values = dump_entity(path, class_, module, field_names)
            elif module.MODEL == 'file':
                values = dump_file(path, class_, module, field_names)
            writer.writerow(values)
    return csv_path


# import ---------------------------------------------------------------

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

def make_row_dict(headers, row):
    """Turns the row into a dict with the headers as keys
    
    @param headers: List of header field names
    @param row: A single row (list of fields, not dict)
    @returns dict
    """
    if len(headers) != len(row):
        raise Exception
    d = {}
    for n in range(0, len(row)):
        d[headers[n]] = row[n]
    return d

def replace_variant_cv_field_values(headers, rows, alt_indexes):
    """Tries to replace variants of controlled-vocab with official values
    
    TODO pass in alternates data
    
    @param headers: List of field names
    @param rows: List of rows (each with list of fields, not dict)
    @param alt_indexes: list
    @returns: list rows
    """
    def replace(fieldname, row, headers, rowd, index):
        """This does the actual work.
        """
        value = rowd.get(fieldname, None)
        # if value appears in index, it is a variant
        if value and index.get(value, None):
            row[headers.index(fieldname)] = index[value]
        return row
    
    for row in rows:
        rowd = make_row_dict(headers, row)
        for field_name, alt_index in alt_indexes.iteritems():
            row = replace(field_name, row, headers, rowd, alt_index)
    return rows

def analyze_headers(model, headers, field_names, exceptions):
    """Analyzes headers and crashes if problems.
    
    @param model: 'entity' or 'file'
    @param headers: List of field names
    @param field_names: List of field names
    @param exceptions: List of nonrequired field names
    """
    headers = deepcopy(headers)
    if model == 'file':
        headers.remove('entity_id')
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

#def analyze_row(model, headers, rowd, choices_values):
#    """Analyzes row values and crashes if problems.
#    
#    TODO refers to lots of globals!!!
#    
#    @param model: 'entity' or 'file'
#    @param headers: List of field names
#    @param rowd: A single row (dict, not list of fields)
#    @param choices_values:
#    @returns: list of invalid values
#    """
#    invalid = []
#    if model == 'entity':
#        if not choice_is_valid(STATUS_CHOICES_VALUES, rowd['status']): invalid.append('status')
#        if not choice_is_valid(PUBLIC_CHOICES_VALUES, rowd['public']): invalid.append('public')
#        if not choice_is_valid(RIGHTS_CHOICES_VALUES, rowd['rights']): invalid.append('rights')
#        # language can be 'eng', 'eng;jpn', 'eng:English', 'jpn:Japanese'
#        for x in rowd['language'].strip().split(';'):
#            if ':' in x:
#                code = x.strip().split(':')[0]
#            else:
#                code = x.strip()
#            if not choice_is_valid(LANGUAGE_CHOICES_VALUES, code) and 'language' not in invalid:
#                invalid.append('language')
#        if not choice_is_valid(GENRE_CHOICES_VALUES, rowd['genre']): invalid.append('genre')
#        if not choice_is_valid(FORMAT_CHOICES_VALUES, rowd['format']): invalid.append('format')
#    elif model == 'file':
#        if not choice_is_valid(PUBLIC_CHOICES_VALUES, rowd['public']): invalid.append('public')
#        if not choice_is_valid(RIGHTS_CHOICES_VALUES, rowd['rights']): invalid.append('rights')
#    return invalid

def analyze_rows(model, headers, required_fields, rows):
    """Analyzes rows and crashes if problems.
    
    @param model: 'entity' or 'file'
    @param headers: List of field names
    @param required_fields: List of required field names
    @param rows: List of rows (each with list of fields, not dict)
    """
    for row in rows:
        rowd = make_row_dict(headers, row)
        missing_required_fields = row_missing_required_fields(required_fields, rowd)
#        analyze_row(model, headers, rowd)
        # print feedback and die
        if missing_required_fields or invalid:
            print(row)
            if missing_required_fields:
                raise Exception('MISSING REQUIRED FIELDS: %s' % missing_required_fields)
            if invalid:
                raise Exception('INVALID VALUES: %s' % invalid)

def load_entity(headers, row, collection_path, class_, module):
    """Write new entity.json file, return new Entity object
    
    @param headers: List of field names
    @param row: row from csv.reader
    @param collection_path: Absolute path to collection
    @param class_: subclass of Entity
    @param module: entity_module
    @returns: entity
    """
    assert False
    # TODO write to tmp file, return Entity object
    # Should not WRITE anything - see new/update_entity()
    
    row = replace_variant_cv_field_values('entity', headers, row)
    rowd = make_row_dict(headers, row)
    # run csvimport_* functions on row data
    for field_name in module.FIELDS:
        rowd[field_name] = module_function(
            module, 'csvimport_%s' % key, rowd[field_name]
        )
    # write blank entity.json template to entity location
    entity_uid = rowd['id']
    entity_path = os.path.join(collection_path, COLLECTION_FILES_PREFIX, entity_uid)
    class_(entity_path).dump_json(path=TEMPLATE_EJSON, template=True)
    # load Entity object from .json
    entity = class_.from_json(entity_path)
    # set values
    for key in rowd.keys():
        setattr(entity, key, rowd[key])
    entity.record_created = datetime.now()
    entity.record_lastmod = datetime.now()
    # write back to file
    entity.dump_json()
    return entity.json_path

def entity_exists():
    """
    TODO whether entity exists in repo
    """
    assert False

def new_entity():
    """
    TODO new entity
    """
    assert False

def update_entity():
    """
    TODO update entity
    """
    assert False

def import_entities(csv_path, collection_path, class_, module, git_name, git_mail):
    """Reads a CSV file, checks for errors, writes entity.json files, commits them.
    
    TODO Commit entity.json files in a big batch.
    
    TODO What if entities already exist???
    
    @param csv_path: Absolute path to CSV data file.
    @param collection_path: Absolute path to collection repo.
    @param class_: subclass of Entity
    @param module: entity_module
    @param git_name: Username for use in changelog, git log
    @param git_mail: User email address for use in changelog, git log
    """
    field_names = module_field_names(module)
    nonrequired_fields = REQUIRED_FIELDS_EXCEPTIONS['entity']
    required_fields = get_required_fields(module.FIELDS, nonrequired_fields)
    # read entire file into memory
    rows = read_csv(csv_path)
    headers = rows.pop(0)
    # check for errors
    analyze_headers('entity', headers, field_names, nonrequired_fields)
    analyze_rows(model, headers, required_fields, rows)
    # make some entity files!
    entity_json_paths = []
    for n,row in enumerate(rows):
        entity = load_entity(headers, row, collection_path, class_, module)
        
        if entity_exists():
            update_entity(entity)
        else:
            new_entity(entity)
        
       entity_json_paths.append(path)
    # TODO commit all the files at once
    assert False

# import files ---------------------------------------------------------

def test_entities(headers, rowds, class_):
    """Test-loads Entities mentioned in rows; crashes if any are missing.
    
    @param headers: list of field names
    @param rowds: List of rowds
    @param class_: subclass of Entity
    @returns: list of invalid entity IDs
    """
    entity_ids = []
    for rowd in rowds:
        entity_id = rowd.pop('entity_id')
        repo,org,cid,eid = entity_id.split('-')
        entity_path = class_.entity_path(None, repo, org, cid, eid)
        try:
            entity = class_.from_json(entity_path)
        except:
            entity_ids.append(entity_id)
    return entity_ids

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
        path = os.path.join(csv_dir, rowd.pop('basename_orig'))
        try:
            f = open(path, 'r')
            f.close()
        except:
            paths.append(path)
    return paths

def load_file(csv_dir, rowd, entity_class, git_name, git_mail, agent):
    """
    @param csv_dir: Absolute path to dir
    @param rowd
    @param class_: subclass of Entity
    @param git_name: Username for use in changelog, git log
    @param git_mail: User email address for use in changelog, git log
    @param agent: 
    @returns: file_ object
    """
    assert False
    # TODO WHAT ABOUT FILE METADATA???
    # TODO WHAT ABOUT EXISTING FILES???
    
    entity_id = rowd.pop('entity_id')
    repo,org,cid,eid = entity_id.split('-')
    entity_path = entity_class.entity_path(None, repo, org, cid, eid)
    entity = entity_class.from_json(entity_path)
    src_path = os.path.join(csv_dir, rowd.pop('basename_orig'))
    role = rowd.pop('role')
    
    assert False
    # TODO WAIT! WHAT ABOUT FILE METADATA!
    entity.add_file(git_name, git_mail, src_path, role, rowd, agent=agent)

def file_exists():
    """
    TODO whether file exists in repo
    """
    assert False

def new_file():
    """
    TODO new file
    """
    assert False

def update_file():
    """
    TODO update file
    """
    assert False

def import_files(csv_path, collection_path, class_, module, git_name, git_mail, agent):
    """Reads a CSV file, checks for errors, imports files.
    
    Note: Each file is an individual commit
    
    TODO What if files already exist???
    
    @param csv_path: Absolute path to CSV data file.
    @param collection_path: Absolute path to collection repo.
    @param class_: subclass of Entity
    @param module: entity_module
    @param git_name: Username for use in changelog, git log
    @param git_mail: User email address for use in changelog, git log
    @param agent:
    """
    field_names = module_field_names(module)
    nonrequired_fields = REQUIRED_FIELDS_EXCEPTIONS['file']
    required_fields = get_required_fields(module.FIELDS, nonrequired_fields)
    
    # read entire file into memory
    rows = read_csv(csv_path)
    headers = rows.pop(0)
    # check for errors
    analyze_headers('file', headers, field_names, nonrequired_fields)
    
    # convert to list of rowds so we don't do this in each following function
    # rm from rows as we go so we don't have two of these potentially giant lists
    rowds = []
    while rows:
        row = rows.pop(0)
        rowds.append(make_row_dict(headers, row))
    
    # check for errors
    analyze_rows(model, headers, required_fields, rowds)
    bad_entities = test_entities(headers, rowds)
    if bad_entities:
        print('ONE OR MORE OBJECTS ARE COULD NOT BE LOADED! - IMPORT CANCELLED!')
        for f in bad_entities:
            print('    %s' % f)
    # check for missing files
    missing_files = find_missing_files(csv_dir, headers, rowds)
    if missing_files:
        print('ONE OR MORE SOURCE FILES ARE MISSING! - IMPORT CANCELLED!')
        for f in missing_files:
            print('    %s' % f)
    else:
        print('Source files present')
    # check for unreadable files
    unreadable_files = find_unreadable_files(csv_dir, headers, rowds)
    if unreadable_files:
        print('ONE OR MORE SOURCE FILES COULD NOT BE OPENED! - IMPORT CANCELLED!')
        for f in unreadable_files:
            print('    %s' % f)
        print('Files must be readable to the user running this script (probably ddr).')
    else:
        print('Source files readable')
    
    if bad_entities or missing_files or unreadable_files:
        raise Exception('Cannot continue!')
        
    # all right let's do this thing!
    for n,rowd in enumerate(rowds):
        file_ = load_file(csv_dir, rowd, entity_class, git_name, git_mail, agent)
        assert False
        
        if file_exists():
            update_file(file_)
        else:
            new_file(file_)
