import os

import DDR


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
