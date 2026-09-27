"""Start ClearLedger using Python 3.10 or later; no packages to install."""
import argparse
from pathlib import Path
from ledger import storage
from ledger.http_app import make_server

ROOT = Path(__file__).resolve().parent
DATABASE = ROOT / '.local' / 'clearledger.sqlite3'


def main():
    parser = argparse.ArgumentParser(description='ClearLedger local assessment application')
    parser.add_argument('command', nargs='?', choices=['serve', 'reset-demo'], default='serve')
    parser.add_argument('--port', type=int, default=8787)
    args = parser.parse_args()
    if args.command == 'reset-demo':
        # Only the disposable local database is reset. Sample/source files are retained.
        DATABASE.unlink(missing_ok=True)
    db = storage.connect(DATABASE)
    storage.seed(db)
    db.close()
    if args.command == 'reset-demo':
        print('Demo reset. Start with: python app.py')
        return
    server = make_server(DATABASE, ROOT / 'web', args.port)
    print(f'ClearLedger: http://127.0.0.1:{server.server_port}  (Ctrl+C to stop)', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
