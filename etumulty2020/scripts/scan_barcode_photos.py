"""Read barcodes from a photo or folder on macOS and optionally assess products."""
import argparse
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile



def read_photos(photos):
    """Return detected barcode payloads for each photo using macOS Vision."""
    helper = Path(__file__).with_name('read_barcode_photos.swift')
    command = ['swift', '-module-cache-path', str(Path(tempfile.gettempdir()) / 'ic-food-swift-cache'),
               str(helper), *map(str, photos)]
    run = subprocess.run(command, text=True, capture_output=True, check=True, timeout=180)
    return [json.loads(line) for line in run.stdout.splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path, help='Photo or folder of photos')
    parser.add_argument('--lookup', action='store_true', help='Look up products in live Open Food Facts')
    args = parser.parse_args()
    if not args.path.exists():
        parser.error('Photo or folder does not exist.')
    extensions = {'.jpg', '.jpeg', '.png', '.heic', '.tif', '.tiff'}
    paths = sorted(args.path.iterdir()) if args.path.is_dir() else [args.path]
    photos = [path for path in paths if path.is_file() and path.suffix.lower() in extensions]
    if not photos:
        parser.error('No supported photos found.')
    try:
        results = read_photos(photos)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError) as exc:
        parser.exit(1, f'Could not read photos: {exc}\n')
    if args.lookup:
        from assess_product import assess_product
        from fetch_product import LookupFailure, fetch_product, validate_barcode
        cache = {}
    for result in results:
        if args.lookup:
            products = []
            for barcode in result['barcodes']:
                try:
                    validate_barcode(barcode)
                    if barcode not in cache:
                        cache[barcode] = assess_product(barcode, fetch_product(barcode, production=True))
                    products.append(cache[barcode])
                except (ValueError, LookupFailure, OSError, sqlite3.Error) as exc:
                    products.append({'barcode': barcode, 'error': str(exc)})
            result['products'] = products
        print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
