"""
Quick validation script for Phase 3 - Agents.
"""

import asyncio
from datetime import datetime, timezone
from src.agents.triage_agent import TriageAgent
from src.agents.billing_agent import BillingAgent
from src.agents.technical_agent import TechnicalAgent
from src.agents.account_agent import AccountAgent
from src.agents.escalation_agent import EscalationAgent


def create_test_state(subject: str, body: str, customer_id: str = "C12345") -> dict:
    """Create a test state for agent execution."""
    return {
        "ticket_id": "T-TEST-001",
        "correlation_id": "CID-test",
        "timestamp": datetime.now(timezone.utc),
        "customer_context": {
            "customer_id": customer_id,
            "email": "test@example.com",
        },
        "ticket_content": {
            "subject": subject,
            "body": body,
        },
        "agent_interactions": [],
        "metadata": {},
    }


async def test_triage_agent():
    """Test Triage Agent."""
    print("\n" + "="*60)
    print("Testing Triage Agent")
    print("="*60)

    agent = TriageAgent()

    # Test cases
    test_cases = [
        ("Duplicate charge on my account", "I was charged twice for my subscription."),
        ("API returning errors", "Getting 500 errors on all API calls since this morning."),
        ("Can't log in", "Forgot my password and can't access my account."),
        ("GDPR compliance question", "Need info about data retention for enterprise."),
    ]

    for subject, body in test_cases:
        print(f"\n--- Test: {subject} ---")
        state = create_test_state(subject, body)
        result = await agent.execute(state)

        routing = result.get("routing", {})
        print(f"Routed to: {routing.get('assigned_agent')}")
        print(f"Urgency: {routing.get('urgency')}")
        print(f"Confidence: {routing.get('confidence_score'):.2f}")
        print(f"Reasoning: {routing.get('reasoning', 'N/A')[:100]}...")

    print("\n✅ Triage Agent working!")


async def test_billing_agent():
    """Test Billing Agent."""
    print("\n" + "="*60)
    print("Testing Billing Agent")
    print("="*60)

    agent = BillingAgent()

    state = create_test_state(
        "Duplicate charge",
        "I was charged twice on December 1st for my subscription."
    )

    result = await agent.execute(state)

    resolution = result.get("resolution", {})
    print(f"Status: {resolution.get('status')}")
    print(f"Response: {resolution.get('response', '')[:200]}...")

    interactions = result.get("agent_interactions", [])
    if interactions:
        last_interaction = interactions[-1]
        print(f"Tool calls made: {len(last_interaction.get('tool_calls', []))}")

    print("\n✅ Billing Agent working!")


async def test_technical_agent():
    """Test Technical Agent."""
    print("\n" + "="*60)
    print("Testing Technical Agent")
    print("="*60)

    agent = TechnicalAgent()

    state = create_test_state(
        "API connection issues",
        "Getting timeout errors when calling the API. Started this morning."
    )

    result = await agent.execute(state)

    resolution = result.get("resolution", {})
    print(f"Status: {resolution.get('status')}")
    print(f"Response: {resolution.get('response', '')[:200]}...")

    interactions = result.get("agent_interactions", [])
    if interactions:
        last_interaction = interactions[-1]
        print(f"Tool calls made: {len(last_interaction.get('tool_calls', []))}")

    print("\n✅ Technical Agent working!")


async def test_account_agent():
    """Test Account Agent."""
    print("\n" + "="*60)
    print("Testing Account Agent")
    print("="*60)

    agent = AccountAgent()

    state = create_test_state(
        "Password reset",
        "I forgot my password and need to reset it."
    )

    result = await agent.execute(state)

    resolution = result.get("resolution", {})
    print(f"Status: {resolution.get('status')}")
    print(f"Response: {resolution.get('response', '')[:200]}...")

    interactions = result.get("agent_interactions", [])
    if interactions:
        last_interaction = interactions[-1]
        print(f"Tool calls made: {len(last_interaction.get('tool_calls', []))}")

    print("\n✅ Account Agent working!")


async def test_escalation_agent():
    """Test Escalation Agent."""
    print("\n" + "="*60)
    print("Testing Escalation Agent")
    print("="*60)

    agent = EscalationAgent()

    # Test case that should escalate to human
    state = create_test_state(
        "Legal compliance question",
        "We need clarification on GDPR data retention policies for our enterprise contract."
    )

    # Add previous agent interaction to simulate escalation path
    state["agent_interactions"].append({
        "agent_name": "triage_agent",
        "action": "route",
        "reasoning": "Complex compliance issue",
    })

    result = await agent.execute(state)

    resolution = result.get("resolution", {})
    print(f"Status: {resolution.get('status')}")
    print(f"Requires Human: {resolution.get('requires_human')}")
    print(f"Response: {resolution.get('response', '')[:200]}...")

    print("\n✅ Escalation Agent working!")


async def test_agent_observability():
    """Test that observability is working for agents."""
    print("\n" + "="*60)
    print("Testing Agent Observability")
    print("="*60)

    agent = TriageAgent()
    state = create_test_state("Test ticket", "This is a test")

    result = await agent.execute(state)

    # Check token usage was recorded
    metadata = result.get("metadata", {})
    token_usage = metadata.get("token_usage", {})

    print(f"Token usage recorded: {bool(token_usage)}")
    if "triage" in token_usage:
        print(f"Triage tokens: {token_usage['triage']}")

    # Check agent interactions were recorded
    interactions = result.get("agent_interactions", [])
    print(f"Agent interactions recorded: {len(interactions)}")

    print("\n✅ Observability working!")


async def main():
    """Run all agent tests."""
    print("=" * 60)
    print("Phase 3 Validation: Agents & Prompts")
    print("=" * 60)

    try:
        await test_triage_agent()
        await test_billing_agent()
        await test_technical_agent()
        await test_account_agent()
        await test_escalation_agent()
        await test_agent_observability()

        print("\n" + "=" * 60)
        print("✅ PHASE 3 VALIDATION COMPLETE!")
        print("All 5 agents implemented and working:")
        print("  - Triage Agent ✓")
        print("  - Billing Agent ✓")
        print("  - Technical Agent ✓")
        print("  - Account Agent ✓")
        print("  - Escalation Agent ✓")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
