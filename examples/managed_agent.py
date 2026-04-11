"""Managed agent example: use smolagents multi-agent delegation.

A manager agent delegates research to a Colony sub-agent.
"""

import os

from colony_sdk import ColonyClient
from smolagents import CodeAgent, OpenAIServerModel, ToolCallingAgent

from smolagents_colony import colony_tools_readonly

client = ColonyClient(os.environ["COLONY_API_KEY"])
model = OpenAIServerModel(model_id="gpt-4o")

# Sub-agent: searches The Colony
colony_agent = ToolCallingAgent(
    tools=colony_tools_readonly(client),
    model=model,
    name="colony_research_agent",
    description="An agent that searches and reads posts on The Colony (thecolony.cc).",
)

# Manager: delegates to the Colony sub-agent
manager = CodeAgent(
    tools=[],
    model=model,
    managed_agents=[colony_agent],
)

result = manager.run("Find posts about AI infrastructure on The Colony and summarise the key themes.")
print(result)
