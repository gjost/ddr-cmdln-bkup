from collections import OrderedDict
from copy import deepcopy
from datetime import datetime
import json
import logging
import os

from DDR import changelog
from DDR import config
from DDR import csvfile
from DDR import dvcs
from DDR import fileio
from DDR import identifier
from DDR import models
from DDR import modules
from DDR import util

COLLECTION_FILES_PREFIX = 'files'


class ModifiedFilesError(Exception):
    pass

class UncommittedFilesError(Exception):
    pass

def test_repository(repo):
    """Raise exception if staged or modified files in repo
    
    Entity.add_files will not work properly if the repo contains staged
    or modified files.
    
    @param repo: GitPython repository
    """
    logging.info('Checking repository')
    staged = dvcs.list_staged(repo)
    if staged:
        logging.error('*** Staged files in repo %s' % repo.working_dir)
        for f in staged:
            logging.error('*** %s' % f)
        raise UncommittedFilesError('Repository contains staged/uncommitted files - import cancelled!')
    modified = dvcs.list_modified(repo)
    if modified:
        logging.error('Modified files in repo: %s' % repo.working_dir)
        for f in modified:
            logging.error('*** %s' % f)
        raise ModifiedFilesError('Repository contains modified files - import cancelled!')
    logging.debug('repository clean')

def test_entities(collection_path, object_class, rowds):
    """Test-loads Entities mentioned in rows; crashes if any are missing.
    
    When files are being updated/added, it's important that all the parent
    entities already exist.
    
    @param collection_path:
    @param rowds: List of rowds
    @param object_class: subclass of Entity
    @returns: dict of Entities by ID
    """
    logging.info('Validating parent entities')
    cidentifier = identifier.Identifier(path=collection_path)
    # get unique entity_ids
    eids = []
    for rowd in rowds:
        fidentifier = identifier.Identifier(
            id=rowd['file_id'], base_path=cidentifier.basepath
        )
        eidentifier = identifier.Identifier(
            id=fidentifier.parent_id(), base_path=cidentifier.basepath
        )
        eids.append(eidentifier)
    # test-load the Entities
    entities = {}
    bad = []
    for eidentifier in eids:
        entity_path = eidentifier.path_abs()
        # update an existing entity
        entity = None
        if os.path.exists(entity_path):
            entity = object_class.from_identifier(eidentifier)
        if entity:
            entities[entity.id] = entity
        else:
            bad.append(eidentifier.id)
    if bad:
        logging.error('One or more entities could not be loaded! - IMPORT CANCELLED!')
        for f in bad:
            logging.error('    %s' % f)
    if bad:
        raise Exception('Cannot continue!')
    return entities

def load_vocab_files(vocabs_path):
    """Loads vocabulary term files in the 'ddr' repository
    
    @param vocabs_path: Absolute path to dir containing vocab .json files.
    @returns: list of raw text contents of files.
    """
    json_paths = []
    for p in os.listdir(vocabs_path):
        path = os.path.join(vocabs_path, p)
        if os.path.splitext(path)[1] == '.json':
            json_paths.append(path)
    json_texts = [
        fileio.read_text(path)
        for path in json_paths
    ]
    return json_texts

def prep_valid_values(json_texts):
    """Prepares dict of acceptable values for controlled-vocab fields.
    
    TODO should be method of DDR.modules.Module
    
    Loads choice values from FIELD.json files in the 'ddr' repository
    into a dict:
    {
        'FIELD': ['VALID', 'VALUES', ...],
        'status': ['inprocess', 'completed'],
        'rights': ['cc', 'nocc', 'pdm'],
        ...
    }
    
    >>> json_texts = [
    ...     '{"terms": [{"id": "advertisement"}, {"id": "album"}, {"id": "architecture"}], "id": "genre"}',
    ...     '{"terms": [{"id": "eng"}, {"id": "jpn"}, {"id": "chi"}], "id": "language"}',
    ... ]
    >>> batch.prep_valid_values(json_texts)
    {u'genre': [u'advertisement', u'album', u'architecture'], u'language': [u'eng', u'jpn', u'chi']}
    
    @param json_texts: list of raw text contents of files.
    @returns: dict
    """
    valid_values = {}
    for text in json_texts:
        data = json.loads(text)
        field = data['id']
        values = [term['id'] for term in data['terms']]
        if values:
            valid_values[field] = values
    return valid_values

def populate_object(obj, module, field_names, rowd):
    """Update entity with values from CSV row.
    
    TODO Populates entity attribs EXCEPT FOR .files!!!
    
    @param obj:
    @param module:
    @param field_names:
    @param rowd:
    @returns: entity,modified
    """
    # run csvload_* functions on row data, set values
    obj.modified = 0
    for field in field_names:
        oldvalue = getattr(obj, field, '')
        value = module.function(
            'csvload_%s' % field,
            rowd[field]
        )
        value = util.normalize_text(value)
        if value != oldvalue:
            obj.modified += 1
        setattr(obj, field, value)
    if obj.modified:
        obj.record_lastmod = datetime.now()

def write_entity_changelog(entity, git_name, git_mail, agent):
    msg = 'Updated entity file {}'
    messages = [
        msg.format(entity.json_path),
        '@agent: %s' % agent,
    ]
    changelog.write_changelog_entry(
        entity.changelog_path, messages,
        user=git_name, email=git_mail)

def write_file_changelogs(entities, git_name, git_mail, agent):
    """Writes entity update/add changelogs, returns list of changelog paths
    
    Assembles appropriate changelog messages and then updates changelog for
    each entity.  update_files() adds lists of updated and added File objects
    to entities in list.
    
    TODO should this go in DDR.changelog.py?
    
    @param entities: list of Entity objects.
    @param git_name:
    @param git_mail:
    @param agent:
    @returns: list of paths relative to repository base
    """
    git_files = []
    for entity in entities:
        messages = []
        if getattr(entity, 'changelog_updated', None):
            for f in entity.changelog_updated:
                messages.append('Updated entity file {}'.format(f.json_path_rel))
        #if getattr(entity, 'changelog_added', None):
        #    for f in entity.changelog_added:
        #        messages.append('Added entity file {}'.format(f.json_path_rel))
        messages.append('@agent: %s' % agent)
        changelog.write_changelog_entry(
            entity.changelog_path,
            messages,
            user=git_name,
            email=git_mail)
        git_files.append(entity.changelog_path_rel)
    return git_files


def update_entities(csv_path, collection_path, vocabs_path, git_name, git_mail, agent):
    """Reads a CSV file, checks for errors, and writes entity.json files
    
    IMPORTANT: All objects in CSV must already exist!
    IMPORTANT: All objects in CSV must have the same set of fields!
    
    This function writes and stages files but does not commit them!
    That is left to the user or to another function.
    
    TODO What if entities already exist???
    TODO do we overwrite fields?
    TODO how to handle excluded fields like XMP???
    
    @param csv_path: Absolute path to CSV data file.
    @param collection_path: Absolute path to collection repo.
    @param vocabs_path: Absolute path to vocab dir
    @param git_name:
    @param git_mail:
    @param agent:
    @returns: list of updated entities
    """
    logging.info('-----------------------------------------------')
    csv_path = os.path.normpath(csv_path)
    vocabs_path = os.path.normpath(vocabs_path)
    collection_path = os.path.normpath(collection_path)
    cidentifier = identifier.Identifier(collection_path)
    
    model = 'entity'
    object_class = identifier.class_for_name(
        identifier.MODEL_CLASSES[model]['module'],
        identifier.MODEL_CLASSES[model]['class']
    )
    logging.debug(object_class)
    module = modules.Module(
        identifier.module_for_name(
            identifier.MODEL_REPO_MODELS[model]['module']
        )
    )
    logging.debug(module)
    
    # check for modified or uncommitted files in repo
    repository = dvcs.repository(collection_path)
    logging.debug(repository)
    test_repository(repository)
    
    logging.info('Reading %s' % csv_path)
    headers,rowds = csvfile.make_rowds(fileio.read_csv(csv_path))
    logging.info('%s rows' % len(rowds))
    
    # check for errors
    field_names = module.field_names()
    nonrequired_fields = module.module.REQUIRED_FIELDS_EXCEPTIONS
    required_fields = module.required_fields(nonrequired_fields)
    valid_values = prep_valid_values(load_vocab_files(vocabs_path))
    logging.info('Validating headers')
    csvfile.validate_headers(headers, field_names, nonrequired_fields)
    logging.info('Validating rows')
    csvfile.validate_rowds(module, headers, required_fields, valid_values, rowds)
    
    logging.info('Updating - - - - - - - - - - - - - - - -')
    git_files = []
    updated = []
    for n,rowd in enumerate(rowds):
        logging.info('%s/%s - %s' % (n+1, len(rowds), rowd['id']))
        
        ## instantiate
        #entity = make_object(collection_path, class_, rowd)
        # load existing object and set new values from CSV
        eidentifier = identifier.Identifier(id=rowd['id'], base_path=cidentifier.basepath)
        entity = eidentifier.object()
        populate_object(entity, module, field_names, rowd)
        
        # write files
        logging.debug('    writing %s' % entity.json_path)
        entity.write_json()
        # TODO better to write to collection changelog?
        write_entity_changelog(entity, git_name, git_mail, agent)
        # stage
        git_files.append(entity.json_path_rel)
        git_files.append(entity.changelog_path_rel)
        updated.append(entity)
    
    # stage modified files
    logging.info('Staging changes to the repo')
    for path in git_files:
        repository.git.add(path)
    for path in util.natural_sort(dvcs.list_staged(repository)):
        if path in git_files:
            logging.debug('| %s' % path)
        else:
            logging.debug('+ %s' % path)
    return updated


def update_files(csv_path, collection_path, vocabs_path, git_name, git_mail, agent):
    """Updates metadata for files in csv_path.
    
    TODO how to handle excluded fields like XMP???
    
    @param csv_path: Absolute path to CSV data file.
    @param collection_path: Absolute path to collection repo.
    @param vocabs_path: Absolute path to vocab dir
    @param git_name:
    @param git_mail:
    @param agent:
    """
    logging.info('-----------------------------------------------')
    csv_path = os.path.normpath(csv_path)
    csv_dir = os.path.dirname(csv_path)
    vocabs_path = os.path.normpath(vocabs_path)
    collection_path = os.path.normpath(collection_path)
    cidentifier = identifier.Identifier(path=collection_path)

    # TODO this still knows too much about entities and files...
    entity_class = identifier.class_for_name(
        identifier.MODEL_CLASSES['entity']['module'],
        identifier.MODEL_CLASSES['entity']['class']
    )
    logging.debug('entity_class %s' % entity_class)
    module = modules.Module(
        identifier.module_for_name(
            identifier.MODEL_REPO_MODELS['file']['module']
        )
    )
    logging.debug('module %s' % module)
    
    # check for modified or uncommitted files in repo
    repository = dvcs.repository(collection_path)
    logging.debug(repository)
    test_repository(repository)
    
    logging.info('Reading %s' % csv_path)
    headers,rowds = csvfile.make_rowds(fileio.read_csv(csv_path))
    logging.info('%s rows' % len(rowds))
    
    # check for errors
    field_names = module.field_names()
    nonrequired_fields = module.module.REQUIRED_FIELDS_EXCEPTIONS
    required_fields = module.required_fields(nonrequired_fields)
    required_fields.append('file_id')
    required_fields.append('basename_orig')
    valid_values = prep_valid_values(load_vocab_files(vocabs_path))
    logging.info('Validating headers')
    csvfile.validate_headers(headers, field_names, nonrequired_fields)
    logging.info('Validating rows')
    csvfile.validate_rowds(module, headers, required_fields, valid_values, rowds)

    entities = test_entities(collection_path, entity_class, rowds)
    for entity in entities.itervalues():
        entity.changelog_updated = []
        entity.changelog_added = []
    
    logging.info('Updating - - - - - - - - - - - - - - - -')
    git_files = []
    for n,rowd in enumerate(rowds):
        logging.info('+ %s/%s - %s' % (n+1, len(rowds), rowd['file_id']))
        
        fidentifier = identifier.Identifier(id=rowd['file_id'], base_path=cidentifier.basepath)
        #file0 = make_object(collection_path, rowd)
        file_ = fidentifier.object()
        populate_object(file_, module, field_names, rowd)
        entity = entities[fidentifier.parent_id()]
        
        # update metadata
        logging.debug('    writing %s' % file_.json_path_rel)
        file_.write_json()
        git_files.append(file_.json_path_rel)
        # TODO better to write to collection changelog?
        entity.changelog_updated.append(file_)

    logging.info('Writing entity changelogs')
    git_files += write_file_changelogs(
        [e for e in entities.itervalues()],
        git_name, git_mail, agent
    )
    
    # stage git_files
    logging.info('Staging changes to the repo')
    for path in git_files:
        repository.git.add(path)
    for path in util.natural_sort(dvcs.list_staged(repository)):
        if path in git_files:
            logging.debug('| %s' % path)
        else:
            logging.debug('+ %s' % path)
