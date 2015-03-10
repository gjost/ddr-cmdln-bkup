VERSION = '0.9.2-beta'
CONFIG_FILES = ['/etc/ddr/ddr.cfg', '/etc/ddr/local.cfg']

class NoConfigError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


from datetime import datetime, timedelta
import logging
logger = logging.getLogger(__name__)
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
    
    @param id: A valid format DDR ID
    """
    alnum = re.findall('\d+', id)
    if not alnum:
        raise Exception('Valid DDR ID required.')
    return alnum.pop()


class Timer( object ):
    """
    from DDR import Timer
    t = Timer()
    t.mark('start')
    ...YOUR CODE HERE...
    t.mark('did something')
    ...MORE CODE...
    t.mark('did something else')
    ...MORE CODE...
    t.display()
    """
    steps = []
    
    def mark( self, msg ):
        now = datetime.now()
        index = len(self.steps)
        if index:
            delta = now - self.steps[-1]['datetime']
        else:
            delta = timedelta(0)
        step = {'index':index, 'datetime':now, 'delta':delta, 'msg':msg}
        self.steps.append(step)
        logger.debug(msg)
    
    def display( self ):
        """Return list of steps arranged slowest first.
        """
        from operator import itemgetter
        ordered = sorted(self.steps, key=itemgetter('delta'))
        logger.debug('TIMER RESULTS -- SLOWEST-FASTEST -----------------------------------')
        for step in ordered:
            logger.debug('{:>10}: {:<14} | {}'.format(step['index'], step['delta'], step['msg']))
        return self.steps
