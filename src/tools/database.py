"""
Mock database tool for customer and ticket queries.
"""

from typing import Any, Dict, List, Optional
from pydantic import Field

from src.tools.base import BaseTool, ToolInput, ToolOutput


class DatabaseQueryInput(ToolInput):
    """Input for database query tool."""

    query_type: str = Field(..., description="Type of query: customer_info, ticket_history, payment_history")
    customer_id: str = Field(..., description="Customer identifier")
    limit: int = Field(default=10, description="Maximum results to return")


# Mock data
MOCK_CUSTOMERS = {
    "C12345": {
        "customer_id": "C12345",
        "name": "John Doe",
        "email": "john.doe@example.com",
        "tier": "pro",
        "account_status": "active",
        "joined_date": "2023-01-15",
    },
    "C67890": {
        "customer_id": "C67890",
        "name": "Jane Smith",
        "email": "jane.smith@example.com",
        "tier": "enterprise",
        "account_status": "active",
        "joined_date": "2022-06-10",
    },
}

MOCK_TICKETS = {
    "C12345": [
        {
            "ticket_id": "T-001",
            "date": "2024-11-20",
            "subject": "Password reset",
            "status": "resolved",
            "resolution_time_hours": 2,
        },
        {
            "ticket_id": "T-002",
            "date": "2024-12-01",
            "subject": "Billing question",
            "status": "resolved",
            "resolution_time_hours": 4,
        },
    ],
    "C67890": [
        {
            "ticket_id": "T-003",
            "date": "2024-10-15",
            "subject": "Feature request",
            "status": "resolved",
            "resolution_time_hours": 48,
        },
    ],
}

MOCK_PAYMENTS = {
    "C12345": [
        {
            "payment_id": "PAY-001",
            "date": "2024-11-01",
            "amount": 49.99,
            "status": "completed",
            "description": "Pro subscription - November",
        },
        {
            "payment_id": "PAY-002",
            "date": "2024-12-01",
            "amount": 49.99,
            "status": "completed",
            "description": "Pro subscription - December",
        },
    ],
    "C67890": [
        {
            "payment_id": "PAY-003",
            "date": "2024-11-01",
            "amount": 199.99,
            "status": "completed",
            "description": "Enterprise subscription - November",
        },
    ],
}


class DatabaseTool(BaseTool):
    """Mock database query tool."""

    def __init__(self):
        super().__init__(
            name="database_query",
            description="Query customer information, ticket history, or payment history from the database",
        )

    async def _execute(self, input_data: DatabaseQueryInput) -> Dict[str, Any]:
        """
        Execute database query.

        Args:
            input_data: Query parameters

        Returns:
            Query results
        """
        customer_id = input_data.customer_id
        query_type = input_data.query_type
        limit = input_data.limit

        if query_type == "customer_info":
            # Return customer information
            customer = MOCK_CUSTOMERS.get(customer_id)
            if not customer:
                return {
                    "found": False,
                    "message": f"Customer {customer_id} not found",
                }
            return {"found": True, "customer": customer}

        elif query_type == "ticket_history":
            # Return ticket history
            tickets = MOCK_TICKETS.get(customer_id, [])
            return {
                "found": len(tickets) > 0,
                "tickets": tickets[:limit],
                "total_count": len(tickets),
            }

        elif query_type == "payment_history":
            # Return payment history
            payments = MOCK_PAYMENTS.get(customer_id, [])
            return {
                "found": len(payments) > 0,
                "payments": payments[:limit],
                "total_count": len(payments),
            }

        else:
            return {
                "error": f"Unknown query type: {query_type}",
                "supported_types": ["customer_info", "ticket_history", "payment_history"],
            }
