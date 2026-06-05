# AGENTS.md — Directives for AI Coding Agents

You are working on **Veil-FHE**, a privacy-preserving ML inference compiler built
on CKKS (OpenFHE) with a PyTorch frontend and a pybind11 C++ backend. Read this
file fully before doing anything. The authoritative design is in **`DESIGN.md`**;
when in doubt, that document wins over your priors.

These directives are binding. Follow them on every task.

---

## 0. Prime directives

1. **`DESIGN.md` is the source of truth.** Do not contradict its locked decisions
   (`DESIGN.md` §4 and §15). If a task seems to require contradicting one, stop
   and ask the human; do not "improve" a locked decision on your own.
2. **Strict TDD, always.** Write a failing test first, watch it fail for the right
   reason, then write the minimum code to pass it, then refactor. No production
   code is added without a test that motivated it.
3. **Intellectual honesty is a hard requirement** (`DESIGN.md` §2.3). Never add
   copy that claims novelty, hides the performance cost of FHE, overstates
   accuracy, or implies security guarantees. If you cannot back a claim with a
   committed benchmark or a citation, do not make the claim.
4. **This is cryptography-adjacent code that protects privacy.** A silently wrong
   result is worse than a loud failure. Prefer compile-time errors over runtime
   surprises; prefer raising over guessing.
5. **Small, reviewable changes.** One logical change per commit and per PR.

---

## 1. What this project is (and is not)

- It **is** an educational, from-scratch FHE inference compiler exploring CKKS
  tradeoffs. It compiles `torch.nn.Module` → ONNX (internal) → an encrypted
  inference graph runnable on OpenFHE CKKS.
- It **is not** novel research, a production system, or audited software. Do not
  let any documentation drift toward implying otherwise.
- The headline reality you must never obscure: **FHE inference is orders of
  magnitude slower than plaintext.** Say so plainly wherever performance comes up.

---

## 2. Repository map (where things live)

- `DESIGN.md` — canonical design/roadmap. Read it.
- `src/backend.cpp` — pybind11 bindings over OpenFHE CKKS. The **only** place
  OpenFHE C++ types appear. Keep the surface minimal.
- `veil/` — the Python compiler and orchestrator. **Never** import OpenFHE types
  here; only call `veil_backend` primitives.
  - `api.py` (compile + ONNX export), `ingest.py`, `transform.py`,
    `calibration.py`, `params.py`, `ir.py`, `model.py`, `errors.py`, `ops/`.
- `tests/` — pytest suite; the spec.
- `benchmarks/` — reproducible performance harness.
- `docs/` — MkDocs Material, **user-facing** (distinct from `DESIGN.md`).
- `cmake/`, `CMakeLists.txt`, `pyproject.toml` — build.

**Layering rule (do not violate):** Python speaks only the `veil_backend`
primitive API. All cryptographic operations stay behind the C++ boundary. The
Python side is a compiler, not a crypto implementation.

---

## 3. Build, test, and lint commands

The project uses **uv** for environment and dependency management (deps pinned in
`uv.lock`). The native build is still driven by scikit-build-core + CMake — uv
does not replace the build backend. Use these exact commands.

```bash
# Set up / update the environment. Builds veil_backend (hermetic OpenFHE via
# FetchContent — slow on a cold cache) and installs the `dev` group.
uv sync                                   # standard
CMAKE_ARGS="-DVEIL_USE_SYSTEM_OPENFHE=ON" uv sync   # faster: link a preinstalled OpenFHE

# Run everything inside the managed env via `uv run`.
uv run pytest -q                          # full suite
uv run pytest tests/test_ops.py -q        # one file
uv run pytest -k "matmul" -q              # by keyword

# C++ unit tests (where built)
ctest --test-dir build --output-on-failure

# Lint / format / types  (run all before committing)
uv run ruff format .
uv run ruff check . --fix
uv run mypy veil
clang-format -i src/*.cpp src/*.hpp 2>/dev/null || true
# clang-tidy runs in CI; run locally if you touched C++.

# Pre-commit (installs the same gates CI enforces, incl. the uv-lock check)
uv run pre-commit run --all-files

# Docs
uvx --with mkdocs-material --with "mkdocstrings[python]" mkdocs serve

# Dependencies: add/remove via uv so uv.lock stays in sync (commit the lock).
uv add <pkg>                              # runtime dependency
uv add --group dev <pkg>                  # dev tooling
uv lock                                   # re-resolve after manual pyproject edits
```

Do NOT use bare `pip install` or hand-edit `uv.lock`. If a command fails because
of the environment (e.g. OpenFHE not installed for the system-build path), say so
explicitly in your summary — do not silently skip the step.

---

## 4. TDD workflow you must follow

For every feature or fix:

1. **Locate or add the test.** Find the relevant `tests/test_*.py`. Write a test
   that encodes the desired behavior and currently fails.
2. **Run it; confirm it fails for the intended reason** (not an import error or a
   typo).
3. **Implement the minimum** to make it pass.
4. **Run the full suite** (`pytest -q`) to confirm no regressions.
5. **Refactor** with the tests green.
6. **Lint, format, type-check** (§3).
7. **Commit** with a Conventional Commit message (§6).

For approximate (CKKS) results, tests assert **bounded error**, never exact
equality, and every tolerance is justified in a comment explaining why that bound
is correct. A test that only passes because the tolerance is loose is a defect —
flag it.

---

## 5. Coding standards

### Python
- Python **3.12+**. Full type annotations on every public function; `mypy` is
  strict and must pass.
- Formatting and linting via **ruff** (it is both formatter and linter here).
- Public functions get docstrings stating shapes, units, level cost (for FHE
  ops), and error conditions.
- Raise the specific exception from `veil/errors.py`, never a bare `Exception`.
  Compile-time problems must surface at compile time with actionable messages
  that name the offending op/node and suggest a fix.
- No `print` for diagnostics; use the `logging` module / project logger.

### C++ (`src/backend.cpp`)
- **C++17.** `clang-format` and `clang-tidy` clean.
- Keep the binding surface minimal: context, keygen, encrypt, decrypt, add, mult
  (+ relin), rotate, Chebyshev eval, bootstrap. Nothing speculative.
- RAII for all OpenFHE handles; let pybind11 propagate exceptions. Never leak a
  raw key into Python. Document ownership of every returned handle.
- Always use OpenFHE `FLEXIBLEAUTO` scaling. Never `FIXEDMANUAL`; never implement
  manual rescaling.

### FHE-specific rules (easy to get wrong — read carefully)
- Track multiplicative-level consumption for every op you add; document it in the
  docstring. The transformer's budget analysis depends on these being correct.
- Bootstrap insertion is **opt-in**. If a network exceeds the profile's depth and
  bootstrap is disabled, raise `LevelBudgetError` at compile time. Never silently
  bootstrap.
- Polynomial activation intervals come from **calibration**, not constants.
  Out-of-domain inputs → warn + clamp by default, `OutOfDomainError` under
  `strict=True`. Never let an out-of-domain value through silently.
- Model **weights are plaintext on the server**; the **input/output** are the
  secret material. Never write an example or doc that sends the secret key or
  `ClientContext` to the server side.

---

## 6. Git, commits, and PRs

- **Conventional Commits.** `type(scope): summary`. Types: `feat`, `fix`, `docs`,
  `test`, `refactor`, `perf`, `build`, `ci`, `chore`. Example:
  `feat(ops): add Halevi-Shoup diagonal matmul`.
- One logical change per commit. Keep the working tree green at each commit.
- Branch names: `feat/...`, `fix/...`, `docs/...`.
- A PR must: pass CI on all platforms, keep or improve coverage, update `docs/`
  and `CHANGELOG.md` when behavior changes, and not modify `DESIGN.md`'s locked
  decisions without explicit human sign-off recorded in the PR description.
- Never commit secrets, keys, large generated artifacts, build trees, or
  benchmark output blobs. Respect `.gitignore`.

---

## 7. Following the roadmap

Work the phases in `DESIGN.md` §14 in order. Do not begin a phase before the
previous phase's **exit criteria** are green. If asked to do work that belongs to
a deferred (post-v1) item — batching, encrypted weights, GPU, extra opsets — stop
and confirm with the human; these are explicitly out of scope for v1.

When you complete a unit of work, your summary states: what test drove it, what
you changed, the commands you ran and their result, and the level cost of any new
FHE op.

---

## 8. When to stop and ask

Stop and ask the human (do not guess) when:
- A task appears to require changing a locked decision (`DESIGN.md` §4/§15).
- You would need to make a performance, accuracy, or security claim you cannot
  back with a benchmark or citation.
- An OpenFHE API you need does not match what `DESIGN.md` describes (the library
  version may have moved; confirm before adapting).
- The correct behavior is genuinely ambiguous and getting it wrong could produce a
  silently incorrect cryptographic result.

A short, specific question is always better than a confident wrong assumption.

---

## 9. Things that are explicitly forbidden

- Claiming novelty, hiding FHE's slowness, or overstating accuracy/security.
- Importing OpenFHE C++ types into the `veil/` Python package.
- Using `ctypes`, adding a Rust shim, or pulling in a second FHE library.
- `FIXEDMANUAL` scaling or hand-rolled rescaling.
- Silent bootstrapping or silent out-of-domain clamping under `strict=True`.
- Production code without a failing test first.
- Pinning OpenFHE to `main` instead of a released tag.
- Using bare `pip install` instead of uv, or hand-editing `uv.lock` (use `uv add`/`uv lock`).
- Committing keys, build artifacts, or large binaries.
