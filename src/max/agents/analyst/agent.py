from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm

from . import prompt
from .tools import search_codebase

model = LiteLlm(model='ollama_chat/gpt-oss:20b')
root_agent = Agent(
    model=model,
    name='root_agent',
    description='Code analyst specialist.',
    instruction=prompt.ANALYST_PROMPT,
    tools=[search_codebase],
)
