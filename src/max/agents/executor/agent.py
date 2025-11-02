from google.adk.agents.llm_agent import Agent
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.models.lite_llm import LiteLlm

model = LiteLlm(model='ollama_chat/gpt-oss:20b')

root_agent = Agent(
    model=model,
    name='root_agent',
    description='Code excecution specialist.',
    instruction="""Y
        You run code and tests safely.

        Safety rules:
        - Never run destructive commands
        - Explain what you'll run
        - Summarize results clearly
        - Suggest fixes for failures""",
        code_executor=BuiltInCodeExecutor(),
)
