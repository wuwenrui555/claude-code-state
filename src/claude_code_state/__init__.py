"""claude-code-state — classify Claude Code's runtime state from its terminal UI.

Public API
==========

State types::

    from claude_code_state import (
        ClaudeState, Working, Idle, Blocked, Dead, BlockedUI,
    )

Top-level classifier::

    from claude_code_state import parse_pane

    state = parse_pane(captured_pane_text)
    match state:
        case Working(status_text=text):
            ...
        case Idle():
            ...
        case Blocked(ui=which, content=body):
            ...
        case None:
            ...  # unclassifiable; previous observation likely still valid

Lower-level building blocks (call directly when ``parse_pane`` is too
coarse — e.g. when you want the status line independently of the
input-chrome check)::

    from claude_code_state import (
        has_input_chrome,
        parse_status_line,
        extract_interactive_content,
        extract_bash_output,
        parse_usage_output,
        InteractiveUIContent,
        UsageInfo,
    )

Optional capture helpers (one per terminal multiplexer)::

    from claude_code_state.capture import tmux

    state = parse_pane(tmux.capture("my-session"))

User overrides
==============

Set ``CLAUDE_CODE_STATE_DIR`` in the environment to point at a
directory containing ``parser_config.json``. The package will:

  * load that file at import time and merge user overrides into the
    built-in patterns (user patterns prepend to built-ins so they match
    first)
  * write pattern-drift warnings to ``<dir>/drift.log``

When unset, the package runs purely on built-ins and drift warnings
propagate through the standard ``logging`` hierarchy (logger name:
``claude_code_state.drift``).
"""

from __future__ import annotations

from .parser import (
    InteractiveUIContent,
    UsageInfo,
    extract_bash_output,
    extract_interactive_content,
    has_input_chrome,
    parse_pane,
    parse_status_line,
    parse_usage_output,
)
from .state import Blocked, BlockedUI, ClaudeState, Dead, Idle, Working

__all__ = [
    # State
    "ClaudeState",
    "Working",
    "Idle",
    "Blocked",
    "Dead",
    "BlockedUI",
    # Top-level classifier
    "parse_pane",
    # Building blocks
    "has_input_chrome",
    "parse_status_line",
    "extract_interactive_content",
    "extract_bash_output",
    "parse_usage_output",
    "InteractiveUIContent",
    "UsageInfo",
]

__version__ = "0.1.0"
