"""Save self-reported food reactions in a separate local SQLite diary."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

from build_ic_database import ROOT, normalize


OUTCOMES = ('tolerated', 'symptoms', 'unsure')
DIARY_PATH = ROOT / 'database/private/food_diary.sqlite3'
SCHEMA_PATH = ROOT / 'database/food_diary_schema.sql'


def record_reaction(food, outcome, *, ingredients=(), notes='', portion='',
                    ate_at=None, database=None, barcode=None):
    """Save one food exposure and return its diary entry ID."""
    food = food.strip()
    if not food:
        raise ValueError('Enter the name of the food or meal.')
    if outcome not in OUTCOMES:
        raise ValueError('Choose tolerated, symptoms, or unsure.')
    if isinstance(ingredients, str):
        raise ValueError('Provide ingredient names as a list.')

    terms = {}
    for ingredient in ingredients:
        name = ingredient.strip()
        if not name:
            raise ValueError('Ingredient names cannot be empty.')
        terms.setdefault(normalize(name), name)

    ate_at = ate_at if ate_at is not None else datetime.now(timezone.utc)
    if ate_at.utcoffset() is None:
        raise ValueError('Include a time zone with the date and time eaten.')

    path = Path(database) if database is not None else DIARY_PATH
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as db, db:
        db.execute('PRAGMA foreign_keys = ON')
        db.executescript(SCHEMA_PATH.read_text())
        entry_id = db.execute(
            'INSERT INTO food_entries (food, outcome, notes, portion, ate_at) VALUES (?, ?, ?, ?, ?)',
            (food, outcome, notes.strip(), portion.strip(), ate_at.astimezone(timezone.utc).isoformat()),
        ).lastrowid
        if barcode:
            db.execute('INSERT INTO food_entry_products (entry_id, barcode) VALUES (?, ?)',
                       (entry_id, barcode))
        db.executemany(
            'INSERT INTO food_entry_ingredients VALUES (?, ?, ?)',
            ((entry_id, name, term) for term, name in terms.items()),
        )
    return entry_id


def summarize_reactions(ingredient, *, database=None):
    """Count diary outcomes for one exact normalized ingredient name."""
    path = Path(database) if database is not None else DIARY_PATH
    counts = dict.fromkeys(OUTCOMES, 0)
    if not path.exists():
        return counts
    with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)) as db:
        counts.update(db.execute(
            '''SELECT e.outcome, COUNT(*)
               FROM food_entry_ingredients i JOIN food_entries e ON e.id = i.entry_id
               WHERE i.normalized_ingredient = ?
               GROUP BY e.outcome''',
            (normalize(ingredient),),
        ))
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--food', required=True, help='Food or meal eaten')
    parser.add_argument('--outcome', required=True, choices=OUTCOMES)
    parser.add_argument('--ingredient', action='append', default=[],
                        help='Known ingredient, one per flag')
    parser.add_argument('--notes', default='', help='How you felt after eating')
    parser.add_argument('--portion', default='')
    parser.add_argument('--ate-at', type=datetime.fromisoformat,
                        help='ISO date and time with a UTC offset')
    args = parser.parse_args()
    try:
        entry_id = record_reaction(
            args.food, args.outcome, ingredients=args.ingredient, notes=args.notes,
            portion=args.portion, ate_at=args.ate_at,
        )
    except (ValueError, OSError, sqlite3.Error) as exc:
        parser.exit(1, f'Could not save diary entry. {exc}\n')
    print(f'Saved diary entry {entry_id}.')


if __name__ == '__main__':
    main()
