"""Optional screen-capture helpers for feeding ``parse_pane``.

These submodules wrap the common terminal multiplexers so callers can
get a pane snapshot in one line. Every helper is opt-in: nothing in
this subpackage is imported by ``claude_code_state`` itself, so the
core parser stays zero-dependency and terminal-mux-agnostic.

Available submodules:
  - ``tmux`` — capture from a tmux pane via the ``tmux`` CLI.

If your environment isn't covered, capture however you like and feed
the resulting string to ``parse_pane``. The parser only needs text;
where the text comes from is your problem.
"""
