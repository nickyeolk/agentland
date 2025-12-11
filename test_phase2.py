"""
Quick validation script for Phase 2 components.
"""

import asyncio
from src.llm.client import get_llm_client
from src.tools.registry import get_tool_registry
from src.tools.database import DatabaseQueryInput
from src.tools.payment import RefundInput
from src.tools.email import EmailInput
from src.tools.knowledge_base import KnowledgeBaseInput


async def test_llm_client():
    """Test LLM client."""
    print("\n=== Testing LLM Client ===")
    client = get_llm_client()

    # Test generation
    response = await client.generate(
        system="You are a triage agent. Analyze customer tickets.",
        user_message="I was charged twice for my subscription this month.",
        agent_name="triage",
    )

    print(f"Response: {response.content}")
    print(f"Tokens: {response.prompt_tokens} prompt + {response.completion_tokens} completion")

    # Get usage summary
    summary = client.get_usage_summary()
    print(f"Total cost: ${summary['total_cost']:.4f}")
    print("✅ LLM Client working!")


async def test_tools():
    """Test mock tools."""
    print("\n=== Testing Tools ===")
    registry = get_tool_registry()

    print(f"Registered tools: {len(registry)}")
    for tool_info in registry.list_tools():
        print(f"  - {tool_info['name']}: {tool_info['description']}")

    # Test Database Tool
    print("\n--- Testing Database Tool ---")
    db_tool = registry.get("database_query")
    result = await db_tool.execute(
        DatabaseQueryInput(
            query_type="customer_info",
            customer_id="C12345",
        )
    )
    print(f"Customer query: {result.success}")
    if result.success:
        print(f"Customer: {result.result['customer']['name']}")

    # Test Payment Tool
    print("\n--- Testing Payment Tool ---")
    payment_tool = registry.get("payment_gateway")
    result = await payment_tool.execute(
        RefundInput(
            payment_id="PAY-001",
            customer_id="C12345",
            amount=49.99,
            reason="Duplicate charge",
        )
    )
    print(f"Refund: {result.success}")
    if result.success and result.result.get('success'):
        print(f"Refund ID: {result.result.get('refund_id', 'N/A')}")

    # Test Email Tool
    print("\n--- Testing Email Tool ---")
    email_tool = registry.get("email_sender")
    result = await email_tool.execute(
        EmailInput(
            to="customer@example.com",
            subject="Refund Confirmation",
            body="Your refund has been processed.",
        )
    )
    print(f"Email: {result.success}")

    # Test Knowledge Base Tool
    print("\n--- Testing Knowledge Base Tool ---")
    kb_tool = registry.get("knowledge_base")
    result = await kb_tool.execute(
        KnowledgeBaseInput(
            query="password reset",
            category="account",
            max_results=2,
        )
    )
    print(f"KB search: {result.success}")
    if result.success:
        print(f"Found {result.result['total_found']} articles")
        for article in result.result['results']:
            print(f"  - {article['title']}")

    print("\n✅ All tools working!")


async def test_agent_tools():
    """Test agent-specific tool mapping."""
    print("\n=== Testing Agent Tool Mapping ===")
    registry = get_tool_registry()

    for agent_type in ["triage", "billing", "technical", "account", "escalation"]:
        tools = registry.get_tools_for_agent(agent_type)
        print(f"{agent_type.capitalize()} Agent: {len(tools)} tools")
        for tool in tools:
            print(f"  - {tool.name}")

    print("\n✅ Agent tool mapping working!")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Phase 2 Validation: LLM Client & Tools")
    print("=" * 60)

    try:
        await test_llm_client()
        await test_tools()
        await test_agent_tools()

        print("\n" + "=" * 60)
        print("✅ PHASE 2 VALIDATION COMPLETE!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
