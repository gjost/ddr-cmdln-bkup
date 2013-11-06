VERSION = 0.1
CONFIG_FILE = '/etc/ddr/ddr.cfg'


import re

def natural_sort( l ):
    """Sort the given list in the way that humans expect.
    src: http://www.codinghorror.com/blog/2007/12/sorting-for-humans-natural-sort-order.html
    """
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    l.sort( key=alphanum_key )
    return l

def natural_order_string( id ):
    """Convert a collection/entity ID into form that can be sorted naturally.
    See natural_sort()
    """
    convert = lambda text: int(text) if text.isdigit() else text
    alnum = [ convert(c) for c in re.split('([0-9]+)', id) ]
    return alnum
