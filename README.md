# claude-code-state

Classify [Claude Code](https://claude.com/claude-code)'s runtime state
by parsing its terminal UI.

## What it does

Given a captured terminal pane (the visible text of Claude Code's
window), classify the running instance into one of:

- **Working** — actively processing. Carries the running status text
  (e.g. `Thinking… (16s · ↑ 827 tokens · thought for 7s)`).
- **Idle** — input box rendered, no spinner. Waiting for the user.
- **Blocked** — input box has been replaced by a blocking UI
  (permission prompt, AskUserQuestion, ExitPlanMode, /config, etc.).
  Carries which UI variant matched and the extracted content (with the
  tool preview above the prompt walked back so consumers can see what
  the user is being asked to approve).

The package also exposes lower-level building blocks: chrome
detection, raw status-line extraction, and interactive-UI extraction.

## Why a package

This logic was extracted from
[ccmux-backend](https://github.com/wuwenrui555/ccmux-backend) where it
drives the Telegram frontend's status updates. Anyone building a
Claude Code observer (status indicator, dashboard, smartwatch buzz,
LED lamp, multi-window monitor) needs the same classification. Each
UI pattern represents a debugging session against Claude Code's
terminal renderer; sharing the regex set means nobody has to redo the
work.

## Architecture

The package is split into two concerns:

```
claude_code_state/         ← parser core (zero deps, terminal-mux agnostic)
└── capture/               ← optional helpers, one per terminal multiplexer
    └── tmux.py            ← `tmux capture-pane` wrapper
```

The parser **only sees text**. Capturing the screen is a separate
problem with implementation choices (tmux / GNU screen / zellij /
PTY / WebSocket-to-remote). The included `capture` submodule covers
tmux. For anything else, capture however you like and feed the
string to `parse_pane`.

## Install

```bash
uv pip install -e .         # from a clone
# or, after publishing:
pip install claude-code-state
```

Python ≥ 3.11. Zero runtime dependencies.

## Quick start

```python
from claude_code_state import parse_pane
from claude_code_state.capture import tmux

state = parse_pane(tmux.capture("my-session"))
print(state)
```

## Usage

```python
from claude_code_state import parse_pane, Working, Idle, Blocked

# Capture however you want — here, raw subprocess:
import subprocess
pane_text = subprocess.check_output(
    ["tmux", "capture-pane", "-p", "-J", "-t", "my-session"], text=True,
)

state = parse_pane(pane_text)
match state:
    case Working(status_text=text):
        print(f"Claude is busy: {text}")
    case Idle():
        print("Claude is waiting for you")
    case Blocked(ui=which, content=body):
        print(f"Claude is blocked on {which}:\n{body}")
    case None:
        pass  # Unclassifiable — keep the previous observation
```

For finer-grained access (e.g. you want to handle the chrome-check
yourself):

```python
from claude_code_state import (
    has_input_chrome, parse_status_line, extract_interactive_content,
)

lines = pane_text.strip().split("\n")
if has_input_chrome(lines):
    status = parse_status_line(pane_text)  # str | None
    ...
else:
    ui = extract_interactive_content(pane_text)  # InteractiveUIContent | None
    ...
```

## How it classifies (in one paragraph)

The pane bottom always renders one of two shapes. **Input chrome**
(`────\n❯\n────\nstatus`) means Claude is alive and the input box is
showing — Working if a spinner with `…` sits above the chrome,
otherwise Idle. **No input chrome** means a blocking UI replaced it;
match against `UI_PATTERNS` (permission prompt, AskUserQuestion,
ExitPlanMode, BashApproval, RestoreCheckpoint, Settings) to extract
the content. Completion summaries (`✻ Worked for 56s`) are
deliberately filtered out of the Working signal — they share the
spinner prefix but lack the `…`.

## Why no Dead state

`parse_pane` never returns `Dead`. A pane alone cannot distinguish a
running-but-frozen Claude from a dead one — the last frame stays on
screen indistinguishable from Idle. Detect Dead by probing the host
process (`tmux display-message -p '#{pane_current_command}'` on the
target window, then check it's not in `{"claude", "node"}`) and
construct `Dead()` yourself.

## User overrides

Set `CLAUDE_CODE_STATE_DIR` in the environment to enable
configuration. The package will:

- Load `<dir>/parser_config.json` at import time and merge user
  overrides into the built-ins. User UI patterns prepend to built-ins
  (try first); other constants take a union/dict-merge.
- Write pattern-drift warnings to `<dir>/drift.log` (created lazily on
  first warning).

Example `parser_config.json`:

```json
{
  "$schema_version": 1,
  "ui_patterns": [
    {
      "name": "permission_prompt",
      "top": ["^\\s*Confirm action"],
      "bottom": ["^\\s*Esc to dismiss"],
      "min_gap": 2
    }
  ],
  "status_spinners": ["✦"]
}
```

When `CLAUDE_CODE_STATE_DIR` is unset, the package runs purely on
built-ins and drift warnings propagate through the standard
`logging` hierarchy (logger name: `claude_code_state.drift`).

## Pattern drift

Claude Code's terminal UI evolves. When the package sees a pane that
*looks* like a prompt (`Esc to ...`, `❯ 1.`, etc.) but no UI pattern
matches, it logs a one-shot warning with a 12-char fingerprint so you
can grep `drift.log` for the new sample, then update `UI_PATTERNS`
(built-in or user-supplied). Dedup is per-process; each unique pane
fingerprint warns at most once between restarts.

## License

MIT. See [LICENSE](LICENSE).
