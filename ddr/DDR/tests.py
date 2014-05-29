import DDR


def test_natural_sort():
    l = ['11', '1', '12', '2', '13', '3']
    DDR.natural_sort(l)
    assert l == ['1', '2', '3', '11', '12', '13']

def test_natural_order_string():
    assert DDR.natural_order_string('ddr-testing-123') == '123'
    assert DDR.natural_order_string('ddr-testing-123-1') == '1'
    assert DDR.natural_order_string('ddr-testing-123-15') == '15'

# Time.mark
# Timer.display
