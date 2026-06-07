# Veil-FHE — Build Roadmap & Checklist

> The execution checklist for Veil-FHE. Work it top to bottom, checking items off
> as you go. It expands [`DESIGN.md` §14](DESIGN.md#14-the-roadmap) into ordered,
> verifiable steps. **Rationale lives in `DESIGN.md`; process rules live in
> `AGENTS.md`; this file is the "what to do next, and how you know it's done."**
>
> **Timeline:** solo, ~3 months (~13 weeks). Week numbers are guidance, not a
> contract. **Do not start a phase until the previous phase's "Phase complete
> when" box is fully checked.**

---

## How to use this document

- `- [ ]` = todo · `- [x]` = done · use `- [~]` for in-progress if helpful.
- **Test/Impl pairs:** algorithmic items list a `Test:` box and an `Impl:` box.
  Strict TDD means you check `Test:` (a failing test exists and fails for the
  right reason) *before* you check `Impl:` (it passes). See `AGENTS.md` §4.
- **Commit hints** (`→ commit: …`) suggest a Conventional Commit boundary. One
  logical change per commit; keep the tree green at each commit.
- **Path/API references** point at the exact file or OpenFHE call to touch.
- When you finish a unit of work, your summary states: the test that drove it,
  what changed, the commands run + results, and the level cost of any new FHE op.

---

## Quality gates — the Definition of Done for *every* task

These apply to all implementation items below. A task is not done until:

- [ ] A failing test motivated the change first (red → green → refactor).
- [ ] Approximate (CKKS) assertions use **bounded error** with a justified
      tolerance comment — never exact equality.
- [ ] `uv run ruff format .` and `uv run ruff check .` are clean.
- [ ] `uv run mypy veil` is clean (Python changes).
- [ ] `clang-format` / `clang-tidy` clean (C++ changes).
- [ ] `uv run pytest -q` passes with no regressions.
- [ ] New FHE ops document their **multiplicative-level cost** in the docstring.
- [ ] No OpenFHE C++ types leaked into the `veil/` Python package.
- [ ] `docs/` and `CHANGELOG.md` updated if behavior changed; `uv.lock` in sync
      if dependencies changed.
- [ ] No claim made that isn't backed by a benchmark or citation (honesty rules,
      `DESIGN.md` §2.3).

---

## Progress at a glance

- [x] **Phase 0** — Repository & build bootstrap (Week 1)
- [ ] **Phase 1** — FHE primitives / C++ backend (Weeks 2–3)
- [ ] **Phase 2** — FHE operator library (Weeks 4–6)
- [ ] **Phase 3** — ONNX ingestor (Weeks 6–7)
- [ ] **Phase 4** — Graph transformer (Weeks 8–9)
- [ ] **Phase 5** — Python API, calibration & persistence (Weeks 10–11)
- [ ] **Phase 6** — Benchmarking & hardening → `v0.1.0` (Weeks 12–13)

---

## Phase 0 — Repository & build bootstrap

**Goal:** the scaffold is a live GitHub repo, the toolchain works, the (empty)
`veil_backend` compiles and imports, and CI is green on Linux.

### 0.1 Create and configure the GitHub repository
- [x] Create `Harikeshav-R/veil-fhe`; push the scaffold; set default branch `main`.
- [x] Add repo description and topics (`fhe`, `homomorphic-encryption`, `ckks`, `openfhe`, `privacy`, `ml-inference`).
- [x] Enable Issues; enable Discussions (optional).
- [x] Branch protection on `main`: require PR, require CI (`lint`, `build-test`) to pass, no direct pushes.
- [x] Confirm `LICENSE` (MIT), `SECURITY.md`, `CODE_OF_CONDUCT.md`, issue/PR templates render on GitHub.
- [x] → commit: `chore: initialize repository`

### 0.2 Local toolchain
- [x] Install `uv`, a C++17 compiler (GCC ≥ 9 or Clang ≥ 10), CMake ≥ 3.24, Ninja, and OpenFHE build prerequisites (OpenMP).
- [x] `uv sync` succeeds on Linux (builds the empty extension hermetically; slow first time).
- [x] `uv run python -c "import veil_backend"` works (stub module, OpenFHE not yet wired).
- [x] `uv run python -c "import veil"` imports the package surface without error.
- [x] `uv run pre-commit install`; `uv run pre-commit run --all-files` passes (incl. `uv-lock`).

### 0.3 Wire OpenFHE into the build (configure-only this phase)
- [x] `cmake/FindOrFetchOpenFHE.cmake` fetches OpenFHE `v1.5.1` and configures without error.
- [x] Verify the in-tree target names / include dirs are correct for FetchContent consumption; fix if the first configure reports missing targets (see `DESIGN.md` §11.1 caveat).
- [x] Confirm `VEIL_USE_SYSTEM_OPENFHE=ON` path also configures against a local OpenFHE install.
- [x] → commit: `build: wire OpenFHE via FetchContent`

### 0.4 CI and docs
- [x] `lint` job green (ruff + mypy via `uv sync --no-install-project`).
- [x] `build-test` job green on **Linux** (ccache caching the OpenFHE build).
- [x] macOS / Windows jobs run (allowed to fail/lag this phase; capture the errors as issues).
- [x] Enable GitHub Pages; `docs.yml` deploys the MkDocs site successfully.
- [x] → commit: `ci: green pipeline on linux + docs deploy`

### ✅ Phase 0 complete when
- [x] `uv sync` builds and `import veil_backend` works locally.
- [x] `lint` + `build-test` (Linux) green on CI; docs site live.
- [x] Branch protection active; pre-commit enforced.

---

## Phase 1 — FHE primitives (C++ backend)

**Goal:** a minimal, lifetime-correct OpenFHE CKKS binding in `src/backend.cpp`,
validated by `tests/test_backend.py`. **Only file touching OpenFHE types.**
Always `FLEXIBLEAUTO`; never `FIXEDMANUAL`. (`DESIGN.md` §4.4, §8.2.)

### 1.1 Activate OpenFHE in the binding
- [ ] Uncomment `#include "openfhe.h"`; link `OPENFHEcore`/`OPENFHEpke`/`OPENFHEbinfhe`.
- [ ] Extension builds + imports with OpenFHE symbols present (`import veil_backend`).
- [ ] → commit: `feat(backend): link OpenFHE into the extension`

### 1.2 Context construction
- [ ] **Test:** constructing a `Context(mult_depth, scaling_mod_size=50, first_mod_size=60, batch_size)` succeeds and reports the expected ring dimension/security.
- [ ] **Impl:** `CCParams<CryptoContextCKKSRNS>` → `SetMultiplicativeDepth`, `SetScalingModSize(50)`, `SetFirstModSize(60)`, `SetBatchSize`, `SetScalingTechnique(FLEXIBLEAUTO)`, `SetSecurityLevel(HEStd_128_classic)`; `GenCryptoContext`; `Enable(PKE | KEYSWITCH | LEVELEDSHE | ADVANCEDSHE)`.
- [ ] → commit: `feat(backend): CKKS crypto context construction`

### 1.3 Key generation
- [ ] **Test:** `keygen(rotation_indices=[...])` produces a usable key set; rotation keys exist for the requested indices.
- [ ] **Impl:** `KeyGen()`; `EvalMultKeyGen(sk)`; `EvalRotateKeyGen(sk, indices)`. Secret key stays inside `Context`; never returned to Python.
- [ ] → commit: `feat(backend): key generation (relin + rotation keys)`

### 1.4 Encrypt / decrypt round-trip
- [ ] **Test (`test_encrypt_decrypt_roundtrip`):** encrypt → decrypt a real vector; assert reconstruction within ~`1e-4` (justify tolerance from 50-bit scaling).
- [ ] **Impl:** `encrypt` via `MakeCKKSPackedPlaintext` + `Encrypt`; `decrypt` via `Decrypt` + `SetLength(n)` + `GetRealPackedValue`.
- [ ] → commit: `feat(backend): encrypt/decrypt round-trip`

### 1.5 Homomorphic primitives
- [ ] **Test (`test_eval_add_matches_plaintext`):** `eval_add` vs numpy, level cost 0.
- [ ] **Impl:** `eval_add` (`EvalAdd`).
- [ ] **Test (`test_eval_mult_consumes_one_level`):** `eval_mult` vs numpy, level cost 1.
- [ ] **Impl:** `eval_mult` (`EvalMult` + relinearization).
- [ ] **Test:** `eval_rotate(steps)` cyclically shifts slots; matches numpy roll.
- [ ] **Impl:** `eval_rotate` (`EvalRotate`).
- [ ] → commit: `feat(backend): add/mult/rotate primitives`

### 1.6 Polynomial evaluation primitive
- [ ] **Test:** `eval_chebyshev(coeffs, a, b)` on a ciphertext approximates a known function over `[a,b]` within a documented bound; record measured level cost.
- [ ] **Impl:** `eval_chebyshev` via `EvalChebyshevSeries` / `EvalChebyshevFunction` (Paterson–Stockmeyer internally).
- [ ] → commit: `feat(backend): chebyshev polynomial evaluation`

### 1.7 Bootstrapping primitive (binding only; opt-in)
- [ ] **Impl:** `enable_bootstrap(level_budget)` (`EvalBootstrapSetup` + `EvalBootstrapKeyGen`) and `bootstrap` (`EvalBootstrap`). Not auto-invoked anywhere yet.
- [ ] **Test:** a value survives a `bootstrap` round-trip within tolerance and the level budget is refreshed.
- [ ] → commit: `feat(backend): bootstrapping primitive (opt-in)`

### 1.8 Cross-platform
- [ ] `build-test` green on **macOS** in CI.
- [ ] `build-test` green on **Windows** in CI (expect the most friction; document any required toolchain notes in `docs/getting-started.md`).

### ✅ Phase 1 complete when
- [ ] `tests/test_backend.py` fully green (remove its phase skip).
- [ ] Every primitive within a documented tolerance; level costs recorded.
- [ ] Extension builds on Linux, macOS, and Windows in CI.

---

## Phase 2 — FHE operator library

**Goal:** encrypted linear algebra in `veil/ops/`, orchestrating the Phase-1
primitives. Validated by `tests/test_ops.py` against plaintext equivalents with
bounded error. (`DESIGN.md` §7.) **Python never imports OpenFHE types.**

### 2.1 Slot-layout abstraction (do this first)
- [ ] **Impl:** a slot-layout object describing how a tensor maps onto ciphertext SIMD slots. Route all ops through it so batched packing can be added later without an API break (`DESIGN.md` §8.7).
- [ ] **Test:** layout round-trips a tensor shape → slot indices → tensor shape.
- [ ] → commit: `feat(ops): slot-layout abstraction`

### 2.2 Polynomial activation fitting (`veil/ops/activation.py`)
- [ ] **Test:** `fit_chebyshev(fn, interval, degree)` for GELU (deg ~3), Sigmoid (deg ~7), ReLU (deg 7–15) has max-abs error over the interval within a documented budget; error grows for narrower degree as expected.
- [ ] **Impl:** offline Chebyshev/minimax fit (numpy/scipy), returning coefficients consumed by `backend.eval_chebyshev`.
- [ ] **Test:** `eval_poly` on a ciphertext matches the plaintext activation within tolerance; record level cost (~⌈log₂ d⌉+1).
- [ ] **Impl:** `eval_poly` wiring fit → backend eval.
- [ ] → commit: `feat(ops): polynomial activation fit + eval`

### 2.3 Encrypted matmul (`veil/ops/linear.py`)
- [ ] **Test:** rotation-index set required for an `m×n` matrix is computed correctly (baby-step/giant-step).
- [ ] **Impl:** Halevi–Shoup diagonal encoding; BSGS rotations.
- [ ] **Test (`test_diagonal_matmul_matches_numpy`):** encrypted `W·x` vs numpy within tolerance; level cost 1.
- [ ] **Impl:** `matmul_diagonal` end to end.
- [ ] → commit: `feat(ops): Halevi-Shoup diagonal matmul`

### 2.4 Encrypted convolution (`veil/ops/conv.py`)
- [ ] **Test:** im2col rearrange of a small input matches a reference im2col.
- [ ] **Impl:** `conv2d_im2col` → diagonal matmul.
- [ ] **Test:** encrypted conv vs `torch.nn.functional.conv2d` within tolerance.
- [ ] → commit: `feat(ops): conv2d via im2col`

### 2.5 Elementwise & structural (`veil/ops/elementwise.py`)
- [ ] **Test/Impl:** `add` (ct+ct, level 0), incl. a residual-connection case.
- [ ] **Test/Impl:** plaintext-`mul` (ct×pt, level 1).
- [ ] **Test/Impl:** `reshape`/`flatten` as slot-layout metadata changes (no FHE op).
- [ ] **Test/Impl:** `average_pool` / global average pool via rotate-and-add (+ scale).
- [ ] → commit: `feat(ops): elementwise, reshape, pooling`

### ✅ Phase 2 complete when
- [ ] `tests/test_ops.py` green for every op in `DESIGN.md` §7.1.
- [ ] Each op has a documented error tolerance and recorded level cost.

---

## Phase 3 — ONNX ingestor

**Goal:** parse, simplify, validate, and lower an ONNX model into the internal IR.
Validated by `tests/test_ingest.py`. (`DESIGN.md` §6 Stage B.)

### 3.1 Internal IR (`veil/ir.py`)
- [ ] **Impl:** finalize `Tensor`/`Node`/`Graph` dataclasses (shapes on every edge; initializers as numpy arrays).
- [ ] **Test:** a hand-built `Graph` round-trips its topology and shapes.

### 3.2 Test fixtures (`tests/fixtures/`)
- [ ] **Impl:** a fixture helper that builds and ONNX-exports tiny torch models: a 2-layer MLP (GELU), a 1-conv-layer CNN, plus models containing rejected ops (`MaxPool`, `If`).
- [ ] Commit the generated `.onnx` fixtures (small) or generate them at test time.
- [ ] → commit: `test(ingest): tiny ONNX fixtures`

### 3.3 Simplify + shape inference
- [ ] **Impl:** run `onnxsim` and `onnx.shape_inference` before lowering.
- [ ] **Test:** a model with foldable constants is simplified (node count drops; shapes annotated).

### 3.4 Op-coverage validation + lowering
- [ ] **Test (`test_rejects_maxpool_with_actionable_error`):** first unsupported op raises `UnsupportedOpError` naming the op, the node, and the recommended alternative.
- [ ] **Impl:** validate against `SUPPORTED_OPS` / `REJECTED_OPS`; raise on first miss.
- [ ] **Test (`test_supported_mlp_ingests`):** the tiny MLP and CNN lower to a `Graph` with extracted weights/biases and correct topology.
- [ ] **Impl:** protobuf → IR (nodes, initializers, edges, attributes).
- [ ] → commit: `feat(ingest): ONNX parse, validate, lower to IR`

### ✅ Phase 3 complete when
- [ ] `tests/test_ingest.py` green.
- [ ] Supported tiny models ingest; each rejected op errors with an actionable message.

---

## Phase 4 — Graph transformer

**Goal:** turn the IR into an FHE-ready, parameterized plan. Validated by
`tests/test_transform.py`. (`DESIGN.md` §6 Stage C, §8.1–§8.2.)

### 4.1 BatchNorm folding (`veil/transform.py`)
- [ ] **Test (`test_batchnorm_fold_is_numerically_equivalent`):** folded graph equals the unfused graph in plaintext within fp tolerance.
- [ ] **Impl:** `fold_batchnorm` fuses BN into the preceding Gemm/Conv (plaintext; never a runtime FHE op).
- [ ] → commit: `feat(transform): fold BatchNorm into Gemm/Conv`

### 4.2 Activation rewriting
- [ ] **Test:** `Relu`/`Sigmoid`/`Gelu` nodes become poly-approx nodes carrying coeffs + interval; intervals come from a supplied calibration dict (use synthetic intervals in tests).
- [ ] **Impl:** `rewrite_activations`.
- [ ] → commit: `feat(transform): rewrite activations to polynomial nodes`

### 4.3 Level-budget analysis
- [ ] **Test:** `analyze_level_budget` returns the correct max depth on hand-computed small graphs (incl. a branch + residual).
- [ ] **Impl:** DAG traversal summing per-node level cost over every path.
- [ ] → commit: `feat(transform): level-budget analysis`

### 4.4 Parameter selection + bootstrap planning (`veil/params.py`, `veil/transform.py`)
- [ ] **Test (`test_depth_overflow_raises_at_compile_time`):** depth > profile + `allow_bootstrap=False` → `LevelBudgetError` at compile time.
- [ ] **Impl:** `params_for(profile, required_depth, batch_size)` derives `CKKSParams`, validates against the profile, raises on overflow.
- [ ] **Test:** with `allow_bootstrap="auto"`, bootstraps are planned at budget-exhaustion points (not silently when disabled).
- [ ] **Impl:** `plan_parameters` incl. bootstrap-insertion planning.
- [ ] → commit: `feat(transform): CKKS param derivation + bootstrap planning`

### ✅ Phase 4 complete when
- [ ] `tests/test_transform.py` green.
- [ ] Fold equivalence verified; budget math correct; overflow errors at compile time (never runtime).

---

## Phase 5 — Python API, calibration & persistence

**Goal:** the public 3-line API works end to end. Validated by
`tests/test_models.py`. (`DESIGN.md` §6 Stages A/D/E/F, §9.)

### 5.1 Calibration (`veil/calibration.py`)
- [ ] **Test:** `calibrate` records per-activation (min, max) via forward hooks on the plaintext model; raises `CalibrationError` when required but missing.
- [ ] **Impl:** forward-hook calibration pass returning interval map.
- [ ] → commit: `feat(calibration): plaintext activation-range pass`

### 5.2 ONNX export hardening (`veil/api.py`, Stage A)
- [ ] **Test:** export of a supported tiny model produces a static ONNX graph (opset 17, `dynamic_axes=None`); a model with dynamic control flow raises `ExportError` with a helpful hint.
- [ ] **Impl:** hardened `torch.onnx.export` per `DESIGN.md` §8.4.
- [ ] → commit: `feat(api): hardened ONNX export`

### 5.3 Lowering to an executable model (Stage E, `veil/model.py`)
- [ ] **Impl:** lower the planned graph into ordered operator closures + slot layout + crypto-context spec → `FHEModel`.
- [ ] **Test:** a lowered MLP produces the right op sequence and rotation-index requirements.
- [ ] → commit: `feat(model): lower planned graph to FHEModel`

### 5.4 compile() end to end (`veil/api.py`)
- [ ] **Impl:** wire `compile()`: export → ingest → calibrate → transform → lower → keygen.
- [ ] **Test:** `compile()` on the tiny MLP returns a ready `FHEModel` (keys generated for the required rotation indices).
- [ ] → commit: `feat(api): end-to-end compile pipeline`

### 5.5 encrypt / forward / decrypt (`veil/model.py`)
- [ ] **Impl:** `encrypt` (client; returns `EncryptedTensor` + `ClientContext`), `forward` (server; public eval keys only), `decrypt` (client).
- [ ] **Test:** a static check / unit test that `forward` never references the secret key or `ClientContext`.
- [ ] → commit: `feat(model): encrypt/forward/decrypt`

### 5.6 Out-of-domain handling
- [ ] **Test:** out-of-calibration input is clamped + warns by default; `strict=True` raises `OutOfDomainError`.
- [ ] **Impl:** the warn/clamp/strict policy (`DESIGN.md` §8.5).
- [ ] → commit: `feat(model): out-of-domain warn/clamp/strict`

### 5.7 Persistence
- [ ] **Test:** `save`/`load` round-trips the compiled graph + crypto params; `save_eval_keys` writes keys separately; `bundle=True` writes everything.
- [ ] **Impl:** serialization (OpenFHE serialization for context/keys; graph metadata for the plan). Eval keys separate by default (`DESIGN.md` §8.6).
- [ ] → commit: `feat(model): save/load + separate eval keys`

### 5.8 End-to-end model tests
- [ ] **Test (`test_mnist_mlp_end_to_end_matches_plaintext`, marked `e2e`):** compile → encrypt → forward → decrypt on a tiny MNIST MLP; FHE output ≈ plaintext within a documented accuracy budget.
- [ ] **Test:** the same for a tiny CNN; and GELU vs ReLU variants (document the accuracy/level difference).
- [ ] → commit: `test(models): end-to-end MLP + CNN`

### ✅ Phase 5 complete when
- [ ] `tests/test_models.py` green (remove its phase skip).
- [ ] The 3-line API in `DESIGN.md` §1 works end to end within the documented accuracy budget.

---

## Phase 6 — Benchmarking & hardening → v0.1.0

**Goal:** real, reproducible numbers; docs that match measured reality; first
tagged release. (`DESIGN.md` §13.)

### 6.1 Benchmark harness (`benchmarks/run_benchmarks.py`)
- [ ] **Impl:** measure (separated) compile / keygen / encrypt / **forward** / decrypt latency; throughput; accuracy degradation (top-1 agreement + max/mean abs error) by activation + degree; levels consumed + whether bootstrap fired + its cost; artifact sizes.
- [ ] **Impl:** emit a markdown/CSV report with a hardware header (CPU, RAM, OS, OpenFHE tag, HEXL on/off).
- [ ] → commit: `feat(bench): reproducible benchmark harness`

### 6.2 First real benchmark run
- [ ] Run on stated hardware for MNIST MLP + CNN (GELU and ReLU variants).
- [ ] Commit the generated report under `benchmarks/` (report only, not raw dumps).
- [ ] → commit: `docs(bench): initial benchmark report`

### 6.3 Optional acceleration / depth validation
- [ ] Validate the `VEIL_WITH_HEXL=ON` build path on x86 and note any speedup in the report.
- [ ] Validate the opt-in bootstrapping path on a model deeper than the `DEEP` profile budget.

### 6.4 Docs & honesty pass
- [ ] Fill `docs/benchmarks.md` with the committed numbers; ensure **every** performance/accuracy figure in `README.md` and `docs/` traces to a committed run.
- [ ] Tighten error messages (unsupported op, level overflow, calibration, out-of-domain) for clarity.
- [ ] Flesh out `docs/getting-started.md` with a complete worked example.
- [ ] → commit: `docs: align claims with measured results`

### 6.5 Release v0.1.0
- [ ] Bump version; update `CHANGELOG.md` `[0.1.0]`.
- [ ] Tag `v0.1.0`; confirm the `wheels.yml` release build produces wheels on all three platforms.
- [ ] (Optional) publish to TestPyPI, then PyPI as `veil-fhe`.
- [ ] → commit / tag: `chore(release): v0.1.0`

### ✅ Phase 6 complete when
- [ ] A reproducible benchmark report is committed.
- [ ] Docs are accurate and all claims are sourced.
- [ ] `v0.1.0` is tagged and wheels build on Linux/macOS/Windows.

---

## Cross-cutting / continuous tasks

Keep these true throughout — not a one-time checkbox:

- [ ] `uv.lock` stays in sync with `pyproject.toml` (the `uv-lock` pre-commit hook enforces this).
- [ ] `CHANGELOG.md` updated on every behavior change.
- [ ] `docs/` updated alongside the code it describes.
- [ ] Test coverage maintained or improved per PR.
- [ ] OpenFHE pinned to a released tag; any bump is a dedicated PR that re-runs benchmarks.
- [ ] No novelty/accuracy/security claim without a benchmark or citation.

---

## Deferred — explicitly out of scope for v1

Do **not** start these without sign-off (`DESIGN.md` §14):

- [ ] Batched SIMD inference (N samples per ciphertext).
- [ ] Encrypted weights / both-blind threat model.
- [ ] GPU acceleration.
- [ ] Additional ONNX opsets (11/12/…).
- [ ] Transformer-scale models.
- [ ] CKKS↔TFHE scheme switching for non-smooth functions.
