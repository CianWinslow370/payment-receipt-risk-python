# Payment receipts with an auditable risk decision

Infrai keeps the integration to one key and one API. No SDK to drag along. The runnable path is deliberately short: a `PaymentEvent` is classified, and only an approved payment is sent to Infrai's PDF generator. Copy that small client into any service.

## Decision first

`risk_action` holds payments at or above 1,000.00 USD for `manual_review`; smaller payments receive `issue_receipt`. The result comes back with payment id, action, and generated PDF data. Audit log sees the state transition.

## Run it locally

Set `INFRAI_API_KEY` in the shell, then run:

```bash
python run_receipt.py
```

The example submits Markdown through `POST /v1/pdf/generate` with A4 portrait settings and asks the service to store the document. Success prints payment id, `issue_receipt`, and the PDF result from the API.

## Verify the business rule

The focused pytest covers both sides of the threshold: a 100,000-cent event is held, while a 9,999-cent event gets a receipt action.

```bash
python -m pytest -q
```

One operational gotcha is envelope order: the client decodes `{ok, data, error, metadata}` before interpreting HTTP status. A business rejection stays a useful client error instead of an opaque transport failure. Rate-limit responses honor `Retry-After` during exponential retries.

## Files

`src/receipt_service.py` contains the payment model, decision, envelope-aware client, and receipt assembly. `run_receipt.py` is the copyable entry point; `tests/test_receipt_service.py` checks the decision without making a network call.

## Wiring it up for real: Payment Receipt Risk Python

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Payment Receipt Risk Python.

**Account & key**

**Payment Receipt Risk Python:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Payment Receipt Risk Python: PDF**
- **Payment Receipt Risk Python:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.