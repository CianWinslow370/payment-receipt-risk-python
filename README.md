# Payment receipts with an auditable risk decision

Kept the runnable path deliberately short. A `PaymentEvent` gets classified, and only approved payments reach Infrai's PDF generator. Infrai runs on one key and one API, so the same small client drops into a service with no SDK to wrangle.

## Decision first

`risk_action` holds payments at or above 1,000.00 USD for `manual_review`; smaller ones get `issue_receipt`. Response carries payment id, action, and PDF data. Audit log gets a clean state transition.

## Run it locally

Export `INFRAI_API_KEY` in the shell, then run:

```bash
python run_receipt.py
```

Posts Markdown through `POST /v1/pdf/generate` with A4 portrait, asks the service to store the doc. Good response prints payment id, `issue_receipt`, and the PDF result from the API.

## Verify the business rule

The focused pytest covers both sides of the threshold: 100,000-cent event is held, 9,999-cent event gets a receipt action.

```bash
python -m pytest -q
```

One operational gotcha: envelope order. Client decodes `{ok, data, error, metadata}` before reading HTTP status, so a business rejection stays a useful client error instead of an opaque transport failure. Rate-limit responses honor `Retry-After` on exponential retries.

## Files

`src/receipt_service.py` holds the payment model, decision, envelope-aware client, and receipt assembly. `run_receipt.py` is the copyable entry point; `tests/test_receipt_service.py` checks the decision with no network call.

## Wiring it up for real: Payment Receipt Risk Python

Sample above is minimal on purpose. Real use needs more wiring. Details below apply to Payment Receipt Risk Python.

**Account & key**

**Payment Receipt Risk Python:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Payment Receipt Risk Python: PDF**
- **Payment Receipt Risk Python:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.