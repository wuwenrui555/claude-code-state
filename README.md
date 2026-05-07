# claude-code-state

Classify the runtime state of [Claude Code](https://claude.com/claude-code) (CC) by parsing its terminal UI.

## About Claude-Code-State

### 1. What it tells you

A running CC instance is always in exactly one of four states, defined by what you (the user) can do in each:

- **`Idle`** — CC has finished its turn and is waiting for your next message. Type into the input box, press Enter, and a new turn starts immediately.
- **`Working`** — CC is processing your previous message (thinking or running tools). You can keep typing, but Enter doesn't send until the current turn finishes; press `Esc` to interrupt instead.
- **`Blocked`** — A dialog has covered the input box (permission prompt, plan review, `AskUserQuestion`, etc.). You can't type free text — you have to pick one of CC's offered choices (arrow keys + Enter, or a number digit).
- **`Dead`** — The host process has exited.

### 2. How it classifies

The pane bottom always renders one of two shapes, and the package classifies based on which. The "chrome" is the input-row sandwich (`────` + `❯` + `────` + status bar) that sits at the bottom while CC is alive.

**Input chrome** (CC alive, input box visible):

```text
✻ Fermenting… (14s · thinking)

────────────────────
❯ 
────────────────────
  ⏵⏵ bypass permissions on (shift+tab to cycle)
```

- **Working**: spinner row with `…` above chrome (e.g., `✻ Thinking… (16s · ↑ 827 tokens · thought for 7s)`)
- **Idle**: no spinner row above chrome, or spinner row without `…` (e.g., `✻ Worked for 2m 28s`)

**Blocking UI** (input chrome replaced):

```text
────────────────────
 Read file                                                                                                

  Read(/etc/passwd)                                                                                       

 Do you want to proceed?                                                                                  
 ❯ 1. Yes                                                                                                 
   2. Yes, allow reading from etc/ during this session                                                    
   3. No                                                                                                  
 Esc to cancel · Tab to amend      
```

- **Blocked**: matches a known UI pattern

### 3. Decision tree

```text
parse_pane(text)
│
├─ empty text?                           ─→ None
│
└─ has input chrome? (────\n❯ in last 20 lines)
   │
   ├─ NO  ─→ try each UI_PATTERN in declaration order
   │         ├─ match                    ─→ Blocked
   │         └─ no match                 ─→ None  [+ drift warning if pane "looks like a prompt"]
   │
   └─ YES ─→ scan up from chrome for spinner row  [· ✻ ✽ ✶ ✳ ✢]
             ├─ spinner with `…`         ─→ Working
             └─ no spinner / completion  ─→ Idle
```

## Usage

### 1. Install

```bash
# from a clone
git clone https://github.com/wuwenrui555/claude-code-state.git
cd claude-code-state
uv pip install -e .

# or directly from GitHub
uv tool install git+https://github.com/wuwenrui555/claude-code-state
```

Python ≥ 3.11. Zero runtime dependencies. The optional `claude_code_state.capture.tmux` helper shells out to the `tmux` CLI (no `libtmux` import) — install nothing extra to use it.

### 2. API

```python
from claude_code_state import (
    # state types
    ClaudeState,                     # union of the four below
    Working,                         # has .status_text: str
    Idle,
    Blocked,                         # has .ui: BlockedUI, .content: str
    Dead,                            # never returned by parse_pane (callers must probe the process)
    BlockedUI,                       # enum: 6 blocking UI variants

    # top-level classifier
    parse_pane,                      # pane_text -> ClaudeState | None

    # lower-level building blocks
    has_input_chrome,                # lines -> bool
    parse_status_line,               # pane_text -> str | None (raw spinner text)
    extract_interactive_content,     # pane_text -> InteractiveUIContent | None
    InteractiveUIContent,            # dataclass(content: str, ui: BlockedUI)
)

# optional tmux capture helper (subpackage, opt-in)
from claude_code_state.capture import tmux
# tmux.capture(target: str) -> str   e.g., "session_name", "session_name:0", "%5" (pane id)
# tmux.TmuxNotInstalledError         raised when tmux binary is missing
```

That's the entire public surface.

### 3. Quick start

```pycon
>>> from claude_code_state import parse_pane, Working, Idle, Blocked

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

## Patterns

The package recognizes two primitives in the captured pane text. **UI patterns** drive `Blocked` classification (which dialog is up); **spinners** drive `Working` vs `Idle` (whether CC is processing).

### 1. UI patterns

When the input chrome is gone, `parse_pane` matches the captured pane against a list of `UI_PATTERN`s — top + bottom regex pairs that bracket a recognizable dialog. The first match wins, and `parse_pane` returns `Blocked(ui=..., content=...)` with `ui` tagging which dialog matched.

Example — the permission prompt pattern:

```python
UIPattern(
    name=BlockedUI.PERMISSION_PROMPT,
    top=(re.compile(r"^\s*Do you want to proceed\?"),),
    bottom=(re.compile(r"^\s*Esc to cancel"),),
    walkback=True,
)
```

When matched, `parse_pane` returns `Blocked(ui=BlockedUI.PERMISSION_PROMPT, content=...)`. The `content` includes the matched region. When `walkback=True`, it also extends up to the nearest `────` separator above the top match — useful for permission prompts where the tool preview (e.g., `Read(/etc/passwd)`) sits above the question and would otherwise be cut off.

#### Drift detection

CC's UI evolves between versions. If a CC release reworded "Do you want to proceed?" to "Confirm action?", the built-in pattern would silently miss it. To catch this, when `parse_pane` sees a pane that looks like a prompt — contains keywords like `Esc to`, `❯ 1.`, `Would you like to`, `Do you want to`, `Type to filter` — but no `UI_PATTERN` matches, it logs a one-shot warning with a 12-char fingerprint of the pane tail. Grep `drift.log` for new fingerprints to spot UI variants the package doesn't yet know about. Deduplication is per-process; each unique pane fingerprint warns at most once between restarts.

### 2. Spinners

`STATUS_SPINNERS` is the set of single characters CC uses to prefix a "still working" status row (cycling like a loading animation). When `parse_pane` finds the input chrome present, it scans up for a row whose first non-space character is one of these spinners — that row's text becomes `Working.status_text`.

Built-in set:

```python
STATUS_SPINNERS = frozenset({"·", "✻", "✽", "✶", "✳", "✢"})
```

The presence of `…` (U+2026) in the same row separates a **running** status (`✻ Thinking…`) from a **completion** summary (`✻ Worked for 56s`) — the former classifies as `Working`, while the latter classifies as `Idle`.

### 3. Overrides

The package ships with built-in `UI_PATTERN`s and `STATUS_SPINNERS` covering known CC UIs. When a CC update breaks one and you don't want to wait for a package release, patch locally:

```bash
export CLAUDE_CODE_STATE_DIR=~/.claude-code-state
mkdir -p "$CLAUDE_CODE_STATE_DIR"
```

Then write `<dir>/parser_config.json`:

```json
{
  "$schema_version": 1,
  "ui_patterns": [
    {
      "name": "permission_prompt",
      "top": ["^\\s*Confirm action"],
      "bottom": ["^\\s*Esc to dismiss"],
      "min_gap": 2,
      "walkback": true
    }
  ],
  "status_spinners": ["✦"],
  "skippable_patterns": ["^\\s*●\\s*How is Claude doing this session\\?"]
}
```

Config is read at import time (not per-call), so restart any process using `claude-code-state` to apply changes.

**Supported keys:**

- `$schema_version` (required, must be `1`) — locks the config to a known schema. When a future package version changes the layout, old configs fail loudly instead of silently mis-loading. File is ignored with a warning if missing or different.
- `ui_patterns` — UI dialog patterns. Each entry: `name` (a `BlockedUI` value, lowercased), `top` regex list, `bottom` regex list, optional `min_gap` (default `2`), optional `walkback` (default `false`). **Prepended** to built-ins, so your patterns try first.
- `status_spinners` — single characters that prefix a status row. **Union** with built-ins.
- `skippable_patterns` — regexes for lines the spinner-scan should silently skip (not surfaced) while scanning above the chrome. **Prepended** to the built-in skip list.

## License

MIT. See [LICENSE](LICENSE).
