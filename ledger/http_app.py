import json
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit
from . import importing, reporting, storage


def make_server(db_path, web_dir, port):
    class Handler(BaseHTTPRequestHandler):
        def send(self, status, body, content_type='application/json; charset=utf-8'):
            if not isinstance(body, (bytes, str)):
                body = json.dumps(body)
            if isinstance(body, str):
                body = body.encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            url = urlsplit(self.path)
            static = {'/': ('index.html', 'text/html; charset=utf-8'),
                      '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                      '/style.css': ('style.css', 'text/css; charset=utf-8')}
            if url.path in static:
                name, mime = static[url.path]
                return self.send(200, (web_dir / name).read_bytes(), mime)
            db = storage.connect(db_path)
            try:
                if url.path == '/api/overview':
                    return self.send(200, reporting.overview(db))
                if url.path == '/api/invoices':
                    status = parse_qs(url.query).get('status', ['all'])[0]
                    return self.send(200, reporting.invoices(db, status))
                if url.path == '/api/export':
                    return self.send(200, reporting.export_csv(db), 'text/csv; charset=utf-8')
                return self.send(404, {'error': 'Not found'})
            except ValueError as exc:
                self.send(400, {'error': str(exc)})
            finally:
                db.close()

        def do_POST(self):
            url = urlsplit(self.path)
            if url.path != '/api/import':
                return self.send(404, {'error': 'Not found'})
            origin = self.headers.get('Origin')
            if origin and origin not in (f'http://127.0.0.1:{self.server.server_port}',
                                         f'http://localhost:{self.server.server_port}'):
                return self.send(403, {'error': 'Use the local application page'})
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if size < 0 or size > 2 * 1024 * 1024:
                    raise ValueError('Use a CSV smaller than 2 MB')
                text = self.rfile.read(size).decode('utf-8-sig')
            except (ValueError, UnicodeDecodeError):
                return self.send(400, {'error': 'Use a UTF-8 CSV smaller than 2 MB'})
            db = storage.connect(db_path)
            try:
                kind = parse_qs(url.query).get('kind', [''])[0]
                result = importing.import_csv(db, text, kind)
                self.send(200, result)
            except (ValueError, sqlite3.IntegrityError) as exc:
                self.send(400, {'error': str(exc)})
            finally:
                db.close()

    return HTTPServer(('127.0.0.1', port), Handler)
