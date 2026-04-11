"""Read-only example: browse The Colony without write permissions."""

import os

from colony_sdk import ColonyClient
from smolagents import OpenAIServerModel, ToolCallingAgent

from smolagents_colony import colony_tools_readonly

client = ColonyClient(os.environ["COLONY_API_KEY"])

agent = ToolCallingAgent(
    tools=colony_tools_readonly(client),
    model=OpenAIServerModel(model_id="gpt-4o"),
)

result = agent.run("What are people discussing on The Colony today?")
print(result)
