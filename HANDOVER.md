# HANDOVER — ClearLedger repair (Track A)

## Overview

ClearLedger runs, and the starter smoke tests pass, but six seeded defects
affect import correctness, payment matching, reporting, and browser
feedback. All six were reproduced, explained, and fixed within the time
budget. Regression tests were added for the five that are testable at the
Python level; the sixth (browser feedback) was verified manually since this
project has no browser-automation harness.

## 1. Investigation & prioritization

| # | Bug | File | Impact | Priority |
|---|---|---|---|---|
| 3 | Payments matched by amount before identity — a payment can silently attach to the wrong customer's invoice if two invoices share an amount | `matching.py` | Silent money misallocation with no error shown | Highest — corrupts data silently |
| 5 | One invalid CSV row aborts the entire import before any row is saved | `importing.py` | Valid rows are lost entirely; owner sees nothing saved | Highest — silent data loss |
| 4 | Re-importing an identical invoice creates a duplicate instead of being skipped | `storage.py` | Inflates invoice counts/totals on retry | High |
| 1 | `status=open` filter actually returns paid invoices (and vice versa) | `reporting.py` | Open-invoice view visibly disagrees with the overview | Medium — visible, easy to spot |
| 2 | CSV export can truncate a cent instead of rounding, due to floating-point drift | `reporting.py` | Downloaded report can disagree with the screen by ₹0.01 | Medium — small, cosmetic |
| 6 | Browser always shows "Import complete" regardless of the actual server response | `app.js` | Owner is told an import succeeded even when it failed or was rejected | Medium — trust/UX issue, no data damage |

Owner complaints mapped directly to bugs:
- *"open-invoice view doesn't agree with the overview"* → Bug 1
- *"the downloaded report and the screen don't always agree"* → Bug 2
- *"when I retry an import, the numbers sometimes move again"* → Bug 4
- *"an import said it was complete, but I couldn't find the records I expected"* → Bugs 5 and 6

## 2. Fixes applied

### Bug 1 — `reporting.py`, `invoices()`
```python
# before
requested = {'open': 'paid', 'paid': 'paid'}[status]
result = [r for r in result if r['status'] == requested]
# after
result = [r for r in result if r['status'] == status]
```
The lookup table mapped both `'open'` and `'paid'` to `'paid'`. Since `status`
already holds the exact value to filter on, the table was unnecessary and wrong.

### Bug 2 — `reporting.py`, `export_csv()`
```python
# before
item[key] = f"{int(item[key] * 100) / 100:.2f}"
# after
item[key] = f"{item[key]:.2f}"
```
`int(x * 100)` truncates rather than rounds, so floating-point drift (e.g.
`19.99` stored internally as `19.989999999999998`) could be chopped down to
`19.98`. Formatting the original value with `:.2f` rounds correctly.

### Bug 3 — `matching.py`, `find_invoice()`
```python
# before
candidates = db.execute('SELECT * FROM invoices ORDER BY id').fetchall()
amount_match = next((r for r in candidates if r['amount'] == payment['amount']), None)
if amount_match is not None:
    return amount_match['id']
exact = invoice_by_key(db, payment['customer_id'], payment['invoice_number'])
return exact['id'] if exact else None
# after
exact = invoice_by_key(db, payment['customer_id'], payment['invoice_number'])
return exact['id'] if exact else None
```
Removed the amount-first shortcut entirely. `BUSINESS_RULES.md` is explicit
that amount alone never establishes identity; only `(customer_id,
invoice_number)` does.

### Bug 4 — `storage.py`, `insert_invoice()`
```python
# after
def insert_invoice(db, row):
    old = invoice_by_key(db, row['customer_id'], row['invoice_number'])
    if old:
        if old['amount'] == row['amount'] and old['due_date'] == row['due_date']:
            return 'skipped'
        raise ValueError('Invoice already exists with different details')
    db.execute(...)
    return 'imported'
```
Added the identity check that was already present in `insert_payment()` but
missing here — mirrors the existing pattern rather than inventing a new one.

### Bug 5 — `importing.py`, `import_csv()`
```python
# before
rows = [normalize(row, kind, customers) for row in reader]
# ... later, in a separate loop, wrapped in try/except

# after
for line, raw_row in enumerate(reader, 2):
    try:
        row = normalize(raw_row, kind, customers)
        ...
    except ValueError as exc:
        ...
```
`normalize()` now runs *inside* the per-row `try/except`, so one bad row is
caught and rejected without stopping the rows before or after it.

### Bug 6 — `web/app.js`, `submitImport()`
```javascript
// after
const response = await fetch(...);
const data = await response.json();
if (!response.ok) {
    feedback.textContent = `Import failed: ${data.error}`;
    return;
}
feedback.textContent = `Imported ${data.imported}, skipped ${data.skipped}, rejected ${data.rejected}.` + ...
```
`fetch()` only rejects on network failure, not on HTTP error statuses, so the
old code never inspected the response and always claimed success. The fix
reads the JSON body and checks `response.ok` before reporting anything.

## 3. Verification

### Regression test suite
Added `tests/test_fixes.py`: one reproduction test plus one self-designed
edge case per testable bug (Bugs 1–5), run alongside the untouched
`tests/test_smoke.py`. Actual output on this machine:

```
PS C:\Users\hp\Desktop\Mystri-Applicant-Assessments\track-a> python -m unittest discover -s tests -v
test_bad_row_first_does_not_block_later_valid_rows ... ok
test_export_amount_is_not_truncated ... ok
test_open_filter_excludes_paid_invoices ... ok
test_overpaid_invoice_counts_as_paid_not_open ... ok
test_payment_attaches_to_correct_customer_not_same_amount ... ok
test_payment_still_matches_by_identity_when_amount_is_unique ... ok
test_reimporting_identical_invoice_is_skipped_not_duplicated ... ok
test_reused_invoice_identity_with_different_amount_is_rejected ... ok
test_valid_rows_still_import_when_one_row_is_invalid ... ok
test_export_has_header ... ok
test_one_valid_invoice ... ok
test_payment_reference_when_amount_is_unique ... ok
test_seed_is_repeatable ... ok
test_seed_summary ... ok

Ran 14 tests in 1.299s

OK
```

### Failing-before / passing-after reproduction

Reverted the Bug 1 fix in `reporting.py` back to the buggy dict-lookup
version, then reran the suite:

```
test_open_filter_excludes_paid_invoices ... FAIL
test_overpaid_invoice_counts_as_paid_not_open ... FAIL
...
======================================================================
FAIL: test_open_filter_excludes_paid_invoices
AssertionError: False is not true
======================================================================
FAIL: test_overpaid_invoice_counts_as_paid_not_open
AssertionError: True is not false
----------------------------------------------------------------------
Ran 14 tests in 1.244s

FAILED (failures=2)
```

Restored the fix (`result = [r for r in result if r['status'] == status]`)
and reran the same command:

```
test_open_filter_excludes_paid_invoices ... ok
test_overpaid_invoice_counts_as_paid_not_open ... ok
...
----------------------------------------------------------------------
Ran 14 tests in 1.486s

OK
```

Reverting the single Bug 1 fix broke two tests at once — both the direct
filter test and the overpayment edge-case test — since both depend on the
same broken filter line, then both passed again once the fix was restored.

### Bug 6 — manual browser verification

Uploaded `wrong-header.csv` under "Import invoices." Instead of the old
false "Import complete," the browser now correctly shows the real server
error:
```
Import failed: Expected CSV header: customer_id,invoice_number,amount,due_date
```

Uploaded `invoices-mixed.csv` (2 valid rows, 1 invalid). The browser now
shows the true counts and the specific rejected line/reason, instead of a
blanket success message:
```
Imported 2, skipped 0, rejected 1.
Line 3: amount must be a positive decimal with at most two decimal places
```

This second case also re-confirms Bug 5 is fixed on real data: the one bad
row was rejected on its own, while the 2 valid rows in the same file were
still imported rather than the whole batch being lost.

### Existing-register preservation check

Ran:
```
python restore_fixture.py --replace
python app.py
```

**Before any new import**, the dashboard/export matched
`fixtures/expected-records.json` exactly: 9 invoices, 7 open, ₹3,698.19
outstanding, and the one documented unmatched payment.

```
customer_id,invoice_number,amount,paid,balance,status
HARBOR,INV-100,1250.00,0.00,1250.00,open
MAPLE,INV-200,1250.00,0.00,1250.00,open
NORTH,INV-300,19.99,10.00,9.99,open
HARBOR,INV-101,300.00,300.00,0.00,paid
MAPLE,INV-201,600.00,0.00,600.00,open
NORTH,INV-301,100.00,0.00,100.00,open
HARBOR,KEEP-700,456.78,56.78,400.00,open
MAPLE,KEEP-700,88.20,0.00,88.20,open
NORTH,KEEP-702,150.00,150.00,0.00,paid
```

**Imported `invoices-new.csv` (HARBOR/INV-102, MAPLE/INV-202) plus a new
payments CSV.** Result: 11 invoices total, no duplicates or corruption of
the original 9. This incidentally re-confirmed the Bug 3 fix on real,
non-seeded data: `HARBOR/INV-100` and `MAPLE/INV-200` share the exact same
amount (₹1,250.00), and the new payment correctly attached only to
`MAPLE/INV-200` (paid ₹0 → ₹1,250.00) while `HARBOR/INV-100` was left
untouched.

```
customer_id,invoice_number,amount,paid,balance,status
HARBOR,INV-100,1250.00,0.00,1250.00,open
MAPLE,INV-200,1250.00,1250.00,0.00,paid
NORTH,INV-300,19.99,19.99,-0.00,paid
HARBOR,INV-101,300.00,300.00,0.00,paid
MAPLE,INV-201,600.00,0.00,600.00,open
NORTH,INV-301,100.00,0.00,100.00,open
HARBOR,KEEP-700,456.78,56.78,400.00,open
MAPLE,KEEP-700,88.20,0.00,88.20,open
NORTH,KEEP-702,150.00,150.00,0.00,paid
HARBOR,INV-102,80.00,0.00,80.00,open
MAPLE,INV-202,200.00,0.00,200.00,open
```

Unmatched payments after import — the original documented one, plus a new
payment referencing a non-existent invoice number that correctly stayed
unmatched rather than misattaching:
```
KEEP-U1 · MAPLE / WAIT-900 · ₹33.33
PAY-404 · HARBOR / INV-NOT-FOUND · ₹50.00
```

**Restarted the app** (`Ctrl+C`, then `python app.py` again) and
re-imported the same `invoices-new.csv`. Result: **"Imported 0, skipped 2,
rejected 0."**
Getting `skipped` rather than `imported` confirms the two new invoices were
still in the database after the restart — a wiped database would have
re-imported them as new rather than recognizing them as duplicates.

## 4. Improvement beyond the required repairs

**Proposed improvement: flag overdue open invoices.** The owner said she
needs a register she can trust "before using it for a busy week" — right
now, an open invoice whose due date has already passed looks identical to
one that isn't due for another month, so nothing helps her prioritize who
to chase for payment first. I'd add an `overdue` boolean to each invoice
returned by `reporting.invoices()` (true when `status == 'open'` and
`due_date` is before today), surface it as a highlighted row/badge in the
dashboard, and add an `overdue_count` to the `/api/overview` summary.

Given the time already spent on the required repairs, I've described this
rather than implemented it, per the option the assessment pack allows when
reliability work uses the available time.

**First test I'd run:** seed an invoice with a `due_date` in the past and
`status='open'`, call `reporting.invoices()`, and assert `overdue` is
`True` for that row and `False` for an open invoice due in the future —
then confirm `overview()['summary']['overdue_count']` matches the expected
count.

## 5. Remaining issues / what I'd do next

- Bug 6 was verified manually in the browser rather than with an automated
  test, since this starter has no browser-automation harness. A follow-up
  would add a lightweight JS/DOM test (or a headless-browser check) so this
  regression is caught automatically too, not just by re-checking by hand.
- The existing-register preservation check (Section 3) was performed
  manually against the restored fixture rather than as a scripted,
  repeatable test. I'd want to script this — restore, import, restart,
  assert against `expected-records.json` — so it runs the same way every
  time rather than relying on manually reading the dashboard.
- Very large CSVs, malformed quoting, and embedded newlines were not
  tested, per `BUSINESS_RULES.md` explicitly placing these out of scope
  for this exercise.
- The overdue-invoice improvement above (Section 4) was designed but not
  implemented within the time budget; building and testing it would be my
  next step with more time.

## Run & test commands

```
python app.py
python -m unittest discover -s tests -v
python restore_fixture.py --replace
python app.py
```

## Tool-use summary

Used Claude (Anthropic's chat assistant, this session running Claude Sonnet
5) throughout: to read and explain the unfamiliar codebase line by line, to
identify and prioritize the six defects against `BUSINESS_RULES.md`, to
draft the fixes and this handover, and to generate the regression test
suite.

Verified rather than trusted its output at each step: ran the disputed
floating-point rounding claim as actual Python code (`19.99 * 100 ==
1998.9999999999998`, `int()` truncating to `1998`) before accepting the
export-rounding explanation, rather than taking the explanation at face
value. Also caught and corrected a false lead myself: browser console
errors that looked like an app bug (`net::ERR_ABORTED 404`, MIME-type
warnings) turned out to be caused by opening the page via VS Code's Live
Server (port 5500) instead of the app's own server (port 8787) — a setup
mistake, not a code defect. All fixes were run against the real project
files on my own machine, not just accepted from generated snippets; the
14/14 passing test output above is from my own terminal.
