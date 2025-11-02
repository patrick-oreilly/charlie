# Max

AI terminal teammate - Local, fast and private.

## What is Max?

Max is a friendly terminal assistant built with Google ADK . 

## Architecture
- Max (Orchestrator agent)
- Analyst - understands code flow and logic
- Excecutor - Runs code, tests and shell commands
- Searcher - Uses a web_search tool to search the web


## Features

- **Local AI**: Runs entirely on your machine using Ollama
- **Project-aware**: Index and query your codebase
- **TUI Interface**: Clean terminal UI built with Textual
- **Multi-agent**: Powered by Google ADK agent framework
- **Vector Search**: ChromaDB integration for semantic code search

## Requirements

- Python 3.10+
- [Ollama](https://ollama.ai/) running locally

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd max

# Install dependencies
pip install -e .
```

## Usage

Launch Max in any project directory:

```bash
max .
```

Or specify a path:

```bash
max /path/to/your/project
```

### Keyboard Shortcuts

- `Ctrl+C` / `Ctrl+Q` - Quit
- `Ctrl+D` - Clear chat history
- `Esc` - Focus input

## Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run formatting and linting:

```bash
black src/
ruff check src/
mypy src/
```

## Architecture

- **CLI**: Typer-based command-line interface
- **TUI**: Textual-based terminal UI
- **Agents**: Google ADK agent system
- **Vector Store**: ChromaDB for code indexing
- **LLM**: Ollama + LangChain integration
