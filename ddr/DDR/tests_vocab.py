from datetime import datetime
import vocab


# Index.add
# Index.terms
# Index.get
# Index._get_by_term_ids
# Index._parent
# Index._children
# Index._siblings
# Index._path
# Index._format
# Index._build
# Index.load_csv
# Index.load_json
# Index.dump_csv
# Index.dump_graphviz
# Index.dump_json
# Index.dump_terms_text
# Index.dump_terms_json
# Index.menu_choices
# Index.path_choices

def test_objects():
    index = vocab.Index()
    index.add( vocab.Term( id=1, parent_id=0, title='music') )
    index.add( vocab.Term( id=2, parent_id=1, title='classical') )
    index.add( vocab.Term( id=3, parent_id=1, title='jazz') )
    index.add( vocab.Term( id=4, parent_id=1, title='electronic') )
    index.add( vocab.Term( id=5, parent_id=2, title='romantic') )
    index.add( vocab.Term( id=6, parent_id=2, title='modern') )
    index.add( vocab.Term( id=7, parent_id=3, title='traditional') )
    index.add( vocab.Term( id=8, parent_id=3, title='fusion') )
    index.add( vocab.Term( id=9, parent_id=4, title='dance') )
    index.add( vocab.Term(id=10, parent_id=4, title='experimental') )
    
    music = index.get(id=1)
    assert index._parent(music) == None
    assert index._siblings(music) == None
    assert len(index._children(music)) == 3
    
    electronic = index.get(title='electronic')
    assert index._parent(electronic).id == 1
    assert index._parent(electronic).title == 'music'
    assert len(index._siblings(electronic)) == 2
    assert index._siblings(electronic)[0].id == 2
    assert index._siblings(electronic)[0].title == 'classical'
    assert len(index._children(electronic)) == 2
    assert index._children(electronic)[0].id == 9
    assert index._children(electronic)[0].title == 'dance'
    
    experimental = index.get(title='experimental')
    assert index._parent(experimental).id == 4
    assert index._parent(experimental).title == 'electronic'
    assert len(index._siblings(experimental)) == 1
    assert index._siblings(experimental)[0].id == 9
    assert index._siblings(experimental)[0].title == 'dance'
    assert index._children(experimental) == []

    assert index.dump_terms_json(id='music', title='Music', description='genres of music') == TERMS_JSON
    assert index.dump_terms_text() == TERMS_TEXT.strip()
    assert index.menu_choices() == MENU_CHOICES

# Term.__init__
# Term.__repr__
# Term._flatten
# Term.json

def test_csv():
    filename = '/tmp/vocab-index-%s' % datetime.now().strftime('%Y%m%d-%H%M%S')
    filename_csv = '%s.csv' % filename
    with open(filename_csv, 'w') as f0:
        f0.write(TERMS_CSV.strip())
    # load file
    index = vocab.Index()
    index.load_csv(filename_csv)
    assert index.dump_terms_csv().strip() == TERMS_CSV.strip()
    os.remove(filename_csv)

def test_json():
    filename = '/tmp/vocab-index-%s' % datetime.now().strftime('%Y%m%d-%H%M%S')
    filename_csv = '%s.csv' % filename
    filename_json = '%s.json' % filename
    with open(filename_csv, 'w') as f0:
        f0.write(TERMS_CSV.strip())
    # load file
    index = vocab.Index()
    index.load_csv(filename_csv)
    assert index.dump_terms_json(id='music', title='Music', description='genres of music') == TERMS_JSON
    os.remove(filename_csv)
    os.remove(filename_json)


TERMS_CSV = """
id,title,title_display,parent_id,change notes,weight,encyc_links,description,created,modified
1,,music,0,,0,[],,,
2,,classical,1,,0,[],,,
3,,jazz,1,,0,[],,,
4,,electronic,1,,0,[],,,
5,,romantic,2,,0,[],,,
6,,modern,2,,0,[],,,
7,,traditional,3,,0,[],,,
8,,fusion,3,,0,[],,,
9,,dance,4,,0,[],,,
10,,experimental,4,,0,[],,,
"""

TERMS_TEXT = """
music
NT classical, jazz, electronic

classical
BT music
NT romantic, modern
RT jazz, electronic

jazz
BT music
NT traditional, fusion
RT classical, electronic

electronic
BT music
NT dance, experimental
RT classical, jazz

romantic
BT classical
RT modern

modern
BT classical
RT romantic

traditional
BT jazz
RT fusion

fusion
BT jazz
RT traditional

dance
BT electronic
RT experimental

experimental
BT electronic
RT dance
"""

TERMS_JSON = """{"description": "genres of music", "terms": [{"description": "", "weight": 0, "created": null, "title": "music", "modified": null, "_title": null, "parent_id": 0, "encyc_urls": [], "id": 1}, {"description": "", "weight": 0, "created": null, "title": "classical", "modified": null, "_title": null, "parent_id": 1, "encyc_urls": [], "id": 2}, {"description": "", "weight": 0, "created": null, "title": "jazz", "modified": null, "_title": null, "parent_id": 1, "encyc_urls": [], "id": 3}, {"description": "", "weight": 0, "created": null, "title": "electronic", "modified": null, "_title": null, "parent_id": 1, "encyc_urls": [], "id": 4}, {"description": "", "weight": 0, "created": null, "title": "romantic", "modified": null, "_title": null, "parent_id": 2, "encyc_urls": [], "id": 5}, {"description": "", "weight": 0, "created": null, "title": "modern", "modified": null, "_title": null, "parent_id": 2, "encyc_urls": [], "id": 6}, {"description": "", "weight": 0, "created": null, "title": "traditional", "modified": null, "_title": null, "parent_id": 3, "encyc_urls": [], "id": 7}, {"description": "", "weight": 0, "created": null, "title": "fusion", "modified": null, "_title": null, "parent_id": 3, "encyc_urls": [], "id": 8}, {"description": "", "weight": 0, "created": null, "title": "dance", "modified": null, "_title": null, "parent_id": 4, "encyc_urls": [], "id": 9}, {"description": "", "weight": 0, "created": null, "title": "experimental", "modified": null, "_title": null, "parent_id": 4, "encyc_urls": [], "id": 10}], "id": "music", "title": "Music"}"""

MENU_CHOICES = [
    (1, 'music'), (2, 'classical'), (3, 'jazz'), (4, 'electronic'),
    (5, 'romantic'), (6, 'modern'), (7, 'traditional'), (8, 'fusion'),
    (9, 'dance'), (10, 'experimental')
]
