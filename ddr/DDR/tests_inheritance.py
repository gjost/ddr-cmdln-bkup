import inheritance


MODEL_FIELDS_INHERITABLE = [
    {'name':'id',},
    {'name':'record_created',},
    {'name':'record_lastmod',},
    {'name':'status', 'inheritable':True,},
    {'name':'public', 'inheritable':True,},
    {'name':'title',},
]
def test_Inheritance_inheritable_fields():
    assert inheritance.inheritable_fields(MODEL_FIELDS_INHERITABLE) == ['status','public']

# TODO inheritance_inherit
# TODO inheritance_selected_inheritables
# TODO inheritance_update_inheritables
