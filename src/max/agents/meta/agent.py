from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm 
from google.adk.tools import google_search
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai.preview import rag

from . import prompt

model = LiteLlm(model_name='ollama_chat/gpt-oss:20b')

root_agent = Agent(
    model=model,
    name='root_agent',
    description='A helpful assistant for user questions.',
    instruction=prompt.MAX_AGENT_PROMPT,
    tools=[google_search],
    ),
