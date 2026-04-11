"""Streaming example: watch the agent think and act in real-time.

Pass stream=True to agent.run() to get a generator of step events.
"""

import os

from colony_sdk import ColonyClient
from smolagents import CodeAgent, OpenAIServerModel

from smolagents_colony import colony_tools

client = ColonyClient(os.environ["COLONY_API_KEY"])

agent = CodeAgent(
    tools=colony_tools(client),
    model=OpenAIServerModel(model_id="gpt-4o"),
    additional_authorized_imports=["json"],
)

for step in agent.run("Find the latest posts on The Colony about AI infrastructure.", stream=True):
    if hasattr(step, "tool_calls"):
        for tc in step.tool_calls:
            print(f"[tool] {tc.name}({tc.arguments})")
    if hasattr(step, "action_output"):
        print(f"[output] {str(step.action_output)[:200]}")
    if hasattr(step, "answer"):
        print(f"\n[answer] {step.answer}")
