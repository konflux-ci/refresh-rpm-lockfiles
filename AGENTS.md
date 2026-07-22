# AGENTS.md

## Project overview

`refresh-rpm-lockfiles` is a Python CLI used as a Renovate `postUpgradeTask`. After Renovate updates a Dockerfile or Containerfile, this tool refreshes associated RPM lockfiles by invoking [rpm-lockfile-prototype](https://github.com/konflux-ci/rpm-lockfile-prototype).

The tool:

1. Reads Renovate upgrade metadata from a JSON file (`-f` / `--file`).
2. Walks the repository for `rpms.in.yaml` files and maps each to its containerfile.
3. Runs `rpm-lockfile-prototype` for matching upgrades, writing `rpms.lock.yaml` next to each `rpms.in.yaml`.

All application code lives in `src/refresh_rpm_lockfiles/__init__.py`. See `README.md` for Renovate configuration examples.

## Setup commands

- Requires Python **3.12+** (`.python-version` pins 3.13; CI also tests 3.12 and 3.14).
- Install [uv](https://docs.astral.sh/uv/) for dependency management.
- Install project and dev dependencies: `uv sync --group dev`
- Optional: install pre-commit hooks: `pre-commit install`

Runtime note: [`rpm-lockfile-prototype`](https://github.com/konflux-ci/rpm-lockfile-prototype) must be on `PATH` when running the CLI against a real repo. Unit tests mock subprocess calls and do not require it.

## Build and test commands

Run these before opening a PR:

```bash
uv run pytest --cov=src --cov-report=term-missing
uv run ruff check
uv run mypy src --check-untyped-defs
```

Focused test runs:

```bash
uv run pytest tests/test_find_files.py
uv run pytest -k "resolve_relative_path"
```

## Code style

- **Formatter/linter:** Ruff with `select = ["ALL"]`, `line-length = 100`, `target-version = "py312"`.
- **Type checking:** mypy on `src/` with `--check-untyped-defs`. Add type annotations for new public functions.
- **Docstrings:** Required on public modules, classes, and functions in `src/` (enforced by Ruff).
- **Logging:** Use `loguru` (`logger.debug`, `logger.info`, `logger.error`). Respect `LOG_LEVEL` env var (default `DEBUG`).
- **Tests:** Live in `tests/`. Ruff relaxes annotation and docstring rules there. Prefer `unittest.mock` patches over real filesystem or subprocess calls.
- Keep changes minimal and focused. Match existing patterns in `__init__.py` (dataclasses, pure path helpers, small functions).

## Testing instructions

CI (`.github/workflows/ci.yml`) runs pytest, ruff, and mypy on every PR. Match those commands locally.

When adding or changing behavior:

- Add or update tests in the matching `tests/test_*.py` file.
- Mock `Path.walk`, `Path.open`, `Path.exists`, and `subprocess.run` as existing tests do.
- Cover edge cases for containerfile resolution: sibling `Dockerfile`/`Containerfile`, `context.containerfile` string or dict form, and relative paths with `..` segments.
- Deduplication of upgrades by `packageFile` is expected (see `test_read_upgrades_from_file_multiple_stages`).
- `update_lockfiles` returns a truthy value if any invocation fails; it attempts all upgrades before returning.

## Architecture notes

### Containerfile discovery

For each `rpms.in.yaml`:

1. If `context.containerfile` is set (string or `{"file": "..."}` dict), resolve relative to the `rpms.in.yaml` directory.
2. Otherwise look for a sibling `Dockerfile`, then `Containerfile`.
3. Skip entries where the resolved containerfile does not exist (logged as error).

Paths stored in the input-file map use repo-relative strings with `..` resolved.

### Renovate integration

Typical invocation from Renovate:

```bash
refresh-rpm-lockfiles -f "$RENOVATE_POST_UPGRADE_COMMAND_DATA_FILE"
```

The data file is JSON: `[{"packageFile": "path/to/Dockerfile"}, ...]`. Use MintMaker presets or manual `postUpgradeTasks` config as documented in `README.md`.

## PR instructions

- Keep `AGENTS.md` under **300 lines** (enforced by `.github/workflows/validate-agents-md.yml`).
- Ensure CI passes: pytest (3.12–3.14), ruff, mypy.
- Run `pre-commit run --all-files` before pushing when possible.
- Do not commit secrets, Renovate tokens, or local test fixture data unrelated to the change.
- CODEOWNERS: `@konflux-ci/mintmaker-maintainers` is requested for review on all changes.

## Security considerations

- The CLI runs `rpm-lockfile-prototype` via `subprocess.run` with fixed arguments derived from repo paths. Do not pass untrusted user input into command construction.
- `S603`/`S607` noqa comments are intentional (known executable name). Prefer fixing new lint findings over adding `noqa`.
- When changing subprocess or path-resolution logic, consider path traversal and unexpected `..` segments.
