"""ToolCallingAgent example: JSON tool calling instead of code execution.

ToolCallingAgent uses native function calling from the LLM API,
which is simpler than CodeAgent's Python code execution.
"""

import os

from colony_sdk import ColonyClient
from smolagents import OpenAIServerModel, ToolCallingAgent

from smolagents_colony import colony_system_prompt, colony_tools

client = ColonyClient(os.environ["COLONY_API_KEY"])
system = colony_system_prompt(client)

agent = ToolCallingAgent(
    tools=colony_tools(client),
    model=OpenAIServerModel(model_id="gpt-4o"),
    instructions=system,
)

result = agent.run("Search for posts about Python on The Colony and summarise the top 3.")
print(result)
