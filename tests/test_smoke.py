"""Smoke tests — verify package imports and basic classification works.

These tests use synthetic pane fixtures crafted to match the documented
chrome / spinner / blocking-UI shapes. They are not meant to cover
every UIPattern — that's the job of the host project's full pane
fixture suite. The point here is to catch import-time breakage, API
regressions, and the most common classifications.
"""

from __future__ import annotations

import pytest

from claude_code_state import (
    Blocked,
    BlockedUI,
    Dead,
    Idle,
    Working,
    has_input_chrome,
    parse_pane,
    parse_status_line,
)


# A minimal Claude Code pane bottom: chrome separator, prompt, separator,
# status bar. Any pane that ends with this shape is in Working or Idle.
CHROME = "─" * 80 + "\n❯\n" + "─" * 80 + "\n  ✓ Auto · Sonnet 4.6 · 0%"

# Same chrome with a spinner+status line above it = Working.
WORKING_PANE = (
    "Some prior content\n\n✻ Thinking… (16s · ↑ 827 tokens · thought for 7s)\n" + CHROME
)

IDLE_PANE = "Some prior content\n\n" + CHROME

# Permission-prompt shape: chrome is gone, replaced by a question +
# numbered choices + footer. Walkback should pick up the tool preview
# above the question.
PERMISSION_PANE = (
    "Some prior content\n" + ("─" * 80) + "\n"
    "Read file\n"
    "/etc/passwd\n"
    "\n"
    "Do you want to proceed?\n"
    "❯ 1. Yes\n"
    "  2. No\n"
    "Esc to cancel\n"
)

# A completion-summary line (no `…`) above chrome should NOT be classified
# as Working — it represents a finished turn.
COMPLETION_PANE = "Some prior content\n\n✻ Worked for 56s\n" + CHROME


def test_import():
    """All public names import cleanly."""
    assert Working is not None
    assert Idle is not None
    assert Blocked is not None
    assert Dead is not None
    assert BlockedUI.PERMISSION_PROMPT == "permission_prompt"


def test_empty_pane_returns_none():
    assert parse_pane("") is None
    assert parse_pane(None) is None  # type: ignore[arg-type]


def test_idle_pane():
    state = parse_pane(IDLE_PANE)
    assert isinstance(state, Idle)


def test_working_pane():
    state = parse_pane(WORKING_PANE)
    assert isinstance(state, Working)
    assert "Thinking…" in state.status_text
    assert "16s" in state.status_text


def test_completion_summary_is_not_working():
    """`✻ Worked for 56s` lacks the `…` and must classify as Idle, not Working."""
    state = parse_pane(COMPLETION_PANE)
    assert isinstance(state, Idle)


def test_permission_prompt_classifies_as_blocked():
    state = parse_pane(PERMISSION_PANE)
    assert isinstance(state, Blocked)
    assert state.ui == BlockedUI.PERMISSION_PROMPT
    # Walkback should have included the tool preview lines.
    assert "Read file" in state.content
    assert "/etc/passwd" in state.content


def test_has_input_chrome():
    assert has_input_chrome(IDLE_PANE.split("\n"))
    assert has_input_chrome(WORKING_PANE.split("\n"))
    assert not has_input_chrome(PERMISSION_PANE.split("\n"))


def test_parse_status_line_returns_text_for_working():
    text = parse_status_line(WORKING_PANE)
    assert text is not None
    assert "Thinking…" in text


def test_parse_status_line_returns_none_for_idle():
    assert parse_status_line(IDLE_PANE) is None


def test_parse_status_line_returns_none_for_completion_summary():
    assert parse_status_line(COMPLETION_PANE) is None


def test_working_rejects_status_text_without_ellipsis():
    """The Working dataclass enforces that status_text contains `…`."""
    with pytest.raises(ValueError, match="ellipsis"):
        Working(status_text="Worked for 56s")


def test_working_rejects_empty_status_text():
    with pytest.raises(ValueError, match="non-empty"):
        Working(status_text="")
