# ClearLedger | Intended behaviour

This document is the public specification. The current implementation may disagree with it.

## Records and identity

- The three existing customers are `HARBOR`, `MAPLE` and `NORTH`. Customer creation is outside scope.
- An invoice is identified by the pair `(customer_id, invoice_number)`. A payment is identified by `payment_id`.
- Trim surrounding whitespace from CSV values. Identifiers remain case-sensitive.
- Re-importing an invoice with the same identity, amount and due date must skip it without changing any totals. Reusing that identity with different details must reject the row and preserve the original.
- Re-importing an identical payment must also skip it. Reusing its ID with different customer, invoice reference or amount must reject the row and preserve the original.
- A new payment may be attached **only** to an invoice with both the same customer ID and invoice number. An amount alone does not establish identity.
- A valid payment with no matching invoice must be retained as unmatched. It must not change any invoice balance. Automatically rematching it after a future invoice import is outside scope.

## CSV imports

Invoice header, in this exact order:

```csv
customer_id,invoice_number,amount,due_date
```

Payment header, in this exact order:

```csv
payment_id,customer_id,invoice_number,amount
```

- Files are UTF-8, optionally with a byte-order mark, smaller than 2 MB. Use ordinary CSV with one record per line for this exercise.
- Each listed field must be present and nonempty. The customer must exist. Dates must be valid `YYYY-MM-DD` dates. Amounts must be positive, no greater than 10,000,000, and have at most two decimal places; no currency symbols or thousands separators.
- An invalid header rejects the whole import, writes nothing and returns an error.
- An invalid **data row** rejects only that row. Other valid rows must still be processed.
- Each import reports `imported`, `skipped` and `rejected` counts. Each rejected row has its CSV line number (header is line 1) and a useful reason.
- A valid header with no data rows is a successful import with zero counts.
- This exercise does not require support for malformed quoting, embedded newlines, extra columns, huge datasets or simultaneous writers.

## Money and reporting

- An invoice's paid amount is the sum of the payments attached to it. Its balance is invoice amount minus paid amount.
- Show and export money accurately to two decimal places. CSV values must agree with the same record on screen. For these two-decimal inputs, calculations must preserve cents.
- `open` means a positive balance at currency precision. `paid` means a zero or negative balance. Both filters must contain only their respective records; `all` contains both.
- Overpayments are permitted: show the negative balance and mark the invoice paid. An overpayment on one invoice must not reduce another invoice's outstanding amount.
- Overview outstanding is the sum of positive invoice balances. Overview open count is the number of open invoices. Unmatched payments appear separately.
- Tax, FX, credit notes, due-date aging, authentication and production deployment are outside scope.

## Browser feedback

- A successful import must show the actual counts. A partially rejected import must also show the rejected line numbers and reasons.
- A failed request must show a useful failure message. It must never claim success.
- Refresh the register after a processed import so the visible records agree with stored data.

## Public API to preserve

Internal Python interfaces are yours to change. Keep these HTTP routes and existing response field names so a reviewer can run the app and check it consistently. Adding fields and routes is fine.

| Request | Response |
| --- | --- |
| `GET /api/overview` | Object with `summary`, `invoices` and `unmatched_payments` |
| `GET /api/invoices?status=all` | Invoice array; `open` and `paid` also supported; invalid status returns 400 |
| `GET /api/export` | CSV of all invoices with `customer_id,invoice_number,amount,paid,balance,status` |
| `POST /api/import?kind=invoices` | Raw CSV body; JSON counts and `errors` array |
| `POST /api/import?kind=payments` | Same response shape for payment CSV |

`summary` fields: `invoice_count`, `open_count`, `outstanding`.

Invoice fields: `id`, `customer_id`, `customer_name`, `invoice_number`, `amount`, `due_date`, `paid`, `balance`, `status`. Money fields in JSON are numbers.

Unmatched payment fields: `payment_id`, `customer_id`, `invoice_number` and `amount`.

Successful and partially successful imports return HTTP 200:

```json
{"imported": 2, "skipped": 0, "rejected": 1,
 "errors": [{"line": 3, "reason": "Amount must be a positive decimal with at most two places"}]}
```

The reason wording can vary. A wholly invalid request returns HTTP 400 and `{"error": "helpful message"}`. A request with a valid header but all invalid data rows is still HTTP 200 with rejected counts.

## Existing register

`fixtures/existing-register.sqlite3` uses the starter schema and contains valid records beyond the fresh demo. Preserve all supplied customer and payment identities, invoice IDs and customer/invoice identities, names, monetary amounts, due dates and payment allocations listed in `fixtures/expected-records.json`. Unmatched payments must stay unmatched. Internal storage/schema representation may change; record meaning and identity must not.

After applying your repair to a copy of this database, valid new invoice and payment imports must work. Existing and newly imported data must survive an app restart. Test a migration if you change the schema. Replacing the owner's records with the six-invoice demo is not a repair. See `fixtures/README.md` for setup and expected totals. Correcting historical misallocations is outside scope.

## Fresh demo reference

A fresh reset has six invoices, two payments, five open invoices and total outstanding **INR 3,209.99**. Reset between experiments when you need the same starting point. Your fixes should work for other valid records too.
