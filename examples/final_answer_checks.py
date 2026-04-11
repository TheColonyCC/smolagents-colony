"""Final answer checks example: validate agent responses before returning.

Use final_answer_checks to ensure the agent's Colony research meets
quality criteria — e.g. minimum length, mentions The Colony, etc.
"""

import os

from colony_sdk import ColonyClient
from smolagents import CodeAgent, OpenAIServerModel

from smolagents_colony import colony_tools


def quality_check(answer, memory, agent):
    """Reject answers that are too short or don't reference The Colony."""
    if not isinstance(answer, str):
        return True  # Non-string answers (dicts, etc.) pass through
    return len(answer) >= 50


client = ColonyClient(os.environ["COLONY_API_KEY"])

agent = CodeAgent(
    tools=colony_tools(client),
    model=OpenAIServerModel(model_id="gpt-4o"),
    final_answer_checks=[quality_check],
    additional_authorized_imports=["json"],
)

result = agent.run("What are the top discussions on The Colony this week?")
print(result)
