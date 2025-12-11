"""
Mock knowledge base search tool.
"""

from typing import Any, Dict, List
from pydantic import Field

from src.tools.base import BaseTool, ToolInput


class KnowledgeBaseInput(ToolInput):
    """Input for knowledge base search."""

    query: str = Field(..., description="Search query")
    category: str = Field(default="all", description="Category filter: all, technical, billing, account")
    max_results: int = Field(default=3, description="Maximum results to return")


# Mock knowledge base articles
MOCK_KB_ARTICLES = [
    {
        "id": "KB-001",
        "title": "How to reset your password",
        "category": "account",
        "content": "To reset your password, go to Settings > Security > Reset Password. You'll receive an email with a reset link.",
        "relevance_score": 0.95,
    },
    {
        "id": "KB-002",
        "title": "Understanding your bill",
        "category": "billing",
        "content": "Your bill includes your subscription tier, any add-ons, and usage charges. Pro tier is $49.99/month.",
        "relevance_score": 0.92,
    },
    {
        "id": "KB-003",
        "title": "Troubleshooting connection issues",
        "category": "technical",
        "content": "If you're experiencing connection issues, try: 1) Clear browser cache 2) Check firewall settings 3) Restart your device.",
        "relevance_score": 0.88,
    },
    {
        "id": "KB-004",
        "title": "How to request a refund",
        "category": "billing",
        "content": "Refunds can be requested within 30 days of payment. Contact support with your payment ID and reason.",
        "relevance_score": 0.90,
    },
    {
        "id": "KB-005",
        "title": "Updating account information",
        "category": "account",
        "content": "Update your email, name, or billing address in Settings > Account > Profile Information.",
        "relevance_score": 0.85,
    },
    {
        "id": "KB-006",
        "title": "API rate limits explained",
        "category": "technical",
        "content": "API rate limits vary by tier: Free (100/day), Pro (1000/day), Enterprise (unlimited).",
        "relevance_score": 0.87,
    },
    {
        "id": "KB-007",
        "title": "Subscription upgrade process",
        "category": "billing",
        "content": "Upgrade your subscription at any time. You'll be prorated for the remaining time in your billing cycle.",
        "relevance_score": 0.89,
    },
    {
        "id": "KB-008",
        "title": "Two-factor authentication setup",
        "category": "account",
        "content": "Enable 2FA in Settings > Security > Two-Factor Authentication. Use an authenticator app like Google Authenticator.",
        "relevance_score": 0.93,
    },
]


class KnowledgeBaseTool(BaseTool):
    """Mock knowledge base search tool."""

    def __init__(self):
        super().__init__(
            name="knowledge_base",
            description="Search the knowledge base for help articles and documentation",
        )

    async def _execute(self, input_data: KnowledgeBaseInput) -> Dict[str, Any]:
        """
        Search knowledge base.

        Args:
            input_data: Search parameters

        Returns:
            Search results
        """
        query = input_data.query.lower()
        category = input_data.category
        max_results = input_data.max_results

        # Filter by category
        articles = MOCK_KB_ARTICLES
        if category != "all":
            articles = [a for a in articles if a["category"] == category]

        # Simple keyword matching for relevance
        results = []
        for article in articles:
            # Check if any query words are in title or content
            title_lower = article["title"].lower()
            content_lower = article["content"].lower()

            relevance = article["relevance_score"]
            for word in query.split():
                if word in title_lower:
                    relevance += 0.1
                if word in content_lower:
                    relevance += 0.05

            results.append({**article, "relevance_score": relevance})

        # Sort by relevance
        results.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Limit results
        results = results[:max_results]

        return {
            "found": len(results) > 0,
            "query": input_data.query,
            "category": category,
            "results": results,
            "total_found": len(results),
        }
