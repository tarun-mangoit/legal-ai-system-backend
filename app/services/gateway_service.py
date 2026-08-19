import hmac
import hashlib
import razorpay
import os
from typing import Dict, Any

class GatewayService:
    def __init__(self):
        # We will use env variables, defaulting to test keys if not provided
        self.key_id = os.getenv("RAZORPAY_KEY_ID", "rzp_test_dummy_key_id")
        self.key_secret = os.getenv("RAZORPAY_KEY_SECRET") or os.getenv("RAZORPAY_SECRET", "dummy_secret")
        self.client = razorpay.Client(auth=(self.key_id, self.key_secret))

    def create_order(self, amount: float, currency: str = "INR", receipt: str = None) -> Dict[str, Any]:
        """
        Creates a Razorpay order.
        """
        if self.key_id == "rzp_test_dummy_key_id":
            import uuid
            return {
                "id": f"order_{str(uuid.uuid4()).replace('-', '')[:14]}",
                "entity": "order",
                "amount": int(amount * 100),
                "currency": currency,
                "receipt": receipt,
                "status": "created"
            }
            
        data = {
            "amount": int(amount * 100),
            "currency": currency,
            "receipt": receipt
        }
        return self.client.order.create(data=data)

    def verify_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        """
        Verifies the payment signature returned by Razorpay on the frontend.
        """
        if self.key_id == "rzp_test_dummy_key_id":
            return True
            
        try:
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            self.client.utility.verify_payment_signature(params_dict)
            return True
        except razorpay.errors.SignatureVerificationError:
            return False

    def verify_webhook_signature(self, payload: str, signature: str, secret: str) -> bool:
        """
        Verifies the webhook signature.
        """
        try:
            expected_signature = hmac.new(
                bytes(secret, 'latin-1'),
                bytes(payload, 'latin-1'),
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected_signature, signature)
        except Exception:
            return False

    def process_refund(self, payment_id: str, amount: float = None) -> Dict[str, Any]:
        """
        Initiates a refund for a payment.
        Amount should be in INR. If amount is None, full refund is initiated.
        """
        data = {}
        if amount:
            data["amount"] = int(amount * 100)
            
        return self.client.payment.refund(payment_id, data)
