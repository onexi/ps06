"""Run barcode lookup and IC assessment from the command line."""
import argparse
import json
import sys

from assess_product import assess_label, assess_product
# Keep validate_barcode available here for existing callers.
from fetch_product import LookupFailure, fetch_product, validate_barcode
from ollama_model import ModelError, explain_quantities
from suggest_ingredients import parse_match_threshold


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument('--barcode', help='Barcode digits, including leading zeros')
    inputs.add_argument('--label', help='Manually entered English ingredient label')
    parser.add_argument('--production', action='store_true', help='Use the live product database instead of staging')
    parser.add_argument('--match-threshold', type=parse_match_threshold, default=50,
                        help='Minimum similarity for close matches, 1–100 (default: 50, 100 uses exact matches)')
    parser.add_argument('--explain-quantities', action='store_true',
                        help='Ask the local Ollama model to explain quantity evidence')
    args = parser.parse_args()
    try:
        if args.label is not None:
            result = assess_label(args.label, match_threshold=args.match_threshold)
        else:
            result = assess_product(args.barcode, fetch_product(args.barcode, args.production),
                                    match_threshold=args.match_threshold)
    except (ValueError, LookupFailure, FileNotFoundError) as exc:
        print(json.dumps({'error':str(exc), 'assessment_incomplete':True}), file=sys.stderr)
        return 1
    if args.explain_quantities:
        assessment = result['assessment']
        evidence = [
            {key: row[key] for key in ('ingredient', 'irritation_rating', 'quantity_evidence', 'quantity_note')
             if key in row}
            for row in assessment['ingredients'] if 'irritation_rating' in row
        ]
        if evidence:
            try:
                assessment['quantity_explanation'] = explain_quantities(evidence)
            except ModelError as exc:
                assessment['quantity_explanation_error'] = str(exc)
    print(json.dumps(result, indent=2))
    return 0

if __name__ == '__main__':
    sys.exit(main())
