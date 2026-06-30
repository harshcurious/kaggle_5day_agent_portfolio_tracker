# Phase 10 — CLI Demo Entrypoint

## Completed plan steps

- Added an `argparse` command-line entrypoint in `src/portfolio_tracker/cli.py`.
- Added `--mock` offline mode using local fixture files under `tests/fixtures/`.
- Added output format support for markdown and raw JSON via `--format markdown|json`.
- Routed data warnings and data gaps to `stderr`.

## High-level code changes

- Added `main(...)` for CLI invocation and testable argument handling.
- Added `build_mock_synthesizer_input(...)` to convert fixture data into schema-valid vector analyses.
- Added `build_mock_memo(...)` for a deterministic offline capstone memo.
- Added `format_markdown_memo(...)` for standard markdown output.
- Added `[project.scripts] portfolio-tracker = "portfolio_tracker.cli:main"` to `pyproject.toml`.

## Additional implementation decisions

- Live mode intentionally returns a clear error for now; offline demo mode is the supported Phase 10 path.
- CLI invalid ticker validation uses the existing `TickerRequest` schema so command-line behavior matches domain validation.
- Mock mode reads fixture files rather than making network calls, preserving unit-test and demo reproducibility.

## Tests created

- `tests/unit/test_cli.py`
  - Verifies invalid ticker exits non-zero and writes an error to `stderr`.
  - Verifies `--mock` markdown output includes a complete memo and warning flags.
  - Verifies `--mock --format json` outputs parseable raw memo JSON and warning flags.

## Commit message

`feat: add offline CLI demo entrypoint`
