import re
from datetime import date


HEADERS = {
    'invoices': ['customer_id', 'invoice_number', 'amount', 'due_date'],
    'payments': ['payment_id', 'customer_id', 'invoice_number', 'amount'],
}


def normalize(row, kind, customer_ids):
    result = {}
    for key in HEADERS[kind]:
        value = row.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f'{key} is required')
        result[key] = value.strip()
    if result['customer_id'] not in customer_ids:
        raise ValueError('Unknown customer_id')
    if not re.fullmatch(r'\d+(?:\.\d{1,2})?', result['amount']):
        raise ValueError('amount must be a positive decimal with at most two decimal places')
    result['amount'] = float(result['amount'])
    if not 0 < result['amount'] <= 10000000:
        raise ValueError('amount must be greater than zero and at most 10000000')
    if kind == 'invoices':
        try:
            parsed = date.fromisoformat(result['due_date'])
            if parsed.isoformat() != result['due_date']:
                raise ValueError()
        except ValueError:
            raise ValueError('due_date must be YYYY-MM-DD') from None
    return result
