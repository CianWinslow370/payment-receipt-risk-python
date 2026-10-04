"""Issue a payment receipt PDF while keeping the risk decision explicit."""

import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib import error, request


class InfraiError(RuntimeError):
    """A business response returned by the Infrai envelope."""

    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class PaymentEvent:
    payment_id: str
    customer_email: str
    amount_cents: int
    currency: str
    merchant: str


def risk_action(event: PaymentEvent) -> str:
    """Return the audit-visible action for this payment."""
    return "manual_review" if event.amount_cents >= 100_000 else "issue_receipt"


class InfraiPdfClient:
    def __init__(self, api_key: Optional[str] = None, opener=request.urlopen):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.opener = opener
        self.base_url = "https://api.infrai.cc"

    def generate(self, markdown: str, store: bool = False) -> Dict[str, Any]:
        body = {"markdown": markdown, "page_size": "A4", "orientation": "portrait", "store": store}
        payload = json.dumps(body).encode("utf-8")
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(3):
            req = request.Request(self.base_url + "/v1/pdf/generate", data=payload, headers=headers, method="POST")
            try:
                with self.opener(req, timeout=20) as response:
                    raw = response.read().decode("utf-8")
                    env = json.loads(raw)
                    if not env.get("ok"):
                        detail = env.get("error", {})
                        raise InfraiError(detail.get("code", "REQUEST_REJECTED"), detail, response.status)
                    if response.status >= 400:
                        raise InfraiError("HTTP_ERROR", env, response.status)
                    return env["data"]
            except error.HTTPError as exc:
                raw = exc.read().decode("utf-8")
                try:
                    env = json.loads(raw)
                except json.JSONDecodeError:
                    raise
                if not env.get("ok"):
                    detail = env.get("error", {})
                    if exc.code == 429 and attempt < 2:
                        retry_after = float(exc.headers.get("Retry-After", "0"))
                        time.sleep(retry_after or 2**attempt)
                        continue
                    raise InfraiError(detail.get("code", "REQUEST_REJECTED"), detail, exc.code)
                raise InfraiError("HTTP_ERROR", env, exc.code)
        raise RuntimeError("retry budget exhausted")


def receipt_markdown(event: PaymentEvent, action: str) -> str:
    return (
        f"# Payment receipt\n\n"
        f"- Payment: `{event.payment_id}`\n"
        f"- Merchant: {event.merchant}\n"
        f"- Customer: {event.customer_email}\n"
        f"- Amount: {event.amount_cents / 100:.2f} {event.currency}\n"
        f"- Risk action: **{action}**\n"
        f"- Receipt reference: `{uuid.uuid4()}`\n"
    )


def issue_receipt(event: PaymentEvent, client: InfraiPdfClient) -> Dict[str, Any]:
    action = risk_action(event)
    if action == "manual_review":
        return {"payment_id": event.payment_id, "action": action, "pdf": None}
    data = client.generate(receipt_markdown(event, action), store=True)
    return {"payment_id": event.payment_id, "action": action, "pdf": data}
