"""Regression tests for the six identified defects — see HANDOVER.md.

Bug 6 (browser always reporting "Import complete") lives in web/app.js and is
covered by manual verification steps in HANDOVER.md, since this project has
no browser-automation harness.
"""
import tempfile
import unittest
from pathlib import Path
from ledger import storage, reporting, importing


class FixedBugsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = storage.connect(Path(self.tmp.name) / 'demo.sqlite3')
        storage.seed(self.db)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    # --- Bug 1: status=open was returning paid invoices ---
    def test_open_filter_excludes_paid_invoices(self):
        open_invoices = reporting.invoices(self.db, status='open')
        self.assertTrue(all(r['status'] == 'open' for r in open_invoices))
        self.assertEqual(len(open_invoices), 5)

    def test_overpaid_invoice_counts_as_paid_not_open(self):
        # Self-designed case: an overpayment should push balance negative,
        # which must still count as 'paid' and be excluded from 'open'.
        importing.import_csv(
            self.db,
            'payment_id,customer_id,invoice_number,amount\nEXTRA-1,NORTH,INV-301,150.00\n',
            'payments')
        open_invoices = reporting.invoices(self.db, status='open')
        self.assertFalse(any(r['invoice_number'] == 'INV-301' for r in open_invoices))

    # --- Bug 2: CSV export truncated cents instead of rounding ---
    def test_export_amount_is_not_truncated(self):
        csv_text = reporting.export_csv(self.db)
        line = next(l for l in csv_text.splitlines() if 'INV-300' in l)
        self.assertIn('19.99', line)
        self.assertNotIn('19.98', line)

    # --- Bug 3: payments matched by amount instead of (customer, invoice) ---
    def test_payment_attaches_to_correct_customer_not_same_amount(self):
        # HARBOR/INV-100 and MAPLE/INV-200 both have amount 1250.00.
        result = importing.import_csv(
            self.db,
            'payment_id,customer_id,invoice_number,amount\nPAY-X,MAPLE,INV-200,1250.00\n',
            'payments')
        self.assertEqual(result['imported'], 1)
        maple_invoice = next(r for r in reporting.invoices(self.db) if r['invoice_number'] == 'INV-200')
        harbor_invoice = next(r for r in reporting.invoices(self.db) if r['invoice_number'] == 'INV-100')
        self.assertEqual(maple_invoice['paid'], 1250.00)
        self.assertEqual(harbor_invoice['paid'], 0)

    def test_payment_still_matches_by_identity_when_amount_is_unique(self):
        # Self-designed case: confirms normal (non-colliding) matching
        # still works after removing the amount-based shortcut.
        result = importing.import_csv(
            self.db,
            'payment_id,customer_id,invoice_number,amount\nPAY-Y,NORTH,INV-301,37.50\n',
            'payments')
        self.assertEqual(result['imported'], 1)
        invoice = next(r for r in reporting.invoices(self.db) if r['invoice_number'] == 'INV-301')
        self.assertEqual(invoice['paid'], 37.50)

    # --- Bug 4: re-importing an invoice duplicated it instead of skipping ---
    def test_reimporting_identical_invoice_is_skipped_not_duplicated(self):
        csv_text = 'customer_id,invoice_number,amount,due_date\nHARBOR,DUP-1,50.00,2026-10-01\n'
        first = importing.import_csv(self.db, csv_text, 'invoices')
        second = importing.import_csv(self.db, csv_text, 'invoices')
        self.assertEqual(first['imported'], 1)
        self.assertEqual(second, {'imported': 0, 'skipped': 1, 'rejected': 0, 'errors': []})
        matches = [r for r in reporting.invoices(self.db) if r['invoice_number'] == 'DUP-1']
        self.assertEqual(len(matches), 1)

    def test_reused_invoice_identity_with_different_amount_is_rejected(self):
        # Self-designed case: same identity, different amount -> reject,
        # original must be preserved untouched.
        importing.import_csv(
            self.db, 'customer_id,invoice_number,amount,due_date\nHARBOR,DUP-2,50.00,2026-10-01\n', 'invoices')
        result = importing.import_csv(
            self.db, 'customer_id,invoice_number,amount,due_date\nHARBOR,DUP-2,99.00,2026-10-01\n', 'invoices')
        self.assertEqual(result['rejected'], 1)
        invoice = next(r for r in reporting.invoices(self.db) if r['invoice_number'] == 'DUP-2')
        self.assertEqual(invoice['amount'], 50.00)

    # --- Bug 5: one bad row cancelled the entire import ---
    def test_valid_rows_still_import_when_one_row_is_invalid(self):
        csv_text = (
            'customer_id,invoice_number,amount,due_date\n'
            'HARBOR,GOOD-1,10.00,2026-10-01\n'
            'HARBOR,BAD-1,not-a-number,2026-10-01\n'
            'MAPLE,GOOD-2,20.00,2026-10-02\n'
        )
        result = importing.import_csv(self.db, csv_text, 'invoices')
        self.assertEqual(result['imported'], 2)
        self.assertEqual(result['rejected'], 1)
        self.assertEqual(result['errors'][0]['line'], 3)

    def test_bad_row_first_does_not_block_later_valid_rows(self):
        # Self-designed case: bad row at the START of the file, to prove
        # the fix isn't accidentally order-dependent.
        csv_text = (
            'customer_id,invoice_number,amount,due_date\n'
            'HARBOR,BAD-2,,2026-10-01\n'
            'MAPLE,GOOD-3,30.00,2026-10-03\n'
        )
        result = importing.import_csv(self.db, csv_text, 'invoices')
        self.assertEqual(result['imported'], 1)
        self.assertEqual(result['rejected'], 1)


if __name__ == '__main__':
    unittest.main()