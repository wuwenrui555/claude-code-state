"""Tests for the optional tmux capture helper.

The integration tests spin up a throwaway tmux session and read its
content. They skip cleanly when the ``tmux`` binary is not on PATH so
the suite stays green in environments without tmux installed.
"""

from __future__ import annotations

import shutil
import subprocess
import time

import pytest

from claude_code_state.capture import tmux


# Skip the integration tests when tmux isn't available, but keep the
# error-path test (it monkeypatches subprocess and doesn't need tmux).
_HAS_TMUX = shutil.which("tmux") is not None


@pytest.fixture
def session():
    """Spin up an isolated tmux session for the test, kill it after."""
    name = f"ccs-test-{int(time.time() * 1000)}"
    subprocess.run(
        ["tmux", "new-session", "-d", "-s", name, "echo hello && sleep 30"],
        check=True,
    )
    # Tiny grace so the shell renders `hello` before we capture.
    time.sleep(0.2)
    yield name
    subprocess.run(["tmux", "kill-session", "-t", name], check=False)


@pytest.mark.skipif(not _HAS_TMUX, reason="tmux binary not available")
def test_capture_returns_pane_content(session):
    """Capturing a real tmux session returns its rendered text."""
    content = tmux.capture(session)
    assert "hello" in content


@pytest.mark.skipif(not _HAS_TMUX, reason="tmux binary not available")
def test_capture_returns_empty_for_missing_session():
    """Invalid target returns empty string instead of raising."""
    content = tmux.capture("definitely-not-a-real-session-xyz-123")
    assert content == ""


def test_tmux_not_installed_raises(monkeypatch):
    """When the tmux binary is missing, a clear typed error is raised."""

    def fail(*_args, **_kwargs):
        raise FileNotFoundError("tmux not found")

    monkeypatch.setattr(subprocess, "run", fail)
    with pytest.raises(tmux.TmuxNotInstalledError, match="not found on PATH"):
        tmux.capture("any-session")
