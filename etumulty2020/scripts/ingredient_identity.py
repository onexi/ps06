"""Look up descriptive ingredient information separately from IC evidence."""


def load_identities(db):
    """Return identities keyed by normalized label terms."""
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='ingredient_identities'").fetchone():
        return {}
    return {
        row['term']: {field: row[field] for field in ('name', 'category', 'description', 'source_url')}
        for row in db.execute('''SELECT t.term, i.name, i.category, i.description, i.source_url
            FROM ingredient_identity_terms t JOIN ingredient_identities i ON i.id=t.identity_id''')
    }
