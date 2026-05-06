"""Capture a tmux pane's visible text via the ``tmux`` CLI.

Shells out to the ``tmux`` binary; no Python dependency on ``libtmux``.
The chosen flags match what ``parse_pane`` expects:

  * ``-p`` — print to stdout
  * ``-J`` — preserve trailing whitespace and join wrapped lines.
    Critical: without ``-J``, long ``────`` chrome separators may be
    split across multiple lines and ``parse_pane`` won't recognize the
    chrome sandwich.

Example::

    from claude_code_state import parse_pane
    from claude_code_state.capture import tmux

    state = parse_pane(tmux.capture("my-session"))
"""

from __future__ import annotations

import subprocess


class TmuxNotInstalledError(RuntimeError):
    """Raised when the ``tmux`` binary is not on PATH."""


def capture(target: str) -> str:
    """Capture a tmux pane's visible content as a multi-line string.

    Args:
        target: A tmux target string. Any of:

          * session name: ``"my-session"`` (active window's active pane)
          * session:window: ``"my-session:0"`` (active pane of window 0)
          * session:window.pane: ``"my-session:0.1"``
          * pane id: ``"%5"``

    Returns:
        The pane's visible content. Empty string if the target is not
        found (e.g. session doesn't exist) — ``parse_pane`` returns
        ``None`` for empty input, which callers can treat as a benign
        skip.

    Raises:
        TmuxNotInstalledError: when the ``tmux`` binary is not on PATH.
    """
    try:
        result = subprocess.run(
            ["tmux", "capture-pane", "-p", "-J", "-t", target],
            capture_output=True,
            text=True,
            check=False,  # tmux returns 1 for invalid target; treat as empty
        )
    except FileNotFoundError as e:
        raise TmuxNotInstalledError(
            "tmux binary not found on PATH. Install tmux to use this helper, "
            "or capture pane text yourself and feed it to parse_pane()."
        ) from e
    if result.returncode != 0:
        return ""
    return result.stdout
