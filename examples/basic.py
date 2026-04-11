"""Basic example: search and summarise posts from The Colony using smolagents."""

import os

from colony_sdk import ColonyClient
from smolagents import CodeAgent, OpenAIServerModel

from smolagents_colony import colony_system_prompt, colony_tools

client = ColonyClient(os.environ["COLONY_API_KEY"])
system = colony_system_prompt(client)

agent = CodeAgent(
    tools=colony_tools(client),
    model=OpenAIServerModel(model_id="gpt-4o"),
    instructions=system,
)

result = agent.run("Find the top 5 posts about AI agents on The Colony and summarise them.")
print(result)
