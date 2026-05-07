# claude-code-state

Classify [Claude Code](https://claude.com/claude-code)'s runtime state by parsing its terminal UI.

## What it tells you

A running Claude Code instance is always in exactly one of four states, defined by what you (the user) can do in each:

- **`Idle`** — Claude has finished its turn and is waiting for your next message. Type into the input box, press Enter, and a new turn starts immediately.
- **`Working`** — Claude is processing your previous message (thinking or running tools). You can keep typing, but Enter doesn't send until the current turn finishes; press `Esc` to interrupt instead.
- **`Blocked`** — A dialog has covered the input box (permission prompt, plan review, `AskUserQuestion`, etc.). You can't type free text — you have to pick one of Claude's offered choices (arrow keys + Enter, or a number digit).
- **`Dead`** — The host process has exited.

`parse_pane` classifies a captured pane into the first three states. It never returns `Dead` on its own — a frozen pane is indistinguishable from an idle one without probing the host process. If you need liveness, call `tmux display-message -p '#{pane_current_command}'` yourself and construct `Dead()` when it's not `claude` / `node`.

## How it classifies

The pane bottom always renders one of two shapes, and the package classifies based on which.

**Input chrome** (Claude alive, input box visible):

```text
✻ Fermenting… (14s · thinking)

──────────────────────────────────────────────────────────────────────────────────────────────────────────
❯ 
──────────────────────────────────────────────────────────────────────────────────────────────────────────
  ⏵⏵ bypass permissions on (shift+tab to cycle)
```

- **Working**: spinner row with `…` above chrome (e.g., `✻ Thinking… (16s · ↑ 827 tokens · thought for 7s)`)
- **Idle**: no spinner row above chrome, or spinner row without `…` (e.g., `✻ Worked for 2m 28s`)

**Blocking UI** (input chrome replaced):

```text
──────────────────────────────────────────────────────────────────────────────────────────────────────────
 Read file                                                                                                

  Read(/etc/passwd)                                                                                       

 Do you want to proceed?                                                                                  
 ❯ 1. Yes                                                                                                 
   2. Yes, allow reading from etc/ during this session                                                    
   3. No                                                                                                  
 Esc to cancel · Tab to amend      
```

Recognized `BlockedUI` variants: `PERMISSION_PROMPT`, `ASK_USER_QUESTION`, `EXIT_PLAN_MODE`, `BASH_APPROVAL`, `RESTORE_CHECKPOINT`, `SETTINGS`. The tool-preview block above a permission prompt is walked back into the extracted `content` so consumers can show what the user is being asked to approve.

The full decision tree:

```text
parse_pane(text)
│
├─ empty text?  ──────────────────────────────────→ None
│
├─ has input chrome? (────\n❯ in last 20 lines)
│
│   NO  ─→ try each UI_PATTERN in declaration order
│           ├─ match  ─→ Blocked(ui, content)
│           └─ none   ─→ None  [+ drift warning if it "looks like a prompt"]
│
│   YES ─→ scan up from chrome for spinner row (`· ✻ ✽ ✶ ✳ ✢`)
│           ├─ spinner with `…`           → Working(status_text=…)
│           └─ no spinner / completion    → Idle()
```

When `parse_pane` returns `None` (chrome absent and no UI matched), callers should fall back to their previous observation — returning `Idle()` would misreport "Claude is waiting" during a frame the package doesn't recognize.

## Install

```bash
# from a clone
uv pip install -e ~/ccmux/claude-code-state

# or directly from GitHub
uv tool install git+https://github.com/wuwenrui555/claude-code-state
```

Python ≥ 3.11. Zero runtime dependencies. The optional `claude_code_state.capture.tmux` helper shells out to the `tmux` CLI (no `libtmux` import) — install nothing extra to use it.

## Quick start

```python
from claude_code_state import parse_pane, Working, Idle, Blocked
from claude_code_state.capture import tmux

state = parse_pane(tmux.capture("my-session"))
match state:
    case Idle():
        print("waiting for you")
    case Working(status_text=text):
        print(f"busy: {text}")
    case Blocked(ui=which, content=body):
        print(f"blocked on {which}:\n{body}")
    case None:
        pass  # unclassifiable; keep the previous observation
```

What `parse_pane` actually returns:

```python
>>> parse_pane(idle_pane)
Idle()

>>> parse_pane(working_pane)
Working(status_text='Thinking… (16s · ↑ 827 tokens · thought for 7s)')

>>> parse_pane(permission_pane)
Blocked(
    ui=BlockedUI.PERMISSION_PROMPT,
    content='Read file\n/etc/passwd\n\nDo you want to proceed?\n❯ 1. Yes\n  2. No\nEsc to cancel',
)
```

If you don't use tmux, capture pane text any way you like (`screen -X hardcopy`, PTY scrape, WebSocket relay, fixture file…) and feed the string to `parse_pane`.

## Pattern drift

Claude Code's UI evolves. When the package sees a pane that *looks* like a prompt (`Esc to ...`, `❯ 1.`, etc.) but no `UI_PATTERN` matches, it logs a one-shot warning with a 12-char fingerprint so you can grep `drift.log` for the new sample, then update `UI_PATTERNS` (built-in or user-supplied). Dedup is per-process; each unique pane fingerprint warns at most once between restarts.

## User overrides

Set `CLAUDE_CODE_STATE_DIR` to enable user-pluggable patterns and a dedicated drift log. The package will:

- Load `<dir>/parser_config.json` at import time and merge user overrides into the built-ins. User UI patterns prepend to built-ins (try first); other constants take a union/dict-merge.
- Write pattern-drift warnings to `<dir>/drift.log` (created lazily on first warning).

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

When the env var is unset, the package runs purely on built-ins and drift warnings propagate through standard `logging` (logger name: `claude_code_state.drift`).

## License

MIT. See [LICENSE](LICENSE).
