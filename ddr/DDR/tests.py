import os

import DDR


def test_find_meta_files():
    basedir = '/tmp'
    cachedir = '.metadata_files'
    cache_path = os.path.join(basedir, cachedir)
    if os.path.exists(cache_path):
        os.remove(cache_path)
    assert not os.path.exists(cache_path)
    paths0 = DDR.find_meta_files('/tmp', recursive=True, force_read=True)
    print('paths: %s' % paths0)
    assert os.path.exists(cache_path)
    paths1 = DDR.find_meta_files('/tmp', recursive=True, force_read=True)
    print('paths: %s' % paths1)

def test_natural_sort():
    l = ['11', '1', '12', '2', '13', '3']
    DDR.natural_sort(l)
    assert l == ['1', '2', '3', '11', '12', '13']

def test_natural_order_string():
    assert DDR.natural_order_string('ddr-testing-123') == '123'
    assert DDR.natural_order_string('ddr-testing-123-1') == '1'
    assert DDR.natural_order_string('ddr-testing-123-15') == '15'

def test_Timer():
    mark_text0 = 'start'
    mark_text1 = 'halfway'
    mark_text2 = 'last one'
    t = DDR.Timer()
    t.mark(mark_text0)
    t.mark(mark_text1)
    t.mark(mark_text2)
    steps = t.display()
    assert len(steps) == 3
    assert steps[0]['index'] == 0
    assert steps[1]['index'] == 1
    assert steps[2]['index'] == 2
    assert steps[0]['msg'] == mark_text0
    assert steps[1]['msg'] == mark_text1
    assert steps[2]['msg'] == mark_text2
    assert steps[2]['datetime'] > steps[1]['datetime'] > steps[0]['datetime']
