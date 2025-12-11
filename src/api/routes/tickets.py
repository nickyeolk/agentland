"""
Ticket management endpoints.
"""

from fastapi import APIRouter, status
from datetime import datetime, timezone
import uuid

from src.api.models.requests import TicketRequest
from src.api.models.responses import TicketResponse, AgentInteraction, TicketResolution, TicketMetadata
from src.observability.context import get_or_create_correlation_id
from src.observability.logger import get_logger
from src.orchestration.graph import process_ticket

router = APIRouter(prefix="/tickets", tags=["tickets"])
logger = get_logger(__name__)


@router.post("", response_model=TicketResponse, status_code=status.HTTP_200_OK)
async def create_ticket(ticket: TicketRequest) -> TicketResponse:
    """
    Create and process a customer support ticket.

    Args:
        ticket: Ticket details

    Returns:
        Processed ticket with resolution
    """
    correlation_id = get_or_create_correlation_id()
    ticket_id = f"T-{uuid.uuid4().hex[:8]}"

    logger.info(
        "ticket_created",
        ticket_id=ticket_id,
        customer_id=ticket.customer_id,
        subject=ticket.subject,
    )

    # Process ticket through the agent workflow
    state = await process_ticket(
        ticket_id=ticket_id,
        correlation_id=correlation_id,
        customer_id=ticket.customer_id,
        subject=ticket.subject,
        body=ticket.body,
        category_hint=ticket.category_hint,
        email=ticket.email or "",
    )

    # Convert state to response format
    agent_interactions = []
    for interaction in state.get("agent_interactions", []):
        agent_interactions.append(
            AgentInteraction(
                agent_name=interaction.get("agent_name", "unknown"),
                timestamp=interaction.get("timestamp", datetime.now(timezone.utc)),
                action=interaction.get("action", ""),
                reasoning=interaction.get("reasoning"),
                tool_calls=interaction.get("tool_calls", []),
                result=interaction.get("result"),
            )
        )

    routing = state.get("routing", {})
    resolution = state.get("resolution", {})
    metadata = state.get("metadata", {})

    logger.info(
        "ticket_processed",
        ticket_id=ticket_id,
        status=resolution.get("status"),
        assigned_agent=routing.get("assigned_agent"),
    )

    return TicketResponse(
        ticket_id=ticket_id,
        correlation_id=correlation_id,
        timestamp=state.get("timestamp", datetime.now(timezone.utc)),
        routing=routing,
        agent_interactions=agent_interactions,
        resolution=TicketResolution(
            status=resolution.get("status", "pending"),
            response=resolution.get("response", ""),
            requires_human=resolution.get("requires_human", False),
        ),
        metadata=TicketMetadata(
            token_usage=metadata.get("token_usage", {}),
            latency_ms=metadata.get("latency_ms", {}),
            error_count=metadata.get("error_count", 0),
            retry_count=metadata.get("retry_count", 0),
        ),
    )


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: str) -> TicketResponse:
    """
    Get ticket status and details.

    Args:
        ticket_id: Ticket identifier

    Returns:
        Ticket details
    """
    # TODO: Implement ticket retrieval from storage
    # For now, return a placeholder

    correlation_id = get_or_create_correlation_id()

    logger.info(
        "ticket_retrieved",
        ticket_id=ticket_id,
    )

    return TicketResponse(
        ticket_id=ticket_id,
        correlation_id=correlation_id,
        timestamp=datetime.now(timezone.utc),
        routing={
            "urgency": "medium",
            "assigned_agent": "placeholder",
            "confidence_score": 0.0,
        },
        agent_interactions=[],
        resolution=TicketResolution(
            status="pending",
            response="Ticket retrieval not yet implemented.",
            requires_human=False,
        ),
        metadata=TicketMetadata(),
    )
