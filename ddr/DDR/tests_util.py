from datetime import datetime
import os

import util


def test_find_meta_files():
    basedir = '/tmp'
    cachedir = '.metadata_files'
    cache_path = os.path.join(basedir, cachedir)
    if os.path.exists(cache_path):
        os.remove(cache_path)
    assert not os.path.exists(cache_path)
    paths0 = util.find_meta_files('/tmp', recursive=True, force_read=True)
    print('paths: %s' % paths0)
    assert os.path.exists(cache_path)
    paths1 = util.find_meta_files('/tmp', recursive=True, force_read=True)
    print('paths: %s' % paths1)

def test_natural_sort():
    l = ['11', '1', '12', '2', '13', '3']
    util.natural_sort(l)
    assert l == ['1', '2', '3', '11', '12', '13']

def test_natural_order_string():
    assert util.natural_order_string('ddr-testing-123') == '123'
    assert util.natural_order_string('ddr-testing-123-1') == '1'
    assert util.natural_order_string('ddr-testing-123-15') == '15'

def test_file_hash():
    path = '/tmp/test-hash-%s' % datetime.now().strftime('%Y%m%dT%H%M%S')
    text = 'hash'
    sha1 = '2346ad27d7568ba9896f1b7da6b5991251debdf2'
    sha256 = 'd04b98f48e8f8bcc15c6ae5ac050801cd6dcfd428fb5f9e65c4e16e7807340fa'
    md5 = '0800fc577294c34e0b28ad2839435945'
    with open(path, 'w') as f:
        f.write(text)
    assert util.file_hash(path, 'sha1') == sha1
    assert util.file_hash(path, 'sha256') == sha256
    assert util.file_hash(path, 'md5') == md5
    os.remove(path)
