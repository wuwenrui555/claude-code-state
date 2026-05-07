# Changelog

All notable changes to `claude-code-state` are documented here. The
format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.3.0] - 2026-05-07

### Added

- GitHub Actions CI: `test` job (matrix py3.11/3.12/3.13, pytest) and
  `lint` job (pre-commit run --all-files).
- Pre-commit configuration (`.pre-commit-config.yaml` +
  `.markdownlint.yaml` + `.markdownlintignore`) running ruff,
  ruff-format, and markdownlint.
- `pre-commit` listed as a dev dependency.
- `[tool.ruff.lint]` config: `select = ["E", "F", "I", "B", "UP"]`
  with `ignore = ["E501"]`.
- `[tool.ruff.format]` config: `quote-style = "double"`.
- `NOTICE` file documenting the attribution chain to
  [ccbot](https://github.com/six-ddc/ccbot) and which primitives are
  inherited (UIPattern shape, _try_extract algorithm, initial
  UI_PATTERNS, parse_status_line skeleton, STATUS_SPINNERS) versus
  original (ClaudeState union, parse_pane, walkback, drift detection,
  OVERLAY/TODO split, completion-summary filtering, override system).
- `LICENSE-MIT-upstream.txt` preserving ccbot's MIT license text.
- `.gitignore` gains notebooks (`.ipynb_checkpoints/`) and local-secret
  (`*.env`, `.env.local`, `*.local`) sections from the bootstrap
  template.

### Changed

- License: MIT → Apache 2.0. The package's own original additions move
  to Apache 2.0; pattern-matching primitives originally extracted from
  ccbot remain under the upstream MIT (preserved in
  `LICENSE-MIT-upstream.txt` and credited in `NOTICE`).
- `pyproject.toml` classifier: `MIT License` →
  `Apache Software License`.
- README: complete rewrite. New structure is four H2 sections
  (`About Claude-Code-State` / `Usage` / `Patterns` / `License`) with
  numbered H3 subsections. Adds a decision-tree diagram for
  `parse_pane`, an `API` section enumerating the public surface with
  type-comment annotations, a `Quick start` using pycon REPL output,
  and a `Patterns` section that splits the two parsing primitives
  (UI patterns + spinners) from the user-override config.
- README: abbreviate "Claude Code" as "CC" after first mention.
- ruff isort applied to imports in `parser.py` and the test files
  (effect of enabling the new `I` rule).

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
