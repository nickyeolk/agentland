"""
Agent state schema and type definitions.

Note: Using plain Python types instead of LangGraph TypedDict due to environment constraints.
This provides the same state management functionality.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict


@dataclass
class CustomerContext:
    """Customer context information."""
    customer_id: str
    tier: str = "unknown"
    email: str = ""
    account_status: str = "unknown"
    history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class TicketContent:
    """Ticket content."""
    subject: str
    body: str
    category_hint: Optional[str] = None


@dataclass
class Routing:
    """Routing decision."""
    urgency: str = "medium"
    assigned_agent: str = ""
    confidence_score: float = 0.0
    reasoning: str = ""


@dataclass
class AgentInteraction:
    """Record of an agent interaction."""
    agent_name: str
    timestamp: datetime
    action: str
    reasoning: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    result: Optional[str] = None


@dataclass
class Resolution:
    """Ticket resolution."""
    status: str = "pending"
    response: str = ""
    requires_human: bool = False
    satisfaction_predicted: Optional[float] = None


@dataclass
class Metadata:
    """Processing metadata."""
    token_usage: Dict[str, Any] = field(default_factory=dict)
    latency_ms: Dict[str, int] = field(default_factory=dict)
    error_count: int = 0
    retry_count: int = 0


@dataclass
class AgentState:
    """
    Complete agent state for the support ticket workflow.

    This replaces LangGraph's TypedDict while providing the same functionality.
    """
    ticket_id: str
    correlation_id: str
    timestamp: datetime
    customer_context: CustomerContext
    ticket_content: TicketContent
    routing: Routing = field(default_factory=Routing)
    agent_interactions: List[AgentInteraction] = field(default_factory=list)
    resolution: Resolution = field(default_factory=Resolution)
    metadata: Metadata = field(default_factory=Metadata)

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            "ticket_id": self.ticket_id,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "customer_context": asdict(self.customer_context),
            "ticket_content": asdict(self.ticket_content),
            "routing": asdict(self.routing),
            "agent_interactions": [asdict(i) for i in self.agent_interactions],
            "resolution": asdict(self.resolution),
            "metadata": asdict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentState":
        """Create state from dictionary."""
        return cls(
            ticket_id=data["ticket_id"],
            correlation_id=data["correlation_id"],
            timestamp=data["timestamp"],
            customer_context=CustomerContext(**data["customer_context"]),
            ticket_content=TicketContent(**data["ticket_content"]),
            routing=Routing(**data.get("routing", {})),
            agent_interactions=[
                AgentInteraction(**i) for i in data.get("agent_interactions", [])
            ],
            resolution=Resolution(**data.get("resolution", {})),
            metadata=Metadata(**data.get("metadata", {})),
        )


def create_initial_state(
    ticket_id: str,
    correlation_id: str,
    customer_id: str,
    subject: str,
    body: str,
    category_hint: Optional[str] = None,
    email: str = "",
) -> Dict[str, Any]:
    """
    Create initial state for a new ticket.

    Args:
        ticket_id: Unique ticket identifier
        correlation_id: Correlation ID for tracing
        customer_id: Customer identifier
        subject: Ticket subject
        body: Ticket body
        category_hint: Optional category hint
        email: Customer email

    Returns:
        Initial state dictionary
    """
    return {
        "ticket_id": ticket_id,
        "correlation_id": correlation_id,
        "timestamp": datetime.utcnow(),
        "customer_context": {
            "customer_id": customer_id,
            "tier": "unknown",
            "email": email,
            "account_status": "unknown",
            "history": [],
        },
        "ticket_content": {
            "subject": subject,
            "body": body,
            "category_hint": category_hint,
        },
        "routing": {
            "urgency": "medium",
            "assigned_agent": "",
            "confidence_score": 0.0,
            "reasoning": "",
        },
        "agent_interactions": [],
        "resolution": {
            "status": "pending",
            "response": "",
            "requires_human": False,
            "satisfaction_predicted": None,
        },
        "metadata": {
            "token_usage": {},
            "latency_ms": {},
            "error_count": 0,
            "retry_count": 0,
        },
    }
