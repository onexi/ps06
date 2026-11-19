"""Serve the IC Food App locally with photo-to-product assessment."""
import argparse
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import threading
from urllib.parse import urlsplit

from assess_product import assess_product
from fetch_product import LookupFailure, fetch_product, validate_barcode
from scan_barcode_photos import read_photos
from food_diary import record_reaction

ROOT = Path(__file__).resolve().parents[1]
MAX_UPLOAD = 20 * 1024 * 1024
IMAGE_TYPES = {'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp'}
SCAN_LOCK = threading.Lock()


class Handler(SimpleHTTPRequestHandler):
    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        route = urlsplit(self.path).path
        if route not in ('/api/scan', '/api/reactions'):
            self.send_json(404, {'error': 'Unknown request.'})
            return
        origin = self.headers.get('Origin')
        if origin and origin != f'http://{self.headers.get("Host")}':
            self.send_json(403, {'error': 'Open the app at its local address to upload a photo.'})
            return
        if route == '/api/reactions':
            self.save_reaction()
            return
        content_type = self.headers.get('Content-Type', '').split(';')[0].lower()
        if content_type not in IMAGE_TYPES:
            self.send_json(415, {'error': 'Choose a JPG, PNG or WebP photo.'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            length = 0
        if not 0 < length <= MAX_UPLOAD:
            self.send_json(413, {'error': 'Choose a photo smaller than 20 MB.'})
            return
        if not SCAN_LOCK.acquire(blocking=False):
            self.send_json(429, {'error': 'Another photo is being checked. Please try again shortly.'})
            return
        try:
            self.connection.settimeout(30)
            body = self.rfile.read(length)
            if len(body) != length:
                self.send_json(400, {'error': 'The photo upload was interrupted. Try again.'})
                return
            with tempfile.TemporaryDirectory(prefix='ic-photo-') as folder:
                path = Path(folder) / ('upload' + IMAGE_TYPES[content_type])
                path.write_bytes(body)
                scans = read_photos([path])
            if not scans or scans[0].get('error'):
                self.send_json(422, {'error': 'This image could not be read. Try another photo.'})
                return
            barcodes = []
            for code in scans[0]['barcodes']:
                try:
                    validate_barcode(code)
                except ValueError:
                    continue
                if code not in barcodes:
                    barcodes.append(code)
            if not barcodes:
                self.send_json(422, {'error': 'No product barcode was readable. Take a closer photo with the full barcode in focus.'})
                return
            if len(barcodes) > 1:
                self.send_json(422, {'error': 'More than one product barcode was found. Crop the photo to one barcode.'})
                return
            barcode = barcodes[0]
            product = fetch_product(barcode, production=True)
            self.send_json(200, assess_product(barcode, product))
        except LookupFailure as exc:
            self.send_json(502, {'error': str(exc)})
        except subprocess.TimeoutExpired:
            self.send_json(504, {'error': 'Reading the photo took too long. Try a smaller, closer photo.'})
        except (OSError, ValueError, sqlite3.Error, subprocess.CalledProcessError):
            self.send_json(500, {'error': 'The local checker could not finish. Check that its database and macOS barcode reader are available.'})
        finally:
            SCAN_LOCK.release()

    def save_reaction(self):
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            self.send_json(415, {'error': 'Send the reaction as JSON.'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 65536:
                raise ValueError('The diary entry is too large or empty.')
            self.connection.settimeout(30)
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError('Enter a reaction using the form.')
            for key in ('food', 'outcome', 'portion', 'notes', 'ate_at', 'barcode'):
                if not isinstance(payload.get(key, ''), str):
                    raise ValueError('Diary fields must contain text.')
            ingredients = payload.get('ingredients', [])
            if not isinstance(ingredients, list) or not all(isinstance(item, str) for item in ingredients):
                raise ValueError('Ingredient names must be a list of text.')
            barcode = payload.get('barcode', '')
            if barcode:
                validate_barcode(barcode)
            ate_at = datetime.fromisoformat(payload['ate_at']) if payload.get('ate_at') else None
            entry_id = record_reaction(
                payload.get('food', ''), payload.get('outcome', ''),
                ingredients=ingredients, portion=payload.get('portion', ''),
                notes=payload.get('notes', ''), ate_at=ate_at, barcode=barcode,
            )
        except (ValueError, UnicodeError) as exc:
            self.send_json(400, {'error': str(exc)})
            return
        except (OSError, sqlite3.Error):
            self.send_json(500, {'error': 'Your reaction could not be saved. Please try again.'})
            return
        self.send_json(201, {'entry_id': entry_id, 'message': 'Reaction saved to your food diary.'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(
        ('127.0.0.1', args.port), partial(Handler, directory=str(ROOT / 'ui-preview'))
    )
    print(f'IC Food App is ready at http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
