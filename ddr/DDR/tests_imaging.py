import os
import urllib

from nose.tools import assert_raises

import imaging


TEST_IMG_URL = 'https://web.archive.org/web/20011221151014im_/http://densho.org/images/logo.jpg'
TEST_IMG_PATH = '/tmp/ddr-test-imaging.jpg'


identify_out = {
    'JPEG': '/tmp/file.jpg JPEG 800x573 800x573+0+0 8-bit DirectClass 63.2KB 0.000u 0:00.000',
    'TIFF': '/tmp/file.tif[0] TIFF 5632x8615 5632x8615+0+0 8-bit DirectClass 147.4MB 0.000u 0:00.000\n/tmp/file.tif[1] TIFF 625x957 625x957+0+0 8-bit DirectClass 147.4MB 0.000u 0:00.000',
    'PDF': '/tmp/file.pdf[0] PDF 397x598 397x598+0+0 16-bit Bilevel DirectClass 30KB 0.100u 0:00.080\n/tmp/file.pdf[1] PDF 397x598 397x598+0+0 16-bit Bilevel DirectClass 30KB 0.090u 0:00.080\n/tmp/file.pdf[2] PDF 397x598 397x598+0+0 16-bit Bilevel DirectClass 30KB 0.090u 0:00.080',
    'DOCX': "identify.im6: no decode delegate for this image format `/tmp/file.docx' @ error/constitute.c/ReadImage/544.",
}

def test_analyze_magick():
    
    jpeg = imaging.analyze_magick(identify_out['JPEG'])
    tiff = imaging.analyze_magick(identify_out['TIFF'])
    pdf = imaging.analyze_magick(identify_out['PDF'])
    docx = imaging.analyze_magick(identify_out['DOCX'])
    assert jpeg['path'] == '/tmp/file.jpg'
    assert jpeg['frames'] == 1
    assert jpeg['format'] == 'JPEG'
    assert jpeg['image'] == True
    assert tiff['path'] == '/tmp/file.tif'
    assert tiff['frames'] == 2
    assert tiff['format'] == 'TIFF'
    assert tiff['image'] == True
    assert pdf['path'] == '/tmp/file.pdf'
    assert pdf['frames'] == 3
    assert pdf['format'] == 'PDF'
    assert pdf['image'] == True
    assert docx['path'] == None
    assert docx['frames'] == 1
    assert docx['format'] == None
    assert docx['image'] == False

def test_analyze():
    if not os.path.exists(TEST_IMG_PATH):
        urllib.urlretrieve(TEST_IMG_URL, TEST_IMG_PATH)
    path0 = '/tmp/missingfile.jpg'
    path1 = TEST_IMG_PATH
    assert_raises(Exception, imaging.analyze, path0)
    assert os.path.exists(path1)
    out1 = imaging.analyze(path1)
    expected1 = {
        'path': '/tmp/ddr-test-imaging.jpg',
        'frames': 1, 'can_thumbnail': None, 'image': True, 'format': 'JPEG'
    }
    assert out1 == expected1

geometry = {
    'ok': ['123x123', '123>x123', '123x123>', '123x', 'x123',],
    'bad': ['123',],
}
def test_geometry_is_ok():
    for s in geometry['ok']:
        assert imaging.geometry_is_ok(s) == True
    for s in geometry['bad']:
        assert imaging.geometry_is_ok(s) == False

def test_make_convert_cmd():
    cmd = imaging.make_convert_cmd(
        src='/tmp/file.tif',
        dest='/tmp/file-thumb.jpg',
        geometry='100x100'
    )
    assert cmd == "convert /tmp/file.tif -resize '100x100' /tmp/file-thumb.jpg"

def test_thumbnail():
    if not os.path.exists(TEST_IMG_PATH):
        urllib.urlretrieve(TEST_IMG_URL, TEST_IMG_PATH)
    src = TEST_IMG_PATH
    dest = '/tmp/ddr-test-imaging-thumb.jpg'
    geometry = '100x100'
    assert os.path.exists(src)
    imaging.thumbnail(src, dest, geometry)
    assert os.path.exists(dest)

def test_extract_xmp():
    if not os.path.exists(TEST_IMG_PATH):
        urllib.urlretrieve(TEST_IMG_URL, TEST_IMG_PATH)
    out0 = imaging.extract_xmp(TEST_IMG_PATH)
    expected0 = '<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Exempi + XMP Core 5.1.2"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"><rdf:Description rdf:about=""/></rdf:RDF></x:xmpmeta>'
    print(out0)
    assert out0 == expected0
