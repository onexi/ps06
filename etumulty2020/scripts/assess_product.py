"""Assess a product record or manually entered ingredient label."""
from datetime import datetime, timezone

from check_ingredients import check
from parse_ingredients import parse_label


def assess_label(label, database=None, *, match_threshold=50):
    parsed = parse_label(label)
    assessment = check(parsed['candidates'], database, label_incomplete=bool(parsed['warnings']),
                       match_threshold=match_threshold)
    quantities = parsed.pop('quantities', {})
    for row in assessment['ingredients']:
        quantity = quantities.get(row['ingredient'], {'status': 'unknown'})
        row['quantity_evidence'] = quantity
        if row.get('irritation_rating') == 'context_dependent' and (
            row['ingredient'].casefold() == 'salt'
            or row.get('display_status') == 'Depends on amount'
            or 'amount' in row.get('rating_basis', '').lower()
        ):
            if quantity['status'] == 'disclosed':
                row['quantity_note'] = 'Amount disclosed. The IC reference gives no numeric cutoff.'
            elif 'upper_bound_percent' in quantity:
                row['quantity_note'] = 'The label gives an upper bound. The exact amount is unknown.'
            else:
                row['quantity_note'] = 'The exact amount is unknown.'
    return {**parsed, 'assessment': assessment}

def assess_product(barcode, product, database=None, *, match_threshold=50):
    common = {'barcode': barcode, 'source': 'Open Food Facts',
        'source_url': f'https://world.openfoodfacts.org/product/{barcode}',
        'retrieved_at': datetime.now(timezone.utc).isoformat(),
        'requires_package_confirmation': True}
    if product is None:
        return {**common, 'lookup_status': 'not_found',
                **assess_label('', database, match_threshold=match_threshold)}
    label = product.get('ingredients_text_en')
    if not isinstance(label, str) or not label.strip():
        label = product.get('ingredients_text', '') if product.get('lang') == 'en' else ''
    if not isinstance(label, str):
        label = ''
    return {**common, 'lookup_status': 'found', 'product_name': product.get('product_name_en') or product.get('product_name'),
        'brands': product.get('brands'), 'product_last_modified': product.get('last_modified_t'),
        'unprocessed_label': product.get('ingredients_text'),
        **assess_label(label, database, match_threshold=match_threshold)}
