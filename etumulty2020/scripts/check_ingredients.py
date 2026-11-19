"""Check already-separated ingredient names. Does not parse raw label text."""
import argparse
import json
from contextlib import closing
from pathlib import Path
import sqlite3
from build_ic_database import ROOT, normalize
from ingredient_identity import load_identities
from suggest_ingredients import parse_match_threshold, suggest_matches

RATING_LABELS = {
    'most_bothersome': 'Most bothersome',
    'foods_to_avoid': 'Foods to avoid',
    'worth_trying_cautiously': 'Worth trying cautiously',
    'usually_bladder_friendly': 'Usually bladder friendly',
    'context_dependent': 'Depends on context',
    'unrated_potential_concern': 'Potential concern',
}


IRRITANT_RATINGS = {'most_bothersome', 'foods_to_avoid', 'unrated_potential_concern'}


def check(ingredients, database=None, *, label_incomplete=False, match_threshold=50):
    match_threshold = parse_match_threshold(match_threshold)
    path = Path(database) if database else ROOT / 'database/ic_reference.sqlite3'
    if not path.is_file():
        raise FileNotFoundError('Build the IC database first: python3 scripts/build_ic_database.py')
    results = []
    with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)) as db:
        db.row_factory = sqlite3.Row
        source_urls = dict(db.execute('SELECT id, url FROM sources'))
        identities = load_identities(db)
        contextual = {
            normalize(row['name']): row
            for row in map(dict, db.execute('''SELECT r.* FROM ic_references r
                WHERE NOT EXISTS (SELECT 1 FROM match_terms m WHERE m.reference_id=r.id)'''))
            if row.get('irritation_rating') == 'context_dependent'
        }
        reference_terms = []
        references_by_term = {}
        if match_threshold < 100:
            reference_terms = db.execute('''SELECT m.term, r.id, r.name, s.url
                FROM match_terms m JOIN ic_references r ON r.id=m.reference_id
                JOIN sources s ON s.id=r.source_id
                WHERE r.kind = 'ingredient' ''').fetchall()
            reference_terms.extend(
                (term, row['id'], row['name'], source_urls[row['source_id']])
                for term, row in contextual.items()
            )
            references = {
                row['id']: row for row in map(dict, db.execute('SELECT * FROM ic_references'))
            }
            references_by_term = {term: references[ref_id] for term, ref_id, _, _ in reference_terms}
        for ingredient in ingredients:
            term = normalize(ingredient)
            result = {'ingredient': ingredient}
            if term in identities:
                result['identity'] = identities[term]
            match = db.execute('''SELECT r.* FROM match_terms m
                JOIN ic_references r ON r.id=m.reference_id WHERE m.term=?''', (term,)).fetchone()
            if match is None:
                ambiguous = db.execute('SELECT 1 FROM ambiguous_terms WHERE term=?', (term,)).fetchone()
                status = 'ambiguous' if ambiguous else 'unknown'
                reference = contextual.get(term)
                evidence_status = 'context_only' if reference else 'unavailable'
            else:
                status = match['classification']
                evidence_status = 'reference_match'
                reference = dict(match)
            result.update(status=status, ic_evidence_status=evidence_status)
            results.append(result)
            if reference is None and term == 'salt':
                result.update(
                    display_status='Salt type unspecified',
                    irritation_rating='context_dependent',
                    rating_basis='Generic salt does not identify a specific salt variety.',
                    ic_evidence_status='context_only',
                )
                continue
            if reference is None:
                result['display_status'] = 'Ingredient unclear' if status == 'ambiguous' else 'IC evidence unavailable'
                if status != 'unknown' or not reference_terms or term == 'baking soda':
                    continue
                suggestions = suggest_matches(term, reference_terms, match_threshold, limit=None)
                if not suggestions:
                    continue
                result['possible_matches'] = suggestions[:3]
                # Use an irritant among the candidates even when another variant
                # has a higher spelling similarity.
                selected = next(
                    (candidate for candidate in suggestions
                     if references_by_term[candidate['matched_term']]['irritation_rating'] in IRRITANT_RATINGS),
                    suggestions[0],
                )
                reference = references_by_term[selected['matched_term']]
                result.update(
                    status=reference['classification'],
                    ic_evidence_status='similar_reference_match',
                    applied_match=selected,
                )
            source_id = reference['source_id']
            rating = reference.get('irritation_rating', 'unrated_potential_concern')
            result.update({
                **{key: reference[key] for key in ('name', 'summary', 'review_status', 'reviewed_on')},
                'source_url': source_urls[source_id],
                'irritation_rating': rating,
                'display_status': reference.get('display_status') or RATING_LABELS[rating],
                'rating_source_url': source_urls[reference.get('rating_source_id', source_id)],
                'rating_basis': reference.get('rating_basis', 'This reference has no recorded source rating.'),
            })
    concerns = any(row.get('irritation_rating') in IRRITANT_RATINGS for row in results)
    incomplete = label_incomplete or not results or any(
        row['ic_evidence_status'] != 'reference_match' for row in results
    )
    if not results:
        assessment_status = 'no_ingredients'
        display_status = 'No ingredients to assess'
        message = 'No ingredients were available to assess. Check the package and enter its ingredient list manually.'
    elif concerns:
        assessment_status = 'bladder_unfriendly'
        display_status = 'Bladder unfriendly'
        message = 'At least one ingredient matched a possible bladder irritant.'
    elif label_incomplete or any('irritation_rating' in row or row['status'] == 'ambiguous' for row in results):
        assessment_status = 'try_and_report'
        display_status = 'Try it and tell us how you feel'
        message = 'No ingredient was flagged as an irritant. Personal tolerance can vary.'
    else:
        assessment_status = 'bladder_friendly'
        display_status = 'Bladder friendly'
        message = 'No ingredients matched the local IC database. Personal tolerance can vary.'
    return {
        'assessment_status': assessment_status,
        'display_status': display_status,
        'concerns_found': concerns,
        'assessment_incomplete': incomplete,
        'message': message,
        'ingredients': results,
    }

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ingredients', nargs='+', help='One ingredient per argument; quote multiword names.')
    parser.add_argument('--match-threshold', type=parse_match_threshold, default=50,
                        help='Minimum similarity for close matches, 1–100 (default: 50, 100 uses exact matches)')
    args = parser.parse_args()
    print(json.dumps(check(args.ingredients, match_threshold=args.match_threshold), indent=2))
