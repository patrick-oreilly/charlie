from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
from .tools import generate_code, refactor_code

model = LiteLlm(model='ollama_chat/gpt-oss:20b')

root_agent = Agent(
    model=model,
    name='root_agent',
    description='Code generation specialist.',
    instruction="""You write and refactor code.

        Best practices:
        - Search existing code to match project style
        - Include type hints and docstrings
        - Follow project conventions
        - Write clean, idiomatic code""",
    tools=[generate_code, refactor_code],
    )
