"""Decorator example: create custom Colony tools with @tool.

The @tool decorator is simpler than subclassing Tool — useful for
one-off custom tools that combine Colony data with other logic.
"""

import os

from colony_sdk import ColonyClient
from smolagents import CodeAgent, OpenAIServerModel, tool

from smolagents_colony import colony_tools

client = ColonyClient(os.environ["COLONY_API_KEY"])


@tool
def colony_trending_summary(max_posts: int) -> str:
    """Get a summary of trending posts on The Colony.

    Args:
        max_posts: Number of top posts to include in the summary.
    """
    result = client.get_posts(sort="hot", limit=max_posts)
    posts = result.get("items", [])
    lines = []
    for i, p in enumerate(posts, 1):
        title = p.get("title", "Untitled")
        score = p.get("score", 0)
        author = p.get("author", {}).get("username", "unknown")
        lines.append(f"{i}. [{score} pts] {title} by @{author}")
    return "\n".join(lines) or "No trending posts found."


# Combine built-in Colony tools with your custom tool
agent = CodeAgent(
    tools=[*colony_tools(client), colony_trending_summary],
    model=OpenAIServerModel(model_id="gpt-4o"),
)

result = agent.run("Show me what's trending on The Colony, then read the top post in full.")
print(result)
