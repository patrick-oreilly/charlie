""" TUI style for MAX"""

# Color palette
BG_DARK = "#0D1117"
PRIMARY = "#4285F4"
PRIMARY_LIGHT = "#8AB4F8"
BG_MEDIUM = "#1A1F2E"
TEXT = "#C9D1D9"
ACCENT = "#669DF6"

MAX_STYLE = f"""
    Screen {{
        background: {BG_DARK};
        padding: 0;
    }}

    RichLog {{
        height: 1fr;
        background: {BG_DARK};
        color: {TEXT};
        border: round {ACCENT};
        overflow-x: hidden;
        overflow-y: auto;
        padding: 2 3;
        margin: 2 2 0 2;
    }}

    Input {{
        dock: bottom;
        width: 100%;
        height: 3;
        margin: 0 2;
        padding: 0 3;
        background: {BG_DARK};
        color: {TEXT};
        border: round {PRIMARY};
    }}

    Input:focus {{
        border: round {PRIMARY_LIGHT};
        background: {BG_DARK};
    }}

    Input > .input--placeholder {{
        color: {ACCENT};
    }}
"""

MAX_BANNER = f"""
[bold {PRIMARY}]
 ███╗   ███╗ █████╗ ██╗  ██╗
 ████╗ ████║██╔══██╗╚██╗██╔╝
 ██╔████╔██║███████║ ╚███╔╝
 ██║╚██╔╝██║██╔══██║ ██╔██╗
 ██║ ╚═╝ ██║██║  ██║██╔╝ ██╗
 ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝
[/bold {PRIMARY}]
[dim]Max v1[/dim]
        """


