"""
State graph orchestrator for multi-agent workflow.

This implements a simple state machine without LangGraph dependency,
providing the same functionality using plain Python.
"""

from typing import Dict, Any, Callable, Awaitable
import time

from src.orchestration.state import create_initial_state
from src.orchestration.nodes import (
    triage_node,
    billing_node,
    technical_node,
    account_node,
    escalation_node,
)
from src.orchestration.edges import route_after_triage
from src.observability.logger import get_logger
from src.observability.tracer import trace_span
from src.observability.metrics import record_ticket_processed

logger = get_logger(__name__)


class TicketWorkflow:
    """
    Ticket processing workflow orchestrator.

    Manages the flow from triage through specialist agents to resolution.
    """

    def __init__(self):
        """Initialize workflow."""
        # Define the node map
        self.nodes: Dict[str, Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = {
            "triage": triage_node,
            "billing": billing_node,
            "technical": technical_node,
            "account": account_node,
            "escalation": escalation_node,
        }

        logger.info("workflow_initialized", nodes=list(self.nodes.keys()))

    async def execute(
        self,
        ticket_id: str,
        correlation_id: str,
        customer_id: str,
        subject: str,
        body: str,
        category_hint: str = None,
        email: str = "",
    ) -> Dict[str, Any]:
        """
        Execute the complete ticket processing workflow.

        Args:
            ticket_id: Ticket identifier
            correlation_id: Correlation ID for tracing
            customer_id: Customer identifier
            subject: Ticket subject
            body: Ticket body
            category_hint: Optional category hint
            email: Customer email

        Returns:
            Final state with resolution
        """
        with trace_span(
            "workflow.execute",
            {"ticket_id": ticket_id, "correlation_id": correlation_id},
        ):
            start_time = time.time()

            logger.info(
                "workflow_started",
                ticket_id=ticket_id,
                correlation_id=correlation_id,
                customer_id=customer_id,
            )

            try:
                # Create initial state
                state = create_initial_state(
                    ticket_id=ticket_id,
                    correlation_id=correlation_id,
                    customer_id=customer_id,
                    subject=subject,
                    body=body,
                    category_hint=category_hint,
                    email=email,
                )

                # Execute workflow steps
                state = await self._execute_workflow(state)

                # Record metrics
                duration = time.time() - start_time
                routing = state.get("routing", {})
                record_ticket_processed(
                    category=routing.get("assigned_agent", "unknown"),
                    urgency=routing.get("urgency", "medium"),
                    duration=duration,
                )

                logger.info(
                    "workflow_completed",
                    ticket_id=ticket_id,
                    status=state.get("resolution", {}).get("status"),
                    duration_seconds=duration,
                )

                return state

            except Exception as e:
                logger.error(
                    "workflow_failed",
                    ticket_id=ticket_id,
                    error=str(e),
                    error_type=type(e).__name__,
                )

                # Update state with error
                if "metadata" not in state:
                    state["metadata"] = {}
                state["metadata"]["error_count"] = state["metadata"].get("error_count", 0) + 1

                state["resolution"] = {
                    "status": "error",
                    "response": f"An error occurred processing your ticket: {str(e)}",
                    "requires_human": True,
                }

                raise

    async def _execute_workflow(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the workflow steps.

        Flow:
        1. Triage -> determines routing
        2. Route to specialist (billing/technical/account/escalation)
        3. Return final state

        Args:
            state: Initial state

        Returns:
            Final state after processing
        """
        # Step 1: Triage
        logger.info("workflow_step", step="triage", ticket_id=state.get("ticket_id"))
        state = await triage_node(state)

        # Step 2: Route to appropriate specialist
        next_node = route_after_triage(state)
        logger.info(
            "workflow_step",
            step=next_node,
            ticket_id=state.get("ticket_id"),
            routed_from="triage",
        )

        # Execute specialist node
        if next_node in self.nodes:
            state = await self.nodes[next_node](state)
        else:
            logger.warning(
                "workflow_unknown_node",
                node=next_node,
                ticket_id=state.get("ticket_id"),
            )
            # Fallback to escalation
            state = await escalation_node(state)

        # Check if further escalation is needed
        # (In a more complex workflow, you could add additional routing here)

        return state


# Global workflow instance
_workflow: TicketWorkflow = None


def get_workflow() -> TicketWorkflow:
    """
    Get the global workflow instance.

    Returns:
        TicketWorkflow instance
    """
    global _workflow
    if _workflow is None:
        _workflow = TicketWorkflow()
    return _workflow


async def process_ticket(
    ticket_id: str,
    correlation_id: str,
    customer_id: str,
    subject: str,
    body: str,
    category_hint: str = None,
    email: str = "",
) -> Dict[str, Any]:
    """
    Process a ticket through the complete workflow.

    This is the main entry point for ticket processing.

    Args:
        ticket_id: Ticket identifier
        correlation_id: Correlation ID for tracing
        customer_id: Customer identifier
        subject: Ticket subject
        body: Ticket body
        category_hint: Optional category hint
        email: Customer email

    Returns:
        Final state with resolution
    """
    workflow = get_workflow()
    return await workflow.execute(
        ticket_id=ticket_id,
        correlation_id=correlation_id,
        customer_id=customer_id,
        subject=subject,
        body=body,
        category_hint=category_hint,
        email=email,
    )
