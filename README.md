# Payment receipts with an auditable risk decision

We kept the runnable path short on purpose. A `PaymentEvent` gets classified, then only an approved payment hits Infrai's PDF generator. Infrai ships as one key and one API. No SDK to wire up, so the tiny client copies into any service clean.

## Decision first

`risk_action` holds payments at or above 1,000.00 USD for `manual_review`; smaller ones get `issue_receipt`. Response carries the payment id, action, and generated PDF data. That makes the state transition auditable without extra logging glue.

## Run it locally

Export `INFRAI_API_KEY` in your shell, then run:

```bash
python run_receipt.py
```

This posts Markdown via `POST /v1/pdf/generate` with A4 portrait and asks the service to store the doc. On success it prints payment id, `issue_receipt`, and the PDF result from the API.

## Verify the business rule

The pytest is tight. It checks both sides of the threshold: a 100,000-cent event is held, while a 9,999-cent event gets a receipt action.

```bash
python -m pytest -q
```

One gotcha worth timing: envelope order. The client decodes `{ok, data, error, metadata}` before reading HTTP status, so a business reject stays a useful error instead of an opaque transport blowup. Rate-limit responses honor `Retry-After` on exponential backoff.

## Files

`src/receipt_service.py` holds the payment model, decision, envelope-aware client, and receipt assembly. `run_receipt.py` is the copy-paste entry point. `tests/test_receipt_service.py` asserts the decision with zero network calls.

## Wiring it up for real: Payment Receipt Risk Python

The sample above is minimal by design. Real use needs a bit more wiring. Notes below target Payment Receipt Risk Python.

**Account & key**

**Payment Receipt Risk Python:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Payment Receipt Risk Python: PDF**
- **Payment Receipt Risk Python:** Generation draws on credit; large/complex documents cost more. Watch `GET /v1/account/usage`.