## What and why

<!-- One logical change. What does this PR do and why? Link the issue. -->

## Checklist

- [ ] A failing test motivated this change first (strict TDD).
- [ ] `ruff format` + `ruff check` + `mypy veil` pass.
- [ ] `pytest -q` passes; approximate assertions use justified tolerances.
- [ ] `docs/` and `CHANGELOG.md` updated if behavior changed.
- [ ] No novelty/accuracy/security claims that aren't backed by a benchmark or citation.
- [ ] No OpenFHE C++ types imported into the `veil/` package.
- [ ] Does **not** alter a locked decision in `DESIGN.md` §4/§15 (or it does, and the human signed off below).

## Locked-decision sign-off (only if applicable)

<!-- If this changes a locked decision, record the explicit approval here. -->
