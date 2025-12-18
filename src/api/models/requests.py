"""
Request models for API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional


class TicketRequest(BaseModel):
    """Request model for creating a ticket."""

    customer_id: str = Field(..., description="Customer identifier")
    subject: str = Field(..., min_length=1, max_length=200, description="Ticket subject")
    body: str = Field(..., min_length=1, max_length=5000, description="Ticket description")
    email: Optional[str] = Field(
        default=None,
        description="Customer email address for notifications",
    )
    category_hint: Optional[str] = Field(
        default=None,
        description="Optional category hint (billing, technical, account)",
    )

    class Config:
        schema_extra = {
            "example": {
                "customer_id": "C12345",
                "subject": "Issue with recent charge",
                "body": "I was charged twice for my subscription this month. Can you help?",
                "category_hint": "billing",
            }
        }
