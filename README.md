# Track A | Repair the register

**A four-hour engineering challenge.** You have inherited ClearLedger, a tiny local application used by a fictional service business to track invoices and payments. The owner needs a register they can trust before using it for a busy week.

The application runs, and the starter tests pass. There are **six deliberately seeded defects** across the import, matching, reporting and browser workflows. The starter tests are only smoke checks. You do not need to find or fix all six to make a strong submission.

Submit within **seven calendar days of the invitation**, with **four hours of total work**. Follow the independent-work and submission rules in `../START_HERE.md`.

## Your mission

1. Investigate the app and record the important problems you can reproduce. Explain their impact and prioritize them.
2. Fix the most important problems you can within the time limit. Add meaningful regression checks that would have caught those problems. Include one failing-before/passing-after reproduction and one additional input case you designed yourself. Record the commands and actual results; these are part of your testing, not a separate report.
3. Add **one small improvement of your choice beyond restoring behaviours already required in BUSINESS_RULES.md**. Explain the owner problem it solves, show it working and include a check for it. If reliability work uses the available time, describe the proposed improvement and the first test you would run; an implemented, verified improvement receives more credit.
4. Leave a concise `HANDOVER.md` using the shared template. Include reproducible evidence, remaining issues and exact run/test commands.

A focused patch is welcome. Preserve the public HTTP routes and response fields in `BUSINESS_RULES.md`; you may change internal code, add fields or routes, or improve the UI. A rewrite is unnecessary. If reliability work uses the available time, describe your proposed improvement instead of rushing it.

## What the owner has noticed

> "The open-invoice view doesn't seem to agree with the overview."
>
> "When I retry an import, the numbers sometimes move again."
>
> "The downloaded report and the screen don't always agree."
>
> "An import said it was complete, but I couldn't find the records I expected."

These are starting points, not a complete list of defects. Use `BUSINESS_RULES.md` as the intended behaviour. Create your own cases where useful; do not merely special-case the supplied sample files.

## Run it

Requires **Python 3.10+** and a modern browser. The starter has no third-party dependencies.

From the extracted `track-a` directory:

```text
python app.py
```

Open `http://127.0.0.1:8787`. Keep the terminal open. Press Ctrl+C to stop the server. If `python` is unavailable, try `py` on Windows or `python3` on macOS/Linux in every command below.

If the port is occupied, run `python app.py --port 8790` and open `http://127.0.0.1:8790` instead.

Run the existing tests:

```text
python -m unittest discover -s tests -v
```

Reset the synthetic data **with the server stopped**:

```text
python app.py reset-demo
python app.py
```

The working database is created locally at `.local/clearledger.sqlite3`. You may reset it for separate experiments. No accounts, credentials, external services or real financial records are needed.

## Preserve the owner's register

The owner already has records beyond the fresh demo. With the server stopped, load a working copy of the supplied register:

```text
python restore_fixture.py --replace
python app.py
```

Your repair must preserve these existing records and allow valid new invoice and payment imports afterward, including after a restart. You may change the schema, but include and test any necessary migration. Resetting the working data does not satisfy this requirement. Keep the original files in `fixtures/` intact.

`fixtures/README.md` specifies the records and expected starting totals. Historical payment corrections are outside scope; the supplied allocations are correct. Include your preservation check in your existing verification evidence, within the same four-hour limit.

## Explore the starter

| Location | Purpose |
| --- | --- |
| `app.py` | Startup and reset command |
| `ledger/` | Validation, storage, importing, matching, reporting and HTTP routes |
| `web/` | Browser interface in plain HTML, CSS and JavaScript |
| `samples/` | Small CSVs for trying imports, including mixed validity and incorrect headers |
| `fixtures/` | Existing register and documented records to preserve |
| `restore_fixture.py` | Copies the supplied register into the working database while the server is stopped |
| `tests/` | A few passing smoke tests, not a complete specification |
| `BUSINESS_RULES.md` | Intended behaviour and public API |

All money is synthetic INR. The customers are fictional. Accounting expertise is not required; the business rules define the task.

## Suggested time budget

| Activity | Minutes |
| --- | ---: |
| Read, run and investigate | 35 |
| Prioritize, fix and add regression checks | 130 |
| One useful improvement | 40 |
| Clean-run verification and handover | 35 |
| **Total, including setup and choosing a track** | **240** |

Reallocate this budget as needed. Stop after four hours; explain what you would do next.

## How this track is scored

| Criterion | Weight | Evidence we value |
| --- | ---: | --- |
| Correctness and reliability | 30% | Fixes satisfy the rules without damaging other workflows |
| Verification | 25% | Reproductions, regression tests and checks beyond the happy path |
| Investigation and prioritization | 20% | A clear account of what broke, why it matters and what you tackled first |
| Useful improvement | 15% | A justified, checked change beyond the required repairs |
| Handover and tool judgment | 10% | Reproducible work, accurate limits and ownership of AI/tool output |

We do not rank by the number of bugs claimed, visual polish, code volume or model used. Reading, reasoning and a carefully checked small change can distinguish a strong submission.

## Submit

Send the chosen track's code, tests and `HANDOVER.md`, following `../START_HERE.md`. Keep the supplied `fixtures/` and include any migration code. Exclude `.local/`, caches and virtual environments. Include any additional dependency instructions. No deployment is required.
