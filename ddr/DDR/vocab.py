"""
DDR.vocab.py -- controlled vocabulary tools

from DDR.vocab import Index, Term
index = Index()
index.add( Term( id=1, parent_id=0, title='music') )
index.add( Term( id=2, parent_id=1, title='classical') )
index.add( Term( id=3, parent_id=1, title='jazz') )
index.add( Term( id=4, parent_id=1, title='electronic') )
index.add( Term( id=5, parent_id=2, title='romantic') )
index.add( Term( id=6, parent_id=2, title='modern') )
index.add( Term( id=7, parent_id=3, title='traditional') )
index.add( Term( id=8, parent_id=3, title='fusion') )
index.add( Term( id=9, parent_id=4, title='dance') )
index.add( Term(id=10, parent_id=4, title='experimental') )

music = index.get(id=1)
index.parent(music)
index.siblings(music)
index.children(music)

electronic = index.get(title='electronic')
index.parent(electronic)
index.siblings(electronic)
index.children(electronic)

experimental = index.get(title='experimental')
index.parent(experimental)
index.siblings(experimental)
index.children(experimental)

from DDR.vocab import Index, Term
index = Index()

index.load_csv(csvfile_abs='/tmp/topics.csv')

with open('/tmp/topic-index.json', 'w') as f:
    f.write(index.dump_json())

with open('/tmp/topic-index.json', 'r') as f:
    index.load_json(f.read())

index.dump_csv('/tmp/topics2.csv')

# JSON file of all terms
with open('/tmp/topics.json', 'w') as f:
    f.write(index.dump_terms_json())

# Text version of all terms
with open('/tmp/topics.txt', 'w') as f:
    f.write(index.dump_terms_text())

index.menu_choices()
index.path_choices()
"""

import csv
import json

CSV_HEADER_MAPPING = [
    {'header':'id',            'attr':'id'},
    {'header':'title',         'attr':'_title'},
    {'header':'title_display', 'attr':'title'},
    {'header':'parent_id',     'attr':'parent_id'},
    {'header':'change notes',  'attr':None},
    {'header':'weight',        'attr':'weight'},
    {'header':'encyc_links',   'attr':'encyc_urls'},
    {'header':'description',   'attr':'description'},
    {'header':'created',       'attr':'created'},
    {'header':'modified',      'attr':'modified'},
]

class Index( object ):
    ids = []
    _terms_by_id = {}
    _titles_to_ids = {}
    _parents_to_children = {}
    
    def add( self, term ):
        """Adds a Term to the Index.
        """
        self.ids.append(term.id)
        self._terms_by_id[term.id] = term
        # enables retrieve by title
        self._titles_to_ids[term.title] = term.id
        # lists of children for each parent
        if not self._parents_to_children.get(term.parent_id):
            self._parents_to_children[term.parent_id] = []
        if (term.id not in self._parents_to_children[term.parent_id]):
            self._parents_to_children[term.parent_id].append(term.id)
    
    def terms( self ):
        return [self._terms_by_id.get(tid, None) for tid in self.ids]
    
    def get( self, id=None, title=None ):
        """Returns Term matching the id or title, or None.
        """
        if title and not id:
            id = self._titles_to_ids.get(title, None)
        if id:
            return self._terms_by_id.get(id, None)
        raise Exception('id or title is required')
    
    def _get_by_term_ids( self, term_ids ):
        terms = []
        for id in term_ids:
            term = self._terms_by_id.get(id, None)
            if term:
                terms.append(term)
        return terms
    
    def _parent( self, term ):
        """Term for term.parent_id or None.
        """
        return self._terms_by_id.get(term.parent_id, None) 
    
    def _children( self, term ):
        """List of terms that have term.id as their parent_id.
        """
        term_ids = self._parents_to_children.get(term.id, [])
        terms = self._get_by_term_ids(term_ids)
        return terms
   
    def _siblings( self, term ):
        """List of other terms with same parent_id.
        """
        parent = self._parent(term)
        if parent:
            return [t for t in self._children(parent) if t != term]
        return None
    
    def _path( self, term ):
        term.path = ''
        path = [term.title]
        t = term
        while t.parent_id:
            t = self._parent(t)
            path.append(t.title)
        path.reverse()
        return ': '.join(path)
    
    def _format( self, term ):
        bt = self._parent(term)
        nt = self._children(term)
        rt = self._siblings(term)
        lines = []
        lines.append(term.title)
        if term.description: lines.append('  %s' % term.description)
        if bt: lines.append('BT %s' % bt.title)
        if nt: lines.append('NT %s' % ', '.join([t.title for t in nt]))
        if rt: lines.append('RT %s' % ', '.join([t.title for t in rt]))
        return '\n'.join(lines)
    
    def _build( self, terms ):
        """Adds list of raw Term objects to Index, adds parent/siblings/children to each Term.
        """
        for term in terms:
            self.add(term)
        for term in terms:
            term.parent = self._parent(term)
            term.siblings = self._siblings(term)
            term.children = self._children(term)
            term.path = self._path(term)
            term.format = self._format(term)
    
    def load_csv( self, csvfile_abs, header_mapping=CSV_HEADER_MAPPING, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC ):
        """Load terms from a CSV file.
        
        See header list in Index.CSV_HEADER_MAPPING.
        
        @param csvfile_abs: Absolute path to CSV file
        @param header_mapping
        @param delimiter
        @param quotechar
        @param quoting
        """
        csvfile = open(csvfile_abs, 'rb')
        reader = csv.reader(csvfile) #, delimiter=delimiter, quotechar=quotechar, quoting=quoting)
        terms = []
        for n,row in enumerate(reader):
            if n:
                term = Term()
                for c,col in enumerate(header_mapping):
                    attr = col['attr']
                    value = row[c]
                    if attr:
                        if (attr in ['id', 'parent_id', 'weight']) and value:
                            value = int(value)
                        elif (attr == 'encyc_urls') and value:
                            value = value.split(',')
                        setattr(term, attr, value)
                terms.append(term)
        self._build(terms)
    
    def load_json( self, jsonfile ):
        """Load terms from a JSON file.
        
        See header list in Index.CSV_HEADER_MAPPING.
        
        @param jsonfile: JSON-formatted text
        @param header_mapping
        """
        pass
    
    def dump_csv( self, csvfile_abs, header_mapping=CSV_HEADER_MAPPING, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC ):
        """Write terms to a CSV file.
        
        See header list in Index.CSV_HEADER_MAPPING.
        
        @param csvfile_abs: Absolute path to CSV file
        @param header_mapping
        @param delimiter
        @param quotechar
        @param quoting
        """
        with open(csvfile_abs, 'wb') as csvfile:
            writer = csv.writer(csvfile) #, delimiter=delimiter, quotechar=quotechar, quoting=quoting)
            # headers
            writer.writerow([header['header'] for header in header_mapping])
            # data
            for tid,term in self._terms_by_id.iteritems():
                values = []
                for header in header_mapping:
                    value = ''
                    if header.get('attr',None):
                        value = getattr(term, header['attr'])
                    values.append(value)
                writer.writerow(values)
    
    def dump_graphviz( self, term_len=50 ):
        """Dumps contents of index to a Graphviz file.
        
        digraph terms {
          rankdir=RL;
          2-classical -> 1-music;
          3-jazz -> 1-music;
        }
        
        Render thusly:
        $ dot -Tpng -o /tmp/terms.png /tmp/terms.gv
        """
        lines = [
            'digraph G {',
            '  rankdir=RL;'
        ]
        for tid,term in self._terms_by_id.iteritems():
            parent = self._parent(term)
            if parent:
                src = '"%s-%s"' % (term.id, term.title[:term_len].replace('"',''))
                dest = '"%s-%s"' % (parent.id, parent.title[:term_len].replace('"',''))
                line = '  %s -> %s;' % (src, dest)
                lines.append(line)
        lines.append('}')
        return '\n'.join(lines)
    
    def dump_json( self ):
        """Dumps contents of index to JSON.
        """
        terms = {}
        for tid,term in self._terms_by_id.iteritems():
            terms[tid] = term._flatten()
        return json.dumps({
            'ids': self.ids,
            'terms_by_id': terms,
            'titles_to_ids': self._titles_to_ids,
            'parents_to_children': self._parents_to_children,
        })
    
    def dump_terms_text( self ):
        """Text format of the entire index.
        """
        terms = [self._format(term) for id,term in self._terms_by_id.iteritems()]
        return '\n\n'.join(terms)

    def dump_terms_json( self, id, title, description ):
        """JSON format of the entire index.
        
        Terms list plus a keyword, title, and description.
        This is the same format used for Elasticsearch facets.
        
        @param id
        @param title
        @param description
        """
        data = {
            'id': id,
            'title': title,
            'description': description,
            'terms': [term._flatten() for term in self.terms()],
        }
        return json.dumps(data)
        
    def menu_choices( self ):
        """List of (id,title) tuples suitable for use in Django multiselect menu.
        """
        return [(term.id,term.title) for term in self.terms()]

    def path_choices( self ):
        """List of (id,title) tuples suitable for use in Django multiselect menu.
        """
        return [('%s [%s]' % (term.path, term.id)) for term in self.terms()]


class Term( object ):
    id = None
    parent_id = None
    created = None
    modified = None
    _title = None
    title = None
    description = ''
    weight = 0
    encyc_urls = []
    parent = None
    siblings = None
    children = None
    path = None

    def __init__(self, id=None, parent_id=None, created=None, modified=None, _title=None, title=None, description='', weight=0, encyc_urls=[]):
        self.id = id
        self.parent_id = parent_id
        self.created = created
        self.modified = modified
        self._title = _title
        self.title = title
        self.description = description
        self.weight = weight
        self.encyc_urls = encyc_urls
    
    def __repr__( self ):
        return "<Term %s: %s>" % (self.id, self.title)
    
    def _flatten( self ):
        data = {}
        for key,val in self.__dict__.iteritems():
            if (key in ['parent']) and val:
                val = getattr(self, key).id
            elif (key in ['siblings', 'children']) and val:
                val = []
                for t in getattr(self, key):
                    val.append(t.id)
            data[key] = val
        return data
    
    def json( self ):
        return json.dumps(self._flatten())
