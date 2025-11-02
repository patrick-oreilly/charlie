import time
from textual.app import App, ComposeResult
from textual.timer import Timer
from textual.widgets import Input, RichLog
from rich.markdown import Markdown
from ..agents.meta import create_meta_agent


class MaxApp(App):
    TITLE = "Max"
    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+d", "clear_log", "Clear"),
        ("escape", "focus_input", "Focus Input"),
    ]
    CSS = """
    Screen {
        background: #0a0a0a;
        padding: 0;
        align: center middle;
    }

    RichLog {
        height: 1fr;
        background: #0a0a0a;
        color: #E5E1DA;
        border: none;
        overflow-x: hidden;
        overflow-y: auto;
        scrollbar-gutter: stable;
        padding: 2 3;
        margin: 2 2 0 2;
    }

    Input {
        dock: bottom;
        width: 100%;
        height: 3;
        margin: 0;
        padding: 0 3;
        background: #1a1a1a;
        color: #E5E1DA;
        border: round #B3C8CF;
    }

    Input:focus {
        border: round #89A8B2;
        background: #1a1a1a;
    }

    Input > .input--placeholder {
        color: #89A8B2;
    }
    """

    # ------------------------------------------------------------------ #
    #  INITIALISATION
    # ------------------------------------------------------------------ #
    def __init__(self, project_path: str):
        super().__init__()
        self.project_path = project_path
        self.chat_history: list[tuple[str, str]] = []
        # State variables for animated dots
        self._dots_count: int = 0
        self._dots_timer: Timer | None = None
        # Performance: throttle chat redraws to 20 FPS
        self._last_redraw_time: float = 0.0
        # Track if we're currently streaming to avoid flickering
        self._is_streaming: bool = False

    def compose(self) -> ComposeResult:
        self.chat_log = RichLog(
            highlight=True,
            markup=True,
            wrap=True,
            min_width=80
        )
        yield self.chat_log
        self.input = Input(placeholder="Ask anything...")
        yield self.input

    async def on_mount(self) -> None:
        self.chat_log.write("[#89A8B2]⚡ Waking up Max[/#89A8B2]\n")
        # NOTE: Using placeholder values for vectorstore and chain
        # as the actual implementations are external to this file.
        self.vectorstore = build_or_load_vectorstore(self.project_path)
        self.chain, self.memory = make_code_chain_with_tools(self.vectorstore)
        self.chat_log.write("[bold #89A8B2]✓[/bold #89A8B2] [#4a6168]Ready[/#4a6168]\n")

 
    def action_clear_log(self) -> None:
        self.chat_history = []
        self.chat_log.clear()
        self.chat_log.write("[#89A8B2]Chat cleared[/#89A8B2]\n")

    def action_focus_input(self) -> None:
        self.input.focus()

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

        # 3. Stream the LLM
        response = ""
        self._is_streaming = True
        try:
            # The async for loop is where the main thread is blocked waiting for the stream,
            # but the timer for the cursor blink continues in the background.
            async for chunk in self.chain.astream(query):
                # Stop dots animation on first chunk to prevent race condition
                if not response:
                    self._stop_dots_animation()

                # Assuming 'chunk' is the string content
                response += chunk
                self.chat_history[-1] = ("ai", response)

                # Update on every token for smooth streaming
                self._redraw_chat()

        except ConnectionError as e:
            response = "❌ **Connection Error**\n\nCould not reach Ollama. Is it running?\n\n```\nollama serve\n```"
            self.chat_history[-1] = ("ai", response)

        except TimeoutError as e:
            response = "❌ **Timeout**\n\nThe model took too long to respond. Try again or use a smaller model."
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


    # ------------------------------------------------------------------ #
    #  ANIMATED DOTS LOGIC
    # ------------------------------------------------------------------ #
    def _start_dots_animation(self) -> None:
        """Starts the animated dots timer."""
        if self._dots_timer is None:
            self._dots_count = 1
            # Animate every 0.5 seconds
            self._dots_timer = self.set_interval(0.5, self._animate_dots)

    def _animate_dots(self) -> None:
        """Called by the timer to cycle through dot animations."""

        self._dots_count = (self._dots_count % 3) + 1
        dots = "." * self._dots_count
        self.chat_history[-1] = ("ai", f"[#89A8B2]Thinking{dots}[/#89A8B2]")
        self._redraw_chat()

    def _stop_dots_animation(self) -> None:
        """Stops the animation timer."""
        if self._dots_timer is not None:
            self._dots_timer.stop()
            self._dots_timer = None
            self._dots_count = 0

    # ------------------------------------------------------------------ #
    #  REDRAW (Markdown rendering)
    # ------------------------------------------------------------------ #
    def _redraw_chat(self) -> None:
        self.chat_log.clear()
        for role, message in self.chat_history:
            if role == "user":
                self.chat_log.write(f"\n[bold #89A8B2]›[/bold #89A8B2] [#E5E1DA]{message}[/#E5E1DA]\n")
            else:
                # If it's a "Thinking" message, use Rich markup, otherwise use Markdown
                if message.startswith("[#89A8B2]Thinking"):
                    self.chat_log.write(message)
                else:
                    # Always render markdown, even during streaming
                    md = Markdown(message)
                    self.chat_log.write(md)