"""
Response models for API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class AgentInteraction(BaseModel):
    """Model for agent interaction details."""

    agent_name: str
    timestamp: datetime
    action: str
    reasoning: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    result: Optional[str] = None


class TicketResolution(BaseModel):
    """Model for ticket resolution details."""

    status: str = Field(..., description="Ticket status (pending, resolved, escalated)")
    response: str = Field(..., description="Response to the customer")
    requires_human: bool = Field(default=False, description="Whether human intervention is needed")
    satisfaction_predicted: Optional[float] = None


class TicketMetadata(BaseModel):
    """Model for ticket processing metadata."""

    token_usage: Dict[str, Any] = Field(default_factory=dict)
    latency_ms: Dict[str, Any] = Field(default_factory=dict)
    error_count: int = 0
    retry_count: int = 0


class TicketResponse(BaseModel):
    """Response model for ticket processing."""

    ticket_id: str
    correlation_id: str
    timestamp: datetime
    routing: Dict[str, Any]
    agent_interactions: List[AgentInteraction]
    resolution: TicketResolution
    metadata: TicketMetadata

    class Config:
        schema_extra = {
            "example": {
                "ticket_id": "T-2025-001",
                "correlation_id": "CID-abc123",
                "timestamp": "2025-12-11T10:30:45.123Z",
                "routing": {
                    "urgency": "medium",
                    "assigned_agent": "billing_agent",
                    "confidence_score": 0.92,
                },
                "agent_interactions": [
                    {
                        "agent_name": "triage_agent",
                        "timestamp": "2025-12-11T10:30:45Z",
                        "action": "route",
                        "reasoning": "Customer mentions 'charge' and 'subscription' indicating billing issue",
                    }
                ],
                "resolution": {
                    "status": "resolved",
                    "response": "I've reviewed your account and found the duplicate charge...",
                    "requires_human": False,
                },
                "metadata": {
                    "token_usage": {"prompt": 450, "completion": 120},
                    "latency_ms": {"triage": 120, "billing": 850},
                    "error_count": 0,
                    "retry_count": 0,
                },
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Health status")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment name")
    timestamp: datetime = Field(..., description="Current timestamp")

    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "environment": "development",
                "timestamp": "2025-12-11T10:30:45.123Z",
            }
        }


class ErrorResponse(BaseModel):
    """Response model for errors."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    correlation_id: Optional[str] = Field(None, description="Request correlation ID")
    timestamp: datetime = Field(..., description="Error timestamp")

    class Config:
        schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Ticket subject is required",
                "correlation_id": "CID-abc123",
                "timestamp": "2025-12-11T10:30:45.123Z",
            }
        }
