"""Validate barcodes and retrieve product records from Open Food Facts."""
import base64
import json
import os
import re
import socket
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class LookupFailure(Exception):
    pass

def validate_barcode(value):
    if not re.fullmatch(r'(?:[0-9]{8}|[0-9]{12,14})', value):
        raise ValueError('Enter an 8, 12, 13, or 14 digit barcode, preserving leading zeros.')
    digits = [int(c) for c in value]
    total = sum(n * (3 if i % 2 == 0 else 1) for i, n in enumerate(reversed(digits[:-1])))
    if (10 - total % 10) % 10 != digits[-1]:
        raise ValueError('Barcode check digit is invalid. Check the number on the package.')
    return value

def fetch_product(barcode, production=False, opener=urlopen):
    validate_barcode(barcode)
    host = 'world.openfoodfacts.org' if production else 'world.openfoodfacts.net'
    request = Request(f'https://{host}/api/v3.6/product/{barcode}.json', headers={
        'User-Agent': os.environ.get('IC_APP_USER_AGENT', 'ICFoodApp/0.1 (local development)'),
        'Accept': 'application/json'})
    if not production:
        request.add_header('Authorization', 'Basic ' + base64.b64encode(b'off:off').decode())
    try:
        with opener(request, timeout=15) as response:
            payload = json.load(response)
    except HTTPError as exc:
        if exc.code == 404:
            return None
        if exc.code == 429:
            raise LookupFailure('Product service rate limit reached. Try again later.') from exc
        raise LookupFailure(f'Product service returned HTTP {exc.code}. Try again later.') from exc
    except (URLError, TimeoutError, socket.timeout) as exc:
        raise LookupFailure('Product service could not be reached. Use --label to check a label manually.') from exc
    except (ValueError, UnicodeError) as exc:
        raise LookupFailure('Product service returned unreadable data.') from exc
    if not isinstance(payload, dict):
        raise LookupFailure('Unexpected product response.')
    if payload.get('status') == 0:
        return None
    product = payload.get('product')
    if not isinstance(product, dict):
        raise LookupFailure('Product response is missing product information.')
    return product
