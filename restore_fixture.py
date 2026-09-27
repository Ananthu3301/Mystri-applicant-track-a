"""Copy the supplied synthetic register into .local with the app stopped."""
import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replace', action='store_true',
                        help='Replace the working database; stop the server first')
    args = parser.parse_args()
    source = ROOT / 'fixtures' / 'existing-register.sqlite3'
    target = ROOT / '.local' / 'clearledger.sqlite3'
    if not target.resolve().is_relative_to(ROOT):
        raise SystemExit('Working database path must stay inside this track folder.')
    if target.exists() and not args.replace:
        raise SystemExit('Working database exists. Stop the app, then use --replace to restore it.')
    if any(Path(str(target) + suffix).exists() for suffix in ('-wal', '-shm', '-journal')):
        raise SystemExit('SQLite sidecar files exist. Stop the app and close database tools before restoring.')
    target.parent.mkdir(exist_ok=True)
    shutil.copy2(source, target)
    print('Existing register restored: 9 invoices, 5 payments. Start with: python app.py')


if __name__ == '__main__':
    main()
