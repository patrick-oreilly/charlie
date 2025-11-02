from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
from .tools import web_search_tool

model = LiteLlm(model='ollama_chat/gpt-oss:20b')

root_agent = Agent(
    model=model,
    name='root_agent',
    description='Information retrieval specialist.',
    instruction='Search for and retrieve relevant information from the web.',
    tools=[web_search_tool],  
)
