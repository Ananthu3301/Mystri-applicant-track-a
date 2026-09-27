import csv
import io
from .validation import HEADERS, normalize
from .storage import insert_invoice, insert_payment
from .matching import find_invoice


def import_csv(db, text, kind):
    if kind not in HEADERS:
        raise ValueError('Unknown import kind')
    reader = csv.DictReader(io.StringIO(text.lstrip('\ufeff')))
    if reader.fieldnames != HEADERS[kind]:
        raise ValueError('Expected CSV header: ' + ','.join(HEADERS[kind]))
    customers = {r[0] for r in db.execute('SELECT customer_id FROM customers')}
    result = {'imported': 0, 'skipped': 0, 'rejected': 0, 'errors': []}
    with db:
        for line, raw_row in enumerate(reader, 2):
            try:
                row = normalize(raw_row, kind, customers)
                if kind == 'invoices':
                    outcome = insert_invoice(db, row)
                else:
                    outcome = insert_payment(db, row, find_invoice(db, row))
                result[outcome] += 1
            except ValueError as exc:
                result['rejected'] += 1
                result['errors'].append({'line': line, 'reason': str(exc)})
    return result
