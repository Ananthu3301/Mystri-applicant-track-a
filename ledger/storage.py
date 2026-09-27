import sqlite3
from pathlib import Path


def connect(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys = ON')
    db.executescript('''
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY, name TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL REFERENCES customers(customer_id),
            invoice_number TEXT NOT NULL, amount REAL NOT NULL, due_date TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS payments (
            payment_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL REFERENCES customers(customer_id),
            invoice_number TEXT NOT NULL, amount REAL NOT NULL,
            invoice_id INTEGER REFERENCES invoices(id)
        );
    ''')
    return db


def seed(db):
    if db.execute('SELECT COUNT(*) FROM customers').fetchone()[0]:
        return
    with db:
        db.executemany('INSERT INTO customers VALUES (?, ?)', [
            ('HARBOR', 'Harbor Design'), ('MAPLE', 'Maple Studio'),
            ('NORTH', 'North Workshop'),
        ])
        db.executemany('''INSERT INTO invoices
            (customer_id, invoice_number, amount, due_date) VALUES (?, ?, ?, ?)''', [
            ('HARBOR', 'INV-100', 1250.00, '2026-09-01'),
            ('MAPLE', 'INV-200', 1250.00, '2026-09-02'),
            ('NORTH', 'INV-300', 19.99, '2026-09-03'),
            ('HARBOR', 'INV-101', 300.00, '2026-09-04'),
            ('MAPLE', 'INV-201', 600.00, '2026-09-05'),
            ('NORTH', 'INV-301', 100.00, '2026-09-06'),
        ])
        for pid, customer, number, amount in [
            ('SEED-1', 'HARBOR', 'INV-101', 300.00),
            ('SEED-2', 'NORTH', 'INV-300', 10.00),
        ]:
            iid = db.execute('SELECT id FROM invoices WHERE customer_id=? AND invoice_number=?',
                             (customer, number)).fetchone()[0]
            db.execute('INSERT INTO payments VALUES (?, ?, ?, ?, ?)',
                       (pid, customer, number, amount, iid))


def invoice_by_key(db, customer_id, invoice_number):
    return db.execute('SELECT * FROM invoices WHERE customer_id=? AND invoice_number=? ORDER BY id',
                      (customer_id, invoice_number)).fetchone()


def insert_invoice(db, row):
    old = invoice_by_key(db, row['customer_id'], row['invoice_number'])
    if old:
        if old['amount'] == row['amount'] and old['due_date'] == row['due_date']:
            return 'skipped'
        raise ValueError('Invoice already exists with different details')
    db.execute('''INSERT INTO invoices (customer_id, invoice_number, amount, due_date)
                  VALUES (:customer_id, :invoice_number, :amount, :due_date)''', row)
    return 'imported'


def insert_payment(db, row, invoice_id):
    old = db.execute('SELECT * FROM payments WHERE payment_id=?', (row['payment_id'],)).fetchone()
    if old:
        if all(old[k] == row[k] for k in ('customer_id', 'invoice_number', 'amount')):
            return 'skipped'
        raise ValueError('Payment ID already exists with different details')
    db.execute('''INSERT INTO payments (payment_id, customer_id, invoice_number, amount, invoice_id)
                  VALUES (:payment_id, :customer_id, :invoice_number, :amount, :invoice_id)''',
               {**row, 'invoice_id': invoice_id})
    return 'imported'
