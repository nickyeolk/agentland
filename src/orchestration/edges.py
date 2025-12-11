"""
Conditional edge logic for routing between nodes.
"""

from typing import Dict, Any, Optional

from src.observability.logger import get_logger

logger = get_logger(__name__)


def route_after_triage(state: Dict[str, Any]) -> str:
    """
    Determine which specialist node to route to after triage.

    Args:
        state: Current state with routing decision

    Returns:
        Next node name
    """
    routing = state.get("routing", {})
    assigned_agent = routing.get("assigned_agent", "")
    confidence = routing.get("confidence_score", 0.0)

    logger.info(
        "routing_decision",
        assigned_agent=assigned_agent,
        confidence=confidence,
        urgency=routing.get("urgency"),
    )

    # Map agent names to node names
    agent_to_node = {
        "billing_agent": "billing",
        "technical_agent": "technical",
        "account_agent": "account",
        "escalation_agent": "escalation",
    }

    next_node = agent_to_node.get(assigned_agent, "escalation")

    logger.info("routing_to_node", next_node=next_node)

    return next_node


def should_escalate(state: Dict[str, Any]) -> bool:
    """
    Check if issue should be escalated after specialist attempt.

    This can be used if a specialist agent sets a flag indicating
    they couldn't resolve the issue.

    Args:
        state: Current state

    Returns:
        True if should escalate to escalation_agent
    """
    resolution = state.get("resolution", {})

    # Check if resolution indicates need for escalation
    # (e.g., specialist agent marked as needing escalation)
    if resolution.get("needs_escalation", False):
        return True

    # Check confidence - if very low, might need escalation
    interactions = state.get("agent_interactions", [])
    if interactions:
        last_interaction = interactions[-1]
        # Custom escalation logic could go here
        pass

    return False


def check_resolution_complete(state: Dict[str, Any]) -> bool:
    """
    Check if ticket resolution is complete.

    Args:
        state: Current state

    Returns:
        True if resolution is complete
    """
    resolution = state.get("resolution", {})
    status = resolution.get("status", "pending")

    # Resolution is complete if status is resolved or escalated
    return status in ["resolved", "escalated"]
