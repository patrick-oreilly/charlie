import time
from textual.app import App, ComposeResult
from textual.timer import Timer
from textual.widgets import Input, RichLog
from rich.markdown import Markdown

# NOTE: These imports are assumed to be available in your execution environment
# They handle the core AI logic:
from .vectorstore import build_or_load_vectorstore
from .chain import make_code_chain


class CharlieApp(App):
    TITLE = "Charlie"
    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+d", "clear_log", "Clear"),
        ("escape", "focus_input", "Focus Input"),
    ]
    CSS = """
    Screen { 
        background: transparent;
        padding: 0;
    }
    
    RichLog { 
        height: 1fr; 
        background: transparent; 
        border: none; 
        overflow-y: auto; 
        scrollbar-gutter: stable;
        padding: 2 4;
        margin-bottom: 0;
    }
    
    Input { 
        dock: bottom;
        width: 1fr;
        height: 3;
        margin: 0 4 3 4;
        padding: 0 3;
        background: rgba(30, 30, 45, 0.6);
        color: rgba(255, 255, 255, 0.9);
        border: round rgba(100, 100, 150, 0.3);
    }
    
    Input:focus {
        border: round rgba(120, 140, 255, 0.6);
        background: rgba(40, 40, 60, 0.8);
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

    def compose(self) -> ComposeResult:
        self.chat_log = RichLog(highlight=True, markup=True, wrap=True)
        yield self.chat_log
        self.input = Input(placeholder="Ask me anything...")
        yield self.input

    async def on_mount(self) -> None:
        self.chat_log.write("[dim]⚡ Waking up Charlie…[/dim]\n")
        # NOTE: Using placeholder values for vectorstore and chain 
        # as the actual implementations are external to this file.
        self.vectorstore = build_or_load_vectorstore(self.project_path)
        self.chain, self.memory = make_code_chain(self.vectorstore)
        self.chat_log.write("[bold green]✓[/bold green] [dim]Ready[/dim]\n")

 
    def action_clear_log(self) -> None:
        self.chat_history = []
        self.chat_log.clear()
        self.chat_log.write("[dim]Chat cleared[/dim]\n")

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
        self.chat_history.append(("ai", "One sec."))
        self._redraw_chat()
        self._start_dots_animation()

        # 3. Stream the LLM
        response = ""
        try:
            # The async for loop is where the main thread is blocked waiting for the stream,
            # but the timer for the cursor blink continues in the background.
            async for chunk in self.chain.astream(query):
                # Assuming 'chunk' is the string content
                response += chunk
                self.chat_history[-1] = ("ai", response)

                # Throttle redraws to max 20 FPS (50ms intervals) for better performance
                current_time = time.time()
                if current_time - self._last_redraw_time >= 0.05:
                    self._redraw_chat()
                    self._last_redraw_time = current_time

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
        # Cycle through: "One sec.", "One sec..", "One sec..."
        self._dots_count = (self._dots_count % 3) + 1
        dots = "." * self._dots_count
        self.chat_history[-1] = ("ai", f"One sec{dots}")
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
                self.chat_log.write(f"\n[bold cyan]›[/bold cyan] {message}\n")
            else:
                # Render the AI response as Markdown
                md = Markdown(message, inline_code_theme="monokai")
                self.chat_log.write(md)