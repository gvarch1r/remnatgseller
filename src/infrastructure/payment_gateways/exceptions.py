class PaymentWebhookIgnored(Exception):
    """Webhook is authentic but does not change payment state (acknowledge with 200, no task)."""
