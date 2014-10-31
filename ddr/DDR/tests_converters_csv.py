"""Functions for converting between Python data and CSV.
"""

from datetime import datetime
import re

from converters import csv


# TODO csv.validate_* --------------------------------------------------------

# csv.load_* ------------------------------------------------------------

def test_load_string():
    assert isinstance(csv.load_string(u'this is a str'), unicode)
    assert isinstance(csv.load_string('this is a str'), unicode)
    padding = csv.load_string('  padded  ')
    assert not re.search('^\s', padding)  # no space at start
    assert not re.search('$\s', padding)  # no space at end
    linebreaks = csv.load_string('line 0\r\nline 1\rline2')
    assert linebreaks == u'line 0\\nline 1\\nline2'

def test_load_datetime():
    fmt = '%Y-%m-%dT%H:%M:%S'
    text0 = None
    data0 = None
    assert csv.load_datetime(text0, fmt) == data0
    text1 = ''
    data1 = None
    assert csv.load_datetime(text1, fmt) == data1
    text2 = '1970-1-1T00:00:00'
    data2 = datetime(1970, 1, 1, 0, 0)
    assert csv.load_datetime(text2, fmt) == data2

def test_load_list():
    text0 = None
    data0 = []
    assert csv.load_list(text0) == data0
    text1 = ''
    data1 = []
    assert csv.load_list(text1) == data1
    text2 = 'thing1; thing2'
    data2 = ['thing1', 'thing2']
    assert csv.load_list(text2) == data2

def test_load_kvlist():
    text0 = None
    data0 = []
    print(text0)
    assert csv.load_kvlist(text0) == data0
    text1 = ''
    data1 = []
    print(text1)
    assert csv.load_kvlist(text1) == data1
    text2 = 'name1:author; name2:photog'
    data2 = [
        {u'name1': u'author'},
        {u'name2': u'photog'}
    ]
    print(text2)
    assert csv.load_kvlist(text2) == data2

def test_load_labelledlist():
    ll0 = csv.load_labelledlist('eng')
    ll1 = csv.load_labelledlist('eng;jpn')
    ll2 = csv.load_labelledlist('eng:English')
    ll3 = csv.load_labelledlist('eng:English; jpn:Japanese')
    assert ll0 == [u'eng']
    assert ll1 == [u'eng', u'jpn']
    assert ll2 == [u'eng']
    assert ll3 == [u'eng', u'jpn']

def test_load_rolepeople():
    text0 = None
    data0 = []
    assert csv.load_rolepeople(text0) == data0
    text1 = ''
    data1 = []
    assert csv.load_rolepeople(text1) == data1
    text2 = 'Watanabe, Joe'
    data2 = [
        {
            u'namepart': u'Watanabe, Joe',
            u'role': u'author'
        }
    ]
    assert csv.load_rolepeople(text2) == data2
    text3 = 'Watanabe, Joe; '
    data3 = [
        {
            u'namepart': u'Watanabe, Joe',
            u'role': u'author'
        }
    ]
    assert csv.load_rolepeople(text3) == data3
    text4 = 'Masuda, Kikuye:author'
    data4 = [
        {
            u'namepart': u'Masuda, Kikuye',
            u'role': u'author'
        }
    ]
    assert csv.load_rolepeople(text4) == data4
    text5 = 'Yorke, Thom:musician; Godrich, Nigel:producer'
    data5 = [
        {
            u'namepart': u'Yorke, Thom',
            u'role': u'musician'
        },
        {
            u'namepart': u'Godrich, Nigel',
            u'role': u'producer'
        }
    ]
    assert csv.load_rolepeople(text5) == data5
    text6 = 'Yorke, Thom:musician; Murakami, Haruki'
    data6 = [
        {
            'namepart': u'Yorke, Thom',
            'role': u'musician'
        },
        {
            'namepart': u'Murakami, Haruki',
            'role': u'author'
        }
    ]
    assert csv.load_rolepeople(text6) == data6


# TODO csv.dump_* ------------------------------------------------------------

def test_dump_string():
    #assert isinstance(csv.load_string(u'this is a str'), unicode)
    #assert isinstance(csv.load_string('this is a str'), unicode)
    #padding = csv.load_string('  padded  ')
    #assert not re.search('^\s', padding)  # no space at start
    #assert not re.search('$\s', padding)  # no space at end
    #linebreaks = csv.load_string('line 0\r\nline 1\rline2')
    #assert linebreaks == 'line 0\\nline 1\\nline2'
    pass

def test_dump_datetime():
    data = datetime(1970, 1, 1, 0, 0); fmt = '%Y-%m-%dT%H:%M:%S'
    text = u'1970-01-01T00:00:00'
    assert csv.dump_datetime(data, fmt) == text

def test_dump_list():
    data0 = ['thing1', 'thing2']
    text0 = 'thing1; thing2'
    assert csv.dump_list(data0) == text0

def test_dump_kvlist():
    data = [
        {u'name1': u'author'},
        {u'name2': u'photog'}
    ]
    text = u'name1:author; name2:photog'
    assert csv.dump_kvlist(data) == text

def test_dump_labelledlist():
    data0 = [u'eng']
    text0 = u'eng'
    assert csv.dump_labelledlist(data0) == text0
    data1 = [u'eng', u'jpn']
    text1 = u'eng; jpn'
    assert csv.dump_labelledlist(data1) == text1

def test_dump_rolepeople():
    data0 = []
    text0 = u''
    assert csv.dump_rolepeople(data0) == text0
    data1 = [
        {
            'namepart': 'Masuda, Kikuye',
            'role': 'author'
        }
    ]
    text1 = u'Masuda, Kikuye:author'
    assert csv.dump_rolepeople(data1) == text1
    data2 = [
        {
            'namepart': 'Yorke, Thom',
            'role': 'musician'
        },
        {
            'namepart': 'Godrich, Nigel',
            'role': 'producer'
        }
    ]
    text2 = u'Yorke, Thom:musician; Godrich, Nigel:producer'
    assert csv.dump_rolepeople(data2) == text2
    # ERROR that has made its way into many files
    data3 = [
        {
            'namepart': "",
            'role': "author"
        }
    ]
    text3 = u''
    assert csv.dump_rolepeople(data3) == text3
    # never got converted to data
    data4 = 'Watanabe, Joe'
    text4 = u'Watanabe, Joe'
    assert csv.dump_rolepeople(data4) == text4
