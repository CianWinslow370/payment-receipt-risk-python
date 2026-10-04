from src.receipt_service import PaymentEvent, risk_action


def test_large_payment_is_held_for_manual_review():
    event = PaymentEvent("pay_9", "risk@example.com", 100_000, "USD", "Example Shop")
    assert risk_action(event) == "manual_review"


def test_small_payment_issues_receipt():
    event = PaymentEvent("pay_10", "buyer@example.com", 9_999, "USD", "Example Shop")
    assert risk_action(event) == "issue_receipt"
