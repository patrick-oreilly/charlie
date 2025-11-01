from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, RichLog
from rich.markdown import Markdown

from .vectorstore import build_or_load_vectorstore
from .chain import make_code_chain


class CharlieApp(App):
    TITLE = "Charlie – Local assistant for Your Codebase"
    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+d", "clear_log", "Clear"),
        ("escape", "focus_input", "Focus Input"),
    ]
    CSS = """
    Screen { background: transparent; }
    RichLog { height: 1fr; background: transparent; border: none; overflow-y: auto; scrollbar-gutter: stable; }
    Input { dock: bottom; border: tall $primary; }
    """

    # ------------------------------------------------------------------ #
    #  INITIALISATION
    # ------------------------------------------------------------------ #
    def __init__(self, project_path: str):
        super().__init__()
        self.project_path = project_path
        self.chat_history: list[tuple[str, str]] = []

    def compose(self) -> ComposeResult:
        yield Header()
        self.chat_log = RichLog(highlight=True, markup=True, wrap=True)
        yield self.chat_log
        self.input = Input(placeholder="Ask about your code…")
        yield self.input
        yield Footer()

    async def on_mount(self) -> None:
        self.chat_log.write("[bold magenta]Initializing Charlie…[/bold magenta]\n")
        self.vectorstore = build_or_load_vectorstore(self.project_path)
        self.chain, self.memory = make_code_chain(self.vectorstore)
        self.chat_log.write("[bold green]Ready! Ask about your codebase.[/bold green]\n")

    # ------------------------------------------------------------------ #
    #  ACTIONS
    # ------------------------------------------------------------------ #
    def action_clear_log(self) -> None:
        self.chat_history = []
        self.chat_log.clear()
        self.chat_log.write("[bold green]Chat cleared.[/bold green]\n")

    def action_focus_input(self) -> None:
        self.input.focus()

    # ------------------------------------------------------------------ #
    #  INPUT → STREAMING → MARKDOWN + BLINKING CURSOR
    # ------------------------------------------------------------------ #
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle the user pressing <Enter> in the Input widget."""
        query = event.value.strip()
        if not query:
            return

        # 1. Show user line immediately
        self.input.value = ""
        self.chat_history.append(("user", query))
        self._redraw_chat()

        # 2. Placeholder + start blinking
        self.chat_history.append(("ai", "_Thinking…_"))
        self._redraw_chat()
        self._cursor_visible = True
        self._start_cursor_blink()

        # 3. Stream the LLM
        response = ""
        try:
            async for chunk in self.chain.astream(query):
                response += chunk
                self.chat_history[-1] = ("ai", response)
                self._redraw_chat()
        finally:
            # 4. Stop blinking & final render
            self._stop_cursor_blink()
            if not response.strip():
                response = "_No response received._"
            self.chat_history[-1] = ("ai", response)
            self._redraw_chat()

            # 5. Save conversation
            self.memory.save_context({"input": query}, {"output": response})

    # ------------------------------------------------------------------ #
    #  CURSOR BLINK HELPERS
    # ------------------------------------------------------------------ #
    def _start_cursor_blink(self) -> None:
        self._cursor_timer = self.set_interval(0.5, self._toggle_cursor)

    def _stop_cursor_blink(self) -> None:
        if hasattr(self, "_cursor_timer"):
            self._cursor_timer.stop()
            self._cursor_visible = False

    def _toggle_cursor(self) -> None:
        self._cursor_visible = not self._cursor_visible
        self._redraw_chat()

    # ------------------------------------------------------------------ #
    #  REDRAW (Markdown + optional cursor)
    # ------------------------------------------------------------------ #
    def _redraw_chat(self) -> None:
        self.chat_log.clear()
        for role, message in self.chat_history:
            if role == "user":
                self.chat_log.write(f"[bold cyan]You:[/bold cyan] {message}\n")
            else:
                md = Markdown(message, inline_code_theme="monokai")
                self.chat_log.write(md)

                # show blinking cursor **only** on the very last AI entry
                if (role, message) == self.chat_history[-1]:
                    cursor = " █" if getattr(self, "_cursor_visible", False) else "  "
                    self.chat_log.write(cursor)