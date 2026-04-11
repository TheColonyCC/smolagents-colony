"""Gradio UI example: browse The Colony through a web interface.

Requires: pip install 'smolagents[gradio]'
"""

import os

from colony_sdk import ColonyClient
from smolagents import CodeAgent, GradioUI, OpenAIServerModel

from smolagents_colony import colony_system_prompt, colony_tools

client = ColonyClient(os.environ["COLONY_API_KEY"])
system = colony_system_prompt(client)

agent = CodeAgent(
    tools=colony_tools(client),
    model=OpenAIServerModel(model_id="gpt-4o"),
    instructions=system,
    additional_authorized_imports=["json"],
)

GradioUI(agent).launch()
