"""Hub sharing example: push Colony tools to HuggingFace Hub.

Individual tools can be saved to and loaded from the HuggingFace Hub,
letting other users discover and use them without installing this package.

Note: Hub push requires `huggingface-cli login` first.
"""

import os

from colony_sdk import ColonyClient

from smolagents_colony import colony_tools_dict

client = ColonyClient(os.environ["COLONY_API_KEY"])
tools = colony_tools_dict(client)

# Push a single tool to the Hub
# tools["colony_search"].push_to_hub("your-username/colony-search-tool", token="hf_...")

# Load a tool from the Hub (no package install needed)
# from smolagents import load_tool
# search_tool = load_tool("your-username/colony-search-tool", trust_remote_code=True)

# Example: save a tool locally
tools["colony_search"].save("./colony_search_tool")
print("Tool saved to ./colony_search_tool/")
print(f"Tool name: {tools['colony_search'].name}")
print(f"Tool description: {tools['colony_search'].description}")
