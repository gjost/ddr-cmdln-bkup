# -*- coding: utf-8 -*-

from datetime import datetime
import os

import envoy
import git
from nose.tools import assert_raises

import batch


# Exporter
# TODO test_make_tmpdir
# TODO test_export

# Checker
# TODO check_repository
# TODO check_csv
# TODO check_eids
# TODO _guess_model
# TODO _ids_in_local_repo
# TODO _load_vocab_files
# TODO _vocab_urls
# TODO _http_get_vocabs
# TODO _validate_csv_file

def test_prep_valid_values():
    json_texts = [
        '{"terms": [{"id": "advertisement"}, {"id": "album"}, {"id": "architecture"}], "id": "genre"}',
        '{"terms": [{"id": "eng"}, {"id": "jpn"}, {"id": "chi"}], "id": "language"}',
    ]
    expected = {u'genre': [u'advertisement', u'album', u'architecture'], u'language': [u'eng', u'jpn', u'chi']}
    assert batch.Checker._prep_valid_values(json_texts) == expected

# Importer
# TODO _fidentifier_parent
# TODO _file_is_new
# TODO _write_entity_changelog
# TODO _write_file_changelogs
# TODO import_entities
# TODO import_files
# TODO register_entity_ids
