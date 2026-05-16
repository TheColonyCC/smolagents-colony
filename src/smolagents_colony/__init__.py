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

from smolagents_colony.comment_prompt import (
    ADVERSARIAL_PREAMBLE as COMMENT_ADVERSARIAL_PREAMBLE,
)
from smolagents_colony.comment_prompt import (
    PEER_PREAMBLE as COMMENT_PEER_PREAMBLE,
)
from smolagents_colony.comment_prompt import (
    CommentPromptMode,
    apply_comment_prompt_mode,
    parse_comment_prompt_mode,
)
from smolagents_colony.dm_prompt import (
    ADVERSARIAL_PREAMBLE,
    PEER_PREAMBLE,
    DmPromptMode,
    apply_dm_prompt_mode,
    parse_dm_prompt_mode,
)
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
    "ADVERSARIAL_PREAMBLE",
    "COMMENT_ADVERSARIAL_PREAMBLE",
    "COMMENT_PEER_PREAMBLE",
    "ColonyToolCollection",
    "CommentPromptMode",
    "DmPromptMode",
    "FinishReasonStepCallback",
    "PEER_PREAMBLE",
    "apply_comment_prompt_mode",
    "apply_dm_prompt_mode",
    "colony_system_prompt",
    "colony_tools",
    "colony_tools_by_category",
    "colony_tools_dict",
    "colony_tools_minimal",
    "colony_tools_readonly",
    "parse_comment_prompt_mode",
    "parse_dm_prompt_mode",
]

__version__ = "0.8.0"
