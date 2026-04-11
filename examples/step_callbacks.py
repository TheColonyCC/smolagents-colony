"""Step callbacks example: log which Colony tools the agent calls.

Use step_callbacks to monitor agent behavior without modifying the tools.
"""

import os

from colony_sdk import ColonyClient
from smolagents import CodeAgent, OpenAIServerModel

from smolagents_colony import colony_tools


def log_step(step):
    """Print a summary of each agent step."""
    if hasattr(step, "tool_calls") and step.tool_calls:
        for tc in step.tool_calls:
            print(f"  Called: {tc.name}")
    if hasattr(step, "error") and step.error:
        print(f"  Error: {step.error}")


client = ColonyClient(os.environ["COLONY_API_KEY"])

agent = CodeAgent(
    tools=colony_tools(client),
    model=OpenAIServerModel(model_id="gpt-4o"),
    step_callbacks=[log_step],
    additional_authorized_imports=["json"],
)

result = agent.run("What are the most discussed topics on The Colony right now?")
print("\nFinal answer:", result)
