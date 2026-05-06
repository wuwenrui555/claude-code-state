# Changelog

All notable changes to `claude-code-state` are documented here. The
format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-05-06

### Removed

- `extract_bash_output`, `parse_usage_output`, and `UsageInfo` are
  no longer part of the public API. They classified shell-command
  echoes and Claude Code's `/usage` modal respectively, neither of
  which is state detection. Carried over by accident from the
  initial extraction; tighten the package's scope to its name.

  **Migration:** if you were relying on these (no known external
  consumers), keep your own copy in your project, or import from
  ccmux-backend's `tmux_pane_parser` module which still ships them.

### Changed

- README's "lower-level building blocks" line updated to reflect the
  trimmed surface.

## [0.1.0] - 2026-05-06

Initial release. Extracted from
[ccmux-backend](https://github.com/wuwenrui555/ccmux-backend)'s
`tmux_pane_parser` and `claude_state` modules.

### Added

- `parse_pane(pane_text) -> ClaudeState | None` top-level classifier.
- `ClaudeState` sealed union: `Working`, `Idle`, `Blocked`, `Dead`.
- `BlockedUI` enum covering 6 known blocking UI variants.
- Lower-level building blocks: `has_input_chrome`,
  `parse_status_line`, `extract_interactive_content`.
- `capture/tmux.py` optional submodule wrapping `tmux capture-pane`
  with the flags `parse_pane` expects (`-p`, `-J`).
- User-pluggable patterns via `$CLAUDE_CODE_STATE_DIR/parser_config.json`.
- Pattern-drift detection that writes one-shot warnings to
  `<dir>/drift.log` when the pane looks like a prompt but no
  built-in `UI_PATTERN` matches.
- 12 smoke tests + 3 capture integration tests (skipped when `tmux`
  binary unavailable).
