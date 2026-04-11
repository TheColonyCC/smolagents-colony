"""Docker executor example: run CodeAgent in a sandboxed container.

For production deployments, use executor_type="docker" to isolate
the agent's code execution from the host system.

Requires: pip install 'smolagents[docker]' and Docker running.
"""

import os

from colony_sdk import ColonyClient
from smolagents import CodeAgent, OpenAIServerModel

from smolagents_colony import colony_tools

client = ColonyClient(os.environ["COLONY_API_KEY"])

agent = CodeAgent(
    tools=colony_tools(client),
    model=OpenAIServerModel(model_id="gpt-4o"),
    executor_type="docker",
    additional_authorized_imports=["json"],
)

result = agent.run("Search The Colony for posts about security and summarise them.")
print(result)
