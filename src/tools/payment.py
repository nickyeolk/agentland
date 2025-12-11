"""
Mock payment gateway tool for refunds and transactions.
"""

from typing import Any, Dict
from pydantic import Field
import random

from src.tools.base import BaseTool, ToolInput


class RefundInput(ToolInput):
    """Input for refund processing."""

    payment_id: str = Field(..., description="Payment identifier to refund")
    customer_id: str = Field(..., description="Customer identifier")
    amount: float = Field(..., description="Amount to refund")
    reason: str = Field(..., description="Reason for refund")


class PaymentQueryInput(ToolInput):
    """Input for payment query."""

    payment_id: str = Field(..., description="Payment identifier")
    customer_id: str = Field(..., description="Customer identifier")


class PaymentTool(BaseTool):
    """Mock payment gateway tool."""

    def __init__(self):
        super().__init__(
            name="payment_gateway",
            description="Process refunds and query payment status",
        )

    async def _execute(self, input_data: ToolInput) -> Dict[str, Any]:
        """
        Execute payment operation.

        Args:
            input_data: Payment operation parameters

        Returns:
            Operation result
        """
        if isinstance(input_data, RefundInput):
            return await self._process_refund(input_data)
        elif isinstance(input_data, PaymentQueryInput):
            return await self._query_payment(input_data)
        else:
            return {
                "success": False,
                "error": "Unknown payment operation",
            }

    async def _process_refund(self, input_data: RefundInput) -> Dict[str, Any]:
        """Process a refund."""
        # Simulate success most of the time
        success = random.random() > 0.1  # 90% success rate

        if success:
            refund_id = f"REF-{random.randint(1000, 9999)}"
            return {
                "success": True,
                "refund_id": refund_id,
                "payment_id": input_data.payment_id,
                "amount": input_data.amount,
                "status": "processed",
                "estimated_arrival": "3-5 business days",
                "message": f"Refund of ${input_data.amount:.2f} has been processed successfully",
            }
        else:
            return {
                "success": False,
                "payment_id": input_data.payment_id,
                "error": "Payment gateway temporarily unavailable",
                "retry_recommended": True,
            }

    async def _query_payment(self, input_data: PaymentQueryInput) -> Dict[str, Any]:
        """Query payment status."""
        # Mock payment data
        return {
            "found": True,
            "payment_id": input_data.payment_id,
            "status": "completed",
            "amount": 49.99,
            "date": "2024-12-01",
            "method": "credit_card",
            "last4": "4242",
        }
