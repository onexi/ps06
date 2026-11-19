"""Rebuild the generated reference database atomically using Python's standard library."""
import json
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unicodedata

ROOT = Path(__file__).resolve().parents[1]

def normalize(term):
    return ' '.join(unicodedata.normalize('NFKC', term).casefold().split())

def build(destination=None):
    destination = Path(destination) if destination else ROOT / 'database/ic_reference.sqlite3'
    seed = json.loads((ROOT / 'database/ic_seed.json').read_text())
    catalog = json.loads((ROOT / 'database/ingredient_catalog.json').read_text())
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, suffix='.sqlite3', delete=False) as f:
        temporary = Path(f.name)
    try:
        with closing(sqlite3.connect(temporary)) as db, db:
            db.executescript((ROOT / 'database/schema.sql').read_text())
            db.execute('INSERT INTO metadata VALUES (?, ?)', ('seed_version', str(seed['version'])))
            for source in seed['sources']:
                db.execute('INSERT INTO sources VALUES (?,?,?,?,?,?,?,?)',
                    tuple(source[k] for k in ('id','organization','title','url','source_reviewed','accessed','evidence_type','notes')))
            for row in seed['references']:
                db.execute('INSERT INTO ic_references VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', tuple(row[k] for k in
                    ('id','name','kind','classification','summary','source_id','reviewed_on','review_status','mapping_note',
                     'irritation_rating','rating_source_id','rating_basis')) + (row.get('display_status'),))
                for term in row['match_terms']:
                    db.execute('INSERT INTO match_terms(term, reference_id) VALUES (?,?)', (normalize(term), row['id']))
            db.executemany('INSERT INTO ambiguous_terms VALUES (?)', [(normalize(t),) for t in seed['ambiguous_terms']])
            for row in catalog:
                db.execute('INSERT INTO ingredient_identities VALUES (?,?,?,?,?)',
                    tuple(row[key] for key in ('id', 'name', 'category', 'description', 'source_url')))
                db.executemany('INSERT INTO ingredient_identity_terms VALUES (?,?)',
                    [(normalize(term), row['id']) for term in row['terms']])
            if db.execute('PRAGMA foreign_key_check').fetchall():
                raise ValueError('Invalid source links')
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination

if __name__ == '__main__':
    print(build())
