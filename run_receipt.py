import json

from src.receipt_service import InfraiPdfClient, PaymentEvent, issue_receipt


event = PaymentEvent("pay_demo_123", "buyer@example.com", 4250, "USD", "Northwind Books")
result = issue_receipt(event, InfraiPdfClient())
print(json.dumps(result, indent=2))
