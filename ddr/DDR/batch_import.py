"""
Check to see if CSV file is internally valid
See which EIDs would be added
Update existing records
Import new records
Register newly added EIDs
"""

from collections import OrderedDict
from copy import deepcopy
from datetime import datetime
import json
import logging
import os

import grequests

from DDR import changelog
from DDR import config
from DDR import csvfile
from DDR import dvcs
from DDR import fileio
from DDR import identifier
from DDR import idservice
from DDR import ingest
from DDR import models
from DDR import modules
from DDR import util

COLLECTION_FILES_PREFIX = 'files'


class ModifiedFilesError(Exception):
    pass

class UncommittedFilesError(Exception):
    pass


# helper functions -----------------------------------------------------

def _fidentifier_parent(fidentifier):
    """Returns entity Identifier for either 'file' or 'file-role'
    
    We want to support adding new files and updating existing ones.
    New file IDs have no SHA1, thus they are actually file-roles.
    Identifier.parent() returns different objects depending on value of 'stubs'.
    This function ensures that the parent of 'fidentifier' will always be an Entity.
    
    @param fidentifier: Identifier
    @returns: boolean
    """
    is_stub = fidentifier.object_class() == models.Stub
    return fidentifier.parent(stubs=is_stub)

def _file_is_new(fidentifier):
    """Indicate whether file is new (ingest) or not (update)
    
    @param fidentifier: Identifier
    @returns: boolean
    """
    return fidentifier.object_class() == models.Stub

def _guess_model(rowds):
    """Loops through rowds and guesses model
    
    # TODO guess schema too
    
    @param rowds: list
    @returns: str model keyword
    """
    logging.debug('Guessing model based on %s rows' % len(rowds))
    models = []
    for rowd in rowds:
        if rowd.get('identifier'):
            if rowd['identifier'].model not in models:
                models.append(rowd['identifier'].model)
    if not models:
        raise Exception('Cannot guess model type!')
    if len(models) > 1:
        raise Exception('More than one model type in imput file!')
    model = models[0]
    # TODO should not know model name
    if model == 'file-role':
        model = 'file'
    logging.debug('model: %s' % model)
    return model

def _load_vocab_files(vocabs_path):
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

def _vocab_urls(module):
    """
    @param module: modules.Module
    @return: list of URLs
    """
    return [
        config.VOCAB_TERMS_URL % field.get('name')
        for field in module.module.FIELDS
        if field.get('vocab')
    ]

def _http_get_vocabs(urls):
    """Gets vocab JSON texts from vocabs API
    
    Gets URL template from config.VOCAB_TERMS_URL
    
    @param module: modules.Module
    @returns list of JSON strings
    """
    # GET URLs in parallel
    responses = grequests.map(
        (grequests.get(u) for u in urls)
    )
    return [r.text for r in responses]

def _prep_valid_values(json_texts):
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
    >>> batch._prep_valid_values(json_texts)
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

def _validate_csv_file(module, vocabs, headers, rowds):
    """Validate CSV headers and data against schema/field definitions
    
    @param module: modules.Module
    @param vocabs: dict Output of _prep_valid_values()
    @param headers: list
    @param rowds: list
    """
    # gather data
    field_names = module.field_names()
    nonrequired_fields = module.module.REQUIRED_FIELDS_EXCEPTIONS
    required_fields = module.required_fields(nonrequired_fields)
    valid_values = _prep_valid_values(vocabs)
    # check
    logging.info('Validating headers')
    header_errs = csvfile.validate_headers(headers, field_names, nonrequired_fields)
    if not header_errs.keys():
        logging.info('ok')
    else:
        for name,errs in header_errs.iteritems():
            if errs:
                logging.error(name)
                for err in errs:
                    logging.error('* %s' % err)
    logging.info('Validating rows')
    rowds_errs = csvfile.validate_rowds(module, headers, required_fields, valid_values, rowds)
    if not rowds_errs.keys():
        logging.info('ok')
    else:
        for name,errs in rowds_errs.iteritems():
            if errs:
                logging.error(name)
                for err in errs:
                    logging.error('* %s' % err)

def _ids_in_local_repo(rowds, model, collection_path):
    """Lists which IDs in CSV are present in local repo.
    
    @param rowds: list of dicts
    @param model: str
    @param collection_path: str Absolute path to collection repo.
    @returns: list of IDs.
    """
    metadata_paths = util.find_meta_files(
        collection_path,
        model=model,
        recursive=True, force_read=True
    )
    existing_ids = [
        identifier.Identifier(path=path)
        for path in metadata_paths
    ]
    new_ids = [rowd['id'] for rowd in rowds]
    already = [i for i in new_ids if i in existing_ids]
    return already

def _write_entity_changelog(entity, git_name, git_mail, agent):
    msg = 'Updated entity file {}'
    messages = [
        msg.format(entity.json_path),
        '@agent: %s' % agent,
    ]
    changelog.write_changelog_entry(
        entity.changelog_path, messages,
        user=git_name, email=git_mail)

def _write_file_changelogs(entities, git_name, git_mail, agent):
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
    

# ----------------------------------------------------------------------

def check_repository(cidentifier):
    """Load repository, check for staged or modified files
    
    Entity.add_files will not work properly if the repo contains staged
    or modified files.
    
    @param cidentifier: Identifier
    @returns: GitPython.Repository
    """
    logging.info('Checking repository')
    repo = dvcs.repository(cidentifier.path_abs())
    logging.info('Checking repository %s' % repo)
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
    logging.debug('ok')
    return repo

def check_csv(csv_path, cidentifier, vocabs_path):
    """Load CSV, validate headers and rows
    
    @param csv_path: Absolute path to CSV data file.
    @param cidentifier: Identifier
    @param vocabs_path: Absolute path to vocab dir
    @param session: requests.session object
    @returns: nothing
    """
    logging.info('Checking CSV file')
    
    logging.info('Reading input file %s' % csv_path)
    headers,rowds = csvfile.make_rowds(fileio.read_csv(csv_path))
    logging.info('%s rows' % len(rowds))
    logging.info('Adding identifiers to rows')
    for rowd in rowds:
        rowd['identifier'] = identifier.Identifier(rowd['id'])
    logging.info('OK')
    
    model = _guess_model(rowds)
    module = modules.Module(
        identifier.module_for_name(
            identifier.MODEL_REPO_MODELS[model]['module']
        )
    )
    logging.info('Loading vocabs from API (%s)' % config.VOCAB_TERMS_URL)
    vocab_urls = _vocab_urls(module)
    vocabs = _http_get_vocabs(vocab_urls)
    _validate_csv_file(module, vocabs, headers, rowds)
    return rowds

def check_eids(rowds, cidentifier, session):
    """
    
    @param csv_path: Absolute path to CSV data file.
    @param cidentifier: Identifier
    @param session: requests.session object
    @returns: nothing
    """
    logging.info('Confirming all entity IDs available')
    csv_eids = [rowd['id'] for rowd in rowds]
    registered,unregistered = idservice.check_eids(session, cidentifier, csv_eids)
    if (unregistered == csv_eids) and not registered:
        logging.info('ALL entity IDs available')
    elif registered:
        logging.info('Already registered: %s' % registered)
    
    # confirm file entities not in repo
    logging.info('Checking for existing IDs')
    already_added = _ids_in_local_repo(rowds, cidentifier.model, cidentifier.path_abs())
    if already_added:
        raise Exception('The following entities already exist: %s' % already_added)
    else:
        logging.info('ok')


def import_entities(csv_path, cidentifier, vocabs_path, git_name, git_mail, agent, dryrun=False):
    """Adds or updates entities from a CSV file
    
    Running function multiple times with the same CSV file is idempotent.
    After the initial pass, files will only be modified if the CSV data
    has been updated.
    
    This function writes and stages files but does not commit them!
    That is left to the user or to another function.
    
    @param csv_path: Absolute path to CSV data file.
    @param cidentifier: Identifier
    @param vocabs_path: Absolute path to vocab dir
    @param git_name: str
    @param git_mail: str
    @param agent: str
    @param dryrun: boolean
    @returns: list of updated entities
    """
    logging.info('------------------------------------------------------------------------')
    logging.info('batch import entity')
    model = 'entity'
    
    repository = dvcs.repository(cidentifier.path_abs())
    logging.info(repository)
    
    logging.info('Reading %s' % csv_path)
    headers,rowds = csvfile.make_rowds(fileio.read_csv(csv_path))
    logging.info('%s rows' % len(rowds))
    
    logging.info('- - - - - - - - - - - - - - - - - - - - - - - -')
    logging.info('Importing')
    start_updates = datetime.now()
    git_files = []
    updated = []
    elapsed_rounds = []
    obj_metadata = None
    
    if dryrun:
        logging.info('Dry run - no modifications')
    for n,rowd in enumerate(rowds):
        logging.info('%s/%s - %s' % (n+1, len(rowds), rowd['id']))
        start_round = datetime.now()
        
        eidentifier = identifier.Identifier(id=rowd['id'], base_path=cidentifier.basepath)
        # if there is an existing object it will be loaded
        entity = eidentifier.object()
        if not entity:
            entity = models.Entity.create(eidentifier.path_abs(), eidentifier)
        modified = entity.load_csv(rowd)
        # Getting obj_metadata takes about 1sec each time
        # TODO caching works as long as all objects have same metadata...
        if not obj_metadata:
            obj_metadata = models.object_metadata(
                eidentifier.fields_module(),
                repository.working_dir
            )
        
        if dryrun:
            pass
        elif modified:
            # write files
            if not os.path.exists(entity.path_abs):
                os.makedirs(entity.path_abs)
            logging.debug('    writing %s' % entity.json_path)
            entity.write_json(obj_metadata=obj_metadata)
            # TODO better to write to collection changelog?
            # TODO write all additions to changelog at one time
            _write_entity_changelog(entity, git_name, git_mail, agent)
            # stage
            git_files.append(entity.json_path_rel)
            git_files.append(entity.changelog_path_rel)
            updated.append(entity)
        
        elapsed_round = datetime.now() - start_round
        elapsed_rounds.append(elapsed_round)
        logging.debug('| %s (%s)' % (eidentifier, elapsed_round))

    if dryrun:
        logging.info('Dry run - no modifications')
    elif updated:
        logging.info('Staging %s modified files' % len(git_files))
        start_stage = datetime.now()
        dvcs.stage(repository, git_files)
        for path in util.natural_sort(dvcs.list_staged(repository)):
            if path in git_files:
                logging.debug('+ %s' % path)
            else:
                logging.debug('| %s' % path)
        elapsed_stage = datetime.now() - start_stage
        logging.debug('ok (%s)' % elapsed_stage)
    
    elapsed_updates = datetime.now() - start_updates
    logging.debug('%s updated in %s' % (len(elapsed_rounds), elapsed_updates))
    logging.info('- - - - - - - - - - - - - - - - - - - - - - - -')
    
    return updated


def import_files(csv_path, cidentifier, vocabs_path, git_name, git_mail, agent, log_path=None, dryrun=False):
    """Adds or updates files from a CSV file
    
    TODO how to handle excluded fields like XMP???
    
    @param csv_path: Absolute path to CSV data file.
    @param cidentifier: Identifier
    @param vocabs_path: Absolute path to vocab dir
    @param git_name: str
    @param git_mail: str
    @param agent: str
    @param log_path: str Absolute path to addfile log for all files
    @param dryrun: boolean
    """
    logging.info('batch import files ----------------------------')
    
    # TODO hard-coded model name...
    model = 'file'
    
    csv_dir = os.path.dirname(csv_path)
    logging.debug('csv_dir %s' % csv_dir)

    # TODO this still knows too much about entities and files...
    entity_class = identifier.class_for_name(
        identifier.MODEL_CLASSES['entity']['module'],
        identifier.MODEL_CLASSES['entity']['class']
    )
    logging.debug('entity_class %s' % entity_class)
    
    logging.info('Reading %s' % csv_path)
    headers,rowds = csvfile.make_rowds(fileio.read_csv(csv_path))
    logging.info('%s rows' % len(rowds))
    
    # check for modified or uncommitted files in repo
    repository = dvcs.repository(cidentifier.path_abs())
    logging.debug(repository)
    #test_repository(repository)

    fidentifiers = {
        rowd['id']: identifier.Identifier(
            id=rowd['id'],
            base_path=cidentifier.basepath
        )
        for rowd in rowds
    }
    fidentifier_parents = {
        fi.id: _fidentifier_parent(fi)
        for fi in fidentifiers.itervalues()
    }
    # eidentifiers, removing duplicates
    eidentifiers = list(set([e for e in fidentifier_parents.itervalues()]))
    entities = {}
    bad_entities = []
    for eidentifier in eidentifiers:
        if os.path.exists(eidentifier.path_abs()):
            entity = eidentifier.object()
            entities[eidentifier.id] = entity
        else:
            if eidentifier.id not in bad_entities:
                bad_entities.append(eidentifier.id)
    if bad_entities:
        for f in bad_entities:
            logging.error('    %s missing' % f)
        raise Exception('%s entities could not be loaded! - IMPORT CANCELLED!' % len(bad_entities))

    # separate into new and existing lists
    rowds_new = []
    rowds_existing = []
    for n,rowd in enumerate(rowds):
        if _file_is_new(fidentifiers[rowd['id']]):
            rowds_new.append(rowd)
        else:
            rowds_existing.append(rowd)
    
    logging.info('- - - - - - - - - - - - - - - - - - - - - - - -')
    logging.info('Updating existing files')
    start_updates = datetime.now()
    git_files = []
    updated = []
    elapsed_rounds_updates = []
    staged = []
    obj_metadata = None
    for n,rowd in enumerate(rowds_existing):
        logging.info('+ %s/%s - %s (%s)' % (n+1, len(rowds), rowd['id'], rowd['basename_orig']))
        start_round = datetime.now()
        
        fidentifier = fidentifiers[rowd['id']]
        eidentifier = fidentifier_parents[fidentifier.id]
        entity = entities[eidentifier.id]
        file_ = fidentifier.object()
        modified = file_.load_csv(rowd)
        # Getting obj_metadata takes about 1sec each time
        # TODO caching works as long as all objects have same metadata...
        if not obj_metadata:
            obj_metadata = models.object_metadata(
                fidentifier.fields_module(),
                repository.working_dir
            )
        
        if dryrun:
            pass
        elif modified:
            logging.debug('    writing %s' % file_.json_path)
            file_.write_json(obj_metadata=obj_metadata)
            # TODO better to write to collection changelog?
            _write_entity_changelog(entity, git_name, git_mail, agent)
            # stage
            git_files.append(file_.json_path_rel)
            git_files.append(entity.changelog_path_rel)
            updated.append(file_)
        
        elapsed_round = datetime.now() - start_round
        elapsed_rounds_updates.append(elapsed_round)
        logging.debug('| %s (%s)' % (fidentifier, elapsed_round))
    
    elapsed_updates = datetime.now() - start_updates
    logging.debug('%s updated in %s' % (len(elapsed_rounds_updates), elapsed_updates))
            
    if dryrun:
        pass
    elif modified:
        logging.info('Staging %s modified files' % len(git_files))
        start_stage = datetime.now()
        dvcs.stage(repository, git_files)
        staged = util.natural_sort(dvcs.list_staged(repository))
        for path in staged:
            if path in git_files:
                logging.debug('+ %s' % path)
            else:
                logging.debug('| %s' % path)
        elapsed_stage = datetime.now() - start_stage
        logging.debug('ok (%s)' % elapsed_stage)
        logging.debug('%s staged in %s' % (len(staged), elapsed_stage))
    
    logging.info('- - - - - - - - - - - - - - - - - - - - - - - -')
    logging.info('Adding new files')
    start_adds = datetime.now()
    elapsed_rounds_adds = []
    logging.info('Checking source files')
    for rowd in rowds_new:
        rowd['src_path'] = os.path.join(csv_dir, rowd['basename_orig'])
        logging.debug('| %s' % rowd['src_path'])
        if not os.path.exists(rowd['src_path']):
            raise Exception('Missing file: %s' % rowd['src_path'])
    if log_path:
        logging.info('addfile logging to %s' % log_path)
    for n,rowd in enumerate(rowds_new):
        logging.info('+ %s/%s - %s (%s)' % (n+1, len(rowds), rowd['id'], rowd['basename_orig']))
        start_round = datetime.now()
        
        fidentifier = fidentifiers[rowd['id']]
        eidentifier = fidentifier_parents[fidentifier.id]
        entity = entities[eidentifier.id]
        logging.debug('| %s' % (entity))

        if dryrun:
            pass
        elif _file_is_new(fidentifier):
            # ingest
            # TODO make sure this updates entity.files
            file_,repo2,log2 = ingest.add_file(
                entity,
                rowd['src_path'],
                fidentifier.parts['role'],
                rowd,
                git_name, git_mail, agent,
                log_path=log_path,
                show_staged=False
            )
        
        elapsed_round = datetime.now() - start_round
        elapsed_rounds_adds.append(elapsed_round)
        logging.debug('| %s (%s)' % (file_, elapsed_round))
    
    elapsed_adds = datetime.now() - start_adds
    logging.debug('%s added in %s' % (len(elapsed_rounds_adds), elapsed_adds))
    logging.info('- - - - - - - - - - - - - - - - - - - - - - - -')
    
    return git_files


def register_entity_ids(csv_path, cidentifier, session, dryrun=True):
    """
    @param csv_path: Absolute path to CSV data file.
    @param cidentifier: Identifier
    @param session: requests.session object
    @param register: boolean Whether or not to register IDs
    @returns: nothing
    """
    logging.info('-----------------------------------------------')
    logging.info('Reading %s' % csv_path)
    headers,rowds = csvfile.make_rowds(fileio.read_csv(csv_path))
    logging.info('%s rows' % len(rowds))
    
    logging.info('Looking up already registered IDs')
    csv_eids = [rowd['id'] for rowd in rowds]
    registered,unregistered = idservice.check_eids(session, cidentifier, csv_eids)
    num_unregistered = len(unregistered)
    logging.info('%s IDs to register.' % num_unregistered)
    if dryrun:
        logging.info('These IDs would be registered if not --dryrun')
        for n,eid in enumerate(unregistered):
            logging.info('| %s/%s %s' % (n, num_unregistered, eid))
    else:
        logging.info('Registering IDs')
        idservice.register_entity_ids(session, cidentifier.id, unregistered)
    
    logging.info('- - - - - - - - - - - - - - - - - - - - - - - -')
