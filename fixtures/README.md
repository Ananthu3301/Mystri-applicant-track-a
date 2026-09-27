# The owner's existing register

`existing-register.sqlite3` is a synthetic SQLite database in the starter schema. It includes the six demo invoices plus three additional invoices, and five payments in total. It contains no deliberately corrupted historical allocations. The existing six application defects still need investigation.

With the app stopped, run `python restore_fixture.py --replace` from `track-a`, then start the app normally. This replaces only the working copy at `.local/clearledger.sqlite3`. The supplied fixture stays intact. Restore it again before checking how your final repair handles an existing database.

## Expected starting state

| Measure | Value |
| --- | ---: |
| Customers | 3 |
| Invoices | 9 |
| Payments | 5 |
| Open invoices | 7 |
| Outstanding INR | 3,698.19 |
| Unmatched payments | 1 |

The additional invoices are:

| Customer | Invoice | Amount INR | Due date | Paid INR | Balance INR |
| --- | --- | ---: | --- | ---: | ---: |
| HARBOR | KEEP-700 | 456.78 | 2026-09-09 | 56.78 | 400.00 |
| MAPLE | KEEP-700 | 88.20 | 2026-09-10 | 0.00 | 88.20 |
| NORTH | KEEP-702 | 150.00 | 2026-09-11 | 150.00 | 0.00 |

`KEEP-P1` pays INR 56.78 toward HARBOR / KEEP-700. `KEEP-P2` pays INR 150.00 toward NORTH / KEEP-702. `KEEP-U1` is an unmatched INR 33.33 payment for MAPLE / WAIT-900. Its reference has no invoice and it must stay unmatched.

`expected-records.json` lists every original customer, invoice and payment, including invoice IDs and payment allocations. Money in that reference is a decimal string for exact comparison. Preserve those identities and values; you may use a different schema/storage representation in your repair. Application JSON money fields must still be numbers, as specified in `BUSINESS_RULES.md`.

## What to check

Start your repaired app against a restored copy. Verify the existing records, import a valid new invoice and a payment, then restart and verify both original and new records. Include any migration code and its check. Do not satisfy this by replacing the register with a fresh demo or by special-casing these record IDs. Explain incomplete work in your handover.

Keep the original fixture and reference JSON unchanged in your submission. Do not submit the generated `.local/` working copy.
