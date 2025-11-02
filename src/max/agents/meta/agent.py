from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm 
from google.adk.tools import AgentTool

from . import prompt
from ..analyst.agent import root_agent as analyst_agent
from ..generator.agent import root_agent as generator_agent
from ..searcher.agent import root_agent as searcher_agent
# from ..executor.agent import root_agent as executor_agent

model = LiteLlm(model='ollama_chat/gpt-oss:20b')

root_agent = Agent(
    model=model,
    name='root_agent',
    description='Orchestrator that routes tasks to specialist agents.',
    instruction=prompt.MAX_AGENT_PROMPT,
    tools=[
        AgentTool(agent=analyst_agent),
        AgentTool(agent=generator_agent),
        AgentTool(agent=searcher_agent),
    ]
)
