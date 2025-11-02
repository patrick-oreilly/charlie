import asyncio
import time
from textual.app import App, ComposeResult
from textual.timer import Timer
from textual.widgets import Input, RichLog
from rich.markdown import Markdown
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from google.genai.types import Content, Part
from google.genai import types

from ..agents.meta.agent import root_agent


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
        background: transparent;
        padding: 0;
        align: center middle;
    }

    RichLog {
        height: 1fr;
        background: transparent;
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
        margin: 0 2;
        padding: 0 3;
        background: rgba(26, 26, 26, 0.8);  
        color: #0a0a0a;
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

        self.user_id = "admin"

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

        self.session_service = InMemorySessionService()

        self.runner = Runner(
            agent=root_agent,
            app_name="Max",
            session_service=self.session_service
        )

        self.session = await self.runner.session_service.create_session(
            app_name="Max",
            user_id=self.user_id,
            state={"project_path": self.project_path},
        )

        self.session_id = self.session.id


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

        self.input.value = ""
        self.chat_history.append(("user", query))
        self._redraw_chat()

        self.chat_history.append(("ai", "Thinking."))
        self._redraw_chat()
        self._start_dots_animation()

        response = ""
        tool_calls = []
        current_agent: str | None = None
        self._is_streaming = True
        try:
            content = types.Content(
                role="user",
                parts=[types.Part(text=query)]
            )

            events = self.runner.run_async(
                user_id=self.user_id,
                session_id=self.session_id,
                new_message=content,
            )
            async for event in events:
                if event.author and event.author != current_agent:
                    current_agent = event.author
                    # Show agent transition (briefly)
                    if current_agent != "meta":
                        self._stop_dots_animation()
                        agent_name = current_agent.title()
                        self.chat_history[-1] = ("ai", f"[dim]→ {agent_name}[/dim]")
                        self._redraw_chat()
                        await asyncio.sleep(0.3)  # Brief pause
                        self.chat_history[-1] = ("ai", "")
                        self._start_dots_animation()

                if not response:
                    self._stop_dots_animation()

                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "tool_call") and part.tool_call:
                            tool_name = part.tool_call.name
                            tool_calls.append(tool_name)
                            tool_display = f"[dim italic]🔧 Using {tool_name}...[/dim italic]"
                            self.chat_history[-1] = ("ai", tool_display)
                            self._redraw_chat()
                            await asyncio.sleep(0.5)
                            
                        elif hasattr(part, "text") and part.text:
                            response += part.text
                            self.chat_history[-1] = ("ai", response)
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

