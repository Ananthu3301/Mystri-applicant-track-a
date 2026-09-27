from .storage import invoice_by_key


def find_invoice(db, payment):
    exact = invoice_by_key(db, payment['customer_id'], payment['invoice_number'])
    return exact['id'] if exact else None