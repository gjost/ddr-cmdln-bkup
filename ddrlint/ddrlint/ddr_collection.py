from datetime import datetime
import hashlib
import json
import os
import re
import sys
import StringIO

from dateutil.parser import parse
from lxml import etree
from lxml.etree import XMLSyntaxError

import yaml



TEST_SUITE_VERSION = 'ddr-collection-0.1'
EMIT_STYLE = 'tap'
OK = 'ok'
WARNING = 'warning'
FAIL = 'not ok'
ERR = 'error'



"""
TODO: Rethink XML readable/parsable/valid tests. How will these work on a collection with thousands of entities, each with multiple files?

TODO: multiple test suites
examples:
- validate a single entity
- validate just the collection metadata files

"""

def _read_xml(path):
    """Just see if we can get a string from the file
    """
    raw = ''
    if os.path.exists(path):
        with open(path, 'r') as f:
            raw = f.read()
    return raw

def _parse_xml(path):
    """Indicate whether file can be parsed as XML.
    @return status,tree:
    status: String ('unknown', syn
    tree: lxml tree object
    """
    raw = _read_xml(path)
    xml = StringIO.StringIO(raw)
    try:
        tree = etree.parse(xml)
        return tree
    except XMLSyntaxError:
        raise
    return None

def _validate_xml(path):
    """Indicate whether XML file is valid.
    @return boolean
    """
    return False

def _entity_eids(ead_path):
    """List of entity EIDs from the EAD.xml.
    """
    try:
        tree = _parse_xml(ead_path)
    except XMLSyntaxError:
        raise
    if tree:
        return tree.xpath('/ead/dsc/c01/did/unittitle/@eid')
    return []

def _entity_paths(files_path, eids):
    """List of entity directory paths.
    """
    return [os.path.join(files_path, eid) for eid in eids if files_path and eids]

def _entity_dirs(entity_paths):
    """Return list of entity dirs that exist.
    """
    return [path for path in entity_paths if os.path.exists(path)]

def _entity_meta_files(entity_paths, filename):
    """File paths of entity files (single files) that exist.
    """
    existing = []
    for path in entity_paths:
        x = os.path.join(path, filename)
        if os.path.exists(x):
            existing.append(x)
    return existing

def _entity_xml_filter(entity_paths, filename, function):
    """File paths of entity XML files that pass the filter function.
    """
    passed = []
    exceptions = []
    for path in entity_paths:
        x = os.path.join(path, filename)
        try:
            if function(x):
                passed.append(x)
        except XMLSyntaxError:
            exceptions.append(x)
    return passed

def _changelog_valid(path):
    """Indicates whether changelog file is valid.

    Example:
    * Initialized collection ddr-testing-32
    -- Geoffrey Jost <geoffrey.jost@densho.org>  Thu, 23 May 2013 12:34:17 
     
    * Initialized entity ddr-testing-32-1
    -- Geoffrey Jost <geoffrey.jost@densho.org>  Thu, 23 May 2013 12:34:35 
     
    * Updated collection file(s) ead.xml
    -- Geoffrey Jost <geoffrey.jost@densho.org>  Thu, 23 May 2013 12:36:04

    Notes:
    - example is indented 4 spaces
    - space after datetime
    """
    valid = False
    if os.path.exists(path):
        with open(path, 'r') as f:
            changelog = f.read()
        num_valid = 0
        entries = changelog.split(' \n\n')
        pattern = '^-- ([\w ]+) <([\w_.-@]+)>$'
        for entry in entries:
            lines = entry.strip().split('\n')
            # signature
            sig = lines.pop().strip()
            # name, email formatted properly
            name = None; mail = None
            name_mail = sig.split('  ')[0]
            if name_mail:
                m = re.match(pattern, name_mail)
                name = m.group(1)
                mail = m.group(2)
            # timestamp can be parsed into datetime
            timestamp = None
            try:    tsraw = sig.split('  ')[1]
            except: tsraw = ''
            try:    ts = parse(tsraw)
            except: ts = None
            if ts and (type(ts) == type(datetime(1970,1,1,00,00,00))):
                timestamp = ts
            if name and mail and timestamp:
                num_valid = num_valid + 1
        if num_valid == len(entries):
            valid = True
    return valid

def _control_valid(path):
    """Indicates whether control file is valid.
    """
    valid = False
    return valid

def _entity_files_info(entity_mets_xmls):
    """List of file info from METS.xml.
    
    <mets>
      <metsHdr/>
        <dmdSec/>
          <amdSec/>
            <fileSec>
              <fileGrp USE="master">
                <file CHECKSUM="38b1886b239ceb54727cd977f6bf1223" CHECKSUMTYPE="md5">
                  <Flocat href="files/crunchbang-flames-full-by-omns.jpg"/>
    """
    entities = []
    for path in entity_mets_xmls:
        files = []
        d = os.path.dirname(path)
        eid = d.split(os.path.sep)[-1]
        try:
            tree = _parse_xml(path)
        except:
            tree = None
        if tree:
            for f in tree.xpath('/mets/fileSec/fileGrp/file'):
                checksum = None
                checksumtype = None
                href = None
                path_abs = None
                
                checksum = f.get('checksum')
                checksumtype = f.get('checksumtype')
                if not checksum:
                    checksum = f.get('CHECKSUM')
                if not checksumtype:
                    checksumtype = f.get('CHECKSUMTYPE')
                
                # TODO Can there be more than one <Flocat> in a <file>?
                for href in f.xpath('Flocat/@href'):
                    path_abs = os.path.join(d, href)
                if href and path_abs and checksum and checksumtype:
                    files.append({'eid': eid,
                                  'href': href,
                                  'abs': path_abs,
                                  'checksum': checksum,
                                  'checksumtype': checksumtype,})
        entities.append(files)
    return entities

def _entity_files_count(entity_files_info):
    """Takes output of entity_files_info and counts the total number of files.
    """
    c = 0
    for e in entity_files_info:
        for f in e:
            c = c + 1
    return c

def _entity_files_existing(entity_files_info):
    """Takes output of entity_files_info and lists files that exist.
    NOTE: result is a flat list of absolute file paths.
    """
    existing = []
    for e in entity_files_info:
        for f in e:
            if os.path.exists(f['abs']):
                existing.append(f)
    return existing

def _checksum_for_file(path, algo, block_size=1024):
    if algo == 'md5':
        h = hashlib.md5()
    elif algo == 'sha1':
        h = hashlib.sha1()
    else:
        return None
    f = open(path, 'rb')
    while True:
        data = f.read(block_size)
        if not data:
            break
        h.update(data)
    f.close()
    return h.hexdigest()

def _verify_entity_file(path, checksum, checksumtype):
    if os.path.exists(path):
        c = _checksum_for_file(path, checksumtype)
        if c and (c == checksum):
            return True
    return False



# TESTS ================================================================



def _emit(code, msg, data=None):
    if EMIT_STYLE == 'tap':
        tap = ['{} - {}'.format(code, msg)]
        if data:
            for line in yaml.dump(data, default_flow_style=False).split('\n'):
                tap.append('    {}'.format(line))
        return '\n'.join(tap).strip()
    elif EMIT_STYLE == 'json':
        if data:
            return '{}: {} : {}'.format(code, msg, json.dumps(data))
        return '{} - {}'.format(code, msg)
    return 'set emit style'
    


def test00_collection_directory_exists(path):
    if os.path.exists(path):
        return _emit(OK, 'collection directory')
    return _emit(FAIL, 'collection directory not found', [path])
        

# changelog file ---------------------------------------------------

def test020_changelog_exists(path):
    if os.path.exists(path):
        return _emit(OK, 'collection changelog')
    return _emit(FAIL, 'collection changelog file not found', [path])

def test021_changelog_valid(path):
    if _changelog_valid(path):
        return _emit(OK, 'Collection changelog file is valid')
    return _emit(FAIL, 'Collection changelog file is not valid', [path])
 
# control file -----------------------------------------------------

def test030_control_exists(path):
    if os.path.exists(path):
        return _emit(OK, 'collection control file')
    return _emit(FAIL, 'collection control file not found', [path])

def test031_control_valid(path):
    if _control_valid(path):
        return _emit(OK, 'collection control file is valid')
    return _emit(FAIL, 'collection control file is not valid', [path])

# ead.xml ----------------------------------------------------------

def test010_ead_exists(path):
    if os.path.exists(path):
        return _emit(OK, 'ead.xml')
    return _emit(FAIL, 'ead.xml file not found', [path])

def test011_ead_readable(path):
    raw = _read_xml(path)
    if raw:
        return _emit(OK, 'ead.xml is readable')
    return _emit(FAIL, 'ead.xml is not readable', [path])

def test012_ead_parsable(path):
    tree = _parse_xml(path)
    if tree:
        return _emit(OK, 'ead.xml is parsable')
    return _emit(FAIL, 'Collection ead.xml is not parsable', [path])

def test013_ead_valid(path):
    return _emit(FAIL, 'Collection ead.xml is not valid', [path])

# entities =========================================================

def test040_entities_dir_exists(path):
    if os.path.exists(path) and os.path.isdir(path):
        return _emit(OK, 'collection entities dir')
    return _emit(FAIL, 'collection entities dir not found', [path])

def test041_entity_dirs_exist(entity_eids, entity_paths):
    passed = []
    failed = []
    for path in entity_paths:
        if os.path.exists(path):
            passed.append(path)
        else:
            failed.append(path)
    if len(passed) == len(entity_eids):
        return _emit(OK, 'entity dirs')
    else:
        return _emit(FAIL, 'entity dirs missing', failed)

# entity changelogs ------------------------------------------------

def test0420_entity_changelogs_exist(entity_changelog_paths, entity_paths):
    passed = []
    failed = []
    for path in entity_changelog_paths:
        if os.path.exists(path):
            passed.append(path)
        else:
            failed.append(path)
    if len(passed) == len(entity_paths):
        return _emit(OK, 'entity changelogs')
    else:
        return _emit(FAIL, 'entity changelogs missing', failed)

def test0421_entity_changelogs_valid(entity_changelog_paths):
    return _emit(FAIL, 'entity changelogs not valid')

# entity control files ---------------------------------------------

def test0430_entity_controls_exist(entity_control_paths, entity_paths):
    passed = []
    failed = []
    for path in entity_control_paths:
        if os.path.exists(path):
            passed.append(path)
        else:
            failed.append(path)
    if len(passed) == len(entity_paths):
        return _emit(OK, 'entity control files')
    else:
        return _emit(FAIL, 'entity control files missing', failed)

def test0431_entity_controls_valid(entity_control_paths):
    return _emit(FAIL, 'entity control files not valid')

# entity mets.xml --------------------------------------------------

def test0440_entity_metsxml_exist(entity_metsxml_paths, entity_paths):
    passed = []
    failed = []
    for path in entity_metsxml_paths:
        if os.path.exists(path):
            passed.append(path)
        else:
            failed.append(path)
    if len(passed) == len(entity_paths):
        return _emit(OK, 'entity mets.xml files')
    else:
        return _emit(FAIL, 'entity mets.xml files missing', failed)

def test0441_entity_mets_readable(entity_metsxml_readable, entity_metsxml_paths):
    passed = []
    failed = []
    for path in entity_metsxml_paths:
        if path in entity_metsxml_readable:
            passed.append(path)
        else:
            failed.append(path)
    if len(passed) == len(entity_metsxml_paths):
        return _emit(OK, 'entity mets.xml files readable')
    else:
        return _emit(FAIL, 'entity mets.xml files not readable', failed)

def test0442_entity_mets_parsable(entity_metsxml_parsable, entity_metsxml_paths):
    passed = []
    failed = []
    for path in entity_metsxml_paths:
        if path in entity_metsxml_parsable:
            passed.append(path)
        else:
            failed.append(path)
    if len(passed) == len(entity_metsxml_paths):
        return _emit(OK, 'entity mets.xml files parsable')
    else:
        return _emit(FAIL, 'entity mets.xml files not parsable', failed)

def test0443_entity_mets_valid(entity_metsxml_valid, entity_metsxml_paths):
    passed = []
    failed = []
    for path in entity_metsxml_paths:
        if path in entity_metsxml_valid:
            passed.append(path)
        else:
            failed.append(path)
    if len(passed) == len(entity_metsxml_paths):
        return _emit(OK, 'entity mets.xml files valid')
    else:
        return _emit(FAIL, 'entity mets.xml files not valid', failed)

# entity files ---------------------------------------------------------

def test0500_entity_files_exist(entity_files_info, entity_files_count):
    passed = []
    failed = []
    if not entity_files_count:
        return _emit(WARNING, 'no entity payload files to find')
    for entity in entity_files_info:
        for f in entity:
            path = f['abs']
            if os.path.exists(path):
                passed.append(path)
            else:
                failed.append(path)
    if len(passed) == entity_files_count:
        return _emit(OK, 'entity payload files all found')
    else:
        return _emit(FAIL, 'entity payload files not found', failed)

def test0501_entity_files_verified(entity_files_info, entity_files_count):
    passed = []
    failed = []
    if not entity_files_count:
        return _emit(WARNING, 'no entity payload files to verify')
    for entity in entity_files_info:
        for f in entity:
            if _verify_entity_file(f['abs'], f['checksum'], f['checksumtype']):
                passed.append(f['abs'])
            else:
                failed.append(f['abs'])
    if len(passed) == entity_files_count:
        return _emit(OK, 'entity payload files all verified')
    else:
        return _emit(FAIL, 'entity payload files not verified', failed)



def collection_all_suite(collection_path):
    """Tests everything that can be tested about a collection.

    You wouldn't want to run this all the time on a collection with hundreds of
    entities/files.
    """
    
    x = [
        'Test suite version: {}'.format(TEST_SUITE_VERSION),
        'path: {}'.format(collection_path),
        '---',
        ]
    
    x.append( test00_collection_directory_exists(collection_path) )
    
    changelog_path = os.path.join(collection_path, 'changelog')
    control_path   = os.path.join(collection_path, 'control')
    ead_path       = os.path.join(collection_path, 'ead.xml')
    files_path     = os.path.join(collection_path, 'files')
    
    x.append( test020_changelog_exists(changelog_path) )
    x.append( test021_changelog_valid(changelog_path) )
    x.append( test030_control_exists(control_path) )
    x.append( test031_control_valid(control_path) )
    x.append( test010_ead_exists(ead_path)   )
    x.append( test011_ead_readable(ead_path) )
    x.append( test013_ead_valid(ead_path) )
    x.append( test040_entities_dir_exists(collection_path) )
    
    # Read ead.xml and get list of entities
    entity_eids  = _entity_eids(ead_path)
    entity_paths = _entity_paths(files_path, entity_eids)
    x.append( test041_entity_dirs_exist(entity_eids, entity_paths) )

    # List paths of entity files found in ead.xml.
    # Each entity should have one of these files, so list lengths should match
    # length of entity_paths.
    entity_changelog_paths  = _entity_meta_files(entity_paths, 'changelog')
    entity_control_paths    = _entity_meta_files(entity_paths, 'control')
    entity_metsxml_paths    = _entity_meta_files(entity_paths, 'mets.xml')
    x.append( test0420_entity_changelogs_exist(entity_changelog_paths, entity_paths) )
    x.append( test0430_entity_controls_exist(entity_control_paths, entity_paths) )
    x.append( test0440_entity_metsxml_exist(entity_metsxml_paths, entity_paths) )
    x.append( test0421_entity_changelogs_valid(entity_changelog_paths) )
    x.append( test0431_entity_controls_valid(entity_control_paths) )
    
    # List paths of entity mets.xml files that pass various tests
    entity_metsxml_readable = _entity_xml_filter(entity_paths, 'mets.xml', _read_xml)
    entity_metsxml_parsable = _entity_xml_filter(entity_paths, 'mets.xml', _parse_xml)
    entity_metsxml_valid    = _entity_xml_filter(entity_paths, 'mets.xml', _validate_xml)
    x.append( test0441_entity_mets_readable(entity_metsxml_readable, entity_metsxml_paths) )
    x.append( test0442_entity_mets_parsable(entity_metsxml_parsable, entity_metsxml_paths) )
    x.append( test0443_entity_mets_valid(entity_metsxml_valid, entity_metsxml_paths) )
    
    # List the files for each entity
    entity_files_info       = _entity_files_info(entity_metsxml_readable)
    entity_files_count      = _entity_files_count(entity_files_info)
    x.append( test0500_entity_files_exist(entity_files_info, entity_files_count) )
    x.append( test0501_entity_files_verified(entity_files_info, entity_files_count) )
    
    return x



if __name__ == '__main__':
    #unittest.main()
    collection_path = './ddr_samples/testcollection'
    tap = collection_all_suite(collection_path)
    print('\n'.join(tap))
