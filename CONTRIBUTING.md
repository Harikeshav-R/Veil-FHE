# Contributing to Veil-FHE

Thanks for your interest. Veil-FHE is a solo research/learning project, so the
process is lightweight — but the engineering standards are strict because the
code is privacy-relevant.

## Before you start

1. Read [`DESIGN.md`](DESIGN.md). It is the source of truth for architecture and
   the locked decisions. Changes that contradict a locked decision (`DESIGN.md`
   §4/§15) need explicit discussion first.
2. If you use an AI coding agent, point it at [`AGENTS.md`](AGENTS.md).

## Development setup

The project uses [uv](https://docs.astral.sh/uv/) for environment and dependency
management. uv reads `pyproject.toml` + `uv.lock`; the native build is still
driven by scikit-build-core + CMake.

```bash
# Standard: hermetic build of OpenFHE via FetchContent (slow first time, cached after).
uv sync                 # creates .venv, builds veil_backend, installs the `dev` group
uv run pre-commit install

# Then work inside the managed env:
uv run pytest
uv run mypy veil
```

Fast inner loop against a preinstalled OpenFHE (recommended once you're iterating
on C++): install OpenFHE on your system, then either

```bash
CMAKE_ARGS="-DVEIL_USE_SYSTEM_OPENFHE=ON" uv sync
# or, for an explicit per-install override:
uv pip install -e . -C cmake.define.VEIL_USE_SYSTEM_OPENFHE=ON
```

Editable installs don't auto-rebuild the C++ extension on source change — re-run
the sync/install (or enable scikit-build-core's experimental
`editable.rebuild`) after touching `src/`.

Dependency-group commands: `uv sync` installs the default `dev` group; build the
docs deps with `uv sync --group docs` and the benchmark deps with
`uv sync --group bench`. Add a dependency with `uv add <pkg>` (runtime) or
`uv add --group dev <pkg>` (tooling); both update `uv.lock`, which is committed.

## The rules

- **Strict TDD.** Write a failing test first, then the minimum code to pass it.
  No production code arrives without a test that motivated it.
- **Approximate assertions only for CKKS results.** Assert bounded error, never
  exact equality, and justify the tolerance in a comment.
- **Intellectual honesty** (`DESIGN.md` §2.3): no novelty claims, no hiding FHE's
  slowness, no overstated accuracy/security. Back claims with benchmarks or
  citations.
- **Layering:** the `veil/` Python package never imports OpenFHE C++ types; it
  calls only the `veil_backend` primitives.

## Before opening a PR

```bash
uv run ruff format . && uv run ruff check . --fix
uv run mypy veil
uv run pytest -q
uv run pre-commit run --all-files
```

Then:
- Use **Conventional Commits** (`feat(scope): …`, `fix: …`, `docs: …`, …).
- Update `docs/` and `CHANGELOG.md` if behavior changed.
- Keep PRs to one logical change. Make sure CI is green on all platforms.

## Reporting bugs and requesting features

Use the issue templates under `.github/ISSUE_TEMPLATE/`. For anything
security-relevant, read [`SECURITY.md`](SECURITY.md) first.

## Code of conduct

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).
