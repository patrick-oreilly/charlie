# Google ADK Migration Guide for Max

## Overview

This guide shows how to migrate from **LangChain + Ollama** to **Google ADK + LiteLLM + Ollama**, maintaining local model execution while gaining ADK's superior agent framework.

**Key Insight:** Google ADK is model-agnostic and supports local models through LiteLLM!

---

## Current vs ADK Architecture

### Current Stack (LangChain)
```
User Input → LangChain Chain → Ollama (mistral-small:24b) → Response
              ↓
         Vectorstore RAG
         Custom Tools
         Memory
```

### New Stack (ADK + LiteLLM)
```
User Input → ADK Agent → LiteLLM → Ollama (mistral-small:24b) → Response
              ↓
         Custom Tool Functions
         Vectorstore RAG (as tool)
         Memory Integration
```

**Advantages:**
- ✅ **Still 100% local** - No cloud dependency!
- ✅ **Still free** - Uses your local Ollama
- ✅ **Better agent framework** - ADK's agent architecture
- ✅ **Cleaner code** - Simpler tool definitions
- ✅ **Model flexibility** - Easy to swap models/providers
- ✅ **Future-proof** - Can switch to Gemini/GPT later

---

## Installation

### 1. Install Dependencies

```bash
pip install google-adk litellm
```

### 2. Verify Ollama Running

```bash
# Check Ollama is running
ollama list

# Pull model if needed
ollama pull mistral-small:24b

# Verify tool support
ollama show mistral-small:24b
```

### 3. Environment Configuration

Create/update `.env`:

```bash
# For local Ollama (NO cloud keys needed!)
OLLAMA_API_BASE=http://localhost:11434

# Optional: Enable LiteLLM debug logging
# LITELLM_LOG=DEBUG
```

**Important:** Set `OLLAMA_API_BASE` env variable - LiteLLM relies on it!

---

## Migration Steps

### Step 1: Convert Tools to ADK Format

ADK tools are simple Python functions with clear docstrings and type hints.

**Create `src/max/adk_tools.py`:**

```python
"""ADK-compatible tools for Max agent."""

from typing import Dict, Any


def search_codebase(query: str) -> Dict[str, Any]:
    """
    Search the codebase using vector similarity to find relevant code.

    Args:
        query: The search query describing what code to find

    Returns:
        Dictionary with status, context (code snippets), and source file paths
    """
    from .vectorstore import build_or_load_vectorstore

    vectorstore = build_or_load_vectorstore(".")
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    results = retriever.get_relevant_documents(query)

    context = "\n\n".join([
        f"File: {doc.metadata.get('source', 'unknown')}\n{doc.page_content}"
        for doc in results
    ])

    sources = [doc.metadata.get("source", "unknown") for doc in results]

    return {
        "status": "success",
        "context": context,
        "sources": sources,
        "num_results": len(results)
    }


def search_internet(query: str) -> Dict[str, Any]:
    """
    Search the internet for current information.

    Args:
        query: The search query

    Returns:
        Dictionary with status and search results
    """
    from .tools import search_internet as _search_internet

    try:
        result = _search_internet(query)
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def get_current_time() -> Dict[str, str]:
    """
    Get the current date and time.

    Returns:
        Dictionary with current timestamp
    """
    from datetime import datetime

    now = datetime.now()
    return {
        "status": "success",
        "timestamp": now.isoformat(),
        "readable": now.strftime("%Y-%m-%d %H:%M:%S")
    }
```

**Key Differences from LangChain:**
- No `@tool` decorator needed
- Just plain Python functions
- Clear docstrings (ADK uses these for tool descriptions)
- Type hints for parameters
- Return dicts instead of strings (more structured)

---

### Step 2: Create ADK Agent

**Create `src/max/adk_agent.py`:**

```python
"""Google ADK agent configuration for Max."""

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from .adk_tools import search_codebase, search_internet, get_current_time
from .memory import get_memory


def create_max_agent(project_path: str):
    """
    Create Max ADK agent with local Ollama model via LiteLLM.

    Args:
        project_path: Path to the project directory

    Returns:
        Tuple of (agent, memory)
    """

    # Configure local Ollama model through LiteLLM
    # CRITICAL: Use 'ollama_chat' provider, NOT 'ollama'!
    local_model = LiteLlm(model="ollama_chat/mistral-small:24b")

    # Create ADK agent
    agent = Agent(
        name="max",
        model=local_model,
        description="Max is an expert software engineer who helps developers understand and work with their codebase.",
        instruction="""You are Max, a friendly and expert software engineer.

Your capabilities:
- Search and analyze codebases using semantic search
- Explain code in simple, clear terms
- Answer questions about software architecture and patterns
- Search the internet for current information when needed
- Reference specific file paths when discussing code

Communication style:
- Be concise and precise
- Use simple, clear language
- When showing code, always reference the file path
- Be friendly and conversational
- If you don't know something, say so

Always use the search_codebase tool to find relevant code before answering questions about the codebase.""",
        tools=[search_codebase, search_internet, get_current_time]
    )

    # Get memory instance
    memory = get_memory()

    return agent, memory
```

**Key Configuration:**

1. **Model Specification:**
   ```python
   LiteLlm(model="ollama_chat/mistral-small:24b")
   ```
   - Provider: `ollama_chat` (NOT `ollama` - important!)
   - Model: Your Ollama model name

2. **Instruction:** ADK uses this as the system prompt

3. **Tools:** List of Python functions (ADK auto-discovers signatures)

---

### Step 3: Update App Integration

**Modify `src/max/app.py`:**

```python
# At the top, change import:
# OLD:
# from .chain import make_code_chain_with_tools

# NEW:
from .adk_agent import create_max_agent


class MaxApp(App):
    # ... existing code ...

    async def on_mount(self) -> None:
        self.chat_log.write("[#89A8B2]⚡ Waking up Max[/#89A8B2]\n")

        # Create ADK agent instead of chain
        self.agent, self.memory = create_max_agent(self.project_path)

        self.chat_log.write("[bold #89A8B2]✓[/bold #89A8B2] [#4a6168]Ready[/#4a6168]\n")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if not query:
            return

        # 1. Show user line immediately
        self.input.value = ""
        self.chat_history.append(("user", query))
        self._redraw_chat()

        # 2. Placeholder + start animated dots
        self.chat_history.append(("ai", "Thinking."))
        self._redraw_chat()
        self._start_dots_animation()

        # 3. Stream the LLM with ADK
        response = ""
        self._is_streaming = True
        try:
            # ADK streaming - similar API to LangChain!
            async for chunk in self.agent.astream(query):
                # Stop dots animation on first chunk
                if not response:
                    self._stop_dots_animation()

                # Extract text from ADK chunk
                # ADK returns dict-like objects with content
                if hasattr(chunk, 'content'):
                    response += chunk.content
                elif isinstance(chunk, dict) and 'content' in chunk:
                    response += chunk['content']
                elif isinstance(chunk, str):
                    response += chunk

                self.chat_history[-1] = ("ai", response)
                self._redraw_chat()

        except ConnectionError as e:
            response = "❌ **Connection Error**\n\nCould not reach Ollama. Is it running?\n\n```\nollama serve\n```"
            self.chat_history[-1] = ("ai", response)

        except Exception as e:
            response = f"❌ **Error**\n\n{str(e)}\n\nCheck logs for details."
            self.chat_history[-1] = ("ai", response)

        finally:
            # 4. Stop animation & final render
            self._is_streaming = False
            self._stop_dots_animation()
            if not response.strip():
                response = "_No response received._"
            self.chat_history[-1] = ("ai", response)
            self._redraw_chat()

            # 5. Save conversation (only save successful responses)
            if response and not response.startswith("❌"):
                self.memory.save_context({"input": query}, {"output": response})
```

**Changes:**
- Import `create_max_agent` instead of `make_code_chain_with_tools`
- Call `self.agent.astream(query)` instead of `self.chain.astream(query)`
- Extract content from chunk (ADK format slightly different)
- Everything else stays the same!

---

## Running the Migrated App

### 1. Start Ollama

```bash
ollama serve
```

### 2. Set Environment Variable

```bash
export OLLAMA_API_BASE=http://localhost:11434
```

### 3. Run Max

```bash
cd /Users/patrickoreilly/Desktop/agents/max
source .venv/bin/activate  # or your venv path
max
```

---

## Testing the Migration

### Verify Tool Calling

Ask Max to search the codebase:
```
› search for the main app class
```

Expected: Max should use `search_codebase` tool and return results with file paths.

### Verify Internet Search

```
› what's the latest version of Python?
```

Expected: Max should use `search_internet` tool.

### Verify Streaming

Watch for smooth token-by-token streaming with markdown rendering.

---

## Troubleshooting

### Issue: "Connection Error"

**Cause:** Ollama not running or wrong API base.

**Fix:**
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Verify env var is set
echo $OLLAMA_API_BASE

# Set it if missing
export OLLAMA_API_BASE=http://localhost:11434
```

### Issue: "Infinite tool call loops"

**Cause:** Using `ollama` provider instead of `ollama_chat`.

**Fix:** Change to:
```python
LiteLlm(model="ollama_chat/mistral-small:24b")
```

### Issue: Tools not working

**Cause:** Model doesn't support tool calling.

**Fix:** Check model capabilities:
```bash
ollama show mistral-small:24b
```

Look for function calling support. If not supported, switch to a compatible model.

### Issue: UnicodeDecodeError on Windows

**Cause:** LiteLLM cache encoding issue.

**Fix:**
```bash
set PYTHONUTF8=1
```

---

## Advanced Configuration

### Switch Between Local & Cloud Models

Create a config file:

```python
# config.py
MODELS = {
    "local": LiteLlm(model="ollama_chat/mistral-small:24b"),
    "gemini": "gemini-2.0-flash-exp",
    "gpt4": LiteLlm(model="gpt-4o"),
}

ACTIVE_MODEL = "local"  # Change this to switch models
```

### Enable Debug Logging

```python
import litellm
litellm._turn_on_debug()
```

### Use Different Ollama Models

```python
# Try different models from Ollama library
LiteLlm(model="ollama_chat/llama3.1:70b")
LiteLlm(model="ollama_chat/qwen2.5:32b")
LiteLlm(model="ollama_chat/gemma2:27b")
```

---

## Comparison: Before vs After

| Feature | LangChain | ADK + LiteLLM |
|---------|-----------|---------------|
| **Model** | Ollama (local) | Ollama (local) ✅ |
| **Cost** | Free | Free ✅ |
| **Privacy** | Local | Local ✅ |
| **Framework** | LangChain LCEL | Google ADK |
| **Code Clarity** | Verbose chains | Clean Agent API |
| **Tool Definition** | `@tool` decorator | Plain functions |
| **Streaming** | `astream()` | `astream()` ✅ |
| **Model Switching** | Code changes | Config change |
| **Future Options** | Limited | Any LiteLLM model |

---

## Migration Checklist

- [ ] Install `google-adk` and `litellm`
- [ ] Verify Ollama is running (`ollama serve`)
- [ ] Set `OLLAMA_API_BASE` environment variable
- [ ] Create `adk_tools.py` with tool functions
- [ ] Create `adk_agent.py` with agent configuration
- [ ] Update `app.py` imports and agent creation
- [ ] Update streaming chunk extraction
- [ ] Test tool calling functionality
- [ ] Test streaming performance
- [ ] Verify memory/history still works

---

## Next Steps

### Option 1: Keep It Local
Continue using Ollama for privacy and cost savings.

### Option 2: Hybrid Approach
Use local models for development, cloud models for production:

```python
import os

if os.getenv("ENV") == "production":
    model = "gemini-2.0-flash-exp"  # Cloud
else:
    model = LiteLlm(model="ollama_chat/mistral-small:24b")  # Local
```

### Option 3: Multi-Agent Architecture
Leverage ADK's multi-agent capabilities:
- Code analysis agent (local model)
- Web search agent (cloud model with tools)
- Planning agent (coordinates others)

---

## Resources

- **ADK Documentation:** https://google.github.io/adk-docs/
- **LiteLLM Integration:** https://docs.litellm.ai/docs/tutorials/google_adk
- **Ollama Models:** https://ollama.com/library
- **ADK GitHub:** https://github.com/google/adk-python

---

## Summary

✅ **Zero vendor lock-in** - Still using local Ollama
✅ **Better framework** - ADK's agent architecture
✅ **Future flexibility** - Easy to switch models later
✅ **Same privacy** - Everything stays local
✅ **Same cost** - Still free!

The migration gives you ADK's superior agent framework while maintaining full control over your models and data.
