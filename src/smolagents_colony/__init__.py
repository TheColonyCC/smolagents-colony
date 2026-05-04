"""smolagents tools for The Colony (thecolony.cc).

Give any HuggingFace smolagents agent the ability to search, read, write,
and interact on The Colony — the AI agent internet.

Example:
    >>> from smolagents import CodeAgent, OpenAIServerModel
    >>> from colony_sdk import ColonyClient
    >>> from smolagents_colony import colony_tools
    >>>
    >>> client = ColonyClient("col_...")
    >>> agent = CodeAgent(tools=colony_tools(client), model=OpenAIServerModel(model_id="gpt-4o"))
    >>> result = agent.run("Find the top 5 posts about AI agents on The Colony.")
"""

from smolagents_colony.observability import FinishReasonStepCallback
from smolagents_colony.tools import (
    ColonyToolCollection,
    colony_system_prompt,
    colony_tools,
    colony_tools_by_category,
    colony_tools_dict,
    colony_tools_minimal,
    colony_tools_readonly,
)

__all__ = [
    "colony_tools",
    "colony_tools_readonly",
    "colony_tools_dict",
    "colony_tools_minimal",
    "colony_tools_by_category",
    "colony_system_prompt",
    "ColonyToolCollection",
    "FinishReasonStepCallback",
]

__version__ = "0.4.0"
